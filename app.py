import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AI Stock Analyzer",
    layout="wide"
)

# --------------------------------------------------
# DARK MODE
# --------------------------------------------------

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
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("AI-Powered Stock Market Analyzer")

st.write("""
Analyze stocks using revenue growth,
profit margins, return on equity,
and risk metrics.
""")

# --------------------------------------------------
# WATCHLIST FOR MARKET RANKINGS
# --------------------------------------------------

WATCHLIST = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "JPM",
    "V",
    "WMT"
]

# --------------------------------------------------
# STOCK DATA FUNCTION
# --------------------------------------------------

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
        history = pd.DataFrame()

    return info, history


# --------------------------------------------------
# RANKING FUNCTION
# --------------------------------------------------

@st.cache_data(ttl=3600)
def get_stock_score(ticker):

    stock = yf.Ticker(ticker)

    try:
        info = stock.info
    except Exception:
        return None

    revenue_growth = (info.get("revenueGrowth") or 0) * 100
    profit_margin = (info.get("profitMargins") or 0) * 100
    roe = (info.get("returnOnEquity") or 0) * 100
    beta = info.get("beta") or 1

    ai_score = (
        revenue_growth * 0.50
        + profit_margin * 0.30
        + roe * 0.20
    )

    investment_score = (
        revenue_growth * 0.30
        + profit_margin * 0.20
        + roe * 0.20
        - beta * 5
    )

    return {
        "Ticker": ticker,
        "AI Score": round(ai_score, 2),
        "Investment Score": round(investment_score, 2)
    }

# --------------------------------------------------
# STOCK SEARCH
# --------------------------------------------------

ticker = st.text_input(
    "Enter Stock Ticker",
    value="AAPL"
).upper()

# --------------------------------------------------
# INDIVIDUAL STOCK ANALYSIS
# --------------------------------------------------

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
    st.subheader(f"Profitability: {rating}")
    st.subheader(f"Risk Level: {risk}")

    # STOCK CHART

    if not history.empty:

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

    # SUMMARY

    summary = f"""
    {info.get('shortName', ticker)} currently has
    revenue growth of {revenue_growth:.2f}%,
    profit margins of {profit_margin:.2f}%,
    and return on equity of {roe:.2f}%.

    Based on the AI financial model,
    the stock scored {score:.2f}
    and is classified as {rating}.

    The risk profile is currently classified
    as {risk}.
    """

    st.subheader("AI Financial Summary")
    st.write(summary)

# --------------------------------------------------
# MARKET RANKINGS
# --------------------------------------------------

st.header("Top AI-Ranked Stocks")

results = []

for symbol in WATCHLIST:

    result = get_stock_score(symbol)

    if result:
        results.append(result)

if len(results) > 0:

    ranking_df = pd.DataFrame(results)

    # TOP AI SCORES

    top_ai = ranking_df.sort_values(
        by="AI Score",
        ascending=False
    )

    fig1 = go.Figure()

    fig1.add_bar(
        x=top_ai["Ticker"],
        y=top_ai["AI Score"]
    )

    fig1.update_layout(
        title="Top AI Scoring Stocks"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    # TOP INVESTMENTS

    top_investments = ranking_df.sort_values(
        by="Investment Score",
        ascending=False
    )

    fig2 = go.Figure()

    fig2.add_bar(
        x=top_investments["Ticker"],
        y=top_investments["Investment Score"]
    )

    fig2.update_layout(
        title="Top AI Investment Picks"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    st.subheader("Current AI Top Pick")

    best_stock = top_investments.iloc[0]["Ticker"]

    st.success(
        f"The current highest-ranked investment in the watchlist is {best_stock}."
    )
