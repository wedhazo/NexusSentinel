"""
Market data endpoints for NexusSentinel API.

This module provides endpoints for querying market data, including:
- Market indices (S&P 500, NASDAQ, Dow Jones, etc.)
- Historical price data for major indices
- Market volatility metrics
- Trading volume statistics
- Market breadth indicators
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

# Import database
from app.database import get_db

# Define __all__ to export models for OpenAPI schema generation
__all__ = [
    "MarketIndex", "HistoricalDataPoint", "MarketOverviewResponse", 
    "VolatilityMetric", "TradingVolumeMetric", "MarketBreadthMetric"
]

# Create router
router = APIRouter(prefix="/market", tags=["Market"])

# --- Pydantic Models for Request/Response ---

class MarketIndex(BaseModel):
    """Schema for market index data."""
    name: str = Field(..., description="Index name", example="S&P 500")
    symbol: str = Field(..., description="Index symbol", example="SPX")
    currentValue: float = Field(..., description="Current index value", example=5280.42)
    change: float = Field(..., description="Point change", example=28.65)
    changePercent: float = Field(..., description="Percentage change", example=0.54)
    color: str = Field(..., description="Display color for UI", example="#4ade80")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "S&P 500",
                "symbol": "SPX",
                "currentValue": 5280.42,
                "change": 28.65,
                "changePercent": 0.54,
                "color": "#4ade80"
            }
        }
    )


class HistoricalDataPoint(BaseModel):
    """Schema for historical market data points."""
    date: str = Field(..., description="Date in ISO format", example="2025-06-14")
    sp500: float = Field(..., description="S&P 500 value", example=5280.42)
    nasdaq: float = Field(..., description="NASDAQ value", example=18432.15)
    dowJones: float = Field(..., description="Dow Jones value", example=41876.22)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-06-14",
                "sp500": 5280.42,
                "nasdaq": 18432.15,
                "dowJones": 41876.22
            }
        }
    )


class VolatilityMetric(BaseModel):
    """Schema for market volatility data."""
    value: float = Field(..., description="Volatility index value", example=18.45)
    change: float = Field(..., description="Change in volatility", example=-0.32)
    level: str = Field(..., description="Volatility level description", example="Moderate")


class TradingVolumeMetric(BaseModel):
    """Schema for trading volume data."""
    value: float = Field(..., description="Trading volume in billions", example=4.2)
    change_percent: float = Field(..., description="Percent change from average", example=12.0)


class MarketBreadthMetric(BaseModel):
    """Schema for market breadth data."""
    percent: float = Field(..., description="Percentage of advancing stocks", example=62.0)
    trend: str = Field(..., description="Market trend description", example="Bullish momentum")


class MarketOverviewResponse(BaseModel):
    """Schema for market overview response."""
    indices: List[MarketIndex] = Field(..., description="Current market indices data")
    historical: List[HistoricalDataPoint] = Field(..., description="Historical data for charts")
    volatility: Optional[VolatilityMetric] = Field(None, description="Market volatility metrics")
    trading_volume: Optional[TradingVolumeMetric] = Field(None, description="Trading volume statistics")
    advancing_stocks: Optional[MarketBreadthMetric] = Field(None, description="Market breadth indicators")


# --- Endpoints ---

@router.get("/overview", response_model=MarketOverviewResponse)
async def get_market_overview(
    days: int = Query(30, description="Number of days of historical data to return", ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive market overview data.
    
    This endpoint returns current market indices data and historical data for charts.
    It includes:
    - Major market indices (S&P 500, NASDAQ, Dow Jones, Russell 2000)
    - Historical price data for the specified number of days
    - Market volatility metrics
    - Trading volume statistics
    - Market breadth indicators
    
    In the future, this will be connected to real market data sources.
    """
    try:
        # In a production environment, this would fetch data from a market data provider
        # or from a database that's regularly updated with market data
        
        # For now, generate mock data that's realistic
        
        # Current market indices
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
            
            # Add some randomness and trend for realistic data
            day_factor = i / days  # 1.0 -> 0.0 as we approach today
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
        
        # Additional market metrics
        volatility = {
            "value": 18.45,
            "change": -0.32,
            "level": "Moderate"
        }
        
        trading_volume = {
            "value": 4.2,
            "change_percent": 12.0
        }
        
        advancing_stocks = {
            "percent": 62.0,
            "trend": "Bullish momentum"
        }
        
        # Return the complete market overview response
        return {
            "indices": indices,
            "historical": historical,
            "volatility": volatility,
            "trading_volume": trading_volume,
            "advancing_stocks": advancing_stocks
        }
        
    except Exception as e:
        # Log the error
        print(f"Error in market overview endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve market data"
        )


@router.get("/indices", response_model=List[MarketIndex])
async def get_market_indices(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current market indices data.
    
    This endpoint returns current values for major market indices:
    - S&P 500
    - NASDAQ
    - Dow Jones
    - Russell 2000
    """
    try:
        # Mock data for now
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
        
        return indices
        
    except Exception as e:
        # Log the error
        print(f"Error in market indices endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve market indices data"
        )


@router.get("/historical", response_model=List[HistoricalDataPoint])
async def get_historical_market_data(
    days: int = Query(30, description="Number of days of historical data to return", ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical market data for major indices.
    
    This endpoint returns historical price data for:
    - S&P 500
    - NASDAQ
    - Dow Jones
    
    The data can be used for generating charts and trend analysis.
    """
    try:
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
            
            # Add some randomness and trend for realistic data
            day_factor = i / days  # 1.0 -> 0.0 as we approach today
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
        
        return historical
        
    except Exception as e:
        # Log the error
        print(f"Error in historical market data endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve historical market data"
        )
