from abc import ABC, abstractmethod
from src.dao.PredictionDAO import PredictionDAO

class PredictionService(ABC):
    '''Service interface for prediction retrieval/storage'''
    @abstractmethod
    def __init__(self, prediction_dao: PredictionDAO) -> None:
        pass

    @abstractmethod
    def getLatestPrediction(self, ticker: str):
        '''Return the latest prediction for ticker as int (0 or 1) or None.'''
        pass

    @abstractmethod
    def savePrediction(self, ticker: str, prediction: int, prediction_date) -> None:
        '''Save a prediction for a ticker on a date.'''
        pass
