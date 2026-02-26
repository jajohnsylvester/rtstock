import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import numpy as np

# Page Layout
st.set_page_config(layout="wide", page_title="NSE Pro Gap Dashboard")

st.title("🛡️ NSE Pro Gap Dashboard")
st.markdown("Automated identification of Bullish and Bearish Gap patterns for Indian Stocks.")

# Sidebar
with st.sidebar:
    st.header("Search Parameters")
    ticker_sym = st.text_input("NSE Ticker (e.g. RELIANCE, SBIN, ADANIENT)", value="SBIN")
    ticker = f"{ticker_sym.upper()}.NS"
    period = st.selectbox("Historical View", ["6mo", "1y", "2y"], index=1)
    st.info("Note: Bearish gaps are labeled below the candle, Bullish above.")

def get_comprehensive_gaps(df):
    df = df.copy()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    
    # Storage for plotting
    df['Marker_Bull'] = np.nan
    df['Marker_Bear'] = np.nan
    df['Gap_Type'] = ""

    for i in range(2, len(df)-2):
        prev, curr, nxt = df.iloc[i-1], df.iloc[i], df.iloc[i+1]
        vol_spike = curr['Volume'] > curr['Vol_Avg'] * 1.5
        vol_climax = curr['Volume'] > curr['Vol_Avg'] * 2.5

        # --- BULLISH GAPS ---
        if curr['Low'] > prev['High']:
            p = curr['Low']
            if nxt['High'] < curr['Low'] or df.iloc[i+2]['High'] < curr['Low']:
                label = "ISLAND (TOP)"
            elif vol_spike and abs(curr['Low'] - curr['MA50'])/curr['MA50'] < 0.05:
                label = "BREAKAWAY (UP)"
            elif vol_climax and curr['Close'] > curr['MA50'] * 1.15:
                label = "EXHAUSTION (UP)"
            else:
                label = "RUNAWAY (UP)"
            
            df.at[df.index[i], 'Gap_Type'] = label
            df.at[df.index[i], 'Marker_Bull'] = p

        # --- BEARISH GAPS ---
        elif curr['High'] < prev['Low']:
            p = curr['High']
            if nxt['Low'] > curr['High'] or df.iloc[i+2]['Low'] > curr['High']:
                label = "ISLAND (BOTT)"
            elif vol_spike and abs(curr['High'] - curr['MA50'])/curr['MA50'] < 0.05:
                label = "BREAKAWAY (DN)"
            elif vol_climax and curr['Close'] < curr['MA50'] * 0.85:
                label = "EXHAUSTION (DN)"
            else:
                label = "RUNAWAY (DN)"
            
            df.at[df.index[i], 'Gap_Type'] = label
            df.at[df.index[i], 'Marker_Bear'] = p
                
    return df

try:
    data = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
    if not data.empty:
        df_res = get_comprehensive_gaps(data)
        labeled = df_res[df_res['Gap_Type'] != ""]

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(f"Technical Chart: {ticker}")
            ap = []
            if not df_res['Marker_Bull'].dropna().empty:
                ap.append(mpf.make_addplot(df_res['Marker_Bull'], type='scatter', markersize=100, marker='^', color='green'))
            if not df_res['Marker_Bear'].dropna().empty:
                ap.append(mpf.make_addplot(df_res['Marker_Bear'], type='scatter', markersize=100, marker='v', color='red'))

            fig, axlist = mpf.plot(df_res, type='candle', style='yahoo', addplot=ap, volume=True, figsize=(14, 8), returnfig=True)
            
            # Text injection
            for idx, row in labeled.iterrows():
                x = df_res.index.get_loc(idx)
                color = 'green' if "UP" in row['Gap_Type'] or "BOTT" in row['Gap_Type'] else 'red'
                y_pos = row['Marker_Bull'] if not pd.isna(row['Marker_Bull']) else row['Marker_Bear']
                axlist[0].text(x, y_pos, row['Gap_Type'], fontsize=8, fontweight='bold', ha='center', color=color)
            
            st.pyplot(fig)

        with col2:
            st.subheader("📊 Detection Summary")
            st.markdown("""
            | Gap Pattern | Trend Context | Typical Outcome |
            | :--- | :--- | :--- |
            | **Breakaway** | Breaking Consolidation | New Trend Start |
            | **Runaway** | Middle of Trend | Continuation |
            | **Exhaustion** | End of Mature Trend | Trend Failure |
            | **Island** | Two opposing gaps | Immediate Reversal |
            """)
            
            st.write("### Found Signals")
            if not labeled.empty:
                summary_tbl = labeled[['Gap_Type', 'Close']].tail(15).sort_index(ascending=False)
                st.table(summary_tbl)
            else:
                st.info("No significant gaps detected.")

except Exception as e:
    st.error(f"Error: {e}")