from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import httpx
import logging
import asyncio
from pydantic import BaseModel, Field
from app.models.stocks_sentiment import SentimentModel  # Import your existing sentiment model

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/enhanced-sentiment",
    tags=["enhanced-sentiment"],
    responses={404: {"description": "Not found"}},
)

# Models for request and response
class EnhancedSentimentRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for sentiment")
    cache: bool = Field(True, description="Whether to use cache for this request")

class EnhancedSentimentResponse(BaseModel):
    symbol: Optional[str] = None
    text: str
    finbert_sentiment: Dict[str, Any]
    traditional_sentiment: Optional[Dict[str, Any]] = None
    combined_score: Optional[float] = None

# Helper function to call the FinBERT service
async def call_finbert_service(text: str, cache: bool = True) -> Dict[str, Any]:
    """Call the FinBERT sentiment service and return the result."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://sentiment_service:8000/sentiment",
                json={"text": text, "cache": cache}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"FinBERT service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"FinBERT service error: {response.text}"
                )
    except httpx.TimeoutException:
        logger.error("FinBERT service timeout")
        raise HTTPException(
            status_code=504,
            detail="FinBERT service timeout"
        )
    except httpx.ConnectError:
        logger.error("FinBERT service connection error")
        raise HTTPException(
            status_code=503,
            detail="FinBERT service unavailable"
        )
    except Exception as e:
        logger.error(f"Error calling FinBERT service: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing sentiment: {str(e)}"
        )

# Get traditional sentiment for a symbol
async def get_traditional_sentiment(symbol: str) -> Dict[str, Any]:
    """Get traditional sentiment for a symbol from existing system."""
    try:
        # This is a placeholder - replace with your actual sentiment retrieval logic
        sentiment = SentimentModel.get_sentiment(symbol)
        return sentiment
    except Exception as e:
        logger.warning(f"Could not retrieve traditional sentiment for {symbol}: {str(e)}")
        return None

# Combine sentiment scores
def combine_sentiment_scores(finbert_result: Dict[str, Any], traditional_result: Optional[Dict[str, Any]]) -> float:
    """Combine sentiment scores from different sources with appropriate weighting."""
    # This is a simple example - you may want a more sophisticated approach
    finbert_score = 0.0
    
    # Map FinBERT labels to numeric scores
    if finbert_result["label"] == "positive":
        finbert_score = finbert_result["score"]
    elif finbert_result["label"] == "negative":
        finbert_score = -finbert_result["score"]
    # neutral is 0.0
    
    # If we have traditional sentiment, combine them (60% FinBERT, 40% traditional)
    if traditional_result and "score" in traditional_result:
        trad_score = traditional_result["score"]
        return (0.6 * finbert_score) + (0.4 * trad_score)
    
    # Otherwise just return the FinBERT score
    return finbert_score

# Endpoint for analyzing text sentiment
@router.post("/analyze", response_model=EnhancedSentimentResponse)
async def analyze_text_sentiment(request: EnhancedSentimentRequest):
    """Analyze sentiment for arbitrary text using FinBERT."""
    finbert_result = await call_finbert_service(request.text, request.cache)
    
    return EnhancedSentimentResponse(
        text=request.text,
        finbert_sentiment=finbert_result,
        traditional_sentiment=None,  # No traditional sentiment for arbitrary text
        combined_score=None
    )

# Endpoint for getting enhanced sentiment for a stock symbol
@router.get("/{symbol}", response_model=EnhancedSentimentResponse)
async def get_enhanced_sentiment(
    symbol: str,
    text: Optional[str] = Query(None, description="Optional specific text to analyze")
):
    """Get enhanced sentiment analysis for a stock symbol."""
    # If no specific text is provided, use the symbol as the text
    analysis_text = text if text else f"{symbol} stock"
    
    # Get sentiment from both sources concurrently
    finbert_task = call_finbert_service(analysis_text)
    traditional_task = get_traditional_sentiment(symbol)
    
    # Wait for both tasks to complete
    finbert_result, traditional_result = await asyncio.gather(
        finbert_task, 
        traditional_task,
        return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(finbert_result, Exception):
        logger.error(f"FinBERT analysis failed: {str(finbert_result)}")
        raise HTTPException(
            status_code=500,
            detail=f"FinBERT analysis failed: {str(finbert_result)}"
        )
    
    # Traditional sentiment might be None or failed, but we continue
    if isinstance(traditional_result, Exception):
        logger.warning(f"Traditional sentiment retrieval failed: {str(traditional_result)}")
        traditional_result = None
    
    # Calculate combined score
    combined_score = combine_sentiment_scores(finbert_result, traditional_result)
    
    return EnhancedSentimentResponse(
        symbol=symbol,
        text=analysis_text,
        finbert_sentiment=finbert_result,
        traditional_sentiment=traditional_result,
        combined_score=combined_score
    )

# Batch sentiment analysis endpoint
@router.post("/batch", response_model=List[EnhancedSentimentResponse])
async def batch_sentiment_analysis(requests: List[EnhancedSentimentRequest]):
    """Analyze sentiment for multiple texts in a batch."""
    if len(requests) > 20:
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds maximum of 20 items"
        )
    
    # Process each request concurrently
    tasks = [analyze_text_sentiment(request) for request in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error processing item {i}: {str(result)}")
            processed_results.append({
                "text": requests[i].text,
                "error": str(result),
                "finbert_sentiment": None,
                "traditional_sentiment": None,
                "combined_score": None
            })
        else:
            processed_results.append(result)
    
    return processed_results

# Health check endpoint
@router.get("/health")
async def health_check():
    """Check health of the enhanced sentiment service and dependencies."""
    health_status = {"status": "healthy", "components": {}}
    
    # Check FinBERT service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://sentiment_service:8000/health")
            if response.status_code == 200:
                health_status["components"]["finbert_service"] = "healthy"
            else:
                health_status["status"] = "degraded"
                health_status["components"]["finbert_service"] = {
                    "status": "unhealthy",
                    "error": f"Status code: {response.status_code}"
                }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["finbert_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check traditional sentiment system
    try:
        # Placeholder for checking your existing sentiment system
        health_status["components"]["traditional_sentiment"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["traditional_sentiment"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status
