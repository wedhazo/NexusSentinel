"""
SQLAlchemy model for stocks_core table.

This module defines the StocksCore model which represents the core information
about stocks/companies in the database.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, BigInteger, 
    ForeignKey, Index, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.database import Base


class StocksCore(Base):
    """
    StocksCore model representing the core information about stocks/companies.
    
    This table contains fundamental information about companies such as
    symbol, name, sector, industry, etc.
    """
    __tablename__ = "stocks_core"
    
    # Primary key
    stock_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core stock information
    symbol = Column(String(20), nullable=False, index=True, unique=True)
    company_name = Column(String(255), nullable=False, index=True)
    exchange = Column(String(50), nullable=True, index=True)
    sector = Column(String(100), nullable=True, index=True)
    industry = Column(String(150), nullable=True, index=True)
    country_of_origin = Column(String(100), nullable=True, index=True)
    cik = Column(String(20), nullable=True, index=True)
    isin = Column(String(20), nullable=True, index=True)
    ceo = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    business_summary = Column(Text, nullable=True)
    number_of_employees = Column(BigInteger, nullable=True)
    fiscal_year_end = Column(String(20), nullable=True)  # Month like "December" or "June"
    ipo_date = Column(Date, nullable=True)
    
    # Metadata fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationships - these will be defined as backref from other models
    # Daily OHLCV data
    daily_ohlcv = relationship("StocksOHLCVDaily", back_populates="stock", cascade="all, delete-orphan")
    
    # Intraday OHLCV data
    intraday_ohlcv = relationship("StocksOHLCVIntraday5Min", back_populates="stock", cascade="all, delete-orphan")
    
    # Financial statements
    quarterly_financials = relationship("StocksFinancialStatementsQuarterly", back_populates="stock", cascade="all, delete-orphan")
    annual_financials = relationship("StocksFinancialStatementsAnnual", back_populates="stock", cascade="all, delete-orphan")
    
    # Technical indicators
    technical_indicators = relationship("StocksTechnicalIndicatorsDaily", back_populates="stock", cascade="all, delete-orphan")
    
    # News articles
    news = relationship("StocksNews", back_populates="stock", cascade="all, delete-orphan")
    
    # Social media posts
    social_posts = relationship("StocksSocialPosts", back_populates="stock", cascade="all, delete-orphan")
    
    # Sentiment summaries
    sentiment_summaries = relationship("StocksSentimentDailySummary", back_populates="stock", cascade="all, delete-orphan")
    
    # Dividends
    dividends = relationship("StocksDividends", back_populates="stock", cascade="all, delete-orphan")
    
    # Stock splits
    splits = relationship("StocksSplits", back_populates="stock", cascade="all, delete-orphan")
    
    # Analyst ratings
    analyst_ratings = relationship("StocksAnalystRatings", back_populates="stock", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        # Composite indexes for common queries
        Index('ix_stocks_core_symbol_exchange', 'symbol', 'exchange'),
        Index('ix_stocks_core_sector_industry', 'sector', 'industry'),
        # Ensure symbol uniqueness per exchange
        UniqueConstraint('symbol', 'exchange', name='uq_stocks_core_symbol_exchange'),
    )
    
    def __repr__(self):
        """String representation of the StocksCore model."""
        return f"<Stock(id={self.stock_id}, symbol='{self.symbol}', company='{self.company_name}')>"
