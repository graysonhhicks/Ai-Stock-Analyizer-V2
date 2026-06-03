import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time

# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("AI Stock Analyzer (Fixed Full Market Ranking)")

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

# ==================================================
# S&P 500 (REAL + CLEANED)
# ==================================================

@st.cache_data(ttl=86400)
def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        table = pd.read_html(url)[0]

        tickers = table["Symbol"].tolist()

        # Fix Yahoo Finance formatting (BRK.B → BRK-B)
        tickers = [t.replace(".", "-") for t in tickers]

        return tickers

    except:
        return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]

# ==================================================
# NASDAQ-100
# ==================================================

def get_nasdaq_tickers():
    return [
        "AAPL","MSFT","NVDA","AMZN","META","TSLA","GOOGL","AVGO","COST",
        "ADBE","NFLX","AMD","INTC","CSCO","PEP","TMUS","QCOM","AMGN","ISRG",
        "TXN","HON","INTU","BKNG","ADI","SBUX","GILD","MDLZ","VRTX","REGN",
        "MU","ADP","PANW","KLAC","LRCX","SNPS","CDNS","MAR"
    ]

# ==================================================
# MARKET SELECTOR
# ==================================================

market = st.selectbox(
    "Select Market",
    ["S&P 500", "NASDAQ 100", "Both"]
)

# ==================================================
# HELPERS
# ==================================================

def normalize(x):
    return max(0, min(100, x))

# ==================================================
# STOCK LOADER (SAFE)
# ==================================================

@st.cache_data(ttl=3600)
def load_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
    except:
        info = {}

    return info

# ==================================================
# AI SCORING
# ==================================================

def score_stock(ticker):

    info = load_stock(ticker)

    revenue = (info.get("revenueGrowth") or 0.08) * 100
    margin = (info.get("profitMargins") or 0.10) * 100
    roe = (info.get("returnOnEquity") or 0.12) * 100
    beta = info.get("beta") or 1
    pe = info.get("trailingPE") or 20

    ai_raw = revenue * 0.5 + margin * 0.3 + roe * 0.2
    ai_score = normalize(ai_raw)

    growth = revenue + roe
    risk = beta
    value = (100 / pe if pe > 0 else 0) + margin + roe

    return {
        "Ticker": ticker,
        "AI Score": ai_score,
        "Growth Score": growth,
        "Risk Score": risk,
        "Value Score": value
    }

# ==================================================
# INDIVIDUAL STOCK VIEW
# ==================================================

ticker = st.text_input("Search Stock", "AAPL").upper()

if ticker:

    info = load_stock(ticker)

    revenue = (info.get("revenueGrowth") or 0.08) * 100
    margin = (info.get("profitMargins") or 0.10) * 100
    roe = (info.get("returnOnEquity") or 0.12) * 100
    beta = info.get("beta") or 1

    ai_score = normalize(revenue * 0.5 + margin * 0.3 + roe * 0.2)

    st.subheader(f"{ticker} AI Score: {ai_score:.2f}")

# ==================================================
# MARKET SCAN
# ==================================================

st.header("Full Market AI Ranking Scanner")

if st.button("Run Full Scan"):

    # -------------------------
    # PICK UNIVERSE
    # -------------------------
    if market == "S&P 500":
        tickers = get_sp500_tickers()

    elif market == "NASDAQ 100":
        tickers = get_nasdaq_tickers()

    else:
        tickers = list(set(get_sp500_tickers() + get_nasdaq_tickers()))

    results = []

    progress = st.progress(0)
    total = len(tickers)

    # -------------------------
    # SCAN ALL STOCKS
    # -------------------------
    for i, t in enumerate(tickers):

        try:
            data = score_stock(t)
            results.append(data)

        except:
            pass

        time.sleep(0.03)  # prevents rate limit crash
        progress.progress((i + 1) / total)

    df = pd.DataFrame(results)

    # IMPORTANT: ensure full ranking works
    df = df.dropna(subset=["AI Score"])
    df = df.sort_values("AI Score", ascending=False)

    # ==================================================
    # TOP TABLES
    # ==================================================

    st.subheader("Top 10 AI Stocks")
    st.dataframe(df.head(10))

    st.subheader("Top 10 Growth Stocks")
    st.dataframe(df.sort_values("Growth Score", ascending=False).head(10))

    st.subheader("Top 10 Low Risk Stocks")
    st.dataframe(df.sort_values("Risk Score", ascending=True).head(10))

    st.subheader("Top 10 Value Stocks")
    st.dataframe(df.sort_values("Value Score", ascending=False).head(10))

    # ==================================================
    # FIXED CHART (THIS IS YOUR MAIN BUG FIX)
    # ==================================================

    top_chart = df.head(25)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=top_chart["Ticker"],
            y=top_chart["AI Score"]
        )
    )

    fig.update_layout(
        title="Top 25 AI Scoring Stocks (Full Market Scan)",
        xaxis_title="Stock",
        yaxis_title="AI Score",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==================================================
    # BEST PICK
    # ==================================================

    best = df.iloc[0]["Ticker"]
    st.success(f"Top AI Pick: {best}")
