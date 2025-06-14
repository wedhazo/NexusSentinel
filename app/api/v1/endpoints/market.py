"""
Market data endpoints for NexusSentinel API.

This module provides endpoints for market data like indices and charts.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db

# Create router
router = APIRouter()

# Pydantic Models
class MarketIndex(BaseModel):
    name: str
    symbol: str
    currentValue: float
    change: float
    changePercent: float
    color: str

class HistoricalDataPoint(BaseModel):
    date: str
    sp500: float
    nasdaq: float
    dowJones: float

class MarketOverviewResponse(BaseModel):
    indices: List[MarketIndex]
    historical: List[HistoricalDataPoint]

# Endpoints
@router.get("/overview", response_model=MarketOverviewResponse)
async def get_market_overview(
    days: int = Query(30, description="Number of days of historical data", ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive market overview data."""
    
    # Mock data for now - would be replaced with real data from database or API
    indices = [
        {
            "name": "S&P 500",
            "symbol": "SPX",
            "currentValue": 5280.42,
            "change": 28.65,
            "changePercent": 0.54,
            "color": "#4ade80"  # green-400
        },
        {
            "name": "NASDAQ",
            "symbol": "COMP",
            "currentValue": 18432.15,
            "change": 145.78,
            "changePercent": 0.79,
            "color": "#4ade80"  # green-400
        },
        {
            "name": "Dow Jones",
            "symbol": "DJI",
            "currentValue": 41876.22,
            "change": -52.43,
            "changePercent": -0.12,
            "color": "#f87171"  # red-400
        },
        {
            "name": "Russell 2000",
            "symbol": "RUT",
            "currentValue": 2245.36,
            "change": 12.68,
            "changePercent": 0.57,
            "color": "#4ade80"  # green-400
        }
    ]
    
    # Generate historical data
    historical = []
    today = datetime.now()
    
    # Base values (current values)
    base_sp500 = 5280.42
    base_nasdaq = 18432.15
    base_dow = 41876.22
    
    # Generate data for the past N days
    for i in range(days, -1, -1):
        past_date = today - timedelta(days=i)
        date_str = past_date.strftime("%Y-%m-%d")
        
        # Add some randomness for realistic data
        day_factor = i / days
        volatility = 0.02  # 2% volatility
        trend = 0.001  # slight upward trend
        
        # Different random walk for each index
        sp500_random = (1 - day_factor) * base_sp500 * (1 + ((hash(f"sp500-{i}") % 1000) / 1000 - 0.5) * volatility + trend * (days - i))
        nasdaq_random = (1 - day_factor) * base_nasdaq * (1 + ((hash(f"nasdaq-{i}") % 1000) / 1000 - 0.5) * volatility + trend * (days - i))
        dow_random = (1 - day_factor) * base_dow * (1 + ((hash(f"dow-{i}") % 1000) / 1000 - 0.5) * volatility + trend * (days - i))
        
        historical.append({
            "date": date_str,
            "sp500": round(base_sp500 * (0.9 + 0.1 * day_factor) + sp500_random * 0.05, 2),
            "nasdaq": round(base_nasdaq * (0.9 + 0.1 * day_factor) + nasdaq_random * 0.05, 2),
            "dowJones": round(base_dow * (0.9 + 0.1 * day_factor) + dow_random * 0.05, 2)
        })
    
    return {
        "indices": indices,
        "historical": historical
    }
