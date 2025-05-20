import schedule
import time
from Tracker2.app import recommender


def job():
    print("📡 Nieuwe voorspellingen aan het ophalen...")
    recommendations = recommender.recommend_for_tickers(["AAPL", "GOOGL", "TSLA", "AMZN"])
    for rec in recommendations:
        print(f"{rec['ticker']} → {rec['signal']} ({rec['predicted_price']}$)")

schedule.every().day.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
