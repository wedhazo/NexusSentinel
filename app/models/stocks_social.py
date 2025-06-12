"""
SQLAlchemy model for stocks_social_posts table.

This module defines the StocksSocialPosts model which represents
social media posts related to stocks with sentiment analysis data.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, ForeignKey, 
    Index, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.database import Base


class StocksSocialPosts(Base):
    """
    StocksSocialPosts model representing social media posts related to stocks.
    
    This table contains social media posts with sentiment analysis data
    for each stock from various platforms like Twitter/X, Reddit, etc.
    """
    __tablename__ = "stocks_social_posts"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Social post data
    platform = Column(String(50), nullable=False, index=True)  # "twitter", "reddit", "stocktwits", etc.
    post_text = Column(Text, nullable=False)
    post_url = Column(String(1000), nullable=True)
    user_id = Column(String(255), nullable=True, index=True)  # Username or user ID
    user_followers = Column(Integer, nullable=True)  # Number of followers
    user_verified = Column(Integer, nullable=True, default=0)  # Whether user is verified
    
    # Post metadata
    created_at = Column(DateTime, nullable=False, index=True)  # When the post was created
    likes = Column(Integer, nullable=True, default=0)  # Number of likes/upvotes
    shares = Column(Integer, nullable=True, default=0)  # Number of retweets/shares
    comments = Column(Integer, nullable=True, default=0)  # Number of comments/replies
    
    # Sentiment analysis data
    sentiment_score = Column(Float, nullable=True, index=True)  # Numerical score (e.g., -1.0 to 1.0)
    sentiment_label = Column(String(20), nullable=True, index=True)  # Categorical label (e.g., "Positive", "Negative", "Neutral")
    sentiment_magnitude = Column(Float, nullable=True)  # Intensity of sentiment
    
    # Additional data
    tags = Column(JSONB, nullable=True)  # Hashtags or other tags
    mentioned_tickers = Column(JSONB, nullable=True)  # Other stock symbols mentioned
    
    # Processing metadata
    processed_at = Column(DateTime, nullable=True)  # When sentiment analysis was performed
    processing_version = Column(String(50), nullable=True)  # Version of sentiment analysis model/algorithm
    
    # System metadata
    created_at_system = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="social_posts")
    
    # Indexes and constraints
    __table_args__ = (
        # Index for querying by platform and date
        Index('ix_stocks_social_posts_platform_date', 'platform', func.date(created_at)),
        # Index for sentiment analysis queries
        Index('ix_stocks_social_posts_sentiment', 'stock_id', 'sentiment_score', 'created_at'),
        # Index for user engagement metrics
        Index('ix_stocks_social_posts_engagement', 'likes', 'shares', 'comments'),
        # Index for time-based sentiment analysis
        Index('ix_stocks_social_posts_time_sentiment', func.date(created_at), 'sentiment_score'),
    )
    
    def __repr__(self):
        """String representation of the StocksSocialPosts model."""
        return f"<StocksSocialPosts(id={self.id}, stock_id={self.stock_id}, platform='{self.platform}', sentiment={self.sentiment_score})>"
