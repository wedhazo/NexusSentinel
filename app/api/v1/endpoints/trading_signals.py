from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx
from typing import List, Optional, Dict, Any
import logging
import asyncio

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/trading-signals",
    tags=["trading-signals"],
    responses={404: {"description": "Not found"}},
)

# Models for request/response
class SignalRequest(BaseModel):
    sentiment_score: float = Field(..., description="Sentiment score from -1.0 (negative) to 1.0 (positive)")
    sentiment_momentum: float = Field(..., description="Change in sentiment over time")
    rsi_14: float = Field(..., description="Relative Strength Index (14-period)")
    volume_change: float = Field(..., description="Percent change in trading volume")
    price_sma_20: Optional[float] = Field(None, description="Price relative to 20-day SMA")
    macd: Optional[float] = Field(None, description="Moving Average Convergence Divergence")
    
    class Config:
        schema_extra = {
            "example": {
                "sentiment_score": 0.75,
                "sentiment_momentum": 0.15,
                "rsi_14": 65.5,
                "volume_change": 1.2,
                "price_sma_20": 1.05,
                "macd": 0.02
            }
        }

class StockSignalRequest(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol")
    use_enhanced_sentiment: bool = Field(True, description="Whether to use enhanced sentiment analysis")
    use_consensus: bool = Field(False, description="Whether to use consensus sentiment from multiple models")

class BatchSignalRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of stock ticker symbols")
    use_enhanced_sentiment: bool = Field(True, description="Whether to use enhanced sentiment analysis")

class SignalResponse(BaseModel):
    signal: str
    confidence: float
    timestamp: str
    features_used: Dict[str, float]
    symbol: Optional[str] = None

# Service URL - can be moved to config later
SIGNAL_SERVICE_URL = "http://signal_generator:8002"
SENTIMENT_SERVICE_URL = "http://sentiment_service:8000"
ENHANCED_SENTIMENT_URL = "http://api:8000/api/v1/enhanced-sentiment"

# Helper function to call the signal generator service
async def call_signal_service(features: Dict[str, Any]):
    """Call the LightGBM signal generator service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SIGNAL_SERVICE_URL}/signal",
                json=features,
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"Signal service error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Signal service error: {response.text}"
                )
                
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"Error connecting to signal service: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Signal service unavailable: {str(exc)}"
        )

# Helper function to get sentiment for a stock
async def get_stock_sentiment(symbol: str, use_enhanced: bool = True, use_consensus: bool = False):
    """Get sentiment analysis for a stock symbol"""
    try:
        async with httpx.AsyncClient() as client:
            if use_enhanced:
                if use_consensus:
                    # Use consensus sentiment (combines FinBERT and LLaMA)
                    endpoint = f"{ENHANCED_SENTIMENT_URL}/analyze-consensus"
                    response = await client.post(
                        endpoint,
                        json={"text": f"{symbol} stock recent performance and outlook"},
                        timeout=60.0  # Longer timeout for LLaMA
                    )
                else:
                    # Use enhanced sentiment (FinBERT)
                    endpoint = f"{ENHANCED_SENTIMENT_URL}/analyze"
                    response = await client.post(
                        endpoint,
                        json={"text": f"{symbol} stock recent performance and outlook"},
                        timeout=30.0
                    )
            else:
                # Use basic sentiment endpoint
                endpoint = f"{ENHANCED_SENTIMENT_URL}/stock/{symbol}"
                response = await client.get(endpoint, timeout=30.0)
            
            if response.status_code != 200:
                logger.error(f"Sentiment service error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Sentiment service error: {response.text}"
                )
                
            sentiment_data = response.json()
            
            # Convert sentiment label to score (-1 to 1)
            sentiment_label = sentiment_data.get("sentiment", "neutral")
            sentiment_score = 0.0  # Default neutral
            
            if sentiment_label == "positive":
                sentiment_score = sentiment_data.get("confidence", 0.7)
            elif sentiment_label == "negative":
                sentiment_score = -sentiment_data.get("confidence", 0.7)
                
            return {
                "sentiment_score": sentiment_score,
                "sentiment_data": sentiment_data
            }
    except httpx.RequestError as exc:
        logger.error(f"Error connecting to sentiment service: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Sentiment service unavailable: {str(exc)}"
        )

# Helper function to get technical indicators for a stock
async def get_technical_indicators(symbol: str):
    """
    Get technical indicators for a stock symbol
    
    Note: In a real implementation, this would fetch data from a market data provider
    or from your existing database. This is a placeholder that returns mock data.
    """
    # Mock data - in production, replace with actual API calls or database queries
    import random
    
    # Generate somewhat realistic mock data
    rsi = random.uniform(30, 70)
    volume_change = random.uniform(0.8, 1.5)
    price_sma_20 = random.uniform(0.9, 1.1)
    macd = random.uniform(-0.1, 0.1)
    
    # Add some randomness to sentiment momentum
    sentiment_momentum = random.uniform(-0.2, 0.2)
    
    return {
        "rsi_14": rsi,
        "volume_change": volume_change,
        "price_sma_20": price_sma_20,
        "macd": macd,
        "sentiment_momentum": sentiment_momentum
    }

@router.post("/generate", response_model=SignalResponse)
async def generate_signal(request: SignalRequest):
    """
    Generate a trading signal based on provided technical and sentiment features
    
    This endpoint accepts technical indicators and sentiment data directly and
    returns a trading signal (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
    """
    # Forward the request to the signal generator service
    return await call_signal_service(request.dict())

@router.post("/stock/{symbol}", response_model=SignalResponse)
async def get_stock_signal(
    symbol: str, 
    use_enhanced_sentiment: bool = True,
    use_consensus: bool = False
):
    """
    Generate a trading signal for a specific stock symbol
    
    This endpoint automatically fetches sentiment and technical data for the
    specified stock and returns a trading signal
    """
    # Get sentiment data for the stock
    sentiment_result = await get_stock_sentiment(
        symbol, 
        use_enhanced=use_enhanced_sentiment,
        use_consensus=use_consensus
    )
    
    # Get technical indicators for the stock
    technical = await get_technical_indicators(symbol)
    
    # Combine data for signal generation
    features = {
        "sentiment_score": sentiment_result["sentiment_score"],
        "sentiment_momentum": technical["sentiment_momentum"],
        "rsi_14": technical["rsi_14"],
        "volume_change": technical["volume_change"],
        "price_sma_20": technical["price_sma_20"],
        "macd": technical["macd"]
    }
    
    # Get trading signal
    signal = await call_signal_service(features)
    
    # Add symbol to response
    signal["symbol"] = symbol
    
    # Add sentiment details
    signal["sentiment_details"] = sentiment_result["sentiment_data"]
    
    return signal

@router.post("/batch", response_model=List[SignalResponse])
async def batch_generate_signals(request: BatchSignalRequest):
    """
    Generate trading signals for multiple stock symbols in a single request
    
    This endpoint is useful for analyzing a watchlist or portfolio of stocks
    """
    results = []
    
    # Process each symbol
    for symbol in request.symbols:
        try:
            # Get signal for this symbol
            signal = await get_stock_signal(
                symbol,
                use_enhanced_sentiment=request.use_enhanced_sentiment
            )
            results.append(signal)
        except Exception as e:
            # Log error but continue processing other symbols
            logger.error(f"Error processing signal for {symbol}: {str(e)}")
            results.append({
                "symbol": symbol,
                "signal": "ERROR",
                "confidence": 0.0,
                "timestamp": None,
                "features_used": {},
                "error": str(e)
            })
    
    return results

@router.get("/health")
async def health_check():
    """Check if the signal generator service is healthy"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SIGNAL_SERVICE_URL}/health")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "service_response": response.json() if response.status_code == 200 else None
            }
    except httpx.RequestError:
        return {"status": "unhealthy", "service_response": None}

@router.get("/model-info")
async def model_info():
    """Get information about the current signal generator model"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SIGNAL_SERVICE_URL}/model-info")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to retrieve model information"
                )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Signal service unavailable: {str(exc)}"
        )
