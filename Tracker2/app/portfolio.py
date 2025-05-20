import json
import os
import pandas as pd
from app.data_fetcher import fetch_stock_data   # haalt actuele koersdata op

# Bestand waarin de portefeuille persistent wordt opgeslagen
PORTFOLIO_FILE = "app/portfolio.json"


# ----------------------------
# Hulpfuncties
# ----------------------------
def load_portfolio():
    """Laad portefeuille‐dict uit JSON. Als bestand niet bestaat: leeg dict."""
    if not os.path.exists(PORTFOLIO_FILE):
        return {}
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_portfolio(port_dict):
    """Schrijf portefeuille‐dict naar JSON‐bestand."""
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(port_dict, f, indent=2)


# ----------------------------
# Kernfunctie: metrics berekenen
# ----------------------------
def portfolio_metrics():
    """
    Berekent:
      • DataFrame met posities en kengetallen
      • Totale actuele waarde
      • Totaal rendement (%)
    """
    port = load_portfolio()
    rows = []
    total_cost = 0.0
    total_now = 0.0

    for tic, item in port.items():
        shares   = float(item["shares"])
        buy_px   = float(item["avg_price"])

        # Haal laatste slotkoers op
        hist     = fetch_stock_data(tic, period="6mo", interval="1d")
        if hist is None or hist.empty:
            continue
        curr_px  = float(hist["Close"].iloc[-1])

        # Kengetallen per positie
        ret_pct  = (curr_px - buy_px) / buy_px * 100 if buy_px != 0 else 0
        vol      = hist["Close"].pct_change().std() * (252 ** 0.5) * 100

        rows.append([tic, shares, buy_px, curr_px, round(ret_pct, 2), round(vol, 2)])

        total_cost += shares * buy_px
        total_now  += shares * curr_px

    df = pd.DataFrame(
        rows,
        columns=["Ticker", "Shares", "Avg Buy €", "Last €", "P/L %", "Vol % pa"],
    )

    # ----------------------------
    # Zero-division-safe berekening
    # ----------------------------
    if total_cost == 0:
        port_ret = 0.0
    else:
        port_ret = (total_now - total_cost) / total_cost * 100

    return df, round(total_now, 2), round(port_ret, 2)
