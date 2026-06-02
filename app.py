import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ----------------------------
# Page Setup
# ----------------------------

st.set_page_config(
    page_title="AI Stock Analyzer",
    layout="wide"
)

st.title("AI-Powered Stock Market Analyzer")

st.write("""
Analyze stocks using revenue growth, profitability,
return on equity, and volatility metrics.
""")

# ----------------------------
# User Input
# ----------------------------

ticker = st.text_input(
    "Enter Stock Ticker",
    value="AAPL"
).upper()

# ----------------------------
# Data Function
# ----------------------------

@st.cache_data(ttl=3600)
def load_stock(ticker):

    stock = yf.Ticker(ticker)

    try:
        info = stock.info
    except Exception:
        info = {}

    try:
        history = stock.history(period="6mo")
    except Exception:
        history = None

    return info, history

# ----------------------------
# Analysis
# ----------------------------

if ticker:

    info, history = load_stock(ticker)

    revenue_growth = (info.get("revenueGrowth") or 0) * 100
    profit_margin = (info.get("profitMargins") or 0) * 100
    roe = (info.get("returnOnEquity") or 0) * 100
    beta = info.get("beta") or 1

    score = (
        revenue_growth * 0.50
        + profit_margin * 0.30
        + roe * 0.20
    )

    if score >= 70:
        rating = "Lucrative / Profitable"
    elif score >= 40:
        rating = "Neutral Profit"
    else:
        rating = "Unlikely Profitable"

    if beta > 1.5:
        risk = "High Risk"
    elif beta > 1:
        risk = "Medium Risk"
    else:
        risk = "Low Risk"

    st.header(info.get("longName", ticker))

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Revenue Growth",
        f"{revenue_growth:.2f}%"
    )

    col2.metric(
        "Profit Margin",
        f"{profit_margin:.2f}%"
    )

    col3.metric(
        "Return on Equity",
        f"{roe:.2f}%"
    )

    st.subheader(f"AI Financial Score: {score:.2f}")
    st.subheader(f"Profitability Classification: {rating}")
    st.subheader(f"Risk Classification: {risk}")

    # Chart

    if history is not None and not history.empty:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history["Close"],
                mode="lines",
                name="Close Price"
            )
        )

        fig.update_layout(
            title="6-Month Stock Price History",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=500
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    summary = f"""
    {info.get('shortName', ticker)} currently shows
    revenue growth of {revenue_growth:.2f}%,
    profit margins of {profit_margin:.2f}%,
    and return on equity of {roe:.2f}%.

    Based on the weighted AI scoring model,
    the stock received a score of {score:.2f}
    and is categorized as '{rating}'.

    Based on beta volatility measurements,
    the stock is classified as '{risk}' risk.
    """

    st.subheader("AI Financial Summary")

    st.write(summary)
