"""
SQLAlchemy models for financial statements data.

This module defines models for both quarterly and annual financial statements.
"""

from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey,
    Index, UniqueConstraint, func, String, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class StocksFinancialStatementsQuarterly(Base):
    """
    Quarterly financial statements data for stocks.
    
    This table contains quarterly financial data such as revenue, net income,
    earnings per share, etc.
    """
    __tablename__ = "stocks_financial_statements_quarterly"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Financial reporting dates
    report_date = Column(Date, nullable=False, index=True)  # Date when report was filed/published
    period_end_date = Column(Date, nullable=False, index=True)  # End date of the fiscal period
    fiscal_year = Column(Integer, nullable=False, index=True)
    fiscal_quarter = Column(Integer, nullable=False, index=True)  # 1, 2, 3, or 4
    
    # Income statement data
    revenue = Column(Float, nullable=True)
    cost_of_revenue = Column(Float, nullable=True)
    gross_profit = Column(Float, nullable=True)
    operating_expense = Column(Float, nullable=True)
    operating_income = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    
    # Per share data
    eps_basic = Column(Float, nullable=True)
    eps_diluted = Column(Float, nullable=True)
    shares_outstanding_basic = Column(Float, nullable=True)
    shares_outstanding_diluted = Column(Float, nullable=True)
    
    # Cash flow data
    operating_cash_flow = Column(Float, nullable=True)
    capital_expenditure = Column(Float, nullable=True)
    free_cash_flow = Column(Float, nullable=True)
    
    # Balance sheet data
    total_assets = Column(Float, nullable=True)
    total_liabilities = Column(Float, nullable=True)
    total_equity = Column(Float, nullable=True)
    cash_and_equivalents = Column(Float, nullable=True)
    short_term_debt = Column(Float, nullable=True)
    long_term_debt = Column(Float, nullable=True)
    
    # Other financial metrics
    ebitda = Column(Float, nullable=True)
    ebit = Column(Float, nullable=True)
    effective_tax_rate = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    currency = Column(String(10), nullable=True, default="USD")
    filing_type = Column(String(20), nullable=True)  # 10-Q, 8-K, etc.
    filing_url = Column(String(500), nullable=True)
    restated = Column(Integer, default=0, nullable=False)  # Flag for restated financials
    notes = Column(Text, nullable=True)
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="quarterly_financials")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock for a specific fiscal period
        UniqueConstraint('stock_id', 'fiscal_year', 'fiscal_quarter', name='uq_stocks_financial_quarterly_period'),
        # Index for querying by report date range
        Index('ix_stocks_financial_quarterly_report_date', 'stock_id', 'report_date'),
        # Index for querying by fiscal period
        Index('ix_stocks_financial_quarterly_fiscal_period', 'stock_id', 'fiscal_year', 'fiscal_quarter'),
    )
    
    def __repr__(self):
        """String representation of the StocksFinancialStatementsQuarterly model."""
        return f"<StocksFinancialQuarterly(stock_id={self.stock_id}, FY={self.fiscal_year}, Q={self.fiscal_quarter}, revenue={self.revenue})>"


class StocksFinancialStatementsAnnual(Base):
    """
    Annual financial statements data for stocks.
    
    This table contains annual financial data such as revenue, net income,
    earnings per share, etc.
    """
    __tablename__ = "stocks_financial_statements_annual"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to stocks_core
    stock_id = Column(Integer, ForeignKey("stocks_core.stock_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Financial reporting dates
    report_date = Column(Date, nullable=False, index=True)  # Date when report was filed/published
    fiscal_year = Column(Integer, nullable=False, index=True)
    fiscal_year_end = Column(Date, nullable=True)  # End date of the fiscal year
    
    # Income statement data
    revenue = Column(Float, nullable=True)
    cost_of_revenue = Column(Float, nullable=True)
    gross_profit = Column(Float, nullable=True)
    operating_expense = Column(Float, nullable=True)
    operating_income = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    
    # Per share data
    eps_basic = Column(Float, nullable=True)
    eps_diluted = Column(Float, nullable=True)
    shares_outstanding_basic = Column(Float, nullable=True)
    shares_outstanding_diluted = Column(Float, nullable=True)
    dividend_per_share = Column(Float, nullable=True)
    
    # Cash flow data
    operating_cash_flow = Column(Float, nullable=True)
    capital_expenditure = Column(Float, nullable=True)
    free_cash_flow = Column(Float, nullable=True)
    
    # Balance sheet data
    total_assets = Column(Float, nullable=True)
    total_liabilities = Column(Float, nullable=True)
    total_equity = Column(Float, nullable=True)
    cash_and_equivalents = Column(Float, nullable=True)
    short_term_debt = Column(Float, nullable=True)
    long_term_debt = Column(Float, nullable=True)
    
    # Other financial metrics
    ebitda = Column(Float, nullable=True)
    ebit = Column(Float, nullable=True)
    effective_tax_rate = Column(Float, nullable=True)
    return_on_equity = Column(Float, nullable=True)
    return_on_assets = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    currency = Column(String(10), nullable=True, default="USD")
    filing_type = Column(String(20), nullable=True)  # 10-K, etc.
    filing_url = Column(String(500), nullable=True)
    restated = Column(Integer, default=0, nullable=False)  # Flag for restated financials
    notes = Column(Text, nullable=True)
    additional_data = Column(JSONB, nullable=True)  # For flexible storage of additional attributes
    
    # Relationship back to stocks_core
    stock = relationship("StocksCore", back_populates="annual_financials")
    
    # Indexes and constraints
    __table_args__ = (
        # Ensure no duplicate entries for a stock for a specific fiscal year
        UniqueConstraint('stock_id', 'fiscal_year', name='uq_stocks_financial_annual_fiscal_year'),
        # Index for querying by report date range
        Index('ix_stocks_financial_annual_report_date', 'stock_id', 'report_date'),
        # Index for querying by fiscal year
        Index('ix_stocks_financial_annual_fiscal_year', 'stock_id', 'fiscal_year'),
    )
    
    def __repr__(self):
        """String representation of the StocksFinancialStatementsAnnual model."""
        return f"<StocksFinancialAnnual(stock_id={self.stock_id}, fiscal_year={self.fiscal_year}, revenue={self.revenue})>"
