import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# App Configuration
st.set_page_config(page_title="India Stock Dashboard", layout="wide")

# --- API Configuration ---
# Get your free key at https://www.alphavantage.co/support/#api-key
API_KEY = 'WSCFG3I31A53WEDR' 

def fetch_stock_data(symbol):
    """
    Fetches intraday data for a given symbol.
    Note: For India, use suffixes like .BSE or .NSE
    """
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    
    # Error handling for invalid symbols or API limits
    if "Time Series (5min)" not in data:
        st.error("Error fetching data. Ensure the symbol is correct (e.g., RELIANCE.BSE) and your API key is valid.")
        return None
    
    # Process the data into a DataFrame
    df = pd.DataFrame.from_dict(data["Time Series (5min)"], orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype(float)
    df = df.sort_index()
    return df

# --- UI Components ---
st.title("📈 Real-Time Indian Stock Viewer")
st.sidebar.header("Settings")

# User Input for Ticker
ticker = st.sidebar.text_input("Enter Ticker (with .BSE or .NSE):", value="RELIANCE.BSE")

if st.sidebar.button("Get Data"):
    with st.spinner(f"Fetching data for {ticker}..."):
        df = fetch_stock_data(ticker)
        
        if df is not None:
            # Layout: Display Metrics
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
                xaxis_title="Time",
                yaxis_title="Price (INR)",
                template="plotly_dark",
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
            
            # Show Raw Data Option
            if st.checkbox("Show Raw Data"):
                st.write(df.tail(10))

else:
    st.info("Enter a stock symbol in the sidebar and click 'Get Data' to begin.")
