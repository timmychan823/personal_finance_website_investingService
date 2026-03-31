# Stock Prediction API Endpoints

## Overview
Your Flask application now includes endpoints to retrieve stock price predictions from the LSTM model.

## Endpoints

### 1. Get Latest Prediction for Single Ticker
**GET** `/predictedDailyReturn?ticker={TICKER}`

Retrieves the latest prediction for a specific stock ticker.

#### Parameters
- `ticker` (required): Stock ticker symbol (e.g., TSLA, AAPL, MSFT)

#### Example Request
```bash
curl "http://localhost:5000/predictedDailyReturn?ticker=TSLA"
```

#### Example Response (Success)
```json
{
  "ticker": "TSLA",
  "prediction": 1,
  "prediction_text": "UP",
  "message": "Stock TSLA is predicted to go UP (Stock price expected to go up)"
}
```

#### Example Response (Not Found)
```json
{
  "ticker": "INVALID",
  "prediction": null,
  "message": "No prediction found for this ticker"
}
```

#### Example Response (Error)
```json
{
  "error": "ticker query parameter is required"
}
```

### 2. Get Latest Predictions for Multiple Tickers
**POST** `/predictedDailyReturn/batch`

Retrieves predictions for multiple stock tickers in a single request.

#### Request Body
```json
{
  "tickers": ["TSLA", "AAPL", "MSFT", "GOOGL"]
}
```

#### Example Request
```bash
curl -X POST "http://localhost:5000/predictedDailyReturn/batch" \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["TSLA", "AAPL", "MSFT"]}'
```

#### Example Response
```json
{
  "results": [
    {
      "ticker": "TSLA",
      "prediction": 1,
      "prediction_text": "UP",
      "status": "success"
    },
    {
      "ticker": "AAPL",
      "prediction": 0,
      "prediction_text": "DOWN",
      "status": "success"
    },
    {
      "ticker": "MSFT",
      "prediction": null,
      "prediction_text": null,
      "status": "not_found",
      "message": "No prediction found for this ticker"
    }
  ],
  "total_requested": 3,
  "total_found": 2,
  "total_not_found": 1,
  "total_errors": 0
}
```

## Prediction Values

- **0**: Stock price predicted to go DOWN
- **1**: Stock price predicted to go UP
- **null**: No prediction available for this ticker

## Usage Examples

### JavaScript (Frontend)
```javascript
// Single ticker
fetch('http://localhost:5000/predictedDailyReturn?ticker=TSLA')
  .then(response => response.json())
  .then(data => {
    if (data.prediction !== null) {
      console.log(`${data.ticker}: ${data.prediction_text}`);
    } else {
      console.log(`No prediction found for ${data.ticker}`);
    }
  });

// Multiple tickers
fetch('http://localhost:5000/predictedDailyReturn/batch', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ tickers: ['TSLA', 'AAPL', 'MSFT'] })
})
  .then(response => response.json())
  .then(data => {
    data.results.forEach(result => {
      if (result.status === 'success') {
        console.log(`${result.ticker}: ${result.prediction_text}`);
      }
    });
  });
```

### Python (Testing)
```python
import requests

# Single ticker
response = requests.get('http://localhost:5000/predictedDailyReturn?ticker=TSLA')
print(response.json())

# Multiple tickers
response = requests.post('http://localhost:5000/predictedDailyReturn/batch',
                        json={'tickers': ['TSLA', 'AAPL', 'MSFT']})
print(response.json())
```

## Error Handling

- **400 Bad Request**: Missing or invalid parameters
- **404 Not Found**: Ticker not found in predictions
- **500 Internal Server Error**: Server/database error

## Rate Limiting

- Batch endpoint limited to 50 tickers per request
- Consider implementing rate limiting for production use

## Database

Predictions are stored in the `public."PredictedDailyReturn"` table:
- `ticker`: Stock symbol
- `prediction`: 0 (down) or 1 (up)
- `prediction_date`: Date of prediction
- `created_at`: Timestamp when stored

## Integration with LSTM Predictor

To generate new predictions, use the LSTM prediction scripts:

```bash
# Generate predictions for all tickers and save to database
python lstm_predictor_util.py --all --save

# Generate prediction for specific ticker
python lstm_predictor_util.py --tickers TSLA --save
```

The API endpoints will then return these stored predictions.