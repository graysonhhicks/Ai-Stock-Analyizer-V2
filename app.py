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

st.write("Stable S&P 500 AI scoring system + Buy Signal extension")

# ==================================================
# S&P 500 LIST (STATIC)
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
# HELPERS
# ==================================================

def normalize(score):
    return max(0, min(100, score))

def classify(score):
    if score < 20:
        return "Bad"
    elif score < 40:
        return "OK"
    return "Good"

# ==================================================
# LOAD STOCK DATA
# ==================================================

@st.cache_data(ttl=3600)
def load_stock(ticker):
    stock = yf.T
