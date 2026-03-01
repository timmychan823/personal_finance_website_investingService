from src.dao.PredictionDAO import PredictionDAO
from .PredictionService import PredictionService
from datetime import date

class PredictionServiceImpl(PredictionService):
    def __init__(self, prediction_dao: PredictionDAO) -> None:
        self.predictionDAO = prediction_dao

    def getLatestPrediction(self, ticker: str):
        '''Return latest prediction (0 or 1) or None.'''
        return self.predictionDAO.getLatestPrediction(ticker)

    def savePrediction(self, ticker: str, prediction: int, prediction_date: date) -> None:
        self.predictionDAO.savePrediction(ticker, prediction, prediction_date)
