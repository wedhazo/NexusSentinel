"""
Sentiment alerts endpoints for NexusSentinel API.

This module provides endpoints for managing sentiment alerts, including:
- Creating new alerts
- Listing all alerts
- Deleting alerts
- Checking and updating alert status based on sentiment scores
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

# Import database and models
from app.database import get_db
from app.models.alerts import SentimentAlert
from app.models.stocks_core import StocksCore
from app.models.stocks_sentiment import StocksSentimentDailySummary

# Define __all__ to export models for OpenAPI schema generation
__all__ = ["AlertCreate", "AlertResponse"]

# Create router
router = APIRouter()

# --- Pydantic Models for Request/Response ---

class AlertCreate(BaseModel):
    """Schema for creating a new sentiment alert."""
    symbol: str = Field(..., description="Stock ticker symbol", example="AAPL")
    threshold: float = Field(..., description="Sentiment score threshold", example=0.8, ge=-1.0, le=1.0)
    direction: str = Field(..., description="Direction for triggering the alert", example="above")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "threshold": 0.8,
                "direction": "above"
            }
        }
    )


class AlertResponse(BaseModel):
    """Schema for sentiment alert response."""
    id: int
    symbol: str
    threshold: float
    direction: str
    created_at: datetime
    triggered: bool
    current_sentiment: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# --- Endpoints ---

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    triggered: Optional[bool] = Query(None, description="Filter by triggered status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all sentiment alerts with optional filtering.
    
    Returns a list of all alerts with their current status.
    Can be filtered by symbol and/or triggered status.
    """
    # Build query with filters
    query = select(SentimentAlert)
    
    if symbol:
        query = query.where(func.upper(SentimentAlert.symbol) == func.upper(symbol))
    
    if triggered is not None:
        query = query.where(SentimentAlert.triggered == triggered)
    
    # Execute query
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Get current sentiment scores for each alert
    alert_responses = []
    for alert in alerts:
        # Get the latest sentiment score for this symbol
        sentiment_query = (
            select(StocksSentimentDailySummary.overall_sentiment_score)
            .join(StocksCore, StocksSentimentDailySummary.stock_id == StocksCore.stock_id)
            .where(func.upper(StocksCore.symbol) == func.upper(alert.symbol))
            .order_by(StocksSentimentDailySummary.date.desc())
            .limit(1)
        )
        sentiment_result = await db.execute(sentiment_query)
        current_sentiment = sentiment_result.scalar_one_or_none()
        
        # Create response with current sentiment
        alert_dict = {
            "id": alert.id,
            "symbol": alert.symbol,
            "threshold": alert.threshold,
            "direction": alert.direction,
            "created_at": alert.created_at,
            "triggered": alert.triggered,
            "current_sentiment": current_sentiment
        }
        alert_responses.append(AlertResponse(**alert_dict))
    
    return alert_responses


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(alert: AlertCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new sentiment alert.
    
    Requires a valid stock symbol, threshold value (-1.0 to 1.0),
    and direction ('above' or 'below').
    """
    # Validate direction
    if alert.direction not in ["above", "below"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direction must be either 'above' or 'below'"
        )
    
    # Check if the stock exists
    stock_query = select(StocksCore).where(func.upper(StocksCore.symbol) == func.upper(alert.symbol))
    stock_result = await db.execute(stock_query)
    stock = stock_result.scalar_one_or_none()
    
    # Create new alert
    new_alert = SentimentAlert(
        symbol=alert.symbol.upper(),
        threshold=alert.threshold,
        direction=alert.direction,
        stock_id=stock.stock_id if stock else None
    )
    
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)
    
    # Get the latest sentiment score for this symbol
    current_sentiment = None
    if stock:
        sentiment_query = (
            select(StocksSentimentDailySummary.overall_sentiment_score)
            .where(
                and_(
                    StocksSentimentDailySummary.stock_id == stock.stock_id,
                    StocksSentimentDailySummary.overall_sentiment_score.is_not(None)
                )
            )
            .order_by(StocksSentimentDailySummary.date.desc())
            .limit(1)
        )
        sentiment_result = await db.execute(sentiment_query)
        current_sentiment = sentiment_result.scalar_one_or_none()
    
    # Check if the alert should be triggered immediately
    if current_sentiment is not None:
        if (alert.direction == "above" and current_sentiment > alert.threshold) or \
           (alert.direction == "below" and current_sentiment < alert.threshold):
            new_alert.triggered = True
            await db.commit()
    
    # Return response
    return {
        "id": new_alert.id,
        "symbol": new_alert.symbol,
        "threshold": new_alert.threshold,
        "direction": new_alert.direction,
        "created_at": new_alert.created_at,
        "triggered": new_alert.triggered,
        "current_sentiment": current_sentiment
    }


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int = Path(..., description="ID of the alert to delete"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a sentiment alert.
    
    Removes the alert with the specified ID from the database.
    """
    # Find the alert
    query = select(SentimentAlert).where(SentimentAlert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    
    # Delete the alert
    await db.delete(alert)
    await db.commit()
    
    return None  # 204 No Content response


@router.post("/check", response_model=List[AlertResponse])
async def check_alerts(db: AsyncSession = Depends(get_db)):
    """
    Check all active alerts against current sentiment scores.
    
    This endpoint evaluates all non-triggered alerts and updates their status
    if the sentiment score crosses the specified threshold.
    
    Returns a list of alerts that were triggered during this check.
    """
    # Get all active (non-triggered) alerts
    query = select(SentimentAlert).where(SentimentAlert.triggered == False)
    result = await db.execute(query)
    active_alerts = result.scalars().all()
    
    newly_triggered = []
    
    # Check each alert
    for alert in active_alerts:
        # Get the latest sentiment score for this symbol
        sentiment_query = (
            select(StocksSentimentDailySummary.overall_sentiment_score)
            .join(StocksCore, StocksSentimentDailySummary.stock_id == StocksCore.stock_id)
            .where(func.upper(StocksCore.symbol) == func.upper(alert.symbol))
            .order_by(StocksSentimentDailySummary.date.desc())
            .limit(1)
        )
        sentiment_result = await db.execute(sentiment_query)
        current_sentiment = sentiment_result.scalar_one_or_none()
        
        # Skip if no sentiment data available
        if current_sentiment is None:
            continue
        
        # Check if threshold is crossed
        if (alert.direction == "above" and current_sentiment > alert.threshold) or \
           (alert.direction == "below" and current_sentiment < alert.threshold):
            # Update alert status
            alert.triggered = True
            newly_triggered.append({
                "id": alert.id,
                "symbol": alert.symbol,
                "threshold": alert.threshold,
                "direction": alert.direction,
                "created_at": alert.created_at,
                "triggered": True,
                "current_sentiment": current_sentiment
            })
    
    # Commit changes if any alerts were triggered
    if newly_triggered:
        await db.commit()
    
    return [AlertResponse(**alert) for alert in newly_triggered]
