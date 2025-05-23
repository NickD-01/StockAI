from flask import Flask, render_template, request, redirect, jsonify, flash, url_for
from flask_login import LoginManager, login_required, current_user
from database import db
from models import User, Portfolio, Watchlist
from auth import auth as auth_blueprint
import pandas as pd
import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from utils.stock_data import fetch_stock_data, get_stock_recommendation

app = Flask(__name__,
            template_folder=os.path.abspath('templates'),
            static_folder=os.path.abspath('static'))

# Configuratie
app.config['SECRET_KEY'] = 'jouw-geheime-sleutel-hier'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database initialisatie
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registreer auth blueprint
app.register_blueprint(auth_blueprint)


@app.route("/")
def index():
    if current_user.is_authenticated:
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).all()
        recommendations = [get_stock_recommendation(item.ticker) for item in watchlist]
    else:
        recommendations = []
    return render_template("index.html", recommendations=recommendations)

@app.route("/daily")
def daily():
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    from utils.stock_data import fetch_stock_data, get_stock_recommendation
    
    def zip_lists(a, b):
        return zip(a, b)
    
    app.jinja_env.filters['zip'] = zip_lists
    
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    recommendations = []
    charts = []
    
    for ticker in tickers:
        try:
            hist_data = fetch_stock_data(ticker, period="3mo", interval="1d")
            
            if hist_data is None or hist_data.empty:
                print(f"Geen data gevonden voor {ticker}")
                continue
            
            # Maak de grafiek
            fig = make_subplots(rows=3, cols=1, 
                              shared_xaxes=True,
                              vertical_spacing=0.05,
                              subplot_titles=(f'{hist_data["Company_Name"].iloc[0]} ({ticker})', 'Volume', 'RSI'),
                              row_heights=[0.6, 0.2, 0.2])

            # Hoofdlijn voor de sluitingskoers
            fig.add_trace(
                go.Scatter(
                    x=hist_data['Date'],
                    y=hist_data['Close'],
                    name='Koers',
                    line=dict(color='black', width=1),
                    showlegend=True
                ),
                row=1, col=1
            )

            # Candlestick chart (optioneel)
            fig.add_trace(
                go.Candlestick(
                    x=hist_data['Date'],
                    open=hist_data['Open'],
                    high=hist_data['High'],
                    low=hist_data['Low'],
                    close=hist_data['Close'],
                    name='OHLC',
                    visible='legendonly'  # Standaard verborgen
                ),
                row=1, col=1
            )
            
            # Rest van de code blijft hetzelfde...
            # Technische indicatoren toevoegen
            # SMA lijnen
            fig.add_trace(
                go.Scatter(
                    x=hist_data['Date'],
                    y=hist_data['SMA20'],
                    name='SMA20',
                    line=dict(color='orange')
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=hist_data['Date'],
                    y=hist_data['SMA50'],
                    name='SMA50',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # Bollinger Bands
            fig.add_trace(
                go.Scatter(
                    x=hist_data['Date'],
                    y=hist_data['BB_upper'],
                    name='BB Upper',
                    line=dict(color='gray', dash='dash'),
                    opacity=0.5
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=hist_data['Date'],
                    y=hist_data['BB_lower'],
                    name='BB Lower',
                    line=dict(color='gray', dash='dash'),
                    opacity=0.5,
                    fill='tonexty'
                ),
                row=1, col=1
            )

            # Volume met EMA
            fig.add_trace(
                go.Bar(
                    x=hist_data['Date'],
                    y=hist_data['Volume'],
                    name='Volume',
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=hist_data['Date'],
                    y=hist_data['Volume_EMA'],
                    name='Volume EMA',
                    line=dict(color='orange')
                ),
                row=2, col=1
            )
            
            # RSI met MACD
            fig.add_trace(
                go.Scatter(
                    x=hist_data['Date'],
                    y=hist_data['RSI'],
                    name='RSI',
                    line=dict(color='purple')
                ),
                row=3, col=1
            )
            
            # RSI referentielijnen
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

            # Layout update
            fig.update_layout(
                height=800,
                showlegend=True,
                xaxis_rangeslider_visible=False
            )
            
            # Haal aanbeveling op
            recommendation = get_stock_recommendation(ticker)
            recommendations.append({
                'name': hist_data['Company_Name'].iloc[0],
                'symbol': ticker,
                'predicted_daily': f"${hist_data['Close'].iloc[-1]:.2f}",
                'predicted_monthly': f"${hist_data['Close'].iloc[-1] * 1.1:.2f}",
                'predicted_yearly': f"${hist_data['Close'].iloc[-1] * 1.3:.2f}",
                'signal': recommendation['signal'],
                'analyst_opinion': recommendation['reason'],
                'analyst_firm': "AI Stock Tracker"
            })
            
            charts.append(fig.to_html(full_html=False, include_plotlyjs=False))
            
        except Exception as e:
            print(f"Fout bij verwerken van {ticker}: {str(e)}")
            continue

    return render_template(
        "daily.html",
        recommendations=recommendations,
        charts=charts
    )

@app.route("/portfolio", methods=["GET", "POST"])
@login_required
def portfolio():
    if request.method == "POST":
        action = request.form.get("action")
        ticker = request.form.get("ticker", "").upper()

        if action == "add":
            try:
                shares = float(request.form["shares"])
                avg_price = float(request.form["avg_price"])
                portfolio_item = Portfolio(user_id=current_user.id, ticker=ticker, shares=shares, avg_price=avg_price)
                db.session.add(portfolio_item)
                db.session.commit()
            except ValueError:
                flash("Ongeldige waarden ingevoerd")

        elif action == "delete":
            Portfolio.query.filter_by(user_id=current_user.id, ticker=ticker).delete()
            db.session.commit()

        return redirect(url_for('portfolio'))

    portfolio_items = Portfolio.query.filter_by(user_id=current_user.id).all()
    portfolio_data, total_value, total_cost = [], 0, 0

    for item in portfolio_items:
        try:
            current_data = fetch_stock_data(item.ticker)
            current_price = current_data['Close'].iloc[-1]
            position_value = current_price * item.shares
            position_cost = item.avg_price * item.shares

            portfolio_data.append({
                'Ticker': item.ticker,
                'Aandelen': item.shares,
                'Gemiddelde Prijs': f"€{item.avg_price:.2f}",
                'Huidige Prijs': f"€{current_price:.2f}",
                'Waarde': f"€{position_value:.2f}",
                'Winst/Verlies': f"€{position_value - position_cost:.2f}"
            })

            total_value += position_value
            total_cost += position_cost
        except Exception:
            flash(f"Fout bij ophalen data voor {item.ticker}")

    df = pd.DataFrame(portfolio_data)
    total_return = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

    return render_template("portfolio.html",
                           table_html=df.to_html(classes="table", index=False),
                           total_value=f"€{total_value:.2f}",
                           total_return=f"{total_return:.2f}")

@app.route("/search")
@login_required
def search():
    ticker = request.args.get("ticker", "").upper()
    if not ticker:
        return render_template("search_result.html", error="Geen ticker opgegeven.")

    try:
        data = fetch_stock_data(ticker)
        current_price = data['Close'].iloc[-1]
        return render_template("search_result.html", ticker=ticker, price=current_price)
    except Exception:
        return render_template("search_result.html", error=f"Fout bij ophalen data voor {ticker}")

@app.route("/tickers")
def tickers():
    query = request.args.get("q", "").upper()
    matches = []

    try:
        with open("tickers.json") as f:
            all_tickers = json.load(f)

        for item in all_tickers:
            if query in item["symbol"].upper() or query in item["name"].upper():
                matches.append({"symbol": item["symbol"], "name": item["name"]})
            if len(matches) >= 10:
                break
    except FileNotFoundError:
        pass

    return jsonify(matches)

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)