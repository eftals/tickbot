import string
import yfinance as yf

import trafilatura
import ollama


def fetch_yahoo_news(ticker: string) -> list[dict]:
    tk = yf.Ticker(ticker)
    items = tk.news or []

    out = []
    for item in items:
        it = item.get("content")
        t = it.get("providerPublishTime")
        out.append(it)
    return out

def extract_article(news_data: dict):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0 Safari/537.36"
        )
    }
    url = news_data["canonicalUrl"]
    html = trafilatura.fetch_url(url["url"])
    article = trafilatura.extract(html)
    news_data["article"] = article


def __main__() -> None:
    news = fetch_yahoo_news("AAPL")
    for item in news:
        extract_article(item)
        for k, v in item.items():
            print(f"{k}: {v}")
            if k == "article":
                r = ollama.chat(model="llama3.1:8b-instruct-q4_K_M",
                                messages=[{"role": "user", "content": f"Summarize this article: {v}"}])
                print(r["message"]["content"])



__main__()