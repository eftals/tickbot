import yhoo
from vector_db import QClient




def __main__() -> None:
    news = yhoo.process_ticker("AAPL")
    qc = QClient()
    for item in news:
        print("Embedding title -->" + item["title"])
        if item["article"] is not None and len(item["article"]) > 0:
            if qc.embed_document("AAPL", "STOCK", item) is False:
                print("Failed to embed document", item["title"])

__main__()