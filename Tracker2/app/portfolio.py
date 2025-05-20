import json, os
import pandas as pd
from app.data_fetcher import fetch_stock_data

PORTFOLIO_FILE = "app/portfolio.json"

def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return {}
    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)

def save_portfolio(port_dict):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(port_dict, f, indent=2)

def portfolio_metrics():
    port = load_portfolio()
    rows = []
    total_cost = total_now = 0

    for tic, item in port.items():
        shares   = item["shares"]
        buy_px   = item["avg_price"]
        hist     = fetch_stock_data(tic, period="6mo", interval="1d")
        curr_px  = hist["Close"].iloc[-1]
        ret_pct  = (curr_px - buy_px) / buy_px * 100
        vol      = hist["Close"].pct_change().std() * (252**0.5) * 100
        rows.append([tic, shares, buy_px, curr_px, ret_pct, vol])
        total_cost += shares * buy_px
        total_now  += shares * curr_px

    df = pd.DataFrame(rows, columns=[
        "Ticker", "Shares", "Avg Buy €", "Last €", "P/L %", "Vol % pa"])
    port_ret = (total_now - total_cost) / total_cost * 100
    return df, round(total_now, 2), round(port_ret, 2)
