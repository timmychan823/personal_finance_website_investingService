"""
LSTM Stock Price Prediction Script

This script retrieves stock data for all tickers stored in the public."Companies" table,
calculates technical indicators, and uses the trained LSTM model to predict whether
the stock price will go up or down in the next trading day.
"""

import psycopg2
import numpy as np
import pandas as pd
import yfinance as yf
import ta
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib
import logging
import sys

# Import database constants
from src.constant.Db_constants import DB_USER, DB_PW, DB_HOST, DB_HOST_OUT_DOCKER, DB_PORT, DB_NAME, COMPANY_TABLE_NAME
from src.dao.PredictionDAOImpl import PredictionDAOImpl
from src.service.PredictionServiceImpl import PredictionServiceImpl

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LSTMStockPredictor:
    """
    Predictor class for stock price movements using LSTM model
    """
    
    def __init__(self, model_path: str, input_scaler_path: str = './lstmModel/inputScaler.joblib'):
        """
        Initialize the LSTM predictor with a trained model and scalers
        
        Args:
            model_path: Path to the trained LSTM model (h5 file)
            input_scaler_path: Path to input scaler joblib file
        """
        try:
            self.model = load_model(model_path)
            logger.info(f"Model loaded successfully from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {str(e)}")
            raise

        # Load scalers
        self.input_scaler = None
        try:
            self.input_scaler = joblib.load(input_scaler_path)
            logger.info(f"Input scaler loaded successfully from {input_scaler_path}")
        except Exception as e:
            logger.warning(f"Failed to load input scaler from {input_scaler_path}: {str(e)}")
        
        # Configuration from training
        self.lookback_period = 10  # Model expects 10 days of historical data
        self.input_features = [
            'Daily Return',
            'Daily Volume Change',
            'S&P 500 Daily Return',
            'S&P 500 Daily Volume Change',
            'RSI',
            'mband',
            'MACD'
        ]
    
    def get_stock_data(self, ticker: str, days: int = 60) -> pd.DataFrame:
        """
        Fetch historical stock data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            days: Number of trading days of history to fetch
        
        Returns:
            DataFrame with stock data
        """
        try:
            logger.info(f"Fetching stock data for {ticker}...")
            dat = yf.Ticker(ticker)
            data = dat.history(period=f"{days}d")
            if data.empty:
                logger.warning(f"No data retrieved for {ticker}")
                return None
            
            logger.info(f"Retrieved {len(data)} trading days for {ticker}")
            return data
        
        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {str(e)}")
            return None
    
    def get_sp500_data(self, days: int = 60) -> pd.DataFrame:
        """
        Fetch historical S&P 500 data for comparison
        
        Args:
            days: Number of trading days of history to fetch
        
        Returns:
            DataFrame with S&P 500 data
        """
        try:
            logger.info("Fetching S&P 500 data...")
            ticker = "^GSPC"
            dat = yf.Ticker(ticker)
            sp500_data = dat.history(period=f"{days}d")

            if sp500_data.empty:
                logger.warning("No S&P 500 data retrieved")
                return None
            
            logger.info(f"Retrieved {len(sp500_data)} trading days for S&P 500")
            return sp500_data
        
        except Exception as e:
            logger.error(f"Error fetching S&P 500 data: {str(e)}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the stock data
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with calculated indicators
        """
        try:
            # Calculate daily returns and volume change
            ta_indicator_applier = ta.add_all_ta_features(
                df,
                open="Open",
                high="High",
                low="Low",
                close="Close",
                volume="Volume",
                fillna=True
            )
            df['Daily Return'] = df['Close'].pct_change()
            df['Daily Volume Change'] = df['Volume'].pct_change()
            # RSI (Relative Strength Index)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14) / 100
            # Bollinger Bands - using middle band normalized
            bb = ta.volatility.BollingerBands(close=df["Close"], window=20, window_dev=2)
            df['mband'] = (bb.bollinger_mavg() - df['Close']) / df['Close']
            # MACD (Moving Average Convergence Divergence)
            df['MACD'] = ta.trend.MACD(df['Close'], window_slow = 26, window_fast = 12, window_sign = 9).macd()/df['Close']
            # Fill NaN values with forward fill then backward fill
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            logger.info("Technical indicators calculated successfully")
            return df
        
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return None
    
    def prepare_features(self, stock_data: pd.DataFrame, sp500_data: pd.DataFrame) -> tuple:
        """
        Prepare feature matrix for LSTM prediction
        
        Args:
            stock_data: DataFrame with stock data and technical indicators
            sp500_data: DataFrame with S&P 500 data
        
        Returns:
            Tuple of (features_array, prepared_dataframe)
        """
        try:
            # Align dates between stock and S&P 500 data
            stock_data = stock_data.copy()
            sp500_data = sp500_data.copy()
            
            # Calculate S&P 500 indicators
            sp500_data['S&P 500 Daily Return'] = sp500_data['Close'].pct_change()
            sp500_data['S&P 500 Daily Volume Change'] = sp500_data['Volume'].pct_change()
            
            # Merge on date
            merged_data = stock_data.join(
                sp500_data[['S&P 500 Daily Return', 'S&P 500 Daily Volume Change']],
                how='inner'
            )
            
            # Fill any remaining NaN values
            merged_data = merged_data.fillna(method='ffill').fillna(method='bfill')
            
            # Ensure we have all required features
            for feature in self.input_features:
                if feature not in merged_data.columns:
                    logger.warning(f"Missing feature: {feature}")
                    return None, None
            
            # Extract feature matrix
            feature_data = merged_data[self.input_features].values
            
            # Ensure we have enough data for lookback period
            if len(feature_data) < self.lookback_period:
                logger.warning(f"Insufficient data. Need {self.lookback_period} days, got {len(feature_data)}")
                return None, None
            
            # Scale/normalize features using the loaded input scaler, fallback to z-score if not available
            if self.input_scaler is not None:
                scaled_features = self.input_scaler.transform(feature_data)
                logger.info("Feature data scaled via inputScaler")
            else:
                raise Exception("Input scaling failed")
            
            # Prepare lookback sequence
            X = scaled_features[-self.lookback_period:].reshape(1, self.lookback_period, len(self.input_features))
            
            logger.info(f"Features prepared successfully. Shape: {X.shape}")
            return X, merged_data
        
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            return None, None
    
    def predict(self, ticker: str) -> dict:
        """
        Make prediction for a single ticker
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with prediction results
        """
        result = {
            'ticker': ticker,
            'prediction': None,
            'confidence': None,
            'status': 'pending',
            'message': ''
        }
        
        try:
            # Get stock data
            stock_data = self.get_stock_data(ticker, days=60)
            if stock_data is None or stock_data.empty:
                result['status'] = 'failed'
                result['message'] = f"Failed to retrieve stock data for {ticker}"
                return result
            
            # Get S&P 500 data
            sp500_data = self.get_sp500_data(days=60)
            if sp500_data is None or sp500_data.empty:
                result['status'] = 'failed'
                result['message'] = f"Failed to retrieve S&P 500 data"
                return result
            
            # Calculate technical indicators
            stock_data = self.calculate_technical_indicators(stock_data)
            if stock_data is None:
                result['status'] = 'failed'
                result['message'] = "Failed to calculate technical indicators"
                return result
            
            # Prepare features
            X, prepared_data = self.prepare_features(stock_data, sp500_data)
            if X is None:
                result['status'] = 'failed'
                result['message'] = "Failed to prepare features for prediction"
                return result
            
            # Make prediction
            prediction_prob = self.model.predict(X, verbose=0)
            logger.info(f"Predicted_prob: {prediction_prob}") #TODO: remove after debugging
            raw_prob = float(prediction_prob[0][0])
            predicted_value = raw_prob

            # Determine up/down prediction
            direction = 1 if predicted_value >= 0.5 else 0

            confidence = raw_prob if direction == 1 else (1 - raw_prob)

            result['status'] = 'success'
            result['prediction'] = direction  # 1 = stock goes up, 0 = stock goes down
            result['confidence'] = confidence
            result['predicted_value'] = predicted_value
            result['message'] = (
                f"Prediction: Stock will {'GO UP' if direction == 1 else 'GO DOWN'} "
                f"(model output {raw_prob:.4f}, transformed {predicted_value:.4f}) with {confidence:.2%} confidence"
            )
            result['prediction_date'] = datetime.now().date()
            
            logger.info(f"{ticker}: {result['message']}")
            return result
        
        except Exception as e:
            result['status'] = 'failed'
            result['message'] = f"Error during prediction: {str(e)}"
            logger.error(result['message'])
            return result
    
    def predict_batch(self, tickers: list) -> list:
        """
        Make predictions for multiple tickers
        
        Args:
            tickers: List of stock ticker symbols
        
        Returns:
            List of prediction results
        """
        results = []
        for ticker in tickers:
            result = self.predict(ticker)
            results.append(result)
        return results


class DatabaseManager:
    """
    Manager class for database operations
    """
    
    def __init__(self):
        """Initialize database connection"""
        try:
            pg_connection_dict = {
                'dbname': DB_NAME,
                'user': DB_USER,
                'password': DB_PW,
                'port': DB_PORT,
                'host': DB_HOST_OUT_DOCKER
            }
            self.conn = psycopg2.connect(**pg_connection_dict)
            self.prediction_dao = PredictionDAOImpl(self.conn)
            self.prediction_service = PredictionServiceImpl(self.prediction_dao)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def get_all_tickers(self) -> list:
        """
        Retrieve all tickers from Companies table
        
        Returns:
            List of ticker strings
        """
        try:
            with self.conn.cursor() as curs:
                query = f'SELECT ticker FROM public."{COMPANY_TABLE_NAME}"'
                curs.execute(query)
                records = curs.fetchall()
                tickers = [record[0] for record in records]
                logger.info(f"Retrieved {len(tickers)} tickers from database: {tickers}")
                return tickers
        
        except Exception as e:
            logger.error(f"Error retrieving tickers from database: {str(e)}")
            return []
    
    def save_prediction(self, ticker: str, prediction: int, prediction_date) -> bool:
        """
        Save prediction to database
        
        Args:
            ticker: Stock ticker symbol
            prediction: Prediction value (0 or 1)
            prediction_date: Date of prediction
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.prediction_service.savePrediction(ticker, prediction, prediction_date)
            logger.info(f"Saved prediction for {ticker}: {prediction}")
            return True
        except Exception as e:
            logger.error(f"Error saving prediction for {ticker}: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        try:
            self.conn.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")


def main():
    """
    Main function to run stock predictions
    """
    model_path = './lstmModel/fypLSTM.h5'
    
    try:
        # Initialize predictor and database manager
        predictor = LSTMStockPredictor(model_path)
        db_manager = DatabaseManager()
        
        # Get all tickers from database
        tickers = db_manager.get_all_tickers()
        
        if not tickers:
            logger.warning("No tickers found in database")
            db_manager.close()
            return
        
        # Make predictions for all tickers
        logger.info(f"Making predictions for {len(tickers)} tickers...")
        results = predictor.predict_batch(tickers)
        
        # Save successful predictions to database
        saved_count = 0
        for result in results:
            if result['status'] == 'success':
                if db_manager.save_prediction(
                    result['ticker'],
                    result['prediction'],
                    result['prediction_date']
                ):
                    saved_count += 1
        
        # Print summary
        logger.info("=" * 60)
        logger.info("PREDICTION SUMMARY")
        logger.info("=" * 60)
        
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')
        
        logger.info(f"Total predictions: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Saved to database: {saved_count}")
        logger.info("=" * 60)
        
        # Print detailed results
        for result in results:
            logger.info(f"\n{result['ticker']}: {result['message']}")
        
        # Close database connection
        db_manager.close()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
