from app.data_fetcher import fetch_stock_data
from app.predictor import predict_next_day, predict_period

def recommend_for_tickers(tickers):
    results = []
    for tic in tickers:
        df = fetch_stock_data(tic)
        d_price, d_signal = predict_next_day(df)
        m_price = predict_period(df, 30)  # Verwijder de tuple unpacking
        y_price = predict_period(df, 365)  # Verwijder de tuple unpacking

        results.append({
            "ticker": tic,
            "predicted_daily": round(d_price, 2),
            "predicted_monthly": round(m_price, 2),
            "predicted_yearly": round(y_price, 2),
            "signal": d_signal
        })
    return results