from selenium import webdriver #TODO: use headless mode to run in background later
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
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

def main():
    nowString = datetime.now().strftime("%Y%m%d%H%M%S")
    logger = logging.getLogger()
    log_path = os.path.join(LOG_DIR, f"newsScraptLog_{nowString}.log")
    logging.basicConfig(filename=log_path, filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') #change this to DEBUG mode for debugging

    logger.info("Task scrapeNews started")
    options = Options()
    options.headless = True  # Enable headless mode for invisible operation
    options.add_argument("--window-size=1920,1200")  # Define the window size of the browser
    options.add_argument('-ignore-certificate-errors')
    options.add_argument('-ignore -ssl-errors')


    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        tableOfSandP500ConstituentsElement = driver.find_element(By.ID, "constituents")
        listOfSandP500ConstituentsTickersElement = tableOfSandP500ConstituentsElement.find_elements(By.CSS_SELECTOR, "tbody > tr > td:first-child")
        listOfSandP500ConstituentsCompanyNameElement = tableOfSandP500ConstituentsElement.find_elements(By.CSS_SELECTOR, "tbody > tr > td:nth-child(2)")
        listOfSandP500ConstituentsSectorElement = tableOfSandP500ConstituentsElement.find_elements(By.CSS_SELECTOR, "tbody > tr > td:nth-child(3)")
        listOfSandP500ConstituentsSubIndustryElement = tableOfSandP500ConstituentsElement.find_elements(By.CSS_SELECTOR, "tbody > tr > td:nth-child(4)")

    except Exception as e:
        logger.error("Errors occured while fetching for tableOfSandP500ConstituentsElement, skipping all remaining steps...")
        raise e

    engine=None
    try:
        engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
        logger.info("Connected successfully")
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error("Failed to connect to Database")
        raise e
    
    listOfSandP500ConstituentsTickers = []
    listOfSandP500Companies = []

    for i in range(len(listOfSandP500ConstituentsTickersElement)):
        ticker = listOfSandP500ConstituentsTickersElement[i].text
        companyName = listOfSandP500ConstituentsCompanyNameElement[i].text
        sector = listOfSandP500ConstituentsSectorElement[i].text
        subIndustry = listOfSandP500ConstituentsSubIndustryElement[i].text
        listOfSandP500Companies.append({"ticker": ticker, "companyName": companyName, "sector": sector, "subIndustry": subIndustry})
        listOfSandP500ConstituentsTickers.append(ticker)
    logger.info(f"Number of companies: {len(listOfSandP500Companies)}. Writting to Database...")
    logger.info("Writting to Database...")
    sandP500Companies_df = pd.DataFrame(listOfSandP500Companies)
    sandP500Companies_df.to_sql(name=COMPANY_TABLE_NAME, con=engine, if_exists="replace", index=False)
    logger.info("Task company list update completed")

    listOfNewsJsonObjects = []

    for ticker in listOfSandP500ConstituentsTickers:
        if len(listOfNewsJsonObjects)>=1000:
            logger.info(f"Number of records: {len(listOfNewsJsonObjects)}. Writting to Database...")
            df = pd.DataFrame(listOfNewsJsonObjects)
            df.to_sql(name=RAW_NEWS_TABLE_NAME, con=engine, if_exists="append", index=False)
            listOfNewsJsonObjects.clear()
        try:
            driver.get(f"https://finance.yahoo.com/quote/{ticker}/latest-news")
            listOfNews = driver.find_elements(By.XPATH, "//div[@class='content yf-10mgn4g']")
            wait = WebDriverWait(driver, 10, 0.5).until(EC.presence_of_all_elements_located((By.XPATH, ".//a[@class='subtle-link fin-size-small titles noUnderline yf-u4gyzs']")))
            ##TODO: 
            # wait before element is ready
            # email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "element_css"))).get_attribute("value")
            for news in listOfNews:
                news_link = news.find_element(By.XPATH, ".//a[@class='subtle-link fin-size-small titles noUnderline yf-u4gyzs']").get_attribute("href")
                newsTitle = news.find_element(By.CSS_SELECTOR, "h3").text
                newsDescription = news.find_element(By.CSS_SELECTOR, "p").text
                newsSourceAndTime = news.find_element(By.XPATH, ".//div[@class='footer yf-10mgn4g']").text
                listOfNewsSourceAndTime = newsSourceAndTime.split("\n")
                now = datetime.now()
                match = re.search("(\d{1,2})", listOfNewsSourceAndTime[2])
                if match != None:
                    value = int(match.group(1))
                    start_of_today = datetime.combine(now.date(), time.min)
                    if "minutes" in listOfNewsSourceAndTime[2]:
                        publishTimeInDateTime = now - timedelta(minutes=value)
                        if publishTimeInDateTime >= start_of_today:
                            newsJsonObject = {"link": news_link, "newsTitle": newsTitle, "newsDescription": newsDescription, "newsSource": listOfNewsSourceAndTime[0], "newsPublishTime": publishTimeInDateTime, "ticker": ticker}
                            listOfNewsJsonObjects.append(newsJsonObject)
                    elif "hours" in listOfNewsSourceAndTime[2]:
                        publishTimeInDateTime = now - timedelta(hours=value)
                        if publishTimeInDateTime >= start_of_today:
                            newsJsonObject = {"link": news_link, "newsTitle": newsTitle, "newsDescription": newsDescription, "newsSource": listOfNewsSourceAndTime[0], "newsPublishTime": publishTimeInDateTime, "ticker": ticker}
                            listOfNewsJsonObjects.append(newsJsonObject)

        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(f"Errors occured while fetching for ticker {ticker}, skipping...")

    logger.info(f"Number of records: {len(listOfNewsJsonObjects)}. Writting to Database...")
    logger.info("Writting to Database...")
    df = pd.DataFrame(listOfNewsJsonObjects)
    df.to_sql(name=RAW_NEWS_TABLE_NAME, con=engine, if_exists="append", index=False)
    listOfNewsJsonObjects.clear()
    logger.info("Task scrapeNews completed")

if __name__ == "__main__":
    main()