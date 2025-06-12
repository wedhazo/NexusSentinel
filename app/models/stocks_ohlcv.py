"""
SQLAlchemy models for OHLCV (Open, High, Low, Close, Volume) data.

This module defines models for both daily and intraday (5-minute) price data.
"""

from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey,
    Index, UniqueConstraint, func, BigInteger, String
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class StocksOHLCVDaily(Base):
    """
    Daily OHLCV (Open, High, Low, Close, Volume) data for stocks.
    
    This table contains end-of-day price data for each stock.
    """
    __tablename__ = "stocks_ohlcv_daily"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Date of the price data
    date = Column(Date, nullable=False, index=True)
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    data_source = Column(String(50), nullable=True)  # Source of the data (e.g., "Yahoo", "Alpha Vantage")
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="daily_ohlcv")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock on a specific date
        UniqueConstraint('stock_id', 'date', name='uq_stocks_ohlcv_daily_stock_date'),
        # Index for querying by date range
        Index('ix_stocks_ohlcv_daily_date_range', 'stock_id', 'date'),
    )
    
    def __repr__(self):
        """String representation of the StocksOHLCVDaily model."""
        return f"<StocksOHLCVDaily(stock_id={self.stock_id}, date='{self.date}', close={self.close})>"


class StocksOHLCVIntraday5Min(Base):
    """
    Intraday 5-minute OHLCV (Open, High, Low, Close, Volume) data for stocks.
    
    This table contains 5-minute interval price data for each stock.
    """
    __tablename__ = "stocks_ohlcv_intraday_5min"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamp of the price data (includes date and time)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    data_source = Column(String(50), nullable=True)  # Source of the data
    is_market_hours = Column(Integer, default=1, nullable=False)  # Flag for market hours data
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="intraday_ohlcv")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock at a specific timestamp
        UniqueConstraint('stock_id', 'timestamp', name='uq_stocks_ohlcv_intraday_stock_timestamp'),
        # Index for querying by timestamp range
        Index('ix_stocks_ohlcv_intraday_timestamp_range', 'stock_id', 'timestamp'),
        # Index for querying by date (extracted from timestamp)
        Index('ix_stocks_ohlcv_intraday_date', 'stock_id', func.date(timestamp)),
    )
    
    def __repr__(self):
        """String representation of the StocksOHLCVIntraday5Min model."""
        return f"<StocksOHLCVIntraday5Min(stock_id={self.stock_id}, timestamp='{self.timestamp}', close={self.close})>"
