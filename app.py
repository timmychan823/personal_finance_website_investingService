import psycopg2
from src.constant.Db_constants import * 
from src.dao.NewsDAOImpl import NewsDAOImpl
from src.service.NewsServiceImpl import NewServiceImpl
from src.service.DataReleaseImpl import DataReleaseServiceImpl
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

@app.route('/listOfNews', methods = ['GET'])
def list_of_news():
    if request.method == 'GET':
        if request.args.get('tickers')=='all':
            tickers='all'
        else:
            tickers = request.args.getlist('tickers')
        try:
            limit = min(int(request.args.get('limit')), 50) #TODO: should also get page number of desired page
        except Exception as e:
            limit = 10        
        logger.info(f"tickers: {tickers}, limit: {limit}")
        list_of_news = (newServiceImpl.getListOfNews(tickers, limit))
        return list_of_news #TODO: should also count the total number of news and return page number of desired page 

@app.route('/listOfUniqueCompanies', methods = ['GET'])
def list_of_unique_companies():
    if request.method == "GET":
        list_of_unique_companies = (newServiceImpl.getListOfUniqueTickers())
        return list_of_unique_companies
    
@app.route('/listOfCompanies', methods = ['GET'])
def list_of_companies():
    if request.method == "GET":
        if request.args.get('sectors')=='all':
            list_of_sectors='all'
        else:
            list_of_sectors = request.args.getlist('sectors')
        if request.args.get('subIndustries')=='all':
            list_of_sub_industries='all'
        else:
            list_of_sub_industries = request.args.getlist('subIndustries')
        try:
            limit = min(int(request.args.get('limit')), 50) #TODO: should also get page number of desired page
        except Exception as e:
            limit = 10
        logger.info(f"list_of_sectors: {list_of_sectors}, list_of_sub_industries: {list_of_sub_industries}, limit: {limit}")
        list_of_companies = (newServiceImpl.getListOfCompanies(list_of_sectors=list_of_sectors, list_of_sub_industries=list_of_sub_industries, limit=limit))
        return list_of_companies #TODO: should also count the total number of news and return page number of desired page 
    
@app.route('/dataReleases', methods = ['GET'])
async def list_of_releases():
    if request.method == 'GET':
        out = await dataReleaseServiceImpl.getDataRelease()
        return out

@app.route("/sentimentAnalysis",methods=['POST'])
def score():
    text=request.get_json()['text']
    return(predict(text, model).to_json(orient='records'))

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port=5000)




