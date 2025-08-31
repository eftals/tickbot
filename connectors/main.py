import yhoo




def __main__() -> None:
    news = yhoo.process_ticker("AAPL")
    for item in news:
        print(item["article"])


__main__()