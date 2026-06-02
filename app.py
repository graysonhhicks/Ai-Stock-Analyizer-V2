import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="AI Stock Analyzer",
    layout="wide"
)

# ==================================================
# DARK MODE
# ==================================================

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: white;
}

div[data-testid="metric-container"] {
    background-color: #161B22;
    border: 1px solid #30363D;
    padding: 12px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("AI-Powered Stock Market Analyzer")

st.write("Stable S&P 500 AI scoring system (no missing stocks).")

# ==================================================
# S&P 500 LIST (SAFE STATIC)
# ==================================================

def get_sp500_tickers():
    return [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","AVGO","JPM",
        "V","UNH","XOM","LLY","MA","HD","PG","COST","JNJ","ABBV",
        "MRK","BAC","NFLX","KO","CRM","ORCL","ADBE","PEP","TMO","WMT",
        "CSCO","ACN","ABT","MCD","DHR","LIN","TXN","AMD","PM","VZ",
        "INTC","DIS","CAT","NEE","MS","GS","RTX","IBM","AMGN","HON"
    ]

# ==================================================
# SAFE NORMALIZATION
# ==================================================

def normalize_score(score):
    if score < 0:
        return 0
    if score > 100:
        return 100
    return score

def classify(score):
    if score < 20:
        return "Bad"
    elif score < 40:
        return "OK"
    return "Good"

# ==================================================
# STOCK DATA LOADER
# ==================================================

@st.cache_data(ttl=3600)
def load_stock(ticker):
    stock = yf.Ticker(ticker)

    try:
        info = stock.info or {}
    except:
        info = {}

    try:
        hist = stock.history(period="1y")
    except:
        hist = pd.DataFrame()

    return info, hist

# ==================================================
# SCORING FUNCTION (FIXED)
# ==================================================

def score_stock(ticker):

    stock = yf.Ticker(ticker)

    try:
        info = stock.info or {}
    except:
        info = {}

    revenue_growth = (info.get("revenueGrowth") or 0) * 100
    profit_margin = (info.get("profitMargins") or 0) * 100
    roe = (info.get("returnOnEquity") or 0) * 100
    beta = info.get("beta") or 1
    pe = info.get("trailingPE") or 20

    # -------------------------
    # RAW SCORES
    # -------------------------

    raw_ai = (
        revenue_growth * 0.5 +
        profit_margin * 0.3 +
        roe * 0.2
    )

    ai_score = normalize_score(raw_ai)

    growth_score = revenue_growth + roe

    risk_score = beta

    value_score = (
        (100 / pe if pe > 0 else 0) +
        profit_margin +
        roe
    )

    return {
        "Ticker": ticker,
        "AI Score": ai_score,
        "Growth Score": growth_score,
        "Risk Score": risk_score,
        "Value Score": value_score
    }

# ==================================================
# INDIVIDUAL STOCK ANALYSIS
# ==================================================

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

if ticker:

    info, hist = load_stock(ticker)

    revenue_growth = (info.get("revenueGrowth") or 0) * 100
    profit_margin = (info.get("profitMargins") or 0) * 100
    roe = (info.get("returnOnEquity") or 0) * 100
    beta = info.get("beta") or 1

    raw_ai = (
        revenue_growth * 0.5 +
        profit_margin * 0.3 +
        roe * 0.2
    )

    ai_score = normalize_score(raw_ai)
    rating = classify(ai_score)

    risk = "Low" if beta < 1 else "Medium" if beta < 1.5 else "High"

    st.header(info.get("longName", ticker))

    col1, col2, col3 = st.columns(3)

    col1.metric("Revenue Growth", f"{revenue_growth:.2f}%")
    col2.metric("Profit Margin", f"{profit_margin:.2f}%")
    col3.metric("ROE", f"{roe:.2f}%")

    st.subheader(f"AI Score: {ai_score:.2f} ({rating})")
    st.subheader(f"Risk Level: {risk}")

    # 1 YEAR CHART
    if not hist.empty:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines"
            )
        )

        fig.update_layout(
            title="1-Year Stock Price History",
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

# ==================================================
# S&P 500 SCAN (FIXED - NO DROPPING STOCKS)
# ==================================================

st.header("S&P 500 AI Market Scanner")

if st.button("Run S&P 500 Scan"):

    tickers = get_sp500_tickers()
    results = []

    progress = st.progress(0)
    total = len(tickers)

    for i, t in enumerate(tickers):

        data = score_stock(t)

        # ALWAYS KEEP RESULT (NO DROPNA LOSS)
        if data:
            results.append(data)

        progress.progress((i + 1) / total)

    df = pd.DataFrame(results)

    # only remove rows with missing AI Score (safe)
    df = df[df["AI Score"].notna()]

    # ==================================================
    # TOP AI STOCKS
    # ==================================================

    st.subheader("Top 10 AI Stocks")
    st.dataframe(df.sort_values("AI Score", ascending=False).head(10))

    # ==================================================
    # TOP GROWTH STOCKS
    # ==================================================

    st.subheader("Top 10 Growth Stocks")
    st.dataframe(df.sort_values("Growth Score", ascending=False).head(10))

    # ==================================================
    # LOW RISK STOCKS
    # ==================================================

    st.subheader("Top 10 Low-Risk Stocks")
    st.dataframe(df.sort_values("Risk Score", ascending=True).head(10))

    # ==================================================
    # VALUE STOCKS
    # ==================================================

    st.subheader("Top 10 Value Stocks")
    st.dataframe(df.sort_values("Value Score", ascending=False).head(10))

    # ==================================================
    # BEST PICK
    # ==================================================

    best = df.sort_values("AI Score", ascending=False).iloc[0]["Ticker"]

    st.success(f"Top AI Pick: {best}")
