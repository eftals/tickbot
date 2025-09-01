import string
import yfinance as yf
import trafilatura
import json

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
    html_raw = trafilatura.fetch_url(url["url"])
    article = trafilatura.extract(
        filecontent=html_raw,
        url = url,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_links=False,
        favor_precision=True,
        favor_recall=False,
    )
    if not article:
        news_data["article"] = trafilatura.extract(html_raw)
    else:
        js = json.loads(article)
        news_data["article"] = js.get("text")
        news_data["title"] = js.get("title")

def process_ticker(ticker: string) -> list[dict]:
    news = fetch_yahoo_news(ticker)
    [extract_article(news_data) for news_data in news]
    return news