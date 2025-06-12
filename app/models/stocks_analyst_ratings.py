"""
SQLAlchemy model for stocks_analyst_ratings table.

This module defines the StocksAnalystRatings model which represents
analyst ratings and price targets for stocks.
"""

from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey, 
    Index, UniqueConstraint, func, String, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class StocksAnalystRatings(Base):
    """
    StocksAnalystRatings model representing analyst ratings for stocks.
    
    This table contains information about analyst ratings including
    the rating firm, rating value, target price, and report date.
    """
    __tablename__ = "stocks_analyst_ratings"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Rating data
    report_date = Column(Date, nullable=False, index=True)  # Date of the analyst report
    firm = Column(String(255), nullable=False, index=True)  # Name of the analyst firm
    analyst_name = Column(String(255), nullable=True)  # Name of the individual analyst
    
    # Rating details
    rating = Column(String(50), nullable=False, index=True)  # e.g., "Buy", "Hold", "Sell", "Outperform"
    previous_rating = Column(String(50), nullable=True)  # Previous rating if this is an update
    target_price = Column(Float, nullable=True)  # Price target
    previous_target_price = Column(Float, nullable=True)  # Previous price target if this is an update
    
    # Additional rating information
    rating_summary = Column(Text, nullable=True)  # Brief summary of the rating
    report_url = Column(String(500), nullable=True)  # URL to the analyst report if available
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    currency = Column(String(10), nullable=True, default="USD")  # Currency of the target price
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="analyst_ratings")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock from a specific firm on a specific date
        UniqueConstraint('stock_id', 'firm', 'report_date', name='uq_stocks_analyst_ratings_stock_firm_date'),
        # Index for querying by report date range
        Index('ix_stocks_analyst_ratings_date_range', 'stock_id', 'report_date'),
        # Index for querying by rating
        Index('ix_stocks_analyst_ratings_rating', 'stock_id', 'rating'),
        # Index for querying by firm
        Index('ix_stocks_analyst_ratings_firm', 'firm'),
    )
    
    def __repr__(self):
        """String representation of the StocksAnalystRatings model."""
        return f"<StocksAnalystRatings(stock_id={self.stock_id}, firm='{self.firm}', rating='{self.rating}', target_price={self.target_price})>"
