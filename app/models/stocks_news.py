"""
SQLAlchemy model for stocks_news table.

This module defines the StocksNews model which represents news articles
related to stocks with sentiment analysis data.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, ForeignKey, 
    Index, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.database import Base


class StocksNews(Base):
    """
    StocksNews model representing news articles related to stocks.
    
    This table contains news articles with sentiment analysis data
    for each stock.
    """
    __tablename__ = "stocks_news"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # News article data
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    content = Column(Text, nullable=True)  # Full article content if available
    summary = Column(Text, nullable=True)  # Summary/snippet of the article
    source = Column(String(255), nullable=False, index=True)  # News source (e.g., "Bloomberg", "CNBC")
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=False, index=True)
    image_url = Column(String(1000), nullable=True)
    
    # Sentiment analysis data
    sentiment_score = Column(Float, nullable=True, index=True)  # Numerical score (e.g., -1.0 to 1.0)
    sentiment_label = Column(String(20), nullable=True, index=True)  # Categorical label (e.g., "Positive", "Negative", "Neutral")
    sentiment_magnitude = Column(Float, nullable=True)  # Intensity of sentiment
    entities = Column(JSONB, nullable=True)  # Named entities mentioned in the article
    keywords = Column(JSONB, nullable=True)  # Keywords extracted from the article
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)  # When sentiment analysis was performed
    processing_version = Column(String(50), nullable=True)  # Version of sentiment analysis model/algorithm
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="news")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock with the same URL
        UniqueConstraint('stock_id', 'url', name='uq_stocks_news_stock_url'),
        # Index for querying by published date range
        Index('ix_stocks_news_published_date_range', 'stock_id', 'published_at'),
        # Index for sentiment analysis queries
        Index('ix_stocks_news_sentiment', 'stock_id', 'sentiment_score', 'published_at'),
        # Index for source and sentiment
        Index('ix_stocks_news_source_sentiment', 'source', 'sentiment_label'),
        # Index for time-based sentiment analysis
        Index('ix_stocks_news_time_sentiment', func.date(published_at), 'sentiment_score'),
    )
    
    def __repr__(self):
        """String representation of the StocksNews model."""
        return f"<StocksNews(id={self.id}, stock_id={self.stock_id}, title='{self.title[:30]}...', sentiment={self.sentiment_score})>"
