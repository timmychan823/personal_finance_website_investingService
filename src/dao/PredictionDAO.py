from abc import ABC, abstractmethod

class PredictionDAO(ABC):
    '''
    DAO interface for storing and retrieving predicted daily returns
    '''
    @abstractmethod
    def __init__(self, conn) -> None:
        pass

    @abstractmethod
    def savePrediction(self, ticker: str, prediction: int, prediction_date) -> None:
        '''Save a prediction (0 or 1) for a ticker on a date.'''
        pass

    @abstractmethod
    def getLatestPrediction(self, ticker: str):
        '''Return the latest prediction for a ticker as int (0 or 1) or None if not found.'''
        pass
