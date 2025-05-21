import json
import os

TICKER_FILE = "app/tickers.json"

def load_tickers():
    if not os.path.exists(TICKER_FILE):
        return []
    with open(TICKER_FILE, "r") as f:
        return json.load(f)

def save_ticker(ticker):
    tickers = load_tickers()
    if ticker not in tickers:
        tickers.append(ticker)
        with open(TICKER_FILE, "w") as f:
            json.dump(tickers, f, indent=2)
