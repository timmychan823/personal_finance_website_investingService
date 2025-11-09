import psycopg2
from .NewsDAO import NewsDAO
from typing import Literal, Any
# , override

class NewsDAOImpl(NewsDAO):
    '''
    Implementation of NewsDAO, used to retrieve data from database
    '''
    def __init__(self, conn)->None:
        self.conn = conn #TODO: how to check the if conn is an instance of connection?

    # @override
    def getListOfNews(self, list_of_tickers:list[str]|Literal['all']|None=None, limit:int|None=10)->list[tuple[Any]]:
        '''
        This function is used to get list of news based on filter from the database

        Parameters
        ----------
        list_of_tickers: list[str], Literal['all'] or None, default None
            this can be list of strings which are tickers eg. ['TSLA', 'AAPL'] or the literal 'all' or None
        limit: int or None, default 10
            this is used to limit the number of records returned, it can be an integer or None

        Returns
        -------
        list[tuple[Any]]
            a list of tuple will be returned, which is a list of news objects from the database
        '''
        try:
            with self.conn.cursor() as curs: 
                query = """
                            SELECT link, "newsTitle", "newsSource", "newsPublishTime", "tickers", "newsSentiment"
                            FROM public."NewsSummary"
                            WHERE
                        """
                if list_of_tickers=="all":
                    query+=" 1=1"
                else:
                    query+=""" "tickers" && ARRAY"""
                    if list_of_tickers != None:
                        query+=str(list_of_tickers)
                    else:
                        query+=str([])
                    query+="::text[]"
                if limit==None:
                    limit=10 
                    query+=f"LIMIT {limit}"
                else:
                    query+=f"LIMIT {limit}"
                query+=";"
                curs.execute(query)
                records = curs.fetchall()
                return records
        except psycopg2.errors.InFailedSqlTransaction:
            self.conn.rollback()  # Rollback the aborted transaction
        except Exception as e:
            self.conn.rollback() # Rollback for other errors as well
    
    # @override
    def getListOfUniqueTickers(self)->list[tuple[str]]:
        '''
        This function is used to get list of unique tickers from database

        Returns
        -------
        list[tuple[str]]
            a list of company tickers will be returned eg. [('TSLA',), ('NVDA',)], which is a list of company tickers, from the database
        '''
        with self.conn.cursor() as curs: 
            query = """
                        SELECT DISTINCT(unnest("tickers")) AS x
                        FROM public."NewsSummary"
                        ORDER BY x
                    """
            query+=";"
            curs.execute(query)
            records = curs.fetchall()
            return records
        
            
    # @override
    def getListOfCompanies(self, list_of_sectors:list[str]|Literal['all']|None=None, list_of_sub_industries: list[str]|Literal['all']|None=None, limit:int|None=10)->list[tuple[str]]:
        '''
        This function is used to get list of companies from database

        Returns
        -------
        list[tuple[str]]
            a list of companies eg. [('TSLA','Tesla, Inc.', 'Consumer Discretionary', 'Automobile Manufacturers',), ("NVDA", "Nvidia", "Information Technology", "Semiconductors",)] will be returned from the database
        '''
        with self.conn.cursor() as curs: 
            query = """
                        SELECT *
                        FROM public."Companies"
                        WHERE 1=1
                    """
            if list_of_sectors != "all":
                query+=""" AND "sector" = ANY(ARRAY"""
                if list_of_sectors != None:
                    query+=str(list_of_sectors)
                else:
                    query+=str([])
                query+="::text[])"
            if list_of_sub_industries != "all":
                query+=""" AND "subIndustry" = ANY(ARRAY"""
                if list_of_sub_industries != None:
                    query+=str(list_of_sub_industries)
                else:
                    query+=str([])
                query+="::text[])"
            if limit==None:
                limit=10 
                query+=f"LIMIT {limit}"
            else:
                query+=f"LIMIT {limit}"
            query+=";"
            curs.execute(query)
            records = curs.fetchall()
            return records