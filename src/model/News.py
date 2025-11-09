class News:
    def __init__(self, news_link: str, news_title: str, news_source: str, news_publish_time: str, tickers: list[str], news_sentiment: float)->None:        
        self.__news_link: str = news_link
        self.__news_title: str = news_title
        self.__news_source: str = news_source
        self.__news_publish_time: str = news_publish_time
        self.__tickers: list[str] = tickers
        self.__news_sentiment: float = news_sentiment

    @property
    def news_link(self):
        return self.__news_link

    @news_link.setter
    def news_link(self, news_link):
        self.__news_link = news_link

    @property
    def news_title(self):
        return self.__news_title

    @news_title.setter
    def news_title(self, news_title):
        self.__news_title = news_title

    @property
    def news_source(self):
        return self.__news_source

    @news_source.setter
    def news_source(self, news_source):
        self.__news_source = news_source

    @property
    def news_publish_time(self):
        return self.__news_publish_time

    @news_publish_time.setter
    def news_publish_time(self, news_publish_time):
        self.__news_publish_time = news_publish_time

    @property
    def tickers(self):
        return self.__tickers

    @tickers.setter
    def tickers(self, tickers):
        self.__tickers = tickers

    @property
    def news_sentiment(self):
        return self.__news_sentiment

    @news_sentiment.setter
    def news_sentiment(self, news_sentiment):
        self.__news_sentiment = news_sentiment