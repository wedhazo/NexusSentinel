#!/usr/bin/env python3
"""
NexusSentinel Auto-Trader Module

This module connects to the WebSocket signal server, receives trading signals,
and executes trades via the Alpaca API. It supports both auto and manual modes,
with configuration via environment variables.

Usage:
    python main.py

Environment Variables:
    ALPACA_API_KEY: Alpaca API key
    ALPACA_API_SECRET: Alpaca API secret
    ALPACA_BASE_URL: Alpaca API base URL (default: https://paper-api.alpaca.markets)
    WEBSOCKET_URL: WebSocket signal server URL (default: ws://websocket_signal_server:8004)
    TRADE_MODE: Trading mode (auto or manual, default: manual)
    CONFIDENCE_THRESHOLD: Minimum confidence threshold for executing trades (default: 0.7)
    MAX_RETRIES: Maximum number of retries for failed API calls (default: 3)
    LOG_LEVEL: Logging level (default: INFO)
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

import websockets
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError, RateLimitException

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("auto_trader.log")
    ]
)
logger = logging.getLogger("auto-trader")

# Load configuration from environment variables
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://websocket_signal_server:8004")
TRADE_MODE = os.getenv("TRADE_MODE", "manual").lower()
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
DEFAULT_QUANTITY = int(os.getenv("DEFAULT_QUANTITY", "1"))

# Check for required environment variables
if not ALPACA_API_KEY or not ALPACA_API_SECRET:
    logger.error("ALPACA_API_KEY and ALPACA_API_SECRET must be set")
    sys.exit(1)

# Initialize Alpaca API client
try:
    api = tradeapi.REST(
        key_id=ALPACA_API_KEY,
        secret_key=ALPACA_API_SECRET,
        base_url=ALPACA_BASE_URL
    )
    account = api.get_account()
    logger.info(f"Connected to Alpaca API. Account status: {account.status}")
    logger.info(f"Trading mode: {TRADE_MODE.upper()}")
except Exception as e:
    logger.error(f"Failed to initialize Alpaca API: {e}")
    sys.exit(1)

# Trade history
trade_history = []

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((APIError, RateLimitException)),
    reraise=True
)
async def execute_buy(symbol: str, qty: int = DEFAULT_QUANTITY) -> Dict[str, Any]:
    """
    Execute a buy order for the specified symbol.
    
    Args:
        symbol: Stock symbol to buy
        qty: Quantity to buy (default: 1)
        
    Returns:
        Dictionary with order details
    """
    try:
        logger.info(f"Buying {qty} shares of {symbol}")
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side="buy",
            type="market",
            time_in_force="gtc"
        )
        
        # Record the trade
        trade_record = {
            "symbol": symbol,
            "action": "BUY",
            "quantity": qty,
            "order_id": order.id,
            "timestamp": datetime.now().isoformat(),
            "status": order.status
        }
        trade_history.append(trade_record)
        
        logger.info(f"Buy order placed for {qty} shares of {symbol}: {order.id}")
        return trade_record
        
    except Exception as e:
        logger.error(f"Error executing buy order for {symbol}: {e}")
        raise

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((APIError, RateLimitException)),
    reraise=True
)
async def execute_sell(symbol: str, qty: int = DEFAULT_QUANTITY) -> Dict[str, Any]:
    """
    Execute a sell order for the specified symbol.
    
    Args:
        symbol: Stock symbol to sell
        qty: Quantity to sell (default: 1)
        
    Returns:
        Dictionary with order details
    """
    try:
        logger.info(f"Selling {qty} shares of {symbol}")
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side="sell",
            type="market",
            time_in_force="gtc"
        )
        
        # Record the trade
        trade_record = {
            "symbol": symbol,
            "action": "SELL",
            "quantity": qty,
            "order_id": order.id,
            "timestamp": datetime.now().isoformat(),
            "status": order.status
        }
        trade_history.append(trade_record)
        
        logger.info(f"Sell order placed for {qty} shares of {symbol}: {order.id}")
        return trade_record
        
    except Exception as e:
        logger.error(f"Error executing sell order for {symbol}: {e}")
        raise

async def process_signal(signal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a trading signal and execute a trade if appropriate.
    
    Args:
        signal_data: Trading signal data
        
    Returns:
        Dictionary with trade details if a trade was executed, None otherwise
    """
    try:
        # Extract signal details
        symbol = signal_data.get("symbol")
        action = signal_data.get("action")
        confidence = float(signal_data.get("confidence", 0))
        
        if not symbol or not action:
            logger.warning(f"Invalid signal: missing symbol or action: {signal_data}")
            return None
        
        # Log the received signal
        logger.info(f"Received signal: {symbol} - {action} (confidence: {confidence:.2f})")
        
        # Check confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
            logger.info(f"Signal confidence {confidence:.2f} below threshold {CONFIDENCE_THRESHOLD} - ignoring")
            return None
        
        # Process based on trading mode
        if TRADE_MODE == "auto":
            # Execute trade automatically
            if action == "BUY":
                return await execute_buy(symbol)
            elif action == "SELL":
                return await execute_sell(symbol)
            else:
                logger.info(f"HOLD signal for {symbol} - no action taken")
                return None
        else:
            # Manual mode - just log the signal
            logger.info(f"🔔 [MANUAL MODE] Signal received for {symbol} → Action: {action}, Confidence: {confidence:.2f}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing signal: {e}")
        return None

async def send_heartbeat(websocket):
    """Send periodic heartbeats to keep the WebSocket connection alive"""
    while True:
        try:
            await websocket.send(json.dumps({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }))
            await asyncio.sleep(HEARTBEAT_INTERVAL)
        except websockets.exceptions.ConnectionClosed:
            break
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            break

async def get_positions() -> List[Dict[str, Any]]:
    """Get current positions from Alpaca"""
    try:
        positions = api.list_positions()
        return [
            {
                "symbol": position.symbol,
                "qty": position.qty,
                "market_value": position.market_value,
                "unrealized_pl": position.unrealized_pl,
                "current_price": position.current_price
            }
            for position in positions
        ]
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return []

async def websocket_client():
    """Connect to the WebSocket signal server and process signals"""
    reconnect_delay = 1  # Start with 1 second delay
    
    while True:
        try:
            logger.info(f"Connecting to WebSocket server at {WEBSOCKET_URL}")
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                # Reset reconnect delay on successful connection
                reconnect_delay = 1
                
                # Start heartbeat task
                heartbeat_task = asyncio.create_task(send_heartbeat(websocket))
                
                # Send initial message
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "client": "auto-trader",
                    "mode": TRADE_MODE
                }))
                
                # Process incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        # Handle different message types
                        if data.get("type") == "pong":
                            logger.debug("Received heartbeat response")
                            continue
                        elif data.get("type") == "signal":
                            await process_signal(data)
                        elif data.get("type") == "error":
                            logger.error(f"Error from server: {data.get('message')}")
                        else:
                            logger.debug(f"Received message: {data}")
                            
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {message}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                
                # Cancel heartbeat task when connection closes
                heartbeat_task.cancel()
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        
        # Exponential backoff for reconnection
        logger.info(f"Reconnecting in {reconnect_delay} seconds...")
        await asyncio.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, 60)  # Double delay, max 60 seconds

def handle_shutdown(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutdown signal received, closing...")
    # Save trade history to file
    with open("trade_history.json", "w") as f:
        json.dump(trade_history, f, indent=2)
    logger.info("Trade history saved to trade_history.json")
    sys.exit(0)

async def status_reporter():
    """Periodically report status and positions"""
    while True:
        try:
            # Get account info
            account = api.get_account()
            logger.info(f"Account value: ${float(account.portfolio_value):.2f}, Cash: ${float(account.cash):.2f}")
            
            # Get positions
            positions = await get_positions()
            if positions:
                logger.info(f"Current positions ({len(positions)}):")
                for position in positions:
                    logger.info(f"  {position['symbol']}: {position['qty']} shares, Value: ${float(position['market_value']):.2f}, P/L: ${float(position['unrealized_pl']):.2f}")
            else:
                logger.info("No open positions")
                
            # Report trade mode
            logger.info(f"Trading mode: {TRADE_MODE.upper()}")
            
            # Wait before next report
            await asyncio.sleep(300)  # Report every 5 minutes
            
        except Exception as e:
            logger.error(f"Error in status reporter: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error

async def main():
    """Main entry point"""
    try:
        logger.info("Starting NexusSentinel Auto-Trader")
        logger.info(f"Trading mode: {TRADE_MODE.upper()}")
        logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        # Start tasks
        await asyncio.gather(
            websocket_client(),
            status_reporter()
        )
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
