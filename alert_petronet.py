import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime
import pytz

# -------- TELEGRAM CONFIG --------
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SYMBOL = "PETRONET.NS"
IST = pytz.timezone("Asia/Kolkata")

STATE_FILE = "day_state.csv"


def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, json=payload, timeout=10)


def load_state():
    if os.path.exists(STATE_FILE):
        return pd.read_csv(STATE_FILE)
    return pd.DataFrame(columns=["date", "high", "low"])


def save_state(date, high, low):
    df = pd.DataFrame([{
        "date": date,
        "high": high,
        "low": low
    }])
    df.to_csv(STATE_FILE, index=False)


def check_levels():
    df = yf.download(
        SYMBOL,
        period="1d",
        interval="5m",
        progress=False
    )

    if df.empty:
        return

    df = df.reset_index()

    # Ensure IST
    if df["Datetime"].dt.tz is None:
        df["Datetime"] = df["Datetime"].dt.tz_localize("UTC")
    df["Datetime"] = df["Datetime"].dt.tz_convert(IST)

    today = datetime.now(IST).date()

    # ---- SCALARS (IMPORTANT FIX) ----
    high_so_far = float(df["High"].max())
    low_so_far = float(df["Low"].min())

    state = load_state()

    if not state.empty and state.iloc[0]["date"] == str(today):
        last_high = float(state.iloc[0]["high"])
        last_low = float(state.iloc[0]["low"])
    else:
        last_high = None
        last_low = None

    now_time = datetime.now(IST).strftime("%H:%M")

    # ---- HIGH ALERT ----
    if last_high is None or high_so_far > last_high:
        send_telegram(
            f"📈 PETRONET LNG NEW DAY HIGH\n"
            f"₹{high_so_far:.2f}\n"
            f"Time: {now_time} IST"
        )
        last_high = high_so_far

    # ---- LOW ALERT ----
    if last_low is None or low_so_far < last_low:
        send_telegram(
            f"📉 PETRONET LNG NEW DAY LOW\n"
            f"₹{low_so_far:.2f}\n"
            f"Time: {now_time} IST"
        )
        last_low = low_so_far

    save_state(str(today), last_high, last_low)


if __name__ == "__main__":
    check_levels()
