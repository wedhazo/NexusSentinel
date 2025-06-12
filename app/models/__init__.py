"""
Models package initialization.

This module imports all models for easy access throughout the application.
"""

from app.models.stocks_core import StocksCore
from app.models.stocks_ohlcv import StocksOHLCVDaily, StocksOHLCVIntraday5Min
from app.models.stocks_financials import StocksFinancialStatementsQuarterly, StocksFinancialStatementsAnnual
from app.models.stocks_technical import StocksTechnicalIndicatorsDaily
from app.models.stocks_news import StocksNews
from app.models.stocks_social import StocksSocialPosts
from app.models.stocks_sentiment import StocksSentimentDailySummary
from app.models.stocks_dividends import StocksDividends
from app.models.stocks_splits import StocksSplits
from app.models.stocks_analyst_ratings import StocksAnalystRatings
from app.models.macro_economic import MacroEconomicData, MacroIndicatorsLookup

# Export all models
__all__ = [
    'StocksCore',
    'StocksOHLCVDaily',
    'StocksOHLCVIntraday5Min',
    'StocksFinancialStatementsQuarterly',
    'StocksFinancialStatementsAnnual',
    'StocksTechnicalIndicatorsDaily',
    'StocksNews',
    'StocksSocialPosts',
    'StocksSentimentDailySummary',
    'StocksDividends',
    'StocksSplits',
    'StocksAnalystRatings',
    'MacroEconomicData',
    'MacroIndicatorsLookup',
]
