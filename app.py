import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time  # 1. Import the time module

# App Configuration
st.set_page_config(page_title="India Stock Dashboard", layout="wide")

# --- API Configuration ---
API_KEY = 'AAJXIIXR1HX6NHXY' 

def fetch_stock_data(symbol):
    """
    Fetches intraday data for a given symbol.
    """
    
    
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&interval=5min&apikey=AAJXIIXR1HX6NHXY'
    response = requests.get(url)
    data = response.json()
    

    
    df = pd.DataFrame.from_dict(data["Time Series (5min)"], orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype(float)
    df = df.sort_index()
    return df

# --- UI Components ---
st.title("📈 Real-Time Indian Stock Viewer")
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
            col2.metric("Last Updated", df.index[-1].strftime('%H:%M:%S'))

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
                title=f"{ticker} Intraday Performance (5-Min Intervals)",
                template="plotly_dark",
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
            
            if st.checkbox("Show Raw Data"):
                st.write(df.tail(10))
            # 2. Add sleep here to wait for 60 seconds before making the API call
            # This is useful if you are looping through symbols to avoid rate limits
            st.warning("Waiting 60 seconds to respect API rate limits...")
            time.sleep(60)     
else:
    st.info("Enter a stock symbol in the sidebar and click 'Get Data' to begin.")
