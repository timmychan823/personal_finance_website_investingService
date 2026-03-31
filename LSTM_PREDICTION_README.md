# LSTM Stock Price Prediction System

This system uses your trained LSTM model (`fypLSTM.h5`) to predict whether stocks will go up or down in the next trading day based on the last 30 trading days of historical data.

## Overview

The prediction system consists of three main components:

1. **lstm_stock_predictor.py** - Core prediction engine
2. **lstm_predictor_util.py** - Command-line utility for easy prediction execution
3. **src/service/LSTMPredictionService.py** - Flask service integration

## Features

- ✅ Retrieves stock data from Yahoo Finance (yfinance)
- ✅ Calculates 7 technical indicators (Daily Return, Volume Change, RSI, Bollinger Bands, MACD, S&P 500 metrics)
- ✅ Uses trained LSTM neural network for predictions
- ✅ Binary classification: UP (1) or DOWN (0)
- ✅ Confidence scores for predictions
- ✅ Database integration with PostgreSQL
- ✅ Batch predictions for multiple tickers
- ✅ Save predictions to database
- ✅ Export results to JSON

## Installation & Setup

### 1. Verify Required Dependencies

Ensure all required packages are installed:

```bash
pip install -r requirements.txt
```

Key packages needed:
- `tensorflow` - For LSTM model loading
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `yfinance` - Stock data retrieval
- `ta` - Technical analysis indicators
- `psycopg2` - PostgreSQL connection
- `scikit-learn` - For preprocessing utilities

### 2. Model File Location

Ensure the LSTM model is in the correct location:
```
lstmModel/fypLSTM.h5
```

### 3. Database Configuration

Update database connection details in `src/constant/Db_constants.py` if needed:

```python
DB_USER = 'personalFinanceWebsiteAdmin'
DB_PW = 'personalFinanceWebsiteAdmin'
DB_HOST = 'localhost'  # or 'appPostgres' in Docker
DB_PORT = '5432'
DB_NAME = 'NewsSummaryDB'
```

## Usage

### Method 1: Command-Line Utility (Recommended for Manual Execution)

#### Predict for all tickers in database:

```bash
python lstm_predictor_util.py --all
```

#### Predict for specific tickers:

```bash
python lstm_predictor_util.py --tickers TSLA AAPL MSFT
```

#### Predict and save to database:

```bash
python lstm_predictor_util.py --all --save
```

#### Predict with verbose output:

```bash
python lstm_predictor_util.py --all --verbose
```

#### Predict and export to JSON:

```bash
python lstm_predictor_util.py --all --export predictions_results.json
```

#### Predict with custom model path:

```bash
python lstm_predictor_util.py --all --model ./path/to/model.h5
```

### Method 2: Direct Script Execution (Automated)

For automated execution or scheduling:

```bash
python lstm_stock_predictor.py
```

This will:
1. Load all tickers from database
2. Make predictions for each ticker
3. Save successful predictions to database
4. Display summary statistics

### Method 3: Flask Integration

Integrate into your Flask app (`app.py`):

```python
from src.service.LSTMPredictionService import LSTMPredictionService, PredictionManager

# Initialize service
lstm_service = LSTMPredictionService(predictionDAO)

# Make single prediction
result = lstm_service.predictStockMovement('TSLA')

# Make and save prediction
result = lstm_service.predictAndSave('TSLA')

# Batch predictions for all tickers
manager = PredictionManager(predictionDAO)
results = manager.predictAllTickers()
```

#### Example Flask Endpoint:

```python
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    ticker = data.get('ticker')
    save = data.get('save', False)
    
    if save:
        result = lstm_service.predictAndSave(ticker)
    else:
        result = lstm_service.predictStockMovement(ticker)
    
    return jsonify(result)

@app.route('/predict-all', methods=['POST'])
def predict_all():
    manager = PredictionManager(predictionDAO)
    results = manager.predictAllTickers()
    return jsonify(results)
```

## Output Format

### Prediction Result

```json
{
  "ticker": "TSLA",
  "prediction": 1,
  "confidence": 0.85,
  "status": "success",
  "message": "Prediction: Stock will GO UP with 85.00% confidence",
  "prediction_date": "2026-03-28"
}
```

### Command-Line Output

```
================================================================================
STOCK PRICE PREDICTION RESULTS
================================================================================

✓ SUCCESSFUL PREDICTIONS (3/3)
--------------------------------------------------------------------------------
Ticker     Prediction      Confidence     Date
--------------------------------------------------------------------------------
TSLA       UP ↑            85.23%         2026-03-28
AAPL       DOWN ↓          72.45%         2026-03-28
MSFT       UP ↑            88.91%         2026-03-28

================================================================================
SUMMARY
================================================================================
Total Predictions:     3
Successful:            3 (100.0%)
Failed:                0
Average Confidence:    82.20%
Predicted UP ↑:        2
Predicted DOWN ↓:      1
================================================================================
```

## Technical Details

### Model Architecture

- **Type**: LSTM (Long Short-Term Memory) Neural Network
- **Input**: 10 previous trading days
- **Features**: 7 technical indicators
- **Output**: Binary classification (0 = down, 1 = up)
- **Training Data**: Historical data from 2016-06-15 to 2024-02-01
- **Testing Data**: Data from 2024-02-01 to 2026-01-09

### Features Used

1. **Daily Return** - Percentage change in closing price
2. **Daily Volume Change** - Percentage change in trading volume
3. **S&P 500 Daily Return** - Market benchmark daily return
4. **S&P 500 Daily Volume Change** - Market benchmark volume change
5. **RSI (Relative Strength Index)** - Momentum indicator (14-period)
6. **mband (Bollinger Bands Middle Band)** - Volatility indicator
7. **MACD (Moving Average Convergence Divergence)** - Trend indicator

### Data Preprocessing

- **Lookback Period**: 10 trading days
- **Normalization**: Z-score normalization using the last 10 days
- **Missing Values**: Forward-fill then backward-fill
- **Alignment**: All data aligned by trading date

## Database Integration

### Prediction Storage

Predictions are saved to the database table (you may need to create this):

```sql
CREATE TABLE IF NOT EXISTS public."Predictions" (
    ticker TEXT NOT NULL,
    prediction INTEGER NOT NULL,
    prediction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, prediction_date)
);
```

### Query Examples

```sql
-- Get latest predictions
SELECT ticker, prediction, prediction_date 
FROM public."Predictions"
WHERE prediction_date = CURRENT_DATE
ORDER BY ticker;

-- Get prediction accuracy (if actual price data available)
SELECT ticker, COUNT(*) as total_predictions,
       SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as up_predictions,
       SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as down_predictions
FROM public."Predictions"
GROUP BY ticker;
```

## Error Handling

The system handles various error scenarios:

- **Missing Model**: Error if model file not found
- **Database Connection**: Error if database unavailable
- **Invalid Ticker**: Skips ticker and logs error
- **Insufficient Data**: Warns if less than 30 days of data
- **API Limits**: Handles yfinance rate limits gracefully

All errors are logged with timestamps and detailed messages.

## Performance Considerations

- **Speed**: Average ~5-10 seconds per ticker (includes data retrieval and prediction)
- **Memory**: Moderate memory usage (~500MB for batch predictions)
- **Network**: Requires internet connection for yfinance
- **Disk**: Model file is ~50MB

## Scheduling

### Windows Task Scheduler

Create scheduled task to run daily:

```batch
cd C:\Users\User\Desktop\Projects\fyp\backend\investingService
venv\Scripts\activate.ps1
python lstm_predictor_util.py --all --save
```

### Linux/Mac Cron

```bash
# Run daily at 4:00 PM
0 16 * * * cd /path/to/investingService && python lstm_predictor_util.py --all --save
```

## Troubleshooting

### Issue: "Model file not found"

```
Solution: Verify model path is correct and file exists
python lstm_predictor_util.py --model ./lstmModel/fypLSTM.h5 --all
```

### Issue: "Database connection failed"

```
Solution: Check database credentials and server status
- Verify credentials in src/constant/Db_constants.py
- Test: psql -U personalFinanceWebsiteAdmin -d NewsSummaryDB
```

### Issue: "No data retrieved for ticker"

```
Solution: Check if ticker is valid on Yahoo Finance
- Verify ticker exists on yfinance
- Some tickers may have different symbols
```

### Issue: "Insufficient data"

```
Solution: Some stocks may not have 30 days of recent data
- The system requires at least 10 days of data
- Stocks with gaps in trading data may fail
```

## Logging

Logs are printed to console with timestamps. To save logs to file:

```python
# In the script, modify logging setup:
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('predictions.log'),
        logging.StreamHandler()
    ]
)
```

## Future Improvements

- [ ] Add confidence threshold filtering
- [ ] Implement model retraining pipeline
- [ ] Add prediction accuracy tracking
- [ ] Support for ensemble predictions
- [ ] Real-time prediction updates
- [ ] Web dashboard for results
- [ ] Automated buy/sell signals
- [ ] Portfolio-level analysis

## License

Same as main project

## Support

For issues or questions, refer to:
- Original training notebook: `lstmModel/fyp_lstm.ipynb`
- Database schema: `usefulSQL.sql`
- Flask app integration: `app.py`
