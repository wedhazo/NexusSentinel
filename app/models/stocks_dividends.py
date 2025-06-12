"""
SQLAlchemy model for stocks_dividends table.

This module defines the StocksDividends model which represents
dividend events for stocks.
"""

from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey, 
    Index, UniqueConstraint, func, String
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class StocksDividends(Base):
    """
    StocksDividends model representing dividend events for stocks.
    
    This table contains information about dividend payments including
    ex-dividend dates, payment amounts, and dividend types.
    """
    __tablename__ = "stocks_dividends"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Dividend data
    ex_date = Column(Date, nullable=False, index=True)  # Ex-dividend date
    record_date = Column(Date, nullable=True)  # Record date
    payment_date = Column(Date, nullable=True)  # Payment date
    declaration_date = Column(Date, nullable=True)  # Declaration date
    
    # Dividend details
    amount = Column(Float, nullable=False)  # Dividend amount per share
    type = Column(String(50), nullable=True)  # Type of dividend (e.g., "Regular", "Special", "Stock")
    frequency = Column(String(20), nullable=True)  # Frequency (e.g., "Quarterly", "Annual", "One-time")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    currency = Column(String(10), nullable=True, default="USD")
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="dividends")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock on a specific ex-date
        UniqueConstraint('stock_id', 'ex_date', name='uq_stocks_dividends_stock_ex_date'),
        # Index for querying by date range
        Index('ix_stocks_dividends_date_range', 'stock_id', 'ex_date'),
        # Index for querying by dividend amount
        Index('ix_stocks_dividends_amount', 'stock_id', 'amount'),
    )
    
    def __repr__(self):
        """String representation of the StocksDividends model."""
        return f"<StocksDividends(stock_id={self.stock_id}, ex_date='{self.ex_date}', amount={self.amount})>"
