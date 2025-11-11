from src.dao.NewsDAO import NewsDAO
from abc import ABC, abstractmethod
from typing import Literal, Any

class NewService(ABC):
    '''
    Service used to handle the business logics of News Summary
    '''
    @abstractmethod
    def __init__(self, news_dao: NewsDAO)->None:
        pass
    
    @abstractmethod
    def getListOfNews(self, list_of_tickers: list[str]|Literal['all']|None=None, limit:int=10, offset:int=0)->dict[str, list[dict[str, Any]]|int]:  
        '''
        Returns a dictionary containing number of news and list of news in json object format
        '''    
        pass 

    @abstractmethod
    def getListOfUniqueTickers(self)->list[str]:      
        '''
        Returns a list of unique tickers
        '''    
        pass 

    @abstractmethod
    def getListOfCompanies(self, list_of_sectors :list[str], list_of_sub_industries: list[str], limit:int|None=10)->list[dict[str, str]]:
        '''
        Returns a list of companies according to filter provided
        '''
        pass