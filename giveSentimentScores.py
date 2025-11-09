from datetime import datetime, timedelta, date, time
import os
import re
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import logging
from typing import Any
from src.constant.Db_constants import *
import concurrent.futures
from itertools import chain
from path_definitions import LOG_DIR 
from finbert.finbert import predict
from pytorch_pretrained_bert.modeling import BertForSequenceClassification
import nltk

nltk.download('punkt')
nltk.download('punkt_tab')
model = BertForSequenceClassification.from_pretrained('./model/', num_labels=3, cache_dir=None)

def main():
    try:
        nowString = datetime.now().strftime("%Y%m%d%H%M%S")
        logger = logging.getLogger()
        directory_path = os.path.join(LOG_DIR, "giveSentimentScores")
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        log_path = os.path.join(directory_path, f"giveSentimentScoresLog_{nowString}.log")
        logging.basicConfig(filename=log_path, filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True) #change this to DEBUG mode for debugging
        pg_connection_dict = {
            'dbname': DB_NAME,
            'user': DB_USER,
            'password': DB_PW,
            'port': DB_PORT,
            'host': DB_HOST_OUT_DOCKER
        }
        conn = psycopg2.connect(**pg_connection_dict)
        list_of_news_for_giving_sentiment = fetch_news_from_db(conn, logger)
        update_sentiment_scores(conn, list_of_news_for_giving_sentiment, logger)
    except Exception as e:
        pass
    finally:
        conn.close()

def fetch_news_from_db(conn: psycopg2.extensions.connection, logger: logging.Logger)->list[tuple[Any]]:
    try:
        logger.info("Task fetch_news_from_db started")
        with conn.cursor() as curs: 
            query = """
                        SELECT link, "newsTitle", "newsSource", "newsPublishTime", "tickers", "newsSentiment"
                        FROM public."NewsSummary"
                        WHERE "newsSentiment" IS NULL AND "newsPublishTime" >= NOW() - INTERVAL '7 days' AND CARDINALITY(tickers) = 1;
                    """
            curs.execute(query)
            records = curs.fetchall()
            logger.info(f"Fetched {len(records)} news from database for sentiment scoring")
            logger.info("Task fetch_news_from_db completed")
            return records
    except psycopg2.errors.InFailedSqlTransaction as e:
        conn.rollback()  # Rollback the aborted transaction
        logger.error("Task fetch_news_from_db failed due to InFailedSqlTransaction")
        raise e
    except Exception as e:
        conn.rollback() # Rollback for other errors as well
        logger.error(f"Task fetch_news_from_db failed due to {e}")
        raise e
def update_sentiment_scores(conn: psycopg2.extensions.connection, list_of_news: list[tuple[Any]], logger: logging.Logger):
    logger.info("Task update_sentiment_scores started")
    global model
    for news in list_of_news:
        try:
            news_link = news[0]
            news_title = news[1]
            news_publish_time = news[3]
            text_to_analyze = news_title
            sentiment_score = float(predict(text_to_analyze, model)['sentiment_score'])
            logger.info(f"Predicted sentiment score {sentiment_score} for news link {news_link} and publish time {news_publish_time}")
            try:
                with conn.cursor() as curs:
                    update_query = """
                                        UPDATE public."NewsSummary"
                                        SET "newsSentiment" = %s
                                        WHERE link = %s AND "newsPublishTime" = %s;
                                    """
                    curs.execute(update_query, (sentiment_score, news_link, news_publish_time))
                    conn.commit()
                    logger.info(f"Updated sentiment score for news link {news_link} and publish time {news_publish_time} in database")
            except psycopg2.errors.InFailedSqlTransaction as e:
                conn.rollback()  # Rollback the aborted transaction
                logger.error(f"Failed to update sentiment score for news link {news_link} and publish time {news_publish_time} due to InFailedSqlTransaction")
                raise e 
            except Exception as e:
                conn.rollback() # Rollback for other errors as well
                logger.error(f"Failed to update sentiment score for news link {news_link} and publish time {news_publish_time} due to {e}")
                raise e

        except Exception as e:
            logger.error(f"Failed to predict sentiment score for news link {news_link} and publish time {news_publish_time}")
            continue


    logger.info("Task update_sentiment_scores completed")

if __name__ == "__main__":
    main()