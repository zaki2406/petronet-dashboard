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




def send(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)


def check_levels():
    df = yf.download(
        SYMBOL,
        period="1d",
        interval="5m",
        progress=False,
        group_by="column"
    )

    if df.empty or len(df) < 3:
        return

    # -------- FLATTEN MULTIINDEX (CRITICAL) --------
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    # -------- TIMEZONE FIX --------
    if df["Datetime"].dt.tz is None:
        df["Datetime"] = df["Datetime"].dt.tz_localize("UTC")
    df["Datetime"] = df["Datetime"].dt.tz_convert(IST)

    # -------- FORCE NUMERIC --------
    for col in ["High", "Low"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["High", "Low"])

    # -------- SPLIT L
