import yfinance as yf
import pandas as pd
import requests
import os
import pytz

# ---------- CONFIG ----------
SYMBOL = "PETRONET.NS"
IST = pytz.timezone("Asia/Kolkata")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = '-5149116513'


def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)


def check_levels():
    df = yf.download(
        SYMBOL,
        period="1d",
        interval="5m",
        progress=False
    )

    if df.empty or len(df) < 3:
        return

    df = df.reset_index()

    # Ensure IST
    if df["Datetime"].dt.tz is None:
        df["Datetime"] = df["Datetime"].dt.tz_localize("UTC")
    df["Datetime"] = df["Datetime"].dt.tz_convert(IST)

    # Split last candle vs previous candles
    last = df.iloc[-1]
    prev = df.iloc[:-1]

    day_high_before = prev["High"].max()
    day_low_before = prev["Low"].min()

    # ---------- HIGH BREAK ----------
    if last["High"] > day_high_before:
        send(
            f"📈 PETRONET LNG NEW DAY HIGH\n"
            f"₹{last['High']:.2f}\n"
            f"Time: {last['Datetime'].strftime('%H:%M')} IST"
        )

    # ---------- LOW BREAK ----------
    if last["Low"] < day_low_before:
        send(
            f"📉 PETRONET LNG NEW DAY LOW\n"
            f"₹{last['Low']:.2f}\n"
            f"Time: {last['Datetime'].strftime('%H:%M')} IST"
        )


if __name__ == "__main__":
    check_levels()
