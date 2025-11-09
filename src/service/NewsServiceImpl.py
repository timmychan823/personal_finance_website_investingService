from src.dao.NewsDAO import NewsDAO
from .NewsService import NewService
import numpy as np
from typing import Literal, Any
# , override

class NewServiceImpl(NewService):
    '''
    Implementation of NewService, used to handle the business logics of News Summary
    '''
    def __init__(self, news_dao: NewsDAO)->None:
        self.newsDAO = news_dao
    
    # @override
    def getListOfNews(self, list_of_tickers: list[str]|Literal['all']|None=None, limit:int|None=10)->list[dict[str, Any]]:   
        '''
        This function is used to get list of news based on filter and reformat data retrieved from database

        Parameters
        ----------
        list_of_tickers: list[str], Literal['all'] or None, default None
            this can be list of strings which are tickers eg. ['TSLA', 'AAPL'] or the literal 'all' or None
        limit: int or None, default 10
            this is used to limit the number of records returned, it can be an integer or None

        Returns
        -------
        list[dict[str, Any]]
            a list of json object will be returned, which is a list of news objects
        '''    
        list_of_news_retrieved = self.newsDAO.getListOfNews(list_of_tickers=list_of_tickers, limit=limit)
        list_of_news_processed = []
        for news in list_of_news_retrieved:
            news_object = {"newsLink": news[0], "newsTitle": news[1], "newsSource": news[2], "newsPublishTime": news[3], "tickers": np.array(news[4]).flatten().tolist()}
            if news[5]:
                news_object["newsSentiment"] = news[5]
            list_of_news_processed.append(news_object)
        return list_of_news_processed
    
    # @override
    def getListOfUniqueTickers(self)->list[str]:      
        '''
        This function is used to get list of unique tickers and reformat data retrieved from database

        Returns
        -------
        list[str]
            a list of tickers eg. ['TSLA', 'NVDA'] will be returned, which is a list of strings
        '''    
        list_of_news_retrieved = np.array(self.newsDAO.getListOfUniqueTickers()).flatten().tolist()
        return list_of_news_retrieved

    # @override
    def getListOfCompanies(self, list_of_sectors :list[str], list_of_sub_industries: list[str], limit:int|None=10)->list[dict[str, str]]:
        '''
        This function is used to get list of companies and reformat data retrieved from database

        Returns
        -------
        list[str]
            a list of companies eg. [{'ticker': 'TSLA', 'companyName': 'Tesla, Inc.', 'sector': 'Consumer Discretionary', 'subIndustry': 'Automobile Manufacturers'}, {'ticker': "NVDA", 'companyName': "Nvidia", 'sector': "Information Technology", 'subIndustry': "Semiconductors"}] will be returned, which is a list of dict[str, str]
        '''    
        list_of_companies_retrieved = self.newsDAO.getListOfCompanies(list_of_sectors=list_of_sectors, list_of_sub_industries=list_of_sub_industries, limit=limit)
        list_of_companies_processed = []
        for company in list_of_companies_retrieved:
            company_object = {"ticker": company[0], "companyName": company[1], "sector": company[2], "subIndustry": company[3]}
            list_of_companies_processed.append(company_object)
        return list_of_companies_processed