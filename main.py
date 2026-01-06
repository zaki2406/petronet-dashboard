import yfinance as yf
import streamlit as st
import pandas as pd
import pytz

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Petronet LNG Dashboard",
    layout="wide"
)

SYMBOL = "PETRONET.NS"

st.title("📊 Petronet LNG – Intraday Trading Dashboard (IST)")
st.caption("15-minute data • VWAP • Daily High/Low timing")

if st.button("🔄 Refresh Now"):
    st.cache_data.clear()

# ---------------- DATA LOADER ----------------
@st.cache_data(ttl=60 * 60)
def load_data():
    df = yf.download(
        SYMBOL,
        period="20d",
        interval="15m",
        progress=False,
        auto_adjust=False
    )

    # -------- Normalize datetime --------
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    if 'Datetime' not in df.columns:
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'Datetime'}, inplace=True)
        elif 'index' in df.columns:
            df.rename(columns={'index': 'Datetime'}, inplace=True)

    df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')

    # -------- Timezone handling --------
    if df['Datetime'].dt.tz is None:
        df['Datetime'] = df['Datetime'].dt.tz_localize('UTC')

    df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')

    # -------- Numeric safety --------
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

    df['Date'] = df['Datetime'].dt.date
    df['Time'] = df['Datetime'].dt.strftime('%H:%M')

    # ---------------- VWAP CALCULATION ----------------
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['TPV'] = df['TP'] * df['Volume']

    df['CumVol'] = df.groupby('Date')['Volume'].cumsum()
    df['CumTPV'] = df.groupby('Date')['TPV'].cumsum()

    df['VWAP'] = df['CumTPV'] / df['CumVol']

    # ---------------- DAILY SUMMARY ----------------
    daily_rows = []

    for date, group in df.groupby('Date'):
        group = group.sort_values('Datetime')

        if len(group) < 5:
            continue

        high_row = group.loc[group['High'].idxmax()]
        low_row = group.loc[group['Low'].idxmin()]

        daily_rows.append({
            'Date': pd.to_datetime(date).strftime('%d-%b'),
            'Open': round(group.iloc[0]['Open'], 2),
            'High': round(high_row['High'], 2),
            'High Time': high_row['Time'],
            'Low': round(low_row['Low'], 2),
            'Low Time': low_row['Time'],
            'Close': round(group.iloc[-1]['Close'], 2),
            'Volume': int(group['Volume'].sum())
        })

    daily_df = pd.DataFrame(daily_rows).tail(15)

    return df, daily_df


# ---------------- LOAD DATA ----------------
intraday_df, df = load_data()

# ---------------- METRICS ----------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("15-Day High", df['High'].max())
col2.metric("15-Day Low", df['Low'].min())
col3.metric("Avg Volume", f"{int(df['Volume'].mean()):,}")

# -------- Today's VWAP --------
today = intraday_df['Date'].max()
today_df = intraday_df[intraday_df['Date'] == today]

if not today_df.empty:
    last_price = round(today_df.iloc[-1]['Close'], 2)
    last_vwap = round(today_df.iloc[-1]['VWAP'], 2)
    col4.metric("Today's VWAP", last_vwap, delta=round(last_price - last_vwap, 2))

st.divider()

# ---------------- TABLE ----------------
st.subheader("Last 15 Trading Days (IST)")

st.dataframe(
    df[['Date', 'Open', 'High', 'High Time', 'Low', 'Low Time', 'Close', 'Volume']],
    use_container_width=True,
    hide_index=True
)

# ---------------- INTRADAY VWAP CHART ----------------
st.subheader("Today – Price vs VWAP (15-min)")

if not today_df.empty:
    chart_df = today_df[['Datetime', 'Close', 'VWAP']].set_index('Datetime')
    st.line_chart(chart_df)

# ---------------- DAILY CLOSE & VOLUME ----------------
st.subheader("Closing Price (Last 15 Days)")
st.line_chart(df.set_index('Date')['Close'])

st.subheader("Daily Volume")
st.bar_chart(df.set_index('Date')['Volume'])
