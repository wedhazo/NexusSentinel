from fastapi import APIRouter
from app.api.v1.endpoints import enhanced_sentiment
# Import other endpoint modules
# from app.api.v1.endpoints import stocks, watchlist, alerts, etc.

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(enhanced_sentiment.router)

# Include other endpoint routers
# api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
# api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
# api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

# Add any global API configurations or middleware here
