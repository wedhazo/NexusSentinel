"""
News endpoints for NexusSentinel API.

This module provides endpoints for querying news data, including:
- Latest news articles across all stocks
- News articles for specific stocks
- News articles filtered by source, date range, or sentiment
- News articles with pagination support
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

# Import database and models
from app.database import get_db
from app.models.stocks_core import StocksCore
from app.models.stocks_news import StocksNews

# Define __all__ to export models for OpenAPI schema generation
__all__ = [
    "NewsItem", "NewsResponse"
]

# Create router
router = APIRouter(prefix="/news", tags=["News"])

# --- Pydantic Models for Request/Response ---

class NewsItem(BaseModel):
    """Schema for news article data."""
    id: int
    stock_id: Optional[int] = None
    symbol: Optional[str] = None
    title: str
    url: str
    source: str
    author: Optional[str] = None
    published_at: datetime
    content: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "stock_id": 42,
                "symbol": "AAPL",
                "title": "Apple Announces New iPhone 17 Pro",
                "url": "https://example.com/news/apple-iphone-17",
                "source": "TechNews",
                "author": "Jane Smith",
                "published_at": "2025-06-14T10:30:00Z",
                "content": "Apple today announced the latest addition to their iPhone lineup...",
                "sentiment_score": 0.75,
                "sentiment_label": "positive"
            }
        }
    )


class NewsResponse(BaseModel):
    """Schema for paginated news response."""
    news: List[NewsItem]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "news": [
                    {
                        "id": 1,
                        "stock_id": 42,
                        "symbol": "AAPL",
                        "title": "Apple Announces New iPhone 17 Pro",
                        "url": "https://example.com/news/apple-iphone-17",
                        "source": "TechNews",
                        "author": "Jane Smith",
                        "published_at": "2025-06-14T10:30:00Z",
                        "sentiment_score": 0.75,
                        "sentiment_label": "positive"
                    }
                ],
                "total": 42,
                "page": 1,
                "page_size": 10
            }
        }
    )


# --- Endpoints ---

@router.get("/", response_model=NewsResponse)
async def get_news(
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    source: Optional[str] = Query(None, description="Filter by news source"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive, neutral, negative)"),
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(10, description="Items per page", ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get news articles with optional filtering and pagination.
    
    This endpoint returns news articles that can be filtered by:
    - Stock symbol
    - News source
    - Date range
    - Sentiment
    
    Results are paginated and sorted by published date (newest first).
    """
    try:
        # Build base query to get total count
        count_query = select(func.count(StocksNews.id))
        
        # Build query to get news items with stock symbol
        query = select(
            StocksNews,
            StocksCore.symbol
        ).outerjoin(
            StocksCore,
            StocksNews.stock_id == StocksCore.stock_id
        )
        
        # Apply filters
        filters = []
        
        if symbol:
            filters.append(func.upper(StocksCore.symbol) == func.upper(symbol))
            
        if source:
            filters.append(func.upper(StocksNews.source) == func.upper(source))
            
        if start_date:
            filters.append(func.date(StocksNews.published_at) >= start_date)
            
        if end_date:
            filters.append(func.date(StocksNews.published_at) <= end_date)
            
        if sentiment:
            if sentiment.lower() == "positive":
                filters.append(StocksNews.sentiment_score > 0.3)
            elif sentiment.lower() == "negative":
                filters.append(StocksNews.sentiment_score < -0.3)
            elif sentiment.lower() == "neutral":
                filters.append(and_(
                    StocksNews.sentiment_score >= -0.3,
                    StocksNews.sentiment_score <= 0.3
                ))
        
        # Add filters to queries
        if filters:
            count_query = count_query.where(and_(*filters))
            query = query.where(and_(*filters))
        
        # Apply sorting and pagination
        query = query.order_by(desc(StocksNews.published_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute queries
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Process results
        news_items = []
        for row in rows:
            news = row[0]  # StocksNews object
            symbol = row[1]  # Symbol from StocksCore
            
            # Convert to dict and add symbol
            news_dict = {
                "id": news.id,
                "stock_id": news.stock_id,
                "symbol": symbol,
                "title": news.title,
                "url": news.url,
                "source": news.source,
                "author": news.author,
                "published_at": news.published_at,
                "content": news.content,
                "sentiment_score": news.sentiment_score,
                "sentiment_label": news.sentiment_label
            }
            
            news_items.append(NewsItem(**news_dict))
        
        # If no real data is available yet, generate some mock data
        if not news_items:
            # This block is temporary until real data is available
            mock_news = generate_mock_news(page, page_size)
            news_items = [NewsItem(**item) for item in mock_news]
            total_count = 42  # Mock total count
        
        return NewsResponse(
            news=news_items,
            total=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        # Log the error
        print(f"Error in get_news endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve news data"
        )


@router.get("/latest", response_model=List[NewsItem])
async def get_latest_news(
    limit: int = Query(5, description="Number of news items to return", ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the latest news articles across all stocks.
    
    This endpoint returns the most recent news articles, sorted by published date.
    """
    try:
        # Build query to get latest news with stock symbol
        query = select(
            StocksNews,
            StocksCore.symbol
        ).outerjoin(
            StocksCore,
            StocksNews.stock_id == StocksCore.stock_id
        ).order_by(
            desc(StocksNews.published_at)
        ).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Process results
        news_items = []
        for row in rows:
            news = row[0]  # StocksNews object
            symbol = row[1]  # Symbol from StocksCore
            
            # Convert to dict and add symbol
            news_dict = {
                "id": news.id,
                "stock_id": news.stock_id,
                "symbol": symbol,
                "title": news.title,
                "url": news.url,
                "source": news.source,
                "author": news.author,
                "published_at": news.published_at,
                "content": news.content,
                "sentiment_score": news.sentiment_score,
                "sentiment_label": news.sentiment_label
            }
            
            news_items.append(NewsItem(**news_dict))
        
        # If no real data is available yet, generate some mock data
        if not news_items:
            # This block is temporary until real data is available
            mock_news = generate_mock_news(1, limit)
            news_items = [NewsItem(**item) for item in mock_news]
        
        return news_items
        
    except Exception as e:
        # Log the error
        print(f"Error in get_latest_news endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest news"
        )


@router.get("/{symbol}", response_model=NewsResponse)
async def get_stock_news(
    symbol: str = Path(..., description="Stock ticker symbol"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(10, description="Items per page", ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get news articles for a specific stock.
    
    This endpoint returns news articles for a given stock symbol,
    with optional date filtering and pagination.
    """
    try:
        # Find the stock by symbol
        stock_query = select(StocksCore).where(func.upper(StocksCore.symbol) == func.upper(symbol))
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with symbol '{symbol}' not found"
            )
        
        # Build base query to get total count
        count_query = select(func.count(StocksNews.id)).where(StocksNews.stock_id == stock.stock_id)
        
        # Build query to get news items
        query = select(StocksNews).where(StocksNews.stock_id == stock.stock_id)
        
        # Apply date filters if provided
        if start_date:
            count_query = count_query.where(func.date(StocksNews.published_at) >= start_date)
            query = query.where(func.date(StocksNews.published_at) >= start_date)
            
        if end_date:
            count_query = count_query.where(func.date(StocksNews.published_at) <= end_date)
            query = query.where(func.date(StocksNews.published_at) <= end_date)
        
        # Apply sorting and pagination
        query = query.order_by(desc(StocksNews.published_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute queries
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        result = await db.execute(query)
        news_items = result.scalars().all()
        
        # Convert to response model and add symbol
        news_list = []
        for news in news_items:
            news_dict = {
                "id": news.id,
                "stock_id": news.stock_id,
                "symbol": symbol,
                "title": news.title,
                "url": news.url,
                "source": news.source,
                "author": news.author,
                "published_at": news.published_at,
                "content": news.content,
                "sentiment_score": news.sentiment_score,
                "sentiment_label": news.sentiment_label
            }
            
            news_list.append(NewsItem(**news_dict))
        
        # If no real data is available yet, generate some mock data
        if not news_list:
            # This block is temporary until real data is available
            mock_news = generate_mock_news(page, page_size, symbol)
            news_list = [NewsItem(**item) for item in mock_news]
            total_count = 15  # Mock total count for specific stock
        
        return NewsResponse(
            news=news_list,
            total=total_count,
            page=page,
            page_size=page_size
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error in get_stock_news endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stock news"
        )


# --- Helper Functions ---

def generate_mock_news(page: int, page_size: int, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate mock news data for development and testing.
    This function will be removed when real data is available.
    """
    mock_news = []
    
    # Stock symbols and their details
    stocks = [
        {"symbol": "AAPL", "name": "Apple", "stock_id": 1},
        {"symbol": "MSFT", "name": "Microsoft", "stock_id": 2},
        {"symbol": "GOOGL", "name": "Google", "stock_id": 3},
        {"symbol": "AMZN", "name": "Amazon", "stock_id": 4},
        {"symbol": "TSLA", "name": "Tesla", "stock_id": 5},
        {"symbol": "META", "name": "Meta", "stock_id": 6},
        {"symbol": "NVDA", "name": "NVIDIA", "stock_id": 7},
    ]
    
    # News sources
    sources = ["Bloomberg", "CNBC", "Reuters", "Wall Street Journal", "Financial Times"]
    
    # Headlines templates
    headlines = [
        "{company} Reports Strong Q2 Earnings, Exceeding Analyst Expectations",
        "{company} Announces New Product Line, Shares {direction}",
        "{company} CEO Discusses Future Growth Strategy in Interview",
        "Analysts Upgrade {company} Stock Rating to 'Buy'",
        "{company} Expands into New Markets, Targeting Growth Opportunities",
        "{company} Faces Regulatory Scrutiny Over Recent Acquisition",
        "Investors React to {company}'s Latest Quarterly Results",
        "{company} Partners with {partner} on New Technology Initiative",
        "Market Report: {company} Leads Sector {direction}",
        "{company} Announces Stock Buyback Program"
    ]
    
    # Calculate base date (today) and adjust for pagination
    base_date = datetime.now() - timedelta(hours=(page-1) * page_size)
    
    # Generate news items
    for i in range(page_size):
        # If symbol is provided, use only that stock, otherwise rotate through stocks
        if symbol:
            stock = next((s for s in stocks if s["symbol"].upper() == symbol.upper()), stocks[0])
        else:
            stock = stocks[i % len(stocks)]
        
        # Generate a realistic sentiment score (-1.0 to 1.0)
        sentiment_score = round((hash(f"{stock['symbol']}-{i}-{page}") % 200 - 100) / 100, 2)
        
        # Determine sentiment label based on score
        if sentiment_score > 0.3:
            sentiment_label = "positive"
            direction = "Rise"
        elif sentiment_score < -0.3:
            sentiment_label = "negative"
            direction = "Fall"
        else:
            sentiment_label = "neutral"
            direction = "Remain Stable"
        
        # Select a headline template and fill it
        headline_template = headlines[i % len(headlines)]
        partner = stocks[(i + 3) % len(stocks)]["name"]
        headline = headline_template.format(
            company=stock["name"],
            direction=direction,
            partner=partner
        )
        
        # Generate a unique ID
        unique_id = (page - 1) * page_size + i + 1
        
        # Create the news item
        news_item = {
            "id": unique_id,
            "stock_id": stock["stock_id"],
            "symbol": stock["symbol"],
            "title": headline,
            "url": f"https://example.com/news/{stock['symbol'].lower()}/{unique_id}",
            "source": sources[i % len(sources)],
            "author": f"Reporter {(i % 5) + 1}",
            "published_at": base_date - timedelta(hours=i * 2),
            "content": f"This is a mock news article about {stock['name']}...",
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label
        }
        
        mock_news.append(news_item)
    
    return mock_news
