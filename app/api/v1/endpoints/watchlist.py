"""
Watchlist endpoints for NexusSentinel API.

This module provides endpoints for managing the watchlist feature, including:
- Getting all watchlist items
- Adding a stock to the watchlist
- Removing a stock from the watchlist

Since authentication is not yet implemented, this is a global watchlist.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, Field, ConfigDict

# Import database and models
from app.database import get_db
from app.models.stocks_core import StocksCore
from app.models.watchlist import Watchlist

# Define __all__ to export models for OpenAPI schema generation
__all__ = ["WatchlistItemCreate", "WatchlistItemResponse"]

# Create router
router = APIRouter()

# --- Pydantic Models for Request/Response ---

class WatchlistItemCreate(BaseModel):
    """Schema for creating a new watchlist item."""
    symbol: str = Field(..., description="Stock ticker symbol", example="AAPL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL"
            }
        }
    )


class WatchlistItemResponse(BaseModel):
    """Schema for watchlist item response."""
    id: int
    symbol: str
    company_name: str
    date_added: datetime
    sentiment_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# --- Endpoints ---

@router.get("/", response_model=List[WatchlistItemResponse])
async def get_watchlist_items(db: AsyncSession = Depends(get_db)):
    """
    Get all watchlist items.
    
    Returns a list of all stocks in the watchlist with their details.
    """
    # Query watchlist items with joined stock information
    query = (
        select(Watchlist, StocksCore.company_name)
        .join(StocksCore, Watchlist.stock_id == StocksCore.stock_id)
        .order_by(Watchlist.date_added.desc())
    )
    
    result = await db.execute(query)
    items = result.all()
    
    # Process results to include company name
    watchlist_items = []
    for item, company_name in items:
        # Get latest sentiment score if available
        sentiment_query = (
            select(StocksCore)
            .where(StocksCore.stock_id == item.stock_id)
            .options(joinedload(StocksCore.sentiment_summaries))
        )
        stock_result = await db.execute(sentiment_query)
        stock = stock_result.scalar_one_or_none()
        
        sentiment_score = None
        if stock and stock.sentiment_summaries:
            # Get the most recent sentiment summary
            latest_sentiment = max(stock.sentiment_summaries, key=lambda x: x.date, default=None)
            if latest_sentiment:
                sentiment_score = latest_sentiment.overall_sentiment_score
        
        watchlist_items.append({
            "id": item.id,
            "symbol": item.symbol,
            "company_name": company_name,
            "date_added": item.date_added,
            "sentiment_score": sentiment_score
        })
    
    return watchlist_items


@router.post("/", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(item: WatchlistItemCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a stock to the watchlist.
    
    Requires a valid stock symbol that exists in the database.
    """
    # Check if the stock exists
    query = select(StocksCore).where(StocksCore.symbol == item.symbol.upper())
    result = await db.execute(query)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{item.symbol}' not found"
        )
    
    # Check if the stock is already in the watchlist
    watchlist_query = select(Watchlist).where(Watchlist.symbol == item.symbol.upper())
    watchlist_result = await db.execute(watchlist_query)
    existing_item = watchlist_result.scalar_one_or_none()
    
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock with symbol '{item.symbol}' is already in the watchlist"
        )
    
    # Create new watchlist item
    new_item = Watchlist(
        symbol=item.symbol.upper(),
        stock_id=stock.stock_id
    )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    # Get sentiment score if available
    sentiment_score = None
    if stock.sentiment_summaries:
        # Get the most recent sentiment summary
        latest_sentiment = max(stock.sentiment_summaries, key=lambda x: x.date, default=None)
        if latest_sentiment:
            sentiment_score = latest_sentiment.overall_sentiment_score
    
    # Return response
    return {
        "id": new_item.id,
        "symbol": new_item.symbol,
        "company_name": stock.company_name,
        "date_added": new_item.date_added,
        "sentiment_score": sentiment_score
    }


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    symbol: str = Path(..., description="Stock ticker symbol to remove from watchlist"),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a stock from the watchlist.
    
    Deletes the watchlist item with the specified symbol.
    """
    # Find and delete the watchlist item
    delete_query = delete(Watchlist).where(Watchlist.symbol == symbol.upper())
    result = await db.execute(delete_query)
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found in watchlist"
        )
    
    await db.commit()
    
    return None  # 204 No Content response
