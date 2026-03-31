import psycopg2
from .PredictionDAO import PredictionDAO
from datetime import date

class PredictionDAOImpl(PredictionDAO):
    '''Implementation of PredictionDAO using a Postgres connection'''
    CREATE_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS public."PredictedDailyReturn" (
        id SERIAL PRIMARY KEY,
        ticker TEXT NOT NULL,
        prediction SMALLINT NOT NULL CHECK (prediction IN (0,1)),
        prediction_date DATE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    '''

    INSERT_SQL = '''
    INSERT INTO public."PredictedDailyReturn" (ticker, prediction, prediction_date)
    VALUES (%s, %s, %s);
    '''

    SELECT_LATEST_SQL = '''
    SELECT prediction, prediction_date, created_at
    FROM public."PredictedDailyReturn"
    WHERE ticker = %s
    ORDER BY prediction_date DESC, created_at DESC
    LIMIT 1;
    '''

    def __init__(self, conn) -> None:
        self.conn = conn
        # ensure table exists
        with self.conn.cursor() as curs:
            curs.execute(self.CREATE_TABLE_SQL)
            self.conn.commit()

    def savePrediction(self, ticker: str, prediction: int, prediction_date: date) -> None:
        try:
            with self.conn.cursor() as curs:
                curs.execute(self.INSERT_SQL, (ticker, int(prediction), prediction_date))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def getLatestPrediction(self, ticker: str):
        with self.conn.cursor() as curs:
            curs.execute(self.SELECT_LATEST_SQL, (ticker,))
            row = curs.fetchone()
            if not row:
                return None
            prediction = int(row[0])
            prediction_date = row[1]
            # created_at is row[2], can be returned if needed
            return {
                'prediction': prediction,
                'prediction_date': prediction_date
            }
