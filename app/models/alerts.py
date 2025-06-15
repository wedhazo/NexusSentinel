"""
Sentiment alerts model for NexusSentinel API.

This module defines the database model for sentiment alerts,
which allow users to be notified when a stock's sentiment score
crosses a specified threshold in a given direction.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class SentimentAlert(Base):
    """Database model for sentiment alerts."""
    
    __tablename__ = "sentiment_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    threshold = Column(Float, nullable=False)
    direction = Column(String, nullable=False)  # "above" or "below"
    created_at = Column(DateTime, default=func.now(), nullable=False)
    triggered = Column(Boolean, default=False, nullable=False)
    
    # Optional relationship to stocks_core table
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id"), nullable=True)
    stock = relationship("StocksCore", back_populates="sentiment_alerts")
    
    def __repr__(self):
        """String representation of the sentiment alert."""
        status = "triggered" if self.triggered else "active"
        return f"<SentimentAlert(id={self.id}, symbol='{self.symbol}', threshold={self.threshold}, direction='{self.direction}', status='{status}')>"
