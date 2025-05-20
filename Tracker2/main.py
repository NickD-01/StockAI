from flask import Flask, render_template, request, redirect
from Tracker2.app.recommender import recommend_for_tickers
from app.portfolio import load_portfolio, save_portfolio, portfolio_metrics
from app.data_fetcher import fetch_stock_data

app = Flask(__name__)
WATCHLIST = ["AAPL", "GOOGL", "TSLA", "AMZN"]

@app.route("/")
def index():
    recs = recommend_for_tickers(WATCHLIST)
    return render_template("index.html", recommendations=recs, tickers=WATCHLIST)

@app.route("/portfolio", methods=["GET", "POST"])
def portfolio():
    if request.method == "POST":
        action = request.form.get("action")
        tic = request.form.get("ticker").upper()
        port = load_portfolio()

        if action == "add":
            sh = float(request.form["shares"])
            avg = float(request.form["avg_price"])
            port[tic] = {"shares": sh, "avg_price": avg}
            save_portfolio(port)

        elif action == "delete" and tic in port:
            del port[tic]
            save_portfolio(port)

        return redirect("/portfolio")

    df, val, ret = portfolio_metrics()
    table = df.to_html(classes="table", index=False)
    return render_template("portfolio.html",
                           table_html=table,
                           total_value=val,
                           total_return=ret)


@app.route("/search")
def search():
    ticker = request.args.get("ticker", "").upper()
    try:
        data = fetch_stock_data(ticker, period="6mo", interval="1d")
        curr_price = data["Close"].iloc[-1]
        return render_template("search_result.html", ticker=ticker, price=curr_price)
    except Exception:
        return render_template("search_result.html", ticker=ticker, error="Ticker niet gevonden.")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
