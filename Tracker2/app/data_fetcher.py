import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, period="1y", interval="1d"):
    """
    Haalt historische aandelen data op met yfinance.

    Args:
        ticker (str): Ticker symbool, bv. 'AAPL'.
        period (str): Periode om data op te halen, bv. '1y', '6mo', '1mo'.
        interval (str): Interval van data, bv. '1d', '1wk', '1mo'.

    Returns:
        pd.DataFrame: DataFrame met aandelen data.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        if hist.empty:
            print(f"⚠️ Geen data gevonden voor {ticker}")
            return None
        return hist
    except Exception as e:
        print(f"Fout bij ophalen data voor {ticker}: {e}")
        return None
