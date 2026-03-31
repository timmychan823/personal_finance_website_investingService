import psycopg2
from src.constant.Db_constants import * 
from src.dao.NewsDAOImpl import NewsDAOImpl
from src.service.NewsServiceImpl import NewServiceImpl
from src.service.DataReleaseImpl import DataReleaseServiceImpl
from src.dao.PredictionDAOImpl import PredictionDAOImpl
from src.service.PredictionServiceImpl import PredictionServiceImpl
from flask import Flask, request, render_template
from flask_cors import CORS
import requests
import logging
import json
import sys
import optparse
import time
from finbert.finbert import predict
from pytorch_pretrained_bert.modeling import BertForSequenceClassification
import nltk
import os
from flask import jsonify

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') #change this to DEBUG mode for debugging
nltk.download('punkt')
nltk.download('punkt_tab')
app = Flask(__name__)
cors = CORS(app)
start = int(round(time.time()))
model = BertForSequenceClassification.from_pretrained('./model/', num_labels=3, cache_dir=None)

pg_connection_dict = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PW,
    'port': DB_PORT,
    'host': DB_HOST
}
con = psycopg2.connect(**pg_connection_dict)
newsDAO = NewsDAOImpl(con)
newServiceImpl = NewServiceImpl(newsDAO)
dataReleaseServiceImpl = DataReleaseServiceImpl()
predictionDAO = PredictionDAOImpl(con)
predictionService = PredictionServiceImpl(predictionDAO)

@app.route('/listOfNews', methods = ['GET'])
def list_of_news():
    if request.method == 'GET':
        if request.args.get('tickers')=='all':
            tickers='all'
        else:
            tickers = request.args.getlist('tickers')
        try:
            limit = min(int(request.args.get('limit')), 50) 
        except Exception as e:
            limit = 10
        try:
            pageNumber = max(int(request.args.get('pageNumber'))-1, 0)
        except Exception as e:
            pageNumber = 0
        offset = pageNumber*limit
        
        logger.info(f"tickers: {tickers}, limit: {limit}, offset: {offset}")
        list_of_news = (newServiceImpl.getListOfNews(tickers, limit, offset))
        return list_of_news 

@app.route('/listOfUniqueCompanies', methods = ['GET'])
def list_of_unique_companies():
    if request.method == "GET":
        list_of_unique_companies = (newServiceImpl.getListOfUniqueTickers())
        return list_of_unique_companies
    
@app.route('/listOfCompanies', methods = ['POST'])
def list_of_companies():
    if request.method == "POST":
        try:
            data = request.get_json()
            list_of_sub_industries = data.get('subIndustries', [])
            search_query = data.get('searchQuery', '')
            try:
                limit = min(int(data.get('limit', 10)), 50)
            except Exception as e:
                limit = 10
            try:
                pageNumber = max(int(data.get('pageNumber', 1)) - 1, 0)
            except Exception as e:
                pageNumber = 0
            offset = pageNumber * limit
            
            logger.info(f"list_of_sub_industries: {list_of_sub_industries}, search_query: {search_query}, limit: {limit}, offset: {offset}")
            list_of_companies = newServiceImpl.getListOfCompaniesBySubIndustries(list_of_sub_industries=list_of_sub_industries, search_query=search_query, limit=limit, offset=offset)
            return list_of_companies
        except Exception as e:
            logger.error(f"Error processing POST request: {str(e)}")
            return {'error': str(e)}, 400
    
@app.route('/dataReleases', methods = ['GET'])
async def list_of_releases():
    if request.method == 'GET':
        out = await dataReleaseServiceImpl.getDataRelease()
        return out
    
##TODO: add getAllSubIndustriesAndSectors
@app.route("/listOfSectorsAndSubIndustries",methods=['GET'])
def list_of_sectors_and_sub_industries():
    if request.method == "GET":
        list_of_sectors_and_sub_industries = {'subIndustriesBySector':newServiceImpl.getAllSectorsAndSubIndustries()}
        return list_of_sectors_and_sub_industries

@app.route("/sentimentAnalysis",methods=['POST'])
def score():
    text=request.get_json()['text']
    return(predict(text, model).to_json(orient='records'))


@app.route('/predictedDailyReturn', methods=['GET'])
def predicted_daily_return():
    if request.method == 'GET':
        ticker = request.args.get('ticker')
        if not ticker:
            return {'error': 'ticker query parameter is required'}, 400
        try:
            prediction_data = predictionService.getLatestPrediction(ticker)
            if prediction_data is None:
                return {'ticker': ticker, 'prediction': None, 'prediction_date': None, 'message': 'No prediction found for this ticker'}, 404

            prediction = prediction_data.get('prediction')
            prediction_date = prediction_data.get('prediction_date')
            prediction_text = 'UP' if prediction == 1 else 'DOWN'
            confidence_note = ' (Stock price expected to go up)' if prediction == 1 else ' (Stock price expected to go down)'

            return {
                'ticker': ticker,
                'prediction': int(prediction),
                'prediction_date': prediction_date.isoformat() if prediction_date else None,
                'prediction_text': prediction_text,
                'message': f'Stock {ticker} is predicted to go {prediction_text}{confidence_note}'
            }
        except Exception as e:
            logger.error(f"Error fetching prediction for {ticker}: {str(e)}")
            return {'error': str(e)}, 500

@app.route('/predictedDailyReturn/batch', methods=['POST'])
def predicted_daily_return_batch():
    if request.method == 'POST':
        try:
            data = request.get_json()
            tickers = data.get('tickers', [])
            
            if not tickers:
                return {'error': 'tickers list is required in request body'}, 400
            
            if not isinstance(tickers, list):
                return {'error': 'tickers must be a list'}, 400
            
            if len(tickers) > 50:  # Limit batch size
                return {'error': 'Maximum 50 tickers allowed per request'}, 400
            
            results = []
            for ticker in tickers:
                try:
                    prediction_data = predictionService.getLatestPrediction(ticker)
                    if prediction_data is not None:
                        prediction = prediction_data.get('prediction')
                        prediction_date = prediction_data.get('prediction_date')
                        prediction_text = 'UP' if prediction == 1 else 'DOWN'
                        results.append({
                            'ticker': ticker,
                            'prediction': int(prediction),
                            'prediction_date': prediction_date.isoformat() if prediction_date else None,
                            'prediction_text': prediction_text,
                            'status': 'success'
                        })
                    else:
                        results.append({
                            'ticker': ticker,
                            'prediction': None,
                            'prediction_date': None,
                            'prediction_text': None,
                            'status': 'not_found',
                            'message': 'No prediction found for this ticker'
                        })
                except Exception as e:
                    results.append({
                        'ticker': ticker,
                        'prediction': None,
                        'prediction_date': None,
                        'prediction_text': None,
                        'status': 'error',
                        'message': str(e)
                    })
            
            return {
                'results': results,
                'total_requested': len(tickers),
                'total_found': len([r for r in results if r['status'] == 'success']),
                'total_not_found': len([r for r in results if r['status'] == 'not_found']),
                'total_errors': len([r for r in results if r['status'] == 'error'])
            }
            
        except Exception as e:
            logger.error(f"Error processing batch prediction request: {str(e)}")
            return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port=5000)




