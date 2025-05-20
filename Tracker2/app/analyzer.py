import yfinance as yf

def get_analyst_recommendation(ticker):
    stock = yf.Ticker(ticker)
    try:
        info = stock.info
        recommendation = info.get("recommendationKey", "No data")  # buy/sell/hold
        firm = info.get("financialCurrency", "Unknown")  # Dit is placeholder – firm is vaak niet beschikbaar
        return recommendation.capitalize(), firm
    except Exception as e:
        return "Error", "Unknown"
