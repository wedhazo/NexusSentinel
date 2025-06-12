"""
SQLAlchemy model for stocks_splits table.

This module defines the StocksSplits model which represents
stock split events for stocks.
"""

from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey, 
    Index, UniqueConstraint, func, String
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class StocksSplits(Base):
    """
    StocksSplits model representing stock split events.
    
    This table contains information about stock splits including
    ex-dates and split ratios (from_shares:to_shares).
    """
    __tablename__ = "stocks_splits"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Split data
    ex_date = Column(Date, nullable=False, index=True)  # Ex-date for the split
    announcement_date = Column(Date, nullable=True)  # Date when split was announced
    execution_date = Column(Date, nullable=True)  # Date when split was executed
    
    # Split ratio details
    from_shares = Column(Integer, nullable=False)  # Number of shares before split
    to_shares = Column(Integer, nullable=False)  # Number of shares after split
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    notes = Column(String(500), nullable=True)  # Any notes about the split
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="splits")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock on a specific ex-date
        UniqueConstraint('stock_id', 'ex_date', name='uq_stocks_splits_stock_ex_date'),
        # Index for querying by date range
        Index('ix_stocks_splits_date_range', 'stock_id', 'ex_date'),
        # Index for querying by split ratio
        Index('ix_stocks_splits_ratio', 'from_shares', 'to_shares'),
    )
    
    def __repr__(self):
        """String representation of the StocksSplits model."""
        return f"<StocksSplits(stock_id={self.stock_id}, ex_date='{self.ex_date}', ratio={self.from_shares}:{self.to_shares})>"
