import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time

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

st.title("AI Stock Analyzer (Full S&P + NASDAQ System)")

# ==================================================
# REAL S&P 500 (WIKIPEDIA + CACHE + FALLBACK)
# ==================================================

@st.cache_data(ttl=86400)
def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        table = pd.read_html(url)[0]
        return table["Symbol"].tolist()

    except:
        # fallback if scraping fails
        return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"]

# ==================================================
# NASDAQ-100 LIST
# ==================================================

def get_nasdaq_tickers():
    return [
        "AAPL","MSFT","NVDA","AMZN","META","TSLA","GOOGL","GOOG","AVGO","COST",
        "ADBE","NFLX","AMD","INTC","CSCO","PEP","TMUS","QCOM","AMGN","ISRG",
        "TXN","HON","INTU","BKNG","ADI","SBUX","GILD","MDLZ","VRTX","REGN",
        "MU","ADP","PANW","KLAC","LRCX","SNPS","CDNS","MAR"
    ]

# ==================================================
# MARKET SELECTOR
# ==================================================

market = st.selectbox(
    "Select Market",
    ["S&P 500", "NASDAQ 100", "Both (Recommended)"]
)

# ==================================================
# HELPERS
# ==================================================

def normalize(x):
    return max(0, min(100, x))

def classify(x):
    if x < 20:
        return "Bad"
    elif x < 40:
        return "OK"
    return "Good"

# ==================================================
# LOAD STOCK DATA
# ==================================================

@st.cache_data(ttl=3600)
def load_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
    except:
        info = {}

    try:
        hist = stock.history(period="1y")
    except:
        hist = pd.DataFrame()

    return info, hist

# ==================================================
# AI SCORING MODEL
# ==================================================

def score_stock(ticker):

    info, _ = load_stock(ticker)

    revenue = (info.get("revenueGrowth") or 0.08) * 100
    margin = (info.get("profitMargins") or 0.10) * 100
    roe = (info.get("returnOnEquity") or 0.12) * 100

    beta = info.get("beta") or 1
    pe = info.get("trailingPE") or 20

    ai_raw = revenue * 0.5 + margin * 0.3 + roe * 0.2
    ai_score = normalize(ai_raw)

    growth_score = revenue + roe

    risk_score = beta

    value_score = (100 / pe if pe > 0 else 0) + margin + roe

    return {
        "Ticker": ticker,
        "AI Score": ai_score,
        "Growth Score": growth_score,
        "Risk Score": risk_score,
        "Value Score": value_score
    }

# ==================================================
# INDIVIDUAL STOCK VIEW
# ==================================================

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

if ticker:

    info, hist = load_stock(ticker)

    revenue = (info.get("revenueGrowth") or 0.08) * 100
    margin = (info.get("profitMargins") or 0.10) * 100
    roe = (info.get("returnOnEquity") or 0.12) * 100
    beta = info.get("beta") or 1

    ai_score = normalize(revenue * 0.5 + margin * 0.3 + roe * 0.2)
    rating = classify(ai_score)
    risk = "Low" if beta < 1 else "Medium" if beta < 1.5 else "High"

    st.header(info.get("longName", ticker))

    col1, col2, col3 = st.columns(3)

    col1.metric("Revenue Growth", f"{revenue:.2f}%")
    col2.metric("Profit Margin", f"{margin:.2f}%")
    col3.metric("ROE", f"{roe:.2f}%")

    st.subheader(f"AI Score: {ai_score:.2f} ({rating})")
    st.subheader(f"Risk: {risk}")

    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines"))

        fig.update_layout(
            title="1-Year Stock Price History",
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

# ==================================================
# MARKET SCAN ENGINE
# ==================================================

st.header("Market Scanner (S&P + NASDAQ + Combined)")

if st.button("Run Scan"):

    if market == "S&P 500":
        tickers = get_sp500_tickers()

    elif market == "NASDAQ 100":
        tickers = get_nasdaq_tickers()

    else:
        tickers = list(set(get_sp500_tickers() + get_nasdaq_tickers()))

    results = []

    progress = st.progress(0)
    total = len(tickers)

    for i, t in enumerate(tickers):

        results.append(score_stock(t))

        # prevents Yahoo Finance overload
        time.sleep(0.05)

        progress.progress((i + 1) / total)

    df = pd.DataFrame(results)

    df = df[df["AI Score"].notna()]

    # ==================================================
    # TABLES
    # ==================================================

    st.subheader("Top 10 AI Stocks")
    st.dataframe(df.sort_values("AI Score", ascending=False).head(10))

    st.subheader("Top 10 Growth Stocks")
    st.dataframe(df.sort_values("Growth Score", ascending=False).head(10))

    st.subheader("Top 10 Low-Risk Stocks")
    st.dataframe(df.sort_values("Risk Score", ascending=True).head(10))

    st.subheader("Top 10 Value Stocks")
    st.dataframe(df.sort_values("Value Score", ascending=False).head(10))

    # ==================================================
    # BEST PICK
    # ==================================================

    best = df.sort_values("AI Score", ascending=False).iloc[0]["Ticker"]
    st.success(f"Top AI Pick: {best}")
