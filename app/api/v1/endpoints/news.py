"""
News endpoints for NexusSentinel API.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db

# Create router
router = APIRouter()

# Pydantic Models
class NewsItem(BaseModel):
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

class NewsResponse(BaseModel):
    news: List[NewsItem]
    total: int
    page: int
    page_size: int

# Endpoints
@router.get("/", response_model=NewsResponse)
async def get_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated news articles."""
    
    # Mock data for now
    mock_news = []
    total_news = 42
    
    # Stock symbols for sample data
    stocks = [
        {"symbol": "AAPL", "name": "Apple", "stock_id": 1},
        {"symbol": "MSFT", "name": "Microsoft", "stock_id": 2},
        {"symbol": "GOOGL", "name": "Google", "stock_id": 3},
        {"symbol": "AMZN", "name": "Amazon", "stock_id": 4},
        {"symbol": "TSLA", "name": "Tesla", "stock_id": 5},
    ]
    
    # News sources
    sources = ["Bloomberg", "CNBC", "Reuters", "Wall Street Journal", "Financial Times"]
    
    # Base date for news
    base_date = datetime.now() - timedelta(hours=(page-1) * page_size)
    
    # Generate news items
    for i in range(page_size):
        if (page-1) * page_size + i >= total_news:
            break
            
        stock = stocks[i % len(stocks)]
        sentiment_score = round((hash(f"{stock['symbol']}-{i}-{page}") % 200 - 100) / 100, 2)
        
        if sentiment_score > 0.3:
            sentiment_label = "positive"
        elif sentiment_score < -0.3:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # Create news item
        news_item = NewsItem(
            id=(page - 1) * page_size + i + 1,
            stock_id=stock["stock_id"],
            symbol=stock["symbol"],
            title=f"{stock['name']} latest news headline #{(page - 1) * page_size + i + 1}",
            url=f"https://example.com/news/{stock['symbol'].lower()}/{(page - 1) * page_size + i + 1}",
            source=sources[i % len(sources)],
            author=f"Reporter {(i % 5) + 1}",
            published_at=base_date - timedelta(hours=i * 2),
            content=f"This is a mock news article about {stock['name']}...",
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label
        )
        
        mock_news.append(news_item)
    
    return {
        "news": mock_news,
        "total": total_news,
        "page": page,
        "page_size": page_size
    }
