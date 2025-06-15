"""
SQLAlchemy model for watchlists table.

This module defines the Watchlist model which represents user-created
watchlists of stocks in the database, with many-to-many relationship to stocks_core.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Table, 
    Index, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

# Association table for many-to-many relationship between watchlists and stocks
watchlist_stocks = Table(
    'watchlist_stocks',
    Base.metadata,
    Column('watchlist_id', Integer, ForeignKey('watchlists.watchlist_id', ondelete='CASCADE'), primary_key=True),
    Column('stock_id', Integer, ForeignKey('stocks_core.stock_id', ondelete='CASCADE'), primary_key=True),
    # Track when a stock was added to the watchlist
    Column('added_at', DateTime, default=func.now(), nullable=False)
)


class Watchlist(Base):
    """
    Watchlist model representing user-created collections of stocks.
    
    This table allows users to create and manage lists of stocks they want to monitor.
    Each watchlist can contain multiple stocks, and each stock can be in multiple watchlists.
    """
    __tablename__ = "watchlists"
    
    # Primary key
    watchlist_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Watchlist information
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    # User reference (for future authentication implementation)
    user_id = Column(Integer, nullable=True, index=True)
    
    # Metadata fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    
    # Many-to-many relationship with stocks
    stocks = relationship(
        "StocksCore",
        secondary=watchlist_stocks,
        backref="watchlists",
        lazy="selectin"
    )
    
    # Indexes for performance
    __table_args__ = (
        # Ensure unique watchlist names per user
        UniqueConstraint('name', 'user_id', name='uq_watchlist_name_user'),
        # Index for quick user lookups
        Index('ix_watchlists_user_id', 'user_id'),
    )
    
    def __repr__(self):
        """String representation of the Watchlist model."""
        return f"<Watchlist(id={self.watchlist_id}, name='{self.name}', stocks={len(self.stocks)})>"
