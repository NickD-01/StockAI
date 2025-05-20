from flask import Flask, render_template, request, redirect
from Tracker2.app.recommender import recommend_for_tickers
from app.portfolio import load_portfolio, save_portfolio, portfolio_metrics

app = Flask(__name__)
WATCHLIST = ["AAPL", "GOOGL", "TSLA", "AMZN"]

@app.route("/")
def index():
    recs = recommend_for_tickers(WATCHLIST)
    return render_template("index.html", recommendations=recs, tickers=WATCHLIST)

@app.route("/portfolio", methods=["GET", "POST"])
def portfolio():
    if request.method == "POST":
        tic   = request.form["ticker"].upper()
        sh    = float(request.form["shares"])
        avg   = float(request.form["avg_price"])
        port  = load_portfolio()
        port[tic] = {"shares": sh, "avg_price": avg}
        save_portfolio(port)
        return redirect("/portfolio")

    df, val, ret = portfolio_metrics()
    table = df.to_html(classes="table", index=False)
    return render_template("portfolio.html",
                           table_html=table,
                           total_value=val,
                           total_return=ret)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
