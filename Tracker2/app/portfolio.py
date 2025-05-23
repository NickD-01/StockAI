from flask_login import current_user
from Tracker2.models import Portfolio, Watchlist
from Tracker2.database import db
import pandas as pd
from .data_fetcher import fetch_stock_data


def get_portfolio():
    return Portfolio.query.filter_by(user_id=current_user.id).all()


def add_to_portfolio(ticker, shares, avg_price):
    portfolio_item = Portfolio(
        user_id=current_user.id,
        ticker=ticker,
        shares=shares,
        avg_price=avg_price
    )
    db.session.add(portfolio_item)
    db.session.commit()


def remove_from_portfolio(ticker):
    Portfolio.query.filter_by(
        user_id=current_user.id,
        ticker=ticker
    ).delete()
    db.session.commit()


def get_watchlist():
    return [item.ticker for item in Watchlist.query.filter_by(user_id=current_user.id).all()]


def add_to_watchlist(ticker):
    if not Watchlist.query.filter_by(user_id=current_user.id, ticker=ticker).first():
        watchlist_item = Watchlist(user_id=current_user.id, ticker=ticker)
        db.session.add(watchlist_item)
        db.session.commit()


def remove_from_watchlist(ticker):
    Watchlist.query.filter_by(
        user_id=current_user.id,
        ticker=ticker
    ).delete()
    db.session.commit()


def portfolio_metrics():
    portfolio = get_portfolio()
    if not portfolio:
        return pd.DataFrame(), 0, 0

    data = []
    total_value = 0
    total_cost = 0

    for item in portfolio:
        try:
            current_data = fetch_stock_data(item.ticker, period="1d")
            if current_data is not None and not current_data.empty:
                current_price = current_data['Close'].iloc[-1]
                position_value = current_price * item.shares
                total_value += position_value
                position_cost = item.avg_price * item.shares
                total_cost += position_cost
                gain_loss = position_value - position_cost

                data.append({
                    'Ticker': item.ticker,
                    'Aandelen': item.shares,
                    'Gemiddelde Prijs': f"${item.avg_price:.2f}",
                    'Huidige Prijs': f"${current_price:.2f}",
                    'Waarde': f"${position_value:.2f}",
                    'Winst/Verlies': f"${gain_loss:.2f}"
                })
        except Exception as e:
            print(f"Fout bij ophalen data voor {item.ticker}: {e}")

    df = pd.DataFrame(data)
    total_return = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

    return df, f"{total_value:.2f}", f"{total_return:.2f}"