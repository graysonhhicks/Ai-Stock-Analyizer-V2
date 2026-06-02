import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

# ==================================================
# DARK MODE
# ==================================================

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("AI Stock Analyzer + Buy Signal Engine")

# ==================================================
# S&P LIST
# ==================================================

def get_sp500_tickers():
    return [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","AVGO","JPM",
        "V","UNH","XOM","LLY","MA","HD","PG","COST","JNJ","ABBV",
        "MRK","BAC","NFLX","KO","CRM","ORCL","ADBE","PEP","TMO","WMT"
    ]

# ==================================================
# HELPERS
# ==================================================

def normalize(x):
    return max(0, min(100, x))

def get_signal(score, beta, margin):
    if score > 70 and beta < 1.3 and margin > 10:
        return "STRONG BUY"
    elif score > 50:
        return "BUY"
    elif score > 30:
        return "HOLD"
    else:
        return "AVOID"

# ==================================================
# DATA LOADER
# ==================================================

@st.cache_data(ttl=3600)
def load_stock(ticker):
    stock = yf.Ticker(ticker)

    try:
        info = stock.info or {}
    except:
        info = {}

    return info

# ==================================================
# SCORING
# ==================================================

def score_stock(ticker):

    info = load_stock(ticker)

    revenue = (info.get("revenueGrowth") or 0.08) * 100
    margin = (info.get("profitMargins") or 0.10) * 100
    roe = (info.get("returnOnEquity") or 0.12) * 100
    beta = info.get("beta") or 1

    raw = revenue * 0.5 + margin * 0.3 + roe * 0.2
    ai_score = normalize(raw)

    signal = get_signal(ai_score, beta, margin)

    return {
        "Ticker": ticker,
        "AI Score": ai_score,
        "Signal": signal
    }

# ==================================================
# SINGLE STOCK
# ==================================================

ticker = st.text_input("Enter Stock", "AAPL").upper()

if ticker:

    info = load_stock(ticker)

    revenue = (info.get("revenueGrowth") or 0.08) * 100
    margin = (info.get("profitMargins") or 0.10) * 100
    roe = (info.get("returnOnEquity") or 0.12) * 100
    beta = info.get("beta") or 1

    ai_score = normalize(revenue * 0.5 + margin * 0.3 + roe * 0.2)
    signal = get_signal(ai_score, beta, margin)

    st.subheader(f"AI Score: {ai_score:.2f}")
    st.subheader(f"Signal: {signal}")

# ==================================================
# S&P SCAN
# ==================================================

st.header("S&P 500 Buy Signal Scanner")

if st.button("Run Scan"):

    tickers = get_sp500_tickers()

    results = []

    progress = st.progress(0)

    for i, t in enumerate(tickers):

        data = score_stock(t)
        results.append(data)

        progress.progress((i + 1) / len(tickers))

    df = pd.DataFrame(results)

    # ==================================================
    # TABLE
    # ==================================================

    st.subheader("Stock Signals")
    st.dataframe(df)

    # ==================================================
    # SIGNAL COUNTS (NEW CHART)
    # ==================================================

    signal_counts = df["Signal"].value_counts()

    fig = go.Figure(
        data=[
            go.Bar(
                x=signal_counts.index,
                y=signal_counts.values
            )
        ]
    )

    fig.update_layout(
        title="Market Buy Signal Distribution",
        xaxis_title="Signal Type",
        yaxis_title="Number of Stocks",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==================================================
    # BEST STOCK
    # ==================================================

    best = df.sort_values("AI Score", ascending=False).iloc[0]

    st.success(f"Top AI Pick: {best['Ticker']} ({best['Signal']})")
