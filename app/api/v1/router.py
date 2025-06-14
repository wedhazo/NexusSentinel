"""
API Router for NexusSentinel API v1.
"""

from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints.stocks import router as stocks_router
from app.api.v1.endpoints.market import router as market_router
from app.api.v1.endpoints.news import router as news_router

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(stocks_router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(market_router, prefix="/market", tags=["Market"])
api_router.include_router(news_router, prefix="/news", tags=["News"])
