import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time

# App Configuration
st.set_page_config(page_title="India Stock Dashboard", layout="wide")

# --- API Configuration ---
API_KEY = 'AAJXIIXR1HX6NHXY' 

def fetch_stock_data(symbol):
    """
    Fetches daily historical data for a given symbol.
    """
    # Changed function to TIME_SERIES_DAILY and removed interval parameter
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Error handling for API limits or invalid symbols
        if "Time Series (Daily)" not in data:
            st.error("Error fetching data. Please check the ticker symbol or API limits.")
            return None

        # Parse the 'Time Series (Daily)' key instead of 'Time Series (5min)'
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
        df.index = pd.to_datetime(df.index)
        
        # Alpha Vantage daily keys are prefixed with numbers (e.g., '1. open')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float)
        df = df.sort_index()
        return df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# --- UI Components ---
st.title("📈 Daily Indian Stock Viewer")
st.sidebar.header("Settings")

ticker = st.sidebar.text_input("Enter Ticker (with .BSE or .NSE):", value="RELIANCE.BSE")

if st.sidebar.button("Get Data"):
    with st.spinner(f"Requesting data for {ticker}..."):
        df = fetch_stock_data(ticker)
        
        if df is not None:
            # Display Metrics
            latest_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            delta = latest_price - prev_price
            
            col1, col2 = st.columns(2)
            col1.metric("Current Price", f"₹{latest_price:.2f}", f"{delta:.2f}")
            # Updated to show the date instead of just time
            col2.metric("Last Trading Day", df.index[-1].strftime('%Y-%m-%d'))

            # Plotly Candlestick Chart
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Price"
            )])

            fig.update_layout(
                title=f"{ticker} Daily Performance (Historical)",
                template="plotly_dark",
                xaxis_rangeslider_visible=True # Enabled for daily views
            )

            st.plotly_chart(fig, use_container_width=True)
            
            if st.checkbox("Show Raw Data"):
                st.write(df.tail(10))
            
            st.warning("Respecting API rate limits (Free tier: 25 requests/day).")
else:
    st.info("Enter a stock symbol (e.g., RELIANCE.BSE) and click 'Get Data'.")
