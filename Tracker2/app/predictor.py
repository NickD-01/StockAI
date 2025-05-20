import numpy as np
from sklearn.linear_model import LinearRegression


def predict_next_day(df):
    df = df.dropna()
    df["Return"] = df["Close"].pct_change()
    df = df.dropna()

    X = np.arange(len(df)).reshape(-1, 1)
    y = df["Close"].values

    model = LinearRegression().fit(X, y)
    next_day = len(df) + 1

    predicted_price = float(model.predict([[next_day]]))  # fix hier
    signal = "Buy" if predicted_price > y[-1] else "Sell"

    return predicted_price, signal


def predict_period(df, days_into_future):
    df = df.dropna()
    df["Return"] = df["Close"].pct_change()
    df = df.dropna()

    X = np.arange(len(df)).reshape(-1, 1)
    y = df["Close"].values

    model = LinearRegression().fit(X, y)
    future_day = len(df) + days_into_future

    predicted_price = float(model.predict([[future_day]]))  # fix hier
    return predicted_price
