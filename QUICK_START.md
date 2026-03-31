# LSTM Stock Predictor - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### 2. Validate Setup
```bash
python test_lstm_setup.py
```

Expected output: All checks should show ✓

### 3. Test with Single Ticker
```bash
python lstm_predictor_util.py --tickers TSLA
```

### 4. Predict for all Tickers
```bash
python lstm_predictor_util.py --all
```

### 5. Save Predictions to Database
```bash
python lstm_predictor_util.py --all --save
```

## Common Commands

### Get predictions for specific stocks
```bash
python lstm_predictor_util.py --tickers TSLA AAPL MSFT
```

### Get detailed output
```bash
python lstm_predictor_util.py --all --verbose
```

### Export results to JSON
```bash
python lstm_predictor_util.py --all --export predictions.json
```

### Use custom model
```bash
python lstm_predictor_util.py --all --model ./path/to/model.h5
```

### Run standalone (auto-save)
```bash
python lstm_stock_predictor.py
```

## Understanding Output

```
TSLA       UP ↑            85.23%         2026-03-28
```

- **TSLA**: Stock symbol
- **UP ↑**: Prediction (UP means stock price will increase)
- **85.23%**: Confidence score (higher = more confident)
- **2026-03-28**: Prediction date

## What Each Script Does

| Script | What it does | When to use |
|--------|-------------|-----------|
| **test_lstm_setup.py** | Checks if everything is installed | First time setup |
| **lstm_predictor_util.py** | CLI tool with nice output | Manual predictions |
| **lstm_stock_predictor.py** | Core prediction engine | Automation/scheduling |
| **LSTMPredictionService.py** | Flask integration | API endpoints |

## Troubleshooting Quick Fixes

### "Model file not found"
Check file exists: `lstmModel/fypLSTM.h5` ✓

### "Database connection failed"
Verify PostgreSQL is running and check `src/constant/Db_constants.py`

### "No data retrieved for ticker"
The ticker may be invalid or have no recent data. Try another ticker.

### "Module not found"
Install missing packages:
```bash
pip install -r requirements.txt
```

## Use in Python Code

### Simple prediction
```python
from lstm_stock_predictor import LSTMStockPredictor

predictor = LSTMStockPredictor('./lstmModel/fypLSTM.h5')
result = predictor.predict('TSLA')

print(f"Prediction: {result['prediction']}")  # 0 = down, 1 = up
print(f"Confidence: {result['confidence']:.2%}")
```

### Batch predictions
```python
tickers = ['TSLA', 'AAPL', 'MSFT']
results = predictor.predict_batch(tickers)

for result in results:
    print(f"{result['ticker']}: {result['message']}")
```

### With Flask
```python
from src.service.LSTMPredictionService import LSTMPredictionService

lstm_service = LSTMPredictionService(predictionDAO)
result = lstm_service.predictAndSave('TSLA')
```

## Schedule Daily Predictions

### Windows (Task Scheduler)
```batch
@echo off
cd C:\Users\User\Desktop\Projects\fyp\backend\investingService
call venv\Scripts\activate.ps1
python lstm_predictor_util.py --all --save
```

### Linux/Mac (Cron)
```bash
# Run daily at 4 PM
0 16 * * * cd /path/to/investingService && python lstm_predictor_util.py --all --save
```

## Expected Time

- Single ticker: 5-10 seconds
- 10 tickers: 50-100 seconds
- 100 tickers: 8-15 minutes

## What's Happening

1. **Gets data** - Downloads 60 days of stock prices from Yahoo Finance
2. **Calculates indicators** - RSI, Bollinger Bands, MACD, etc.
3. **Normalizes** - Scales features for LSTM
4. **Predicts** - Runs through trained LSTM model
5. **Saves** - Stores prediction in database (if requested)

## Model Details

- **Type**: LSTM Neural Network
- **Input**: 10 days of 7 technical indicators
- **Output**: Stock goes UP (1) or DOWN (0)
- **Training**: 2016-2024 historical data
- **File**: fypLSTM.h5 (~50MB)

## Next Steps

1. ✅ Run `python test_lstm_setup.py`
2. ✅ Try `python lstm_predictor_util.py --tickers TSLA`
3. ✅ Run full predictions with `python lstm_predictor_util.py --all`
4. ✅ Schedule with Task Scheduler or Cron
5. ✅ Integrate with Flask (see LSTM_PREDICTION_README.md)

## More Help

- **Full Documentation**: See LSTM_PREDICTION_README.md
- **Implementation Details**: See IMPLEMENTATION_SUMMARY.md
- **Troubleshooting**: See LSTM_PREDICTION_README.md#Troubleshooting

---

That's it! You're ready to predict stock movements. 🚀
