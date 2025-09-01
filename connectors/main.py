import yhoo
from vector_db import QClient


tickers = [ "AAPL", "IBM", "C", "GS", "QQQM" ]

def __main__() -> None:
    for ticker in tickers:
        news = yhoo.process_ticker(ticker)
        qc = QClient()
        for item in news:
            print("Embedding title -->" + item["title"])
            if item["article"] is not None and len(item["article"]) > 0:
                if qc.embed_document(ticker, "STOCK", item) is False:
                    print("Failed to embed document", item["title"])
            else:
                print("Failed to embed document", item["title"])

__main__()