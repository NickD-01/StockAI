import yfinance as yf
import pandas as pd
from typing import Optional, Tuple
import yfinance as yf
import pandas as pd
from typing import Optional
import numpy as np


def fetch_stock_data(
    ticker: str,
    period: str = "3mo",
    interval: str = "1d",
    columns: tuple[str, ...] = ("Open", "High", "Low", "Close", "Volume"),
) -> Optional[pd.DataFrame]:
    """
    Download historische data voor een ticker en voeg technische indicatoren toe.

    Parameters
    ----------
    ticker : str
        Aandeel symbool (bijv. 'AAPL')
    period : str
        Tijdsperiode ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
    interval : str
        Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
    columns : tuple[str, ...]
        Kolommen om te behouden

    Returns
    -------
    pd.DataFrame | None
        DataFrame met Date-kolom, OHLCV-kolommen en technische indicatoren,
        of None bij fouten / ontbrekende data.
    """
    try:
        # Haal ruwe data op
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            print(f"⚠️  Geen data gevonden voor {ticker}")
            return None

        # Reset index en normaliseer datum
        hist = hist.reset_index()
        hist["Date"] = pd.to_datetime(hist["Date"], utc=True).dt.tz_localize(None)

        # Bereken technische indicatoren
        # SMA's
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA200'] = hist['Close'].rolling(window=200).mean()

        # EMA's
        hist['EMA12'] = hist['Close'].ewm(span=12, adjust=False).mean()
        hist['EMA26'] = hist['Close'].ewm(span=26, adjust=False).mean()

        # MACD
        hist['MACD'] = hist['EMA12'] - hist['EMA26']
        hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        hist['MACD_Hist'] = hist['MACD'] - hist['Signal']

        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        hist['BB_middle'] = hist['Close'].rolling(window=20).mean()
        std = hist['Close'].rolling(window=20).std()
        hist['BB_upper'] = hist['BB_middle'] + (std * 2)
        hist['BB_lower'] = hist['BB_middle'] - (std * 2)

        # Volume EMA
        hist['Volume_EMA'] = hist['Volume'].ewm(span=20, adjust=False).mean()

        # Voeg bedrijfsinfo toe
        info = stock.info
        hist['Company_Name'] = info.get('longName', ticker)
        hist['Sector'] = info.get('sector', 'Unknown')
        hist['Industry'] = info.get('industry', 'Unknown')

        # Bewaar alle kolommen inclusief de nieuwe indicatoren
        base_columns = list({"Date", *columns})
        technical_columns = [col for col in hist.columns if col not in base_columns]

        return hist[base_columns + technical_columns]

    except Exception as err:
        print(f"❌ Fout bij ophalen data ({ticker}): {err}")
        return None

def get_stock_recommendation(ticker: str) -> dict:
    """
    Genereer een aanbeveling gebaseerd op technische analyse.
    """
    try:
        df = fetch_stock_data(ticker)
        if df is None or df.empty:
            return {
                'ticker': ticker,
                'signal': 'ERROR',
                'confidence': 0,
                'reason': 'Geen data beschikbaar'
            }

        latest = df.iloc[-1]
        signals = []
        confidence = 0

        # RSI signalen
        if latest['RSI'] < 30:
            signals.append('Oversold (RSI)')
            confidence += 20
        elif latest['RSI'] > 70:
            signals.append('Overbought (RSI)')
            confidence -= 20

        # Moving Average signalen
        if latest['Close'] > latest['SMA200']:
            signals.append('Boven 200-SMA')
            confidence += 10
        if latest['Close'] > latest['SMA50']:
            signals.append('Boven 50-SMA')
            confidence += 15
        if latest['Close'] < latest['SMA50']:
            signals.append('Onder 50-SMA')
            confidence -= 15

        # MACD signalen
        if latest['MACD'] > latest['Signal']:
            signals.append('MACD bullish')
            confidence += 15
        else:
            signals.append('MACD bearish')
            confidence -= 15

        # Bollinger Bands
        if latest['Close'] < latest['BB_lower']:
            signals.append('Onder BB')
            confidence += 20
        elif latest['Close'] > latest['BB_upper']:
            signals.append('Boven BB')
            confidence -= 20

        # Bepaal signaal
        if confidence >= 30:
            signal = 'STRONG BUY'
        elif confidence > 0:
            signal = 'BUY'
        elif confidence > -30:
            signal = 'HOLD'
        elif confidence > -60:
            signal = 'SELL'
        else:
            signal = 'STRONG SELL'

        return {
            'ticker': ticker,
            'signal': signal,
            'confidence': confidence,
            'reason': ' | '.join(signals),
            'company_name': latest['Company_Name'],
            'sector': latest['Sector'],
            'current_price': latest['Close'],
            'rsi': latest['RSI'],
            'macd': latest['MACD']
        }

    except Exception as e:
        print(f"Fout bij genereren aanbeveling voor {ticker}: {e}")
        return {
            'ticker': ticker,
            'signal': 'ERROR',
            'confidence': 0,
            'reason': str(e)
        }