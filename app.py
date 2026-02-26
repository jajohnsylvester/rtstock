import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="NSE Interactive Gap Pro")

st.title("🏹 NSE Interactive Gap Pro")
st.markdown("Identifies **Breakaway, Runaway, Exhaustion, and Island Reversal** patterns.")

# 2. Sidebar Settings
with st.sidebar:
    st.header("Search & Settings")
    ticker_input = st.text_input("NSE Ticker", value="SBIN")
    ticker = f"{ticker_input.upper()}.NS"
    period = st.selectbox("Lookback Period", ["6mo", "1y", "2y"], index=1)
    st.info("Scroll to Zoom | Click-Drag to Pan")

# 3. Logic Engine
@st.cache_data
def get_analysis(symbol, p):
    # Fetch with MultiIndex fix
    df = yf.download(symbol, period=p, interval="1d", auto_adjust=True, multi_level_index=False)
    if df.empty: return df
    
    df = df.copy()
    
    # Technical Indicators
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    # Gap Detection using Vectorized Masks
    prev_high = df['High'].shift(1)
    prev_low = df['Low'].shift(1)
    
    is_gap_up = df['Low'] > prev_high
    is_gap_dn = df['High'] < prev_low
    vol_spike = df['Volume'] > (df['Vol_Avg'] * 1.5)
    near_ma = (df['Low'] - df['MA50']).abs() / df['MA50'] < 0.05
    
    # Initialize Columns
    df['Gap_Type'] = ""
    
    # Apply Logic via .loc to ensure alignment
    # Bullish
    df.loc[is_gap_up & vol_spike & near_ma, 'Gap_Type'] = "BREAKAWAY (UP)"
    # Island Check (Current is Gap Up AND Next is Gap Down)
    is_island = is_gap_up & (df['High'].shift(-1) < df['Low'])
    df.loc[is_island, 'Gap_Type'] = "ISLAND REVERSAL"
    # Runaway
    df.loc[is_gap_up & (df['Gap_Type'] == ""), 'Gap_Type'] = "RUNAWAY (UP)"
    
    # Bearish
    df.loc[is_gap_dn & vol_spike, 'Gap_Type'] = "BREAKAWAY (DN)"
    df.loc[is_gap_dn & (df['Gap_Type'] == ""), 'Gap_Type'] = "RUNAWAY (DN)"

    # Create Marker Positions and Colors safely
    # This ensures the resulting series is the exact same length as the DF
    df['Marker_Pos'] = np.where(is_gap_up, df['Low'] * 0.97, 
                       np.where(is_gap_dn, df['High'] * 1.03, np.nan))
    
    # Fix for Volume Color Length Error
    df['Vol_Color'] = np.where(df['Close'] >= df['Open'], 'rgba(0, 200, 0, 0.5)', 'rgba(255, 0, 0, 0.5)')
    
    return df

# 4. Main App Logic
try:
    df = get_analysis(ticker, period)
    
    if not df.empty:
        # Create Plotly Figure
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # Candlestick Trace
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Price"
        ), row=1, col=1)

        # Volume Trace (Using the pre-aligned Vol_Color column)
        fig.add_trace(go.Bar(
            x=df.index, y=df['Volume'], 
            marker_color=df['Vol_Color'], 
            name="Volume"
        ), row=2, col=1)

        # Annotations (Labels)
        markers = df[df['Gap_Type'] != ""]
        for idx, row in markers.iterrows():
            is_bullish = "UP" in row['Gap_Type'] or "REVERSAL" in row['Gap_Type']
            fig.add_annotation(
                x=idx, y=row['Marker_Pos'],
                text=row['Gap_Type'],
                showarrow=True, arrowhead=1,
                ax=0, ay=40 if is_bullish else -40,
                font=dict(color="blue" if is_bullish else "red", size=10),
                bgcolor="rgba(255, 255, 255, 0.9)"
            )

        fig.update_layout(height=800, xaxis_rangeslider_visible=False, 
                          template='plotly_white', hovermode='x unified')
        
        # Dashboard Layout
        col_plot, col_table = st.columns([3, 1])
        
        with col_plot:
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        
        with col_table:
            st.subheader("📋 Detected Gaps")
            if not markers.empty:
                st.dataframe(markers[['Gap_Type', 'Close']].sort_index(ascending=False), use_container_width=True)
            else:
                st.info("No gaps found.")

    else:
        st.error("Invalid ticker or no data found.")

except Exception as e:
    st.error(f"Development Error: {e}")
