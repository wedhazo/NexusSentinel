"""
SQLAlchemy models for macroeconomic data.

This module defines models for macroeconomic indicators and their values,
which can provide context for stock market analysis.
"""

from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey, 
    Index, UniqueConstraint, func, String, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class MacroIndicatorsLookup(Base):
    """
    MacroIndicatorsLookup model representing metadata for macroeconomic indicators.
    
    This table serves as a lookup/reference table for macroeconomic indicators,
    containing metadata about each indicator such as name, description, frequency, etc.
    """
    __tablename__ = "macro_indicators_lookup"
    
    # Primary key
    indicator_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Indicator metadata
    indicator_name = Column(String(255), nullable=False, unique=True, index=True)
    indicator_code = Column(String(50), nullable=True, index=True)  # Short code/symbol for the indicator
    description = Column(Text, nullable=True)  # Detailed description of the indicator
    
    # Measurement details
    unit = Column(String(50), nullable=False)  # Unit of measurement (e.g., "%", "USD Billions")
    frequency = Column(String(50), nullable=False)  # Data frequency (e.g., "Daily", "Monthly", "Quarterly")
    
    # Source information
    source = Column(String(255), nullable=True)  # Data source (e.g., "Federal Reserve", "BLS", "World Bank")
    source_url = Column(String(500), nullable=True)  # URL to the data source
    
    # Geographic scope
    country = Column(String(100), nullable=True, index=True)  # Country the indicator applies to
    region = Column(String(100), nullable=True, index=True)  # Region (if applicable)
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)  # Category (e.g., "Interest Rates", "Employment", "GDP")
    subcategory = Column(String(100), nullable=True)  # Subcategory
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # Whether the indicator is currently tracked
    notes = Column(Text, nullable=True)  # Additional notes about the indicator
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship to MacroEconomicData
    values = relationship("MacroEconomicData", back_populates="indicator", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        # Index for common queries
        Index('ix_macro_indicators_category_country', 'category', 'country'),
        Index('ix_macro_indicators_frequency', 'frequency'),
    )
    
    def __repr__(self):
        """String representation of the MacroIndicatorsLookup model."""
        return f"<MacroIndicator(id={self.indicator_id}, name='{self.indicator_name}', unit='{self.unit}')>"


class MacroEconomicData(Base):
    """
    MacroEconomicData model representing actual values for macroeconomic indicators.
    
    This table contains the time series data for macroeconomic indicators,
    with each record representing a value for a specific indicator at a specific date.
    """
    __tablename__ = "macro_economic_data"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to macro_indicators_lookup
    indicator_id = Column(Integer, ForeignKey("macro_indicators_lookup.indicator_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Date and value
    date = Column(Date, nullable=False, index=True)  # Date of the observation
    value = Column(Float, nullable=False)  # The actual value of the indicator
    
    # Additional value details
    original_value = Column(Float, nullable=True)  # Original value before any adjustments
    is_adjusted = Column(Integer, default=0, nullable=False)  # Whether the value is seasonally adjusted
    is_estimated = Column(Integer, default=0, nullable=False)  # Whether the value is an estimate
    is_revised = Column(Integer, default=0, nullable=False)  # Whether the value has been revised
    
    # Period information (for non-daily data)
    period_start = Column(Date, nullable=True)  # Start of the period this value represents
    period_end = Column(Date, nullable=True)  # End of the period this value represents
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    source_date = Column(DateTime, nullable=True)  # When this data was published by the source
    notes = Column(Text, nullable=True)  # Any notes about this specific value
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to MacroIndicatorsLookup
    indicator = relationship("MacroIndicatorsLookup", back_populates="values")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for an indicator on a specific date
        UniqueConstraint('indicator_id', 'date', name='uq_macro_economic_data_indicator_date'),
        # Index for querying by date range
        Index('ix_macro_economic_data_date_range', 'indicator_id', 'date'),
        # Index for time-based analysis
        Index('ix_macro_economic_data_time_value', 'date', 'value'),
    )
    
    def __repr__(self):
        """String representation of the MacroEconomicData model."""
        return f"<MacroEconomicData(indicator_id={self.indicator_id}, date='{self.date}', value={self.value})>"
