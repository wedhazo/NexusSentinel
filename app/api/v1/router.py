from fastapi import APIRouter
from app.api.v1.endpoints import enhanced_sentiment, trading_signals

# Create main API v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    enhanced_sentiment.router,
    prefix="/enhanced-sentiment",
    tags=["enhanced-sentiment"]
)

# Trading signals (LightGBM-based)
api_router.include_router(
    trading_signals.router,
    prefix="/trading-signals",
    tags=["trading-signals"],
)

# Add other endpoint routers here as needed
# Example:
# from app.api.v1.endpoints import stocks, watchlists, alerts
# api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
# api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
# api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

# Export the router for use in the main application
