"""
API endpoints for watchlists management.

This module provides CRUD operations for watchlists, allowing users to
create, read, update, and delete watchlists of stocks they want to monitor.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.watchlists import Watchlist
from app.models.stocks_core import StocksCore
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Define Pydantic models for request/response schemas
class StockItem(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class WatchlistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the watchlist")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the watchlist")

class WatchlistCreate(WatchlistBase):
    stock_symbols: List[str] = Field(default_factory=list, description="List of stock symbols to add to the watchlist")

class WatchlistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the watchlist")
    description: Optional[str] = Field(None, max_length=500, description="Description of the watchlist")
    stock_symbols: Optional[List[str]] = Field(None, description="List of stock symbols to update in the watchlist")

class WatchlistResponse(WatchlistBase):
    watchlist_id: int
    created_at: datetime
    last_updated: datetime
    stocks: List[StockItem] = []
    
    class Config:
        from_attributes = True

# Create router
router = APIRouter()

@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlists(
    skip: int = Query(0, ge=0, description="Number of watchlists to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of watchlists to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all watchlists with their stocks.
    
    Returns a list of watchlists, each containing its metadata and associated stocks.
    """
    query = select(Watchlist).options(selectinload(Watchlist.stocks)).offset(skip).limit(limit)
    result = await db.execute(query)
    watchlists = result.scalars().all()
    
    return watchlists

@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: int = Path(..., ge=1, description="The ID of the watchlist to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific watchlist by ID.
    
    Returns detailed information about a watchlist, including its stocks.
    """
    query = select(Watchlist).options(selectinload(Watchlist.stocks)).where(Watchlist.watchlist_id == watchlist_id)
    result = await db.execute(query)
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist with ID {watchlist_id} not found"
        )
    
    return watchlist

@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist: WatchlistCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new watchlist.
    
    Accepts watchlist metadata and an optional list of stock symbols to add to the watchlist.
    """
    # Create new watchlist instance
    db_watchlist = Watchlist(
        name=watchlist.name,
        description=watchlist.description
    )
    
    # Add stocks to watchlist if symbols are provided
    if watchlist.stock_symbols:
        # Find stocks by symbols
        query = select(StocksCore).where(StocksCore.symbol.in_(watchlist.stock_symbols))
        result = await db.execute(query)
        stocks = result.scalars().all()
        
        # Check if all symbols were found
        found_symbols = {stock.symbol for stock in stocks}
        missing_symbols = set(watchlist.stock_symbols) - found_symbols
        
        if missing_symbols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock symbols not found: {', '.join(missing_symbols)}"
            )
        
        # Add stocks to watchlist
        db_watchlist.stocks = stocks
    
    try:
        # Add and commit to database
        db.add(db_watchlist)
        await db.commit()
        await db.refresh(db_watchlist)
        return db_watchlist
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Watchlist with this name already exists"
        )

@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_update: WatchlistUpdate,
    watchlist_id: int = Path(..., ge=1, description="The ID of the watchlist to update"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing watchlist.
    
    Updates watchlist metadata and/or its associated stocks.
    """
    # Check if watchlist exists
    query = select(Watchlist).options(selectinload(Watchlist.stocks)).where(Watchlist.watchlist_id == watchlist_id)
    result = await db.execute(query)
    db_watchlist = result.scalar_one_or_none()
    
    if not db_watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist with ID {watchlist_id} not found"
        )
    
    # Update fields if provided
    if watchlist_update.name is not None:
        db_watchlist.name = watchlist_update.name
    
    if watchlist_update.description is not None:
        db_watchlist.description = watchlist_update.description
    
    # Update stocks if provided
    if watchlist_update.stock_symbols is not None:
        # Find stocks by symbols
        query = select(StocksCore).where(StocksCore.symbol.in_(watchlist_update.stock_symbols))
        result = await db.execute(query)
        stocks = result.scalars().all()
        
        # Check if all symbols were found
        found_symbols = {stock.symbol for stock in stocks}
        missing_symbols = set(watchlist_update.stock_symbols) - found_symbols
        
        if missing_symbols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock symbols not found: {', '.join(missing_symbols)}"
            )
        
        # Replace stocks in watchlist
        db_watchlist.stocks = stocks
    
    try:
        # Commit changes
        await db.commit()
        await db.refresh(db_watchlist)
        return db_watchlist
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Watchlist with this name already exists"
        )

@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: int = Path(..., ge=1, description="The ID of the watchlist to delete"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a watchlist.
    
    Removes a watchlist and its associations with stocks.
    """
    # Check if watchlist exists
    query = select(Watchlist).where(Watchlist.watchlist_id == watchlist_id)
    result = await db.execute(query)
    db_watchlist = result.scalar_one_or_none()
    
    if not db_watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist with ID {watchlist_id} not found"
        )
    
    # Delete watchlist
    await db.delete(db_watchlist)
    await db.commit()
    
    return None
