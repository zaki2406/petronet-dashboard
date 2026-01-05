import yfinance as yf
import streamlit as st
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Petronet LNG Dashboard",
    layout="wide"
)

SYMBOL = "PETRONET.NS"
st.title("📊 Petronet LNG – Daily Trading Dashboard (IST)")
st.title("Petronet LNG – 15 Day Dashboard")

if st.button("🔄 Refresh Now"):
    st.cache_data.clear()

# ---------------- DATA ----------------
@st.cache_data(ttl=60 * 60)
def load_data():
    df = yf.download(
        SYMBOL,
        period="20d",
        interval="15m",
        progress=False,
        group_by="column"
    )

    # Flatten MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    # Ensure timezone awareness → convert to IST
    if df['Datetime'].dt.tz is None:
        df['Datetime'] = df['Datetime'].dt.tz_localize('UTC')

    df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')

    # Force numeric columns
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

    df['Date'] = df['Datetime'].dt.date
    df['Time'] = df['Datetime'].dt.strftime('%H:%M')

    daily_rows = []

    for date, group in df.groupby('Date'):
        group = group.sort_values('Datetime')

        if len(group) < 5:
            continue

        high_row = group.loc[group['High'].idxmax()]
        low_row = group.loc[group['Low'].idxmin()]

        daily_rows.append({
            'Date': pd.to_datetime(date).strftime('%d-%b'),
            'Open': round(float(group.iloc[0]['Open']), 2),
            'High': round(float(high_row['High']), 2),
            'High Time': high_row['Time'],   # IST
            'Low': round(float(low_row['Low']), 2),
            'Low Time': low_row['Time'],     # IST
            'Close': round(float(group.iloc[-1]['Close']), 2),
            'Volume': int(group['Volume'].sum())
        })

    return pd.DataFrame(daily_rows).tail(15)


df = load_data()

# ---------------- METRICS ----------------
col1, col2, col3 = st.columns(3)

col1.metric("15-Day High", df['High'].max())
col2.metric("15-Day Low", df['Low'].min())
col3.metric("Avg Volume", f"{int(df['Volume'].mean()):,}")

st.divider()

# ---------------- TABLE ----------------
st.subheader("Last 15 Trading Days (IST)")

st.dataframe(
    df[['Date', 'Open', 'High', 'High Time', 'Low', 'Low Time', 'Close', 'Volume']],
    use_container_width=True,
    hide_index=True
)

# ---------------- CHARTS ----------------
st.subheader("Closing Price (15 Days)")
st.line_chart(df.set_index('Date')['Close'])

st.subheader("Daily Volume")
st.bar_chart(df.set_index('Date')['Volume'])






