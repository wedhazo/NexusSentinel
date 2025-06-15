"""
API Router for NexusSentinel API v1.

This module aggregates all endpoint routers for API version 1 and
exports them as a single router to be included in the main application.
"""

from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints.stocks import router as stocks_router
# Newly added endpoint routers
from app.api.v1.endpoints.market import router as market_router
from app.api.v1.endpoints.news import router as news_router
# Import additional endpoint routers as they are created
# from app.api.v1.endpoints.users import router as users_router
# from app.api.v1.endpoints.auth import router as auth_router
# from app.api.v1.endpoints.watchlists import router as watchlists_router
# from app.api.v1.endpoints.alerts import router as alerts_router

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(stocks_router, prefix="/stocks", tags=["Stocks"])
# New routers
api_router.include_router(market_router, prefix="/market", tags=["Market"])
api_router.include_router(news_router, prefix="/news", tags=["News"])
# Include additional routers as they are created
# api_router.include_router(users_router, prefix="/users", tags=["Users"])
# api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# api_router.include_router(watchlists_router, prefix="/watchlists", tags=["Watchlists"])
# api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])

# Export the router for use in the main application
