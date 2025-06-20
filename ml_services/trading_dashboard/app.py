import streamlit as st
import websockets
import asyncio
import json
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
from threading import Thread
import nest_asyncio
import altair as alt
import uuid

# Apply nest_asyncio to make asyncio work with Streamlit
nest_asyncio.apply()

# Constants and configuration
API_URL = os.getenv("API_URL", "http://api:8000")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://websocket_signal_server:8004")
AUTO_TRADER_API = os.getenv("AUTO_TRADER_API", "http://auto_trader:8000")

# For local development:
# API_URL = "http://localhost:8000"
# WEBSOCKET_URL = "ws://localhost:8004"
# AUTO_TRADER_API = "http://localhost:8001"

# Page configuration
st.set_page_config(
    page_title="NexusSentinel Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for WebSocket and signals
if "signals" not in st.session_state:
    st.session_state.signals = []
if "ws_connected" not in st.session_state:
    st.session_state.ws_connected = False
if "trade_history" not in st.session_state:
    st.session_state.trade_history = []
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())[:8]
if "mode" not in st.session_state:
    st.session_state.mode = "manual"
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()

# Function to get account info from auto-trader
def get_account_info():
    try:
        response = requests.get(f"{AUTO_TRADER_API}/account")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get account info: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error getting account info: {e}")
        return None

# Function to get positions from auto-trader
def get_positions():
    try:
        response = requests.get(f"{AUTO_TRADER_API}/positions")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get positions: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error getting positions: {e}")
        return []

# Function to get trade history from auto-trader
def get_trade_history():
    try:
        response = requests.get(f"{AUTO_TRADER_API}/trades")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get trade history: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error getting trade history: {e}")
        return []

# Function to set trading mode
def set_trading_mode(mode):
    try:
        response = requests.post(
            f"{AUTO_TRADER_API}/set-mode",
            json={"mode": mode.lower()}
        )
        if response.status_code == 200:
            st.session_state.mode = mode.lower()
            return True
        else:
            st.error(f"Failed to set mode: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error setting mode: {e}")
        return False

# Function to execute a manual trade
def execute_manual_trade(signal):
    try:
        response = requests.post(
            f"{AUTO_TRADER_API}/manual-trade",
            json=signal
        )
        if response.status_code == 200:
            st.success(f"✅ Trade executed: {signal['symbol']} {signal['action']}")
            return response.json()
        else:
            st.error(f"Failed to execute trade: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error executing trade: {e}")
        return None

# WebSocket message handler
async def handle_websocket():
    reconnect_delay = 1
    
    while True:
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                st.session_state.ws_connected = True
                
                # Subscribe to signals
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "client": f"dashboard-{st.session_state.client_id}",
                    "mode": "observer"
                }))
                
                # Process incoming messages
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # Handle different message types
                        if data.get("type") == "signal":
                            # Add timestamp if not present
                            if "timestamp" not in data:
                                data["timestamp"] = datetime.now().isoformat()
                                
                            # Add to signals list (limit to 100 most recent)
                            st.session_state.signals.insert(0, data)
                            if len(st.session_state.signals) > 100:
                                st.session_state.signals = st.session_state.signals[:100]
                                
                            st.session_state.last_update = datetime.now()
                        elif data.get("type") == "trade":
                            # Add to trade history
                            st.session_state.trade_history.insert(0, data)
                            if len(st.session_state.trade_history) > 100:
                                st.session_state.trade_history = st.session_state.trade_history[:100]
                                
                            st.session_state.last_update = datetime.now()
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        st.error(f"Error processing message: {e}")
                        break
                        
        except Exception as e:
            st.session_state.ws_connected = False
            
            # Wait before reconnecting
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 30)  # Exponential backoff, max 30 seconds

# Start WebSocket connection in a background thread
def start_websocket_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handle_websocket())

# Start WebSocket thread if not already running
if not st.session_state.ws_connected:
    thread = Thread(target=start_websocket_thread, daemon=True)
    thread.start()

# Sidebar for configuration and account info
with st.sidebar:
    st.title("📊 NexusSentinel")
    st.subheader("Trading Dashboard")
    
    # Trading mode selection
    st.subheader("🔄 Trading Mode")
    col1, col2 = st.columns(2)
    
    with col1:
        manual_button = st.button(
            "Manual Mode", 
            type="primary" if st.session_state.mode == "manual" else "secondary",
            use_container_width=True
        )
    
    with col2:
        auto_button = st.button(
            "Auto Mode", 
            type="primary" if st.session_state.mode == "auto" else "secondary",
            use_container_width=True
        )
    
    if manual_button:
        if set_trading_mode("manual"):
            st.success("Switched to Manual Mode")
    
    if auto_button:
        if set_trading_mode("auto"):
            st.warning("⚠️ Switched to Auto Mode - Trades will execute automatically!")
    
    st.markdown(f"**Current Mode:** {'🤖 AUTO' if st.session_state.mode == 'auto' else '👨‍💻 MANUAL'}")
    
    # Account information
    st.subheader("💰 Account")
    account = get_account_info()
    
    if account:
        equity = float(account.get("equity", 0))
        cash = float(account.get("cash", 0))
        buying_power = float(account.get("buying_power", 0))
        
        # Display account metrics
        col1, col2 = st.columns(2)
        col1.metric("Equity", f"${equity:,.2f}")
        col2.metric("Cash", f"${cash:,.2f}")
        
        # Create a simple portfolio value chart
        if "portfolio_history" not in st.session_state:
            st.session_state.portfolio_history = []
        
        # Add current value to history (limit to 100 points)
        st.session_state.portfolio_history.append({
            "timestamp": datetime.now(),
            "equity": equity
        })
        
        if len(st.session_state.portfolio_history) > 100:
            st.session_state.portfolio_history = st.session_state.portfolio_history[-100:]
        
        # Plot portfolio value over time
        if len(st.session_state.portfolio_history) > 1:
            df = pd.DataFrame(st.session_state.portfolio_history)
            chart = alt.Chart(df).mark_line().encode(
                x='timestamp:T',
                y=alt.Y('equity:Q', scale=alt.Scale(zero=False)),
                tooltip=['timestamp:T', 'equity:Q']
            ).properties(height=200)
            st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Unable to retrieve account information")
    
    # Connection status
    st.subheader("📡 Connection Status")
    if st.session_state.ws_connected:
        st.success("Connected to Signal Server")
    else:
        st.error("Disconnected from Signal Server")
        if st.button("Reconnect"):
            st.experimental_rerun()
    
    # Last update time
    st.caption(f"Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")

# Main content area
st.title("📈 NexusSentinel Trading Dashboard")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📊 Live Signals", "📝 Positions & History", "📈 Market Overview"])

# Tab 1: Live Signals
with tab1:
    st.subheader("🔔 Live Trading Signals")
    
    # Auto-refresh button
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)
    if auto_refresh:
        time.sleep(5)
        st.experimental_rerun()
    
    # Display signals
    if not st.session_state.signals:
        st.info("Waiting for signals...")
    else:
        for i, signal in enumerate(st.session_state.signals[:10]):  # Show 10 most recent signals
            with st.expander(
                f"{signal.get('symbol', 'Unknown')} → {signal.get('action', 'Unknown')} "
                f"(Confidence: {signal.get('confidence', 0):.2f})",
                expanded=(i == 0)  # Expand only the most recent signal
            ):
                # Display signal details
                col1, col2, col3 = st.columns(3)
                
                col1.metric("Symbol", signal.get("symbol", "Unknown"))
                col2.metric("Action", signal.get("action", "Unknown"))
                col3.metric("Confidence", f"{signal.get('confidence', 0):.2f}")
                
                # Display additional details if available
                if "sentiment" in signal:
                    st.write("Sentiment:", signal["sentiment"])
                
                if "technicals" in signal:
                    st.write("Technical Indicators:")
                    tech = signal["technicals"]
                    tech_cols = st.columns(len(tech))
                    for i, (key, value) in enumerate(tech.items()):
                        tech_cols[i].metric(key, f"{value:.2f}" if isinstance(value, (int, float)) else value)
                
                # Show timestamp
                st.caption(f"Signal received: {signal.get('timestamp', 'Unknown')}")
                
                # Manual trade execution button (only in manual mode)
                if st.session_state.mode == "manual":
                    if st.button(f"Execute {signal.get('action', 'Trade')}", key=f"trade_{i}"):
                        result = execute_manual_trade(signal)
                        if result:
                            st.success(f"Trade executed: {result}")

# Tab 2: Positions & History
with tab2:
    col1, col2 = st.columns(2)
    
    # Current positions
    with col1:
        st.subheader("📋 Current Positions")
        positions = get_positions()
        
        if positions:
            # Create a DataFrame for better display
            positions_df = pd.DataFrame(positions)
            
            # Format numeric columns
            numeric_cols = ["qty", "market_value", "unrealized_pl", "current_price"]
            for col in numeric_cols:
                if col in positions_df.columns:
                    positions_df[col] = positions_df[col].astype(float)
            
            # Display as a table
            st.dataframe(
                positions_df,
                use_container_width=True,
                column_config={
                    "market_value": st.column_config.NumberColumn(
                        "Market Value",
                        format="$%.2f"
                    ),
                    "unrealized_pl": st.column_config.NumberColumn(
                        "Unrealized P/L",
                        format="$%.2f"
                    ),
                    "current_price": st.column_config.NumberColumn(
                        "Current Price",
                        format="$%.2f"
                    ),
                }
            )
            
            # Create a pie chart of portfolio allocation
            if len(positions) > 0:
                fig = px.pie(
                    positions_df,
                    values='market_value',
                    names='symbol',
                    title='Portfolio Allocation'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No open positions")
    
    # Trade history
    with col2:
        st.subheader("📜 Trade History")
        trades = get_trade_history()
        
        if trades:
            # Create a DataFrame for better display
            trades_df = pd.DataFrame(trades)
            
            # Sort by timestamp if available
            if "timestamp" in trades_df.columns:
                trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])
                trades_df = trades_df.sort_values("timestamp", ascending=False)
            
            # Display as a table
            st.dataframe(
                trades_df,
                use_container_width=True,
                column_config={
                    "timestamp": st.column_config.DatetimeColumn(
                        "Time",
                        format="D MMM, HH:mm:ss"
                    )
                }
            )
        else:
            st.info("No trade history available")

# Tab 3: Market Overview
with tab3:
    st.subheader("📊 Market Overview")
    
    # This section could integrate with your existing market data APIs
    # For now, we'll display some placeholder content
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Movers")
        
        # Sample data - replace with real API calls
        movers_data = [
            {"symbol": "AAPL", "change": 2.5},
            {"symbol": "MSFT", "change": 1.8},
            {"symbol": "GOOGL", "change": -1.2},
            {"symbol": "AMZN", "change": 3.1},
            {"symbol": "META", "change": -2.3}
        ]
        
        movers_df = pd.DataFrame(movers_data)
        
        # Create a bar chart
        fig = px.bar(
            movers_df,
            x="symbol",
            y="change",
            color="change",
            color_continuous_scale=["red", "gray", "green"],
            title="Daily % Change"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sentiment Analysis")
        
        # Sample data - replace with real sentiment data
        sentiment_data = [
            {"symbol": "AAPL", "sentiment": 0.8},
            {"symbol": "MSFT", "sentiment": 0.6},
            {"symbol": "GOOGL", "sentiment": -0.3},
            {"symbol": "AMZN", "sentiment": 0.5},
            {"symbol": "META", "sentiment": -0.2}
        ]
        
        sentiment_df = pd.DataFrame(sentiment_data)
        
        # Create a horizontal bar chart
        fig = px.bar(
            sentiment_df,
            y="symbol",
            x="sentiment",
            orientation="h",
            color="sentiment",
            color_continuous_scale=["red", "gray", "green"],
            title="Market Sentiment"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent news
    st.subheader("📰 Recent Market News")
    
    # Sample news - replace with real news API
    news_items = [
        {
            "headline": "Fed Signals Potential Rate Cut in Coming Months",
            "source": "Financial Times",
            "timestamp": "2 hours ago"
        },
        {
            "headline": "Tech Stocks Rally on Strong Earnings Reports",
            "source": "CNBC",
            "timestamp": "4 hours ago"
        },
        {
            "headline": "Oil Prices Surge Amid Middle East Tensions",
            "source": "Bloomberg",
            "timestamp": "6 hours ago"
        }
    ]
    
    for item in news_items:
        with st.expander(f"{item['headline']} ({item['source']})"):
            st.write(f"Source: {item['source']}")
            st.write(f"Time: {item['timestamp']}")
            st.write("Click to read full article...")

# Footer
st.markdown("---")
st.caption("NexusSentinel Trading Dashboard | © 2025 | Data refreshes automatically")
