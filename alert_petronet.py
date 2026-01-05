import yfinance as yf
import pandas as pd
import requests
import pytz
from datetime import datetime
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "-5149116513"
SYMBOL = "PETRONET.NS"

IST = pytz.timezone("Asia/Kolkata")

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def check_levels():
    df = yf.download(
        SYMBOL,
        period="1d",
        interval="5m",
        progress=False
    )

    if df.empty:
        return

    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True).dt.tz_convert(IST)

    high_so_far = df['High'].max()
    low_so_far = df['Low'].min()

    now = datetime.now(IST).strftime("%H:%M")

    # Persist state using GitHub Actions cache workaround
    try:
        with open("state.txt") as f:
            last_high, last_low = map(float, f.read().split(","))
    except:
        last_high, last_low = 0, float("inf")

    if high_so_far > last_high:
        send(f"🚨 PETRONET NEW DAY HIGH\n₹{high_so_far:.2f}\n⏰ {now} IST")
        last_high = high_so_far

    if low_so_far < last_low:
        send(f"⚠️ PETRONET NEW DAY LOW\n₹{low_so_far:.2f}\n⏰ {now} IST")
        last_low = low_so_far

    with open("state.txt", "w") as f:
        f.write(f"{last_high},{last_low}")

if __name__ == "__main__":
    check_levels()
