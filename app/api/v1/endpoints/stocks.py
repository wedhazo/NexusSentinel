"""
Stock data endpoints for NexusSentinel API.

This module provides endpoints for querying stock data, including:
- Comprehensive stock data for a specific symbol
- Sentiment analysis data submission
- Aggregated sentiment data by date and source
- CRUD operations for stock management
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from pydantic import BaseModel, Field, ConfigDict

# Import database and models
from app.database import get_db
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


# Define __all__ to export models for OpenAPI schema generation
__all__ = [
    "StockCoreCreate", "StockCoreResponse", "SentimentAnalysisCreate",
    "SentimentAnalysisResponse", "AggregatedSentimentResponse", "StockFullDataResponse",
    "StockSentimentItem", "TopBottomStocksResponse"
]

# Create router
router = APIRouter(prefix="/stocks", tags=["Stocks"])


# --- Pydantic Models for Request/Response ---

class StockCoreCreate(BaseModel):
    """Schema for creating a new stock entry."""
    symbol: str = Field(..., description="Stock ticker symbol", example="AAPL")
    company_name: str = Field(..., description="Company name", example="Apple Inc.")
    exchange: Optional[str] = Field(None, description="Stock exchange", example="NASDAQ")
    sector: Optional[str] = Field(None, description="Business sector", example="Technology")
    industry: Optional[str] = Field(None, description="Specific industry", example="Consumer Electronics")
    country_of_origin: Optional[str] = Field(None, description="Country of origin", example="United States")
    cik: Optional[str] = Field(None, description="SEC Central Index Key", example="0000320193")
    isin: Optional[str] = Field(None, description="International Securities Identification Number", example="US0378331005")
    ceo: Optional[str] = Field(None, description="Chief Executive Officer", example="Tim Cook")
    website: Optional[str] = Field(None, description="Company website", example="https://www.apple.com")
    business_summary: Optional[str] = Field(None, description="Brief company description")
    number_of_employees: Optional[int] = Field(None, description="Number of employees", example=147000)
    fiscal_year_end: Optional[str] = Field(None, description="Fiscal year end month", example="September")
    ipo_date: Optional[date] = Field(None, description="Initial Public Offering date", example="1980-12-12")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "country_of_origin": "United States",
                "website": "https://www.apple.com",
                "business_summary": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
            }
        }
    )


class StockCoreResponse(StockCoreCreate):
    """Schema for stock core data response."""
    stock_id: int
    created_at: datetime
    last_updated: datetime
    is_active: int

    model_config = ConfigDict(from_attributes=True)


class SentimentAnalysisCreate(BaseModel):
    """Schema for submitting new sentiment analysis results."""
    symbol: str = Field(..., description="Stock ticker symbol", example="AAPL")
    date: date = Field(..., description="Date of sentiment data", example="2025-06-11")
    # NOTE: validation for allowed sources can be added with a validator or Literal
    source: str = Field(..., description="Source of sentiment data", example="news")
    sentiment_score: float = Field(..., description="Sentiment score (-1.0 to 1.0)", example=0.75, ge=-1.0, le=1.0)
    # NOTE: validation for allowed labels can be added with a validator or Literal
    sentiment_label: str = Field(..., description="Sentiment label", example="positive")
    volume: int = Field(..., description="Number of mentions/articles", example=42, ge=0)
    content_sample: Optional[str] = Field(None, description="Sample of content that generated this sentiment")
    source_details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the source")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "date": "2025-06-11",
                "source": "news",
                "sentiment_score": 0.75,
                "sentiment_label": "positive",
                "volume": 42,
                "content_sample": "Apple's new product line exceeds analyst expectations.",
                "source_details": {
                    "publisher": "Financial Times",
                    "author": "John Doe",
                    "url": "https://example.com/article"
                }
            }
        }
    )


class SentimentAnalysisResponse(BaseModel):
    """Schema for sentiment analysis response."""
    id: int
    stock_id: int
    symbol: str
    date: date
    source: str
    sentiment_score: float
    sentiment_label: str
    volume: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AggregatedSentimentResponse(BaseModel):
    """Schema for aggregated sentiment data response."""
    symbol: str
    date: date
    source: str
    avg_sentiment_score: float
    total_volume: int
    sentiment_distribution: Dict[str, int]
    
    model_config = ConfigDict(from_attributes=True)


class StockSentimentItem(BaseModel):
    """Schema for individual stock sentiment data."""
    symbol: str
    sentiment_score: float
    date: date

    model_config = ConfigDict(from_attributes=True)


class TopBottomStocksResponse(BaseModel):
    """Schema for top/bottom stocks response."""
    top_20: List[StockSentimentItem]
    bottom_20: List[StockSentimentItem]

    model_config = ConfigDict(from_attributes=True)


class StockFullDataResponse(BaseModel):
    """Schema for full stock data response with all related information."""
    # Core stock data
    stock_id: int
    symbol: str
    company_name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country_of_origin: Optional[str] = None
    cik: Optional[str] = None
    isin: Optional[str] = None
    ceo: Optional[str] = None
    website: Optional[str] = None
    business_summary: Optional[str] = None
    number_of_employees: Optional[int] = None
    fiscal_year_end: Optional[str] = None
    ipo_date: Optional[date] = None
    core_last_updated: Optional[datetime] = None
    
    # Daily OHLCV data
    daily_open: Optional[float] = None
    daily_high: Optional[float] = None
    daily_low: Optional[float] = None
    daily_close: Optional[float] = None
    daily_adjusted_close: Optional[float] = None
    daily_volume: Optional[int] = None
    
    # Intraday data (latest 5min bar)
    intraday_timestamp: Optional[datetime] = None
    intraday_open: Optional[float] = None
    intraday_high: Optional[float] = None
    intraday_low: Optional[float] = None
    intraday_close: Optional[float] = None
    intraday_volume: Optional[int] = None
    
    # Latest quarterly financial data
    q_report_date: Optional[date] = None
    q_period_end_date: Optional[date] = None
    q_fiscal_year: Optional[int] = None
    q_fiscal_quarter: Optional[int] = None
    q_revenue: Optional[float] = None
    q_net_income: Optional[float] = None
    q_eps_basic: Optional[float] = None
    q_ebitda: Optional[float] = None
    q_free_cash_flow: Optional[float] = None
    
    # Latest annual financial data
    a_report_date: Optional[date] = None
    a_fiscal_year: Optional[int] = None
    a_revenue: Optional[float] = None
    a_net_income: Optional[float] = None
    a_eps_basic: Optional[float] = None
    a_ebitda: Optional[float] = None
    a_free_cash_flow: Optional[float] = None
    
    # Technical indicators
    sma_5: Optional[float] = None
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_100: Optional[float] = None
    sma_200: Optional[float] = None
    ema_10: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_100: Optional[float] = None
    ema_200: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    rsi_14: Optional[float] = None
    rsi_20: Optional[float] = None
    bbands_upper: Optional[float] = None
    bbands_middle: Optional[float] = None
    bbands_lower: Optional[float] = None
    atr_14: Optional[float] = None
    adx_14: Optional[float] = None
    obv: Optional[float] = None
    vwap: Optional[float] = None
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None
    cci_14: Optional[float] = None
    
    # Latest news
    latest_news_title: Optional[str] = None
    latest_news_url: Optional[str] = None
    latest_news_published_at: Optional[datetime] = None
    latest_news_sentiment: Optional[float] = None
    latest_news_sentiment_label: Optional[str] = None
    
    # Latest social post
    latest_social_post_text: Optional[str] = None
    latest_social_platform: Optional[str] = None
    latest_social_created_at: Optional[datetime] = None
    latest_social_sentiment: Optional[float] = None
    
    # Daily sentiment summary
    news_avg_sentiment: Optional[float] = None
    news_volume_24h: Optional[int] = None
    twitter_avg_sentiment: Optional[float] = None
    twitter_mentions_24h: Optional[int] = None
    reddit_avg_sentiment: Optional[float] = None
    reddit_mentions_24h: Optional[int] = None
    wallstreetbets_mentions_24h: Optional[int] = None
    overall_sentiment_score: Optional[float] = None
    sentiment_trend: Optional[str] = None
    
    # Latest dividend
    latest_dividend_ex_date: Optional[date] = None
    latest_dividend_amount: Optional[float] = None
    latest_dividend_type: Optional[str] = None
    
    # Latest split
    latest_split_ex_date: Optional[date] = None
    latest_split_from_shares: Optional[int] = None
    latest_split_to_shares: Optional[int] = None
    
    # Latest analyst rating
    latest_rating_report_date: Optional[date] = None
    latest_rating_firm: Optional[str] = None
    latest_rating: Optional[str] = None
    latest_rating_target_price: Optional[float] = None
    
    # Macro economic data
    macro_value: Optional[float] = None
    macro_indicator_name: Optional[str] = None
    macro_indicator_unit: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# --- Endpoints ---

@router.get("/{symbol}", response_model=StockFullDataResponse)
async def get_stock_full_data(
    symbol: str = Path(..., description="Stock ticker symbol", example="AAPL"),
    query_date: date = Query(None, description="Date for which to retrieve data (defaults to today)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive data for a specific stock symbol.
    
    This endpoint returns detailed information about a stock, including:
    - Core company information
    - Daily and intraday price data
    - Financial statements (quarterly and annual)
    - Technical indicators
    - News and social media sentiment
    - Dividends, splits, and analyst ratings
    - Macroeconomic indicators
    
    Similar to the comprehensive SQL query example.
    """
    # Default to today if no date provided
    if query_date is None:
        query_date = date.today()
    
    # Use raw SQL for this complex query to match the example
    # This gives us more control over the exact query structure
    query = text("""
    SELECT
        -- Core Stock Data
        sc.stock_id,
        sc.symbol,
        sc.company_name,
        sc.exchange,
        sc.sector,
        sc.industry,
        sc.country_of_origin,
        sc.cik,
        sc.isin,
        sc.ceo,
        sc.website,
        sc.business_summary,
        sc.number_of_employees,
        sc.fiscal_year_end,
        sc.ipo_date,
        sc.last_updated AS core_last_updated,
        
        -- Daily OHLCV Data
        sod.open AS daily_open,
        sod.high AS daily_high,
        sod.low AS daily_low,
        sod.close AS daily_close,
        sod.adjusted_close AS daily_adjusted_close,
        sod.volume AS daily_volume,
        
        -- Intraday OHLCV (latest 5min bar)
        soi.timestamp AS intraday_timestamp,
        soi.open AS intraday_open,
        soi.high AS intraday_high,
        soi.low AS intraday_low,
        soi.close AS intraday_close,
        soi.volume AS intraday_volume,
        
        -- Latest Quarterly Financial Statement
        sfsq.report_date AS q_report_date,
        sfsq.period_end_date AS q_period_end_date,
        sfsq.fiscal_year AS q_fiscal_year,
        sfsq.fiscal_quarter AS q_fiscal_quarter,
        sfsq.revenue AS q_revenue,
        sfsq.net_income AS q_net_income,
        sfsq.eps_basic AS q_eps_basic,
        sfsq.ebitda AS q_ebitda,
        sfsq.free_cash_flow AS q_free_cash_flow,
        
        -- Latest Annual Financial Statement
        sfsa.report_date AS a_report_date,
        sfsa.fiscal_year AS a_fiscal_year,
        sfsa.revenue AS a_revenue,
        sfsa.net_income AS a_net_income,
        sfsa.eps_basic AS a_eps_basic,
        sfsa.ebitda AS a_ebitda,
        sfsa.free_cash_flow AS a_free_cash_flow,
        
        -- Daily Technical Indicators
        stid.sma_5, stid.sma_10, stid.sma_20, stid.sma_50, stid.sma_100, stid.sma_200,
        stid.ema_10, stid.ema_20, stid.ema_50, stid.ema_100, stid.ema_200,
        stid.macd, stid.macd_signal, stid.macd_hist,
        stid.rsi_14, stid.rsi_20,
        stid.bbands_upper, stid.bbands_middle, stid.bbands_lower,
        stid.atr_14, stid.adx_14, stid.obv, stid.vwap,
        stid.stochastic_k, stid.stochastic_d, stid.cci_14,
        
        -- Latest News Article
        sn.title AS latest_news_title,
        sn.url AS latest_news_url,
        sn.published_at AS latest_news_published_at,
        sn.sentiment_score AS latest_news_sentiment,
        sn.sentiment_label AS latest_news_sentiment_label,
        
        -- Latest Social Post
        ssp.post_text AS latest_social_post_text,
        ssp.platform AS latest_social_platform,
        ssp.created_at AS latest_social_created_at,
        ssp.sentiment_score AS latest_social_sentiment,
        
        -- Daily Sentiment Summary
        ssds.news_avg_sentiment,
        ssds.news_volume_24h,
        ssds.twitter_avg_sentiment,
        ssds.twitter_mentions_24h,
        ssds.reddit_avg_sentiment,
        ssds.reddit_mentions_24h,
        ssds.wallstreetbets_mentions_24h,
        ssds.overall_sentiment_score,
        ssds.sentiment_trend,
        
        -- Latest Dividend
        sd.ex_date AS latest_dividend_ex_date,
        sd.amount AS latest_dividend_amount,
        sd.type AS latest_dividend_type,
        
        -- Latest Stock Split
        ss.ex_date AS latest_split_ex_date,
        ss.from_shares AS latest_split_from_shares,
        ss.to_shares AS latest_split_to_shares,
        
        -- Latest Analyst Rating
        sar.report_date AS latest_rating_report_date,
        sar.firm AS latest_rating_firm,
        sar.rating AS latest_rating,
        sar.target_price AS latest_rating_target_price,
        
        -- Macroeconomic Data
        med.value AS macro_value,
        mil.indicator_name AS macro_indicator_name,
        mil.unit AS macro_indicator_unit
        
    FROM
        stocks_core sc
    LEFT JOIN
        stocks_ohlcv_daily sod ON sc.stock_id = sod.stock_id AND sod.date = :query_date
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_ohlcv_intraday_5min
        WHERE stock_id = sc.stock_id AND DATE(timestamp) = :query_date
        ORDER BY timestamp DESC
        LIMIT 1
    ) soi ON TRUE
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_financial_statements_quarterly
        WHERE stock_id = sc.stock_id AND report_date <= :query_date
        ORDER BY report_date DESC, fiscal_year DESC, fiscal_quarter DESC
        LIMIT 1
    ) sfsq ON TRUE
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_financial_statements_annual
        WHERE stock_id = sc.stock_id AND report_date <= :query_date
        ORDER BY report_date DESC, fiscal_year DESC
        LIMIT 1
    ) sfsa ON TRUE
    LEFT JOIN
        stocks_technical_indicators_daily stid ON sc.stock_id = stid.stock_id AND stid.date = :query_date
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_news
        WHERE stock_id = sc.stock_id AND DATE(published_at) <= :query_date
        ORDER BY published_at DESC
        LIMIT 1
    ) sn ON TRUE
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_social_posts
        WHERE stock_id = sc.stock_id AND DATE(created_at) <= :query_date
        ORDER BY created_at DESC
        LIMIT 1
    ) ssp ON TRUE
    LEFT JOIN
        stocks_sentiment_daily_summary ssds ON sc.stock_id = ssds.stock_id AND ssds.date = :query_date
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_dividends
        WHERE stock_id = sc.stock_id AND ex_date <= :query_date
        ORDER BY ex_date DESC
        LIMIT 1
    ) sd ON TRUE
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_splits
        WHERE stock_id = sc.stock_id AND ex_date <= :query_date
        ORDER BY ex_date DESC
        LIMIT 1
    ) ss ON TRUE
    LEFT JOIN LATERAL (
        SELECT *
        FROM stocks_analyst_ratings
        WHERE stock_id = sc.stock_id AND report_date <= :query_date
        ORDER BY report_date DESC
        LIMIT 1
    ) sar ON TRUE
    LEFT JOIN
        macro_economic_data med ON med.date = :query_date
    LEFT JOIN
        macro_indicators_lookup mil ON med.indicator_id = mil.indicator_id
    WHERE
        UPPER(sc.symbol) = UPPER(:symbol)
    """)
    
    # Execute the query with parameters - pass date object directly
    result = await db.execute(
        query, 
        {"symbol": symbol, "query_date": query_date}
    )
    
    # Fetch the result
    stock_data = result.fetchone()
    
    # Check if stock exists
    if not stock_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found"
        )
    
    # Convert SQLAlchemy Row to dict and create a StockFullDataResponse
    stock_dict = dict(stock_data)
    return StockFullDataResponse(**stock_dict)


@router.post("/sentiment", response_model=SentimentAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_sentiment_analysis(
    sentiment_data: SentimentAnalysisCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit new sentiment analysis results for a stock.
    
    This endpoint allows adding new sentiment data from various sources like:
    - News articles
    - Twitter/X posts
    - Reddit discussions
    - WallStreetBets mentions
    - Other social media platforms
    
    The data will be used to update the daily sentiment summary.
    """
    # First, find the stock by symbol
    query = select(StocksCore).where(func.upper(StocksCore.symbol) == func.upper(sentiment_data.symbol))
    result = await db.execute(query)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{sentiment_data.symbol}' not found"
        )
    
    # Create new sentiment entry based on source type
    if sentiment_data.source == 'news':
        # Create a news entry with sentiment
        news_entry = StocksNews(
            stock_id=stock.stock_id,
            title=sentiment_data.content_sample[:500] if sentiment_data.content_sample else f"News about {stock.symbol}",
            url=sentiment_data.source_details.get('url', '#') if sentiment_data.source_details else '#',
            source=sentiment_data.source_details.get('publisher', 'Unknown') if sentiment_data.source_details else 'Unknown',
            author=sentiment_data.source_details.get('author') if sentiment_data.source_details else None,
            published_at=datetime.combine(sentiment_data.date, datetime.min.time()),
            content=sentiment_data.content_sample,
            sentiment_score=sentiment_data.sentiment_score,
            sentiment_label=sentiment_data.sentiment_label,
        )
        db.add(news_entry)
        await db.flush()
        sentiment_id = news_entry.id
        
    elif sentiment_data.source in ['twitter', 'reddit', 'wallstreetbets']:
        # Create a social post entry
        social_post = StocksSocialPosts(
            stock_id=stock.stock_id,
            platform=sentiment_data.source,
            post_text=sentiment_data.content_sample[:1000] if sentiment_data.content_sample else f"Post about {stock.symbol}",
            created_at=datetime.combine(sentiment_data.date, datetime.min.time()),
            sentiment_score=sentiment_data.sentiment_score,
            user_id=sentiment_data.source_details.get('user_id') if sentiment_data.source_details else None,
            post_url=sentiment_data.source_details.get('url') if sentiment_data.source_details else None,
        )
        db.add(social_post)
        await db.flush()
        sentiment_id = social_post.id
        
    else:
        # Generic sentiment data - update daily summary directly
        sentiment_id = 0
    
    # Update or create daily sentiment summary
    query = select(StocksSentimentDailySummary).where(
        and_(
            StocksSentimentDailySummary.stock_id == stock.stock_id,
            StocksSentimentDailySummary.date == sentiment_data.date
        )
    )
    result = await db.execute(query)
    daily_summary = result.scalar_one_or_none()
    
    if not daily_summary:
        # Create new summary if it doesn't exist
        daily_summary = StocksSentimentDailySummary(
            stock_id=stock.stock_id,
            date=sentiment_data.date,
        )
        db.add(daily_summary)
    
    # Update the appropriate fields based on source
    if sentiment_data.source == 'news':
        daily_summary.news_avg_sentiment = (
            (daily_summary.news_avg_sentiment or 0) * (daily_summary.news_volume_24h or 0) + 
            sentiment_data.sentiment_score * sentiment_data.volume
        ) / ((daily_summary.news_volume_24h or 0) + sentiment_data.volume) if sentiment_data.volume > 0 else daily_summary.news_avg_sentiment
        daily_summary.news_volume_24h = (daily_summary.news_volume_24h or 0) + sentiment_data.volume
    
    elif sentiment_data.source == 'twitter':
        daily_summary.twitter_avg_sentiment = (
            (daily_summary.twitter_avg_sentiment or 0) * (daily_summary.twitter_mentions_24h or 0) + 
            sentiment_data.sentiment_score * sentiment_data.volume
        ) / ((daily_summary.twitter_mentions_24h or 0) + sentiment_data.volume) if sentiment_data.volume > 0 else daily_summary.twitter_avg_sentiment
        daily_summary.twitter_mentions_24h = (daily_summary.twitter_mentions_24h or 0) + sentiment_data.volume
    
    elif sentiment_data.source == 'reddit':
        daily_summary.reddit_avg_sentiment = (
            (daily_summary.reddit_avg_sentiment or 0) * (daily_summary.reddit_mentions_24h or 0) + 
            sentiment_data.sentiment_score * sentiment_data.volume
        ) / ((daily_summary.reddit_mentions_24h or 0) + sentiment_data.volume) if sentiment_data.volume > 0 else daily_summary.reddit_avg_sentiment
        daily_summary.reddit_mentions_24h = (daily_summary.reddit_mentions_24h or 0) + sentiment_data.volume
    
    elif sentiment_data.source == 'wallstreetbets':
        daily_summary.wallstreetbets_mentions_24h = (daily_summary.wallstreetbets_mentions_24h or 0) + sentiment_data.volume
    
    # Recalculate overall sentiment score (weighted average of all sources)
    total_mentions = (
        (daily_summary.news_volume_24h or 0) + 
        (daily_summary.twitter_mentions_24h or 0) + 
        (daily_summary.reddit_mentions_24h or 0)
    )
    
    if total_mentions > 0:
        daily_summary.overall_sentiment_score = (
            (daily_summary.news_avg_sentiment or 0) * (daily_summary.news_volume_24h or 0) +
            (daily_summary.twitter_avg_sentiment or 0) * (daily_summary.twitter_mentions_24h or 0) +
            (daily_summary.reddit_avg_sentiment or 0) * (daily_summary.reddit_mentions_24h or 0)
        ) / total_mentions
    
    # Determine sentiment trend
    # Get previous day's sentiment
    yesterday = sentiment_data.date - timedelta(days=1)
    query = select(StocksSentimentDailySummary.overall_sentiment_score).where(
        and_(
            StocksSentimentDailySummary.stock_id == stock.stock_id,
            StocksSentimentDailySummary.date == yesterday
        )
    )
    result = await db.execute(query)
    prev_sentiment = result.scalar_one_or_none()
    
    if prev_sentiment is not None and daily_summary.overall_sentiment_score is not None:
        if daily_summary.overall_sentiment_score > prev_sentiment + 0.1:
            daily_summary.sentiment_trend = "Improving"
        elif daily_summary.overall_sentiment_score < prev_sentiment - 0.1:
            daily_summary.sentiment_trend = "Declining"
        else:
            daily_summary.sentiment_trend = "Stable"
    else:
        daily_summary.sentiment_trend = "Unknown"
    
    # Commit changes
    await db.commit()
    
    # Return the response
    return {
        "id": sentiment_id,
        "stock_id": stock.stock_id,
        "symbol": stock.symbol,
        "date": sentiment_data.date,
        "source": sentiment_data.source,
        "sentiment_score": sentiment_data.sentiment_score,
        "sentiment_label": sentiment_data.sentiment_label,
        "volume": sentiment_data.volume,
        "created_at": datetime.now()
    }


@router.get("/sentiment/aggregate", response_model=List[AggregatedSentimentResponse])
async def get_aggregated_sentiment(
    symbol: str = Query(..., description="Stock ticker symbol", example="AAPL"),
    start_date: date = Query(..., description="Start date for aggregation"),
    end_date: date = Query(..., description="End date for aggregation"),
    sources: List[str] = Query(None, description="Filter by sources (news, twitter, reddit, wallstreetbets)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated sentiment data by date and source.
    
    This endpoint returns sentiment data aggregated by date and source for a specific stock.
    You can filter by date range and specific sources.
    """
    # Find the stock by symbol
    query = select(StocksCore).where(func.upper(StocksCore.symbol) == func.upper(symbol))
    result = await db.execute(query)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found"
        )
    
    # Get daily sentiment summaries for the date range
    query = select(StocksSentimentDailySummary).where(
        and_(
            StocksSentimentDailySummary.stock_id == stock.stock_id,
            StocksSentimentDailySummary.date >= start_date,
            StocksSentimentDailySummary.date <= end_date
        )
    ).order_by(StocksSentimentDailySummary.date)
    
    result = await db.execute(query)
    summaries = result.scalars().all()
    
    # Process and aggregate the data
    aggregated_data = []
    
    for summary in summaries:
        # Add news sentiment if available and requested
        if (not sources or 'news' in sources) and summary.news_volume_24h:
            aggregated_data.append({
                "symbol": stock.symbol,
                "date": summary.date,
                "source": "news",
                "avg_sentiment_score": summary.news_avg_sentiment,
                "total_volume": summary.news_volume_24h,
                "sentiment_distribution": {
                    # Estimated distribution based on average score
                    "positive": int(summary.news_volume_24h * max(0, (summary.news_avg_sentiment + 1) / 2)),
                    "neutral": int(summary.news_volume_24h * (1 - abs(summary.news_avg_sentiment))),
                    "negative": int(summary.news_volume_24h * max(0, (-summary.news_avg_sentiment + 1) / 2))
                }
            })
        
        # Add Twitter sentiment if available and requested
        if (not sources or 'twitter' in sources) and summary.twitter_mentions_24h:
            aggregated_data.append({
                "symbol": stock.symbol,
                "date": summary.date,
                "source": "twitter",
                "avg_sentiment_score": summary.twitter_avg_sentiment,
                "total_volume": summary.twitter_mentions_24h,
                "sentiment_distribution": {
                    # Estimated distribution based on average score
                    "positive": int(summary.twitter_mentions_24h * max(0, (summary.twitter_avg_sentiment + 1) / 2)),
                    "neutral": int(summary.twitter_mentions_24h * (1 - abs(summary.twitter_avg_sentiment))),
                    "negative": int(summary.twitter_mentions_24h * max(0, (-summary.twitter_avg_sentiment + 1) / 2))
                }
            })
        
        # Add Reddit sentiment if available and requested
        if (not sources or 'reddit' in sources) and summary.reddit_mentions_24h:
            aggregated_data.append({
                "symbol": stock.symbol,
                "date": summary.date,
                "source": "reddit",
                "avg_sentiment_score": summary.reddit_avg_sentiment,
                "total_volume": summary.reddit_mentions_24h,
                "sentiment_distribution": {
                    # Estimated distribution based on average score
                    "positive": int(summary.reddit_mentions_24h * max(0, (summary.reddit_avg_sentiment + 1) / 2)),
                    "neutral": int(summary.reddit_mentions_24h * (1 - abs(summary.reddit_avg_sentiment))),
                    "negative": int(summary.reddit_mentions_24h * max(0, (-summary.reddit_avg_sentiment + 1) / 2))
                }
            })
        
        # Add WallStreetBets mentions if available and requested
        if (not sources or 'wallstreetbets' in sources) and summary.wallstreetbets_mentions_24h:
            # We don't have sentiment scores for WSB, just mention counts
            aggregated_data.append({
                "symbol": stock.symbol,
                "date": summary.date,
                "source": "wallstreetbets",
                "avg_sentiment_score": 0.0,  # Neutral by default
                "total_volume": summary.wallstreetbets_mentions_24h,
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": summary.wallstreetbets_mentions_24h,
                    "negative": 0
                }
            })
    
    return aggregated_data


@router.get("/top-bottom-20", response_model=TopBottomStocksResponse)
async def get_top_bottom_stocks(
    query_date: date = Query(None, description="Date for which to retrieve data (defaults to today)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the top 20 and bottom 20 stocks by sentiment score for a given date.

    The sentiment score is derived from `stocks_sentiment_daily_summary.overall_sentiment_score`.
    """
    # Default to today if no date provided
    if query_date is None:
        query_date = date.today()

    # Base selectable columns
    base_cols = [
        StocksCore.symbol,
        StocksSentimentDailySummary.overall_sentiment_score.label("sentiment_score"),
        StocksSentimentDailySummary.date,
    ]

    # --- Top 20 (descending) ---
    top_q = (
        select(*base_cols)
        .join(
            StocksSentimentDailySummary,
            StocksCore.stock_id == StocksSentimentDailySummary.stock_id,
        )
        .where(
            StocksSentimentDailySummary.date == query_date,
            StocksSentimentDailySummary.overall_sentiment_score.is_not(None),
        )
        .order_by(desc(StocksSentimentDailySummary.overall_sentiment_score))
        .limit(20)
    )

    # --- Bottom 20 (ascending) ---
    bottom_q = (
        select(*base_cols)
        .join(
            StocksSentimentDailySummary,
            StocksCore.stock_id == StocksSentimentDailySummary.stock_id,
        )
        .where(
            StocksSentimentDailySummary.date == query_date,
            StocksSentimentDailySummary.overall_sentiment_score.is_not(None),
        )
        .order_by(StocksSentimentDailySummary.overall_sentiment_score)
        .limit(20)
    )

    # Execute queries
    top_res = await db.execute(top_q)
    bottom_res = await db.execute(bottom_q)

    # Transform results to list of StockSentimentItem
    top_items = [
        StockSentimentItem(
            symbol=row.symbol,
            sentiment_score=row.sentiment_score,
            date=row.date,
        )
        for row in top_res.fetchall()
    ]

    bottom_items = [
        StockSentimentItem(
            symbol=row.symbol,
            sentiment_score=row.sentiment_score,
            date=row.date,
        )
        for row in bottom_res.fetchall()
    ]

    return TopBottomStocksResponse(top_20=top_items, bottom_20=bottom_items)


@router.post("/", response_model=StockCoreResponse, status_code=status.HTTP_201_CREATED)
async def create_stock(
    stock_data: StockCoreCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new stock entry in the database.
    
    This endpoint allows adding new stocks to the system.
    """
    # Check if stock with this symbol already exists
    query = select(StocksCore).where(func.upper(StocksCore.symbol) == func.upper(stock_data.symbol))
    result = await db.execute(query)
    existing_stock = result.scalar_one_or_none()
    
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock with symbol '{stock_data.symbol}' already exists"
        )
    
    # Create new stock
    new_stock = StocksCore(**stock_data.model_dump())
    db.add(new_stock)
    await db.commit()
    await db.refresh(new_stock)
    
    return new_stock


@router.get("/", response_model=List[StockCoreResponse])
async def list_stocks(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    country: Optional[str] = Query(None, description="Filter by country of origin"),
    search: Optional[str] = Query(None, description="Search by symbol or company name"),
    limit: int = Query(100, description="Limit the number of results", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List stocks with optional filtering.
    
    This endpoint returns a list of stocks with various filtering options.
    """
    # Build query with filters
    query = select(StocksCore)
    
    # Apply filters if provided
    if sector:
        query = query.where(func.upper(StocksCore.sector) == func.upper(sector))
    if industry:
        query = query.where(func.upper(StocksCore.industry) == func.upper(industry))
    if exchange:
        query = query.where(func.upper(StocksCore.exchange) == func.upper(exchange))
    if country:
        query = query.where(func.upper(StocksCore.country_of_origin) == func.upper(country))
    if search:
        query = query.where(
            or_(
                func.upper(StocksCore.symbol).contains(func.upper(search)),
                func.upper(StocksCore.company_name).contains(func.upper(search))
            )
        )
    
    # Apply pagination
    query = query.order_by(StocksCore.symbol).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    stocks = result.scalars().all()
    
    return stocks


@router.put("/{symbol}", response_model=StockCoreResponse)
async def update_stock(
    symbol: str = Path(..., description="Stock ticker symbol", example="AAPL"),
    stock_data: StockCoreCreate = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing stock's information.
    
    This endpoint allows updating stock details.
    """
    # Find the stock by symbol
    query = select(StocksCore).where(func.upper(StocksCore.symbol) == func.upper(symbol))
    result = await db.execute(query)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found"
        )
    
    # Update stock data
    stock_data_dict = stock_data.model_dump(exclude_unset=True)
    for key, value in stock_data_dict.items():
        setattr(stock, key, value)
    
    # Update last_updated timestamp
    stock.last_updated = func.now()
    
    await db.commit()
    await db.refresh(stock)
    
    return stock


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock(
    symbol: str = Path(..., description="Stock ticker symbol", example="AAPL"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a stock and all its related data.
    
    This endpoint removes a stock and all associated data from the database.
    """
    # Find the stock by symbol
    query = select(StocksCore).where(func.upper(StocksCore.symbol) == func.upper(symbol))
    result = await db.execute(query)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found"
        )
    
    # Delete the stock (cascade will delete related data)
    await db.delete(stock)
    await db.commit()
    
    return None
