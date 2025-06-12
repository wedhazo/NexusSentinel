"""
SQLAlchemy model for stocks_sentiment_daily_summary table.

This module defines the StocksSentimentDailySummary model which represents
daily aggregated sentiment data from various sources for stocks.
"""

from sqlalchemy import (
    Column, Integer, Float, String, Date, DateTime, ForeignKey, 
    Index, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.database import Base


class StocksSentimentDailySummary(Base):
    """
    StocksSentimentDailySummary model representing daily sentiment summaries.
    
    This table contains aggregated sentiment data from various sources (news, social media)
    for each stock on a daily basis.
    """
    __tablename__ = "stocks_sentiment_daily_summary"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Date of the sentiment summary
    date = Column(Date, nullable=False, index=True)
    
    # News sentiment data
    news_avg_sentiment = Column(Float, nullable=True)  # Average sentiment score from news articles
    news_volume_24h = Column(Integer, nullable=True)   # Number of news articles in the last 24 hours
    
    # Twitter sentiment data
    twitter_avg_sentiment = Column(Float, nullable=True)  # Average sentiment score from Twitter
    twitter_mentions_24h = Column(Integer, nullable=True)  # Number of Twitter mentions in the last 24 hours
    
    # Reddit sentiment data
    reddit_avg_sentiment = Column(Float, nullable=True)  # Average sentiment score from Reddit
    reddit_mentions_24h = Column(Integer, nullable=True)  # Number of Reddit mentions in the last 24 hours
    wallstreetbets_mentions_24h = Column(Integer, nullable=True)  # Number of WallStreetBets mentions
    
    # Overall sentiment metrics
    overall_sentiment_score = Column(Float, nullable=True, index=True)  # Combined sentiment score
    sentiment_trend = Column(String(20), nullable=True, index=True)  # Trend direction (e.g., "Improving", "Declining", "Stable")
    
    # Additional sentiment metrics
    sentiment_volatility = Column(Float, nullable=True)  # Volatility of sentiment over the day
    sentiment_volume_total = Column(Integer, nullable=True)  # Total mentions across all platforms
    sentiment_sources_count = Column(Integer, nullable=True)  # Number of distinct sources contributing
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    calculation_method = Column(String(50), nullable=True)  # Method used to calculate sentiment
    calculation_version = Column(String(50), nullable=True)  # Version of calculation algorithm
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="sentiment_summaries")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock on a specific date
        UniqueConstraint('stock_id', 'date', name='uq_stocks_sentiment_daily_summary_stock_date'),
        # Index for querying by date range
        Index('ix_stocks_sentiment_daily_date_range', 'stock_id', 'date'),
        # Index for sentiment trend analysis
        Index('ix_stocks_sentiment_trend', 'sentiment_trend', 'date'),
        # Index for overall sentiment score queries
        Index('ix_stocks_sentiment_score', 'overall_sentiment_score', 'date'),
        # Index for high-volume stocks
        Index('ix_stocks_sentiment_volume', 'sentiment_volume_total', 'date'),
    )
    
    def __repr__(self):
        """String representation of the StocksSentimentDailySummary model."""
        return f"<StocksSentimentDailySummary(stock_id={self.stock_id}, date='{self.date}', score={self.overall_sentiment_score})>"
