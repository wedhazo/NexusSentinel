"""
SQLAlchemy model for stocks_technical_indicators_daily table.

This module defines the StocksTechnicalIndicatorsDaily model which represents
daily technical indicators calculated for stocks.
"""

from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey,
    Index, UniqueConstraint, func, String
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class StocksTechnicalIndicatorsDaily(Base):
    """
    StocksTechnicalIndicatorsDaily model representing daily technical indicators.
    
    This table contains various technical indicators calculated on a daily basis
    for each stock, including moving averages, oscillators, and other technical metrics.
    """
    __tablename__ = "stocks_technical_indicators_daily"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Date of the technical indicators
    date = Column(Date, nullable=False, index=True)
    
    # Simple Moving Averages (SMA)
    sma_5 = Column(Float, nullable=True)
    sma_10 = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_100 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    
    # Exponential Moving Averages (EMA)
    ema_10 = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    ema_100 = Column(Float, nullable=True)
    ema_200 = Column(Float, nullable=True)
    
    # Moving Average Convergence Divergence (MACD)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    
    # Relative Strength Index (RSI)
    rsi_14 = Column(Float, nullable=True)
    rsi_20 = Column(Float, nullable=True)
    
    # Bollinger Bands
    bbands_upper = Column(Float, nullable=True)
    bbands_middle = Column(Float, nullable=True)
    bbands_lower = Column(Float, nullable=True)
    
    # Average True Range (ATR)
    atr_14 = Column(Float, nullable=True)
    
    # Average Directional Index (ADX)
    adx_14 = Column(Float, nullable=True)
    
    # On-Balance Volume (OBV)
    obv = Column(Float, nullable=True)
    
    # Volume Weighted Average Price (VWAP)
    vwap = Column(Float, nullable=True)
    
    # Stochastic Oscillator
    stochastic_k = Column(Float, nullable=True)
    stochastic_d = Column(Float, nullable=True)
    
    # Commodity Channel Index (CCI)
    cci_14 = Column(Float, nullable=True)
    
    # Additional indicators
    ichimoku_cloud_a = Column(Float, nullable=True)
    ichimoku_cloud_b = Column(Float, nullable=True)
    parabolic_sar = Column(Float, nullable=True)
    williams_r = Column(Float, nullable=True)
    mfi_14 = Column(Float, nullable=True)  # Money Flow Index
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    calculation_method = Column(String(50), nullable=True)  # Method used to calculate indicators
    calculation_version = Column(String(50), nullable=True)  # Version of calculation algorithm
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="technical_indicators")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock on a specific date
        UniqueConstraint('stock_id', 'date', name='uq_stocks_technical_indicators_daily_stock_date'),
        # Index for querying by date range
        Index('ix_stocks_technical_indicators_daily_date_range', 'stock_id', 'date'),
        # Index for common technical indicator queries
        Index('ix_stocks_technical_indicators_daily_rsi', 'stock_id', 'date', 'rsi_14'),
        Index('ix_stocks_technical_indicators_daily_macd', 'stock_id', 'date', 'macd'),
    )
    
    def __repr__(self):
        """String representation of the StocksTechnicalIndicatorsDaily model."""
        return f"<StocksTechnicalIndicatorsDaily(stock_id={self.stock_id}, date='{self.date}')>"
