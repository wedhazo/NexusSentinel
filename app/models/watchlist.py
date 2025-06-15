"""
Watchlist model for NexusSentinel API.

This module defines the database model for watchlist items,
which represent stocks that users are interested in tracking.
Since authentication is not yet implemented, this is a global watchlist.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Watchlist(Base):
    """Database model for watchlist items."""
    
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id"), nullable=False)
    date_added = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationship to stocks_core table
    stock = relationship("StocksCore", back_populates="watchlist_items")
    
    def __repr__(self):
        """String representation of the watchlist item."""
        return f"<Watchlist(id={self.id}, symbol='{self.symbol}')>"
