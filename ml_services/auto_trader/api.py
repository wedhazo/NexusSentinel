#!/usr/bin/env python3
"""
NexusSentinel Auto-Trader API

This module provides a FastAPI service for the auto-trader module, exposing endpoints
to get account info, positions, trade history, execute manual trades, and set the trading mode.

Usage:
    uvicorn api:app --host 0.0.0.0 --port 8000

Environment Variables:
    ALPACA_API_KEY: Alpaca API key
    ALPACA_API_SECRET: Alpaca API secret
    ALPACA_BASE_URL: Alpaca API base URL (default: https://paper-api.alpaca.markets)
    TRADE_MODE: Trading mode (auto or manual, default: manual)
    LOG_LEVEL: Logging level (default: INFO)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import alpaca_trade_api as tradeapi
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from alpaca_trade_api.rest import APIError, RateLimitException

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("auto_trader_api.log")
    ]
)
logger = logging.getLogger("auto-trader-api")

# Load configuration from environment variables
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
DEFAULT_QUANTITY = int(os.getenv("DEFAULT_QUANTITY", "1"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Global variables
TRADE_MODE = os.getenv("TRADE_MODE", "manual").lower()
TRADE_HISTORY_FILE = "trade_history.json"
trade_history = []

# Load trade history from file if it exists
if os.path.exists(TRADE_HISTORY_FILE):
    try:
        with open(TRADE_HISTORY_FILE, "r") as f:
            trade_history = json.load(f)
        logger.info(f"Loaded {len(trade_history)} trades from history file")
    except Exception as e:
        logger.error(f"Error loading trade history: {e}")

# Check for required environment variables
if not ALPACA_API_KEY or not ALPACA_API_SECRET:
    logger.error("ALPACA_API_KEY and ALPACA_API_SECRET must be set")
    raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET must be set")

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
    raise

# Pydantic models
class TradeSignal(BaseModel):
    symbol: str
    action: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    quantity: Optional[int] = Field(DEFAULT_QUANTITY, description="Number of shares to trade")

class TradeModeRequest(BaseModel):
    mode: str = Field(..., description="Trading mode: 'auto' or 'manual'")

class TradeResponse(BaseModel):
    symbol: str
    action: str
    quantity: int
    order_id: Optional[str] = None
    status: str
    timestamp: str

class AccountInfo(BaseModel):
    equity: str
    cash: str
    buying_power: str
    status: str
    currency: str
    portfolio_value: str
    pattern_day_trader: bool
    trading_blocked: bool
    account_blocked: bool
    created_at: str
    multiplier: str

class Position(BaseModel):
    symbol: str
    qty: str
    market_value: str
    cost_basis: str
    unrealized_pl: str
    unrealized_plpc: str
    current_price: str
    lastday_price: str
    change_today: str

# Initialize FastAPI app
app = FastAPI(
    title="NexusSentinel Auto-Trader API",
    description="API for the NexusSentinel auto-trader module",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def save_trade_history():
    """Save trade history to file"""
    try:
        with open(TRADE_HISTORY_FILE, "w") as f:
            json.dump(trade_history, f, indent=2)
        logger.info(f"Saved {len(trade_history)} trades to history file")
    except Exception as e:
        logger.error(f"Error saving trade history: {e}")

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((APIError, RateLimitException)),
    reraise=True
)
async def execute_buy(symbol: str, qty: int = DEFAULT_QUANTITY) -> Dict[str, Any]:
    """Execute a buy order for the specified symbol."""
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
        save_trade_history()
        
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
    """Execute a sell order for the specified symbol."""
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
        save_trade_history()
        
        logger.info(f"Sell order placed for {qty} shares of {symbol}: {order.id}")
        return trade_record
        
    except Exception as e:
        logger.error(f"Error executing sell order for {symbol}: {e}")
        raise

# API endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "NexusSentinel Auto-Trader API",
        "version": "1.0.0",
        "trading_mode": TRADE_MODE,
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Alpaca API connection
        account = api.get_account()
        return {
            "status": "healthy",
            "alpaca_connection": "connected",
            "trading_mode": TRADE_MODE,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "alpaca_connection": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/account", response_model=AccountInfo)
async def get_account_info():
    """Get account information from Alpaca."""
    try:
        account = api.get_account()
        return {
            "equity": account.equity,
            "cash": account.cash,
            "buying_power": account.buying_power,
            "status": account.status,
            "currency": account.currency,
            "portfolio_value": account.portfolio_value,
            "pattern_day_trader": account.pattern_day_trader,
            "trading_blocked": account.trading_blocked,
            "account_blocked": account.account_blocked,
            "created_at": account.created_at,
            "multiplier": account.multiplier
        }
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting account info: {str(e)}")

@app.get("/positions", response_model=List[Position])
async def get_positions():
    """Get current positions from Alpaca."""
    try:
        positions = api.list_positions()
        return [
            {
                "symbol": position.symbol,
                "qty": position.qty,
                "market_value": position.market_value,
                "cost_basis": position.cost_basis,
                "unrealized_pl": position.unrealized_pl,
                "unrealized_plpc": position.unrealized_plpc,
                "current_price": position.current_price,
                "lastday_price": position.lastday_price,
                "change_today": position.change_today
            }
            for position in positions
        ]
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting positions: {str(e)}")

@app.get("/trades", response_model=List[Dict[str, Any]])
async def get_trades():
    """Get trade history."""
    return trade_history

@app.post("/set-mode", response_model=Dict[str, str])
async def set_mode(request: TradeModeRequest):
    """Set trading mode (auto or manual)."""
    global TRADE_MODE
    
    if request.mode.lower() not in ["auto", "manual"]:
        raise HTTPException(status_code=400, detail="Mode must be 'auto' or 'manual'")
    
    TRADE_MODE = request.mode.lower()
    logger.info(f"Trading mode set to {TRADE_MODE.upper()}")
    
    return {"mode": TRADE_MODE}

@app.get("/mode", response_model=Dict[str, str])
async def get_mode():
    """Get current trading mode."""
    return {"mode": TRADE_MODE}

@app.post("/manual-trade", response_model=TradeResponse)
async def manual_trade(signal: TradeSignal):
    """Execute a manual trade."""
    global TRADE_MODE
    
    # Check if we're in manual mode
    if TRADE_MODE != "manual":
        logger.warning(f"Manual trade requested but mode is {TRADE_MODE}")
        raise HTTPException(status_code=400, detail="Cannot execute manual trade in auto mode")
    
    try:
        if signal.action == "BUY":
            result = await execute_buy(signal.symbol, signal.quantity)
            return result
        elif signal.action == "SELL":
            result = await execute_sell(signal.symbol, signal.quantity)
            return result
        else:
            logger.info(f"HOLD signal for {signal.symbol} - no action taken")
            return {
                "symbol": signal.symbol,
                "action": "HOLD",
                "quantity": signal.quantity,
                "order_id": None,
                "status": "no_action",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error executing manual trade: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")

@app.post("/auto-trade", response_model=TradeResponse)
async def auto_trade(signal: TradeSignal):
    """Execute an automatic trade."""
    global TRADE_MODE
    
    # Check if we're in auto mode
    if TRADE_MODE != "auto":
        logger.warning(f"Auto trade requested but mode is {TRADE_MODE}")
        raise HTTPException(status_code=400, detail="Cannot execute auto trade in manual mode")
    
    try:
        if signal.action == "BUY":
            result = await execute_buy(signal.symbol, signal.quantity)
            return result
        elif signal.action == "SELL":
            result = await execute_sell(signal.symbol, signal.quantity)
            return result
        else:
            logger.info(f"HOLD signal for {signal.symbol} - no action taken")
            return {
                "symbol": signal.symbol,
                "action": "HOLD",
                "quantity": signal.quantity,
                "order_id": None,
                "status": "no_action",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error executing auto trade: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
