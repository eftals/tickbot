import string
import yfinance as yf

import trafilatura


def fetch_yahoo_news(ticker: string) -> list[dict]:
    tk = yf.Ticker(ticker)
    items = tk.news or []

    out = []
    for item in items:
        it = item.get("content")
        t = it.get("providerPublishTime")
        out.append(it)
    return out

def extract_article(news_data: dict) -> None:
    url = news_data["canonicalUrl"]
    html = trafilatura.fetch_url(url["url"])
    article = trafilatura.extract(html)
    news_data["article"] = article


def process_ticker(ticker: string) -> list[dict]:
    news = fetch_yahoo_news(ticker)
    [extract_article(news_data) for news_data in news]
    return news