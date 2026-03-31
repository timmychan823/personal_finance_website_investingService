"""
LSTM Prediction Service Integration with Flask

This module provides integration of the LSTM stock predictor with the Flask application.
It can be used to add API endpoints for making predictions on demand.
"""

from lstm_stock_predictor import LSTMStockPredictor, DatabaseManager
from src.service.PredictionService import PredictionService
import logging

logger = logging.getLogger(__name__)


class LSTMPredictionService(PredictionService):
    """
    Service class that extends PredictionService with LSTM-based predictions
    """
    
    def __init__(self, prediction_dao, model_path: str = './lstmModel/fypLSTM.h5'):
        """
        Initialize LSTM Prediction Service
        
        Args:
            prediction_dao: Data Access Object for predictions
            model_path: Path to the trained LSTM model
        """
        self.predictionDAO = prediction_dao
        self.model_path = model_path
        
        try:
            self.lstm_predictor = LSTMStockPredictor(model_path)
            logger.info(f"LSTM model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to initialize LSTM predictor: {str(e)}")
            self.lstm_predictor = None
    
    def getLatestPrediction(self, ticker: str):
        """
        Get latest prediction for a ticker from database
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Prediction value (0 or 1) or None
        """
        return self.predictionDAO.getLatestPrediction(ticker)
    
    def savePrediction(self, ticker: str, prediction: int, prediction_date) -> None:
        """
        Save prediction to database
        
        Args:
            ticker: Stock ticker symbol
            prediction: Prediction value (0 or 1)
            prediction_date: Date of prediction
        """
        self.predictionDAO.savePrediction(ticker, prediction, prediction_date)
    
    def predictStockMovement(self, ticker: str) -> dict:
        """
        Predict stock movement for a ticker using LSTM model
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with prediction results containing:
            - prediction: 0 (down) or 1 (up)
            - confidence: Confidence score (0-1)
            - message: Human-readable message
            - status: 'success' or 'failed'
        """
        if self.lstm_predictor is None:
            return {
                'ticker': ticker,
                'prediction': None,
                'confidence': None,
                'status': 'failed',
                'message': 'LSTM model not initialized'
            }
        
        return self.lstm_predictor.predict(ticker)
    
    def predictBatch(self, tickers: list) -> list:
        """
        Predict stock movements for multiple tickers
        
        Args:
            tickers: List of stock ticker symbols
        
        Returns:
            List of prediction result dictionaries
        """
        if self.lstm_predictor is None:
            return [{
                'ticker': t,
                'prediction': None,
                'confidence': None,
                'status': 'failed',
                'message': 'LSTM model not initialized'
            } for t in tickers]
        
        return self.lstm_predictor.predict_batch(tickers)
    
    def predictAndSave(self, ticker: str) -> dict:
        """
        Make prediction and save to database
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with prediction results
        """
        result = self.predictStockMovement(ticker)
        
        if result['status'] == 'success':
            try:
                self.savePrediction(
                    result['ticker'],
                    result['prediction'],
                    result['prediction_date']
                )
                result['saved'] = True
                logger.info(f"Prediction saved for {ticker}")
            except Exception as e:
                result['saved'] = False
                logger.error(f"Failed to save prediction for {ticker}: {str(e)}")
        
        return result


class PredictionManager:
    """
    Manager class for handling both database and LSTM predictions
    """
    
    def __init__(self, prediction_dao, model_path: str = './lstmModel/fypLSTM.h5'):
        """
        Initialize Prediction Manager
        
        Args:
            prediction_dao: Data Access Object for predictions
            model_path: Path to the trained LSTM model
        """
        self.lstm_service = LSTMPredictionService(prediction_dao, model_path)
        self.db_manager = None
    
    def predictAllTickers(self) -> list:
        """
        Predict for all tickers in database
        
        Returns:
            List of prediction results
        """
        try:
            self.db_manager = DatabaseManager()
            tickers = self.db_manager.get_all_tickers()
            
            results = self.lstm_service.predictBatch(tickers)
            
            # Save successful predictions
            saved_count = 0
            for result in results:
                if result['status'] == 'success':
                    try:
                        self.lstm_service.savePrediction(
                            result['ticker'],
                            result['prediction'],
                            result['prediction_date']
                        )
                        saved_count += 1
                    except Exception as e:
                        logger.error(f"Failed to save prediction for {result['ticker']}: {str(e)}")
            
            logger.info(f"Predictions completed. Saved {saved_count}/{len(results)}")
            return results
        
        except Exception as e:
            logger.error(f"Error predicting all tickers: {str(e)}")
            return []
        
        finally:
            if self.db_manager:
                self.db_manager.close()
    
    def close(self):
        """Close all connections"""
        if self.db_manager:
            self.db_manager.close()
