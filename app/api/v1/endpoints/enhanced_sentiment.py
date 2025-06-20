from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
from typing import List, Optional, Dict, Any
import logging
import asyncio

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/enhanced-sentiment",
    tags=["enhanced-sentiment"],
    responses={404: {"description": "Not found"}},
)

# Models for request/response
class SentimentRequest(BaseModel):
    text: str
    cache: bool = True

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    model: str

class LlamaSentimentResponse(BaseModel):
    text: str
    sentiment: str
    explanation: Optional[str] = None
    processing_time: float
    model: str = "llama3-8b"

class ConsensusSentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    finbert_sentiment: Optional[Dict[str, Any]] = None
    llama_sentiment: Optional[Dict[str, Any]] = None
    consensus_method: str = "weighted"

class BatchSentimentRequest(BaseModel):
    texts: List[str]
    cache: bool = True

# Service URLs - can be moved to config later
SENTIMENT_SERVICE_URL = "http://sentiment_service:8000"
LLAMA_SERVICE_URL = "http://llama3_sentiment_service:8001"

# Helper function to call the FinBERT sentiment service
async def call_sentiment_service(text: str, cache: bool = True):
    """Call the FinBERT sentiment service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SENTIMENT_SERVICE_URL}/sentiment",
                json={"text": text, "cache": cache},
                timeout=30.0  # Increased timeout for model inference
            )
            
            if response.status_code != 200:
                logger.error(f"FinBERT sentiment service error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"FinBERT sentiment service error: {response.text}"
                )
                
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"Error connecting to FinBERT sentiment service: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"FinBERT sentiment service unavailable: {str(exc)}"
        )

# Helper function to call the LLaMA sentiment service
async def call_llama_sentiment_service(text: str):
    """Call the LLaMA 3 sentiment service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLAMA_SERVICE_URL}/llama-sentiment",
                json={"text": text},
                timeout=60.0  # Longer timeout for LLaMA inference
            )
            
            if response.status_code != 200:
                logger.error(f"LLaMA sentiment service error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLaMA sentiment service error: {response.text}"
                )
                
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"Error connecting to LLaMA sentiment service: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"LLaMA sentiment service unavailable: {str(exc)}"
        )

@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyze sentiment for any financial text using FinBERT
    
    Returns sentiment (positive, negative, neutral) and confidence score
    """
    return await call_sentiment_service(request.text, request.cache)

@router.post("/analyze-llama", response_model=LlamaSentimentResponse)
async def analyze_llama_sentiment(request: SentimentRequest):
    """
    Analyze sentiment for financial text using LLaMA 3 with nuanced understanding
    
    This endpoint is designed to handle complex financial texts including sarcasm,
    implicit meaning, and financial jargon
    """
    return await call_llama_sentiment_service(request.text)

@router.post("/analyze-consensus", response_model=ConsensusSentimentResponse)
async def analyze_consensus_sentiment(request: SentimentRequest):
    """
    Analyze sentiment using both FinBERT and LLaMA 3 models and provide a consensus result
    
    This endpoint combines the strengths of both models:
    - FinBERT: Fast, specialized for financial texts
    - LLaMA 3: Better at understanding context, sarcasm, and nuance
    
    If one service is unavailable, results from the available service will be used
    """
    finbert_result = None
    llama_result = None
    
    # Run both API calls concurrently
    finbert_task = asyncio.create_task(
        call_sentiment_service(request.text, request.cache)
    )
    llama_task = asyncio.create_task(
        call_llama_sentiment_service(request.text)
    )
    
    # Wait for both tasks with error handling
    try:
        finbert_result = await finbert_task
    except HTTPException as e:
        logger.warning(f"FinBERT service unavailable: {str(e)}")
        finbert_result = None
    
    try:
        llama_result = await llama_task
    except HTTPException as e:
        logger.warning(f"LLaMA service unavailable: {str(e)}")
        llama_result = None
    
    # Handle case where both services are unavailable
    if finbert_result is None and llama_result is None:
        raise HTTPException(
            status_code=503,
            detail="Both sentiment services are currently unavailable"
        )
    
    # Determine consensus sentiment
    consensus_sentiment = "neutral"  # Default
    confidence = 0.5  # Default
    
    if finbert_result and llama_result:
        # Both services available - weighted consensus
        # FinBERT provides a confidence score we can use
        finbert_sentiment = finbert_result.get("sentiment")
        llama_sentiment = llama_result.get("sentiment")
        finbert_confidence = finbert_result.get("confidence", 0.5)
        
        # Simple weighted consensus
        if finbert_sentiment == llama_sentiment:
            # Both agree - use that sentiment with high confidence
            consensus_sentiment = finbert_sentiment
            confidence = max(0.8, finbert_confidence)  # At least 0.8 confidence when both agree
        else:
            # Disagreement - use FinBERT's confidence as a weight
            consensus_sentiment = finbert_sentiment
            confidence = finbert_confidence
            
            # If FinBERT has low confidence, prefer LLaMA's result
            if finbert_confidence < 0.6:
                consensus_sentiment = llama_sentiment
                confidence = 0.6  # Moderate confidence when using LLaMA over low-confidence FinBERT
    
    elif finbert_result:
        # Only FinBERT available
        consensus_sentiment = finbert_result.get("sentiment")
        confidence = finbert_result.get("confidence", 0.5)
    
    elif llama_result:
        # Only LLaMA available
        consensus_sentiment = llama_result.get("sentiment")
        confidence = 0.6  # Moderate fixed confidence for LLaMA
    
    return {
        "text": request.text,
        "sentiment": consensus_sentiment,
        "confidence": confidence,
        "finbert_sentiment": finbert_result,
        "llama_sentiment": llama_result,
        "consensus_method": "weighted"
    }

@router.get("/stock/{symbol}", response_model=SentimentResponse)
async def get_stock_sentiment(symbol: str, cache: bool = True):
    """
    Get sentiment analysis for a specific stock symbol
    
    Analyzes the sentiment around the given stock symbol
    """
    # Construct a text that focuses on the stock
    text = f"Analysis of {symbol} stock performance and outlook"
    return await call_sentiment_service(text, cache)

@router.post("/batch", response_model=List[SentimentResponse])
async def batch_analyze_sentiment(request: BatchSentimentRequest):
    """
    Analyze sentiment for multiple texts in a single request
    
    Useful for processing multiple news items or tweets at once
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SENTIMENT_SERVICE_URL}/batch-sentiment",
                json=[{"text": text, "cache": request.cache} for text in request.texts],
                timeout=60.0  # Longer timeout for batch processing
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Sentiment service error: {response.text}"
                )
                
            return response.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Sentiment service unavailable: {str(exc)}"
        )

@router.get("/health")
async def health_check():
    """Check if the sentiment services are healthy"""
    results = {}
    
    # Check FinBERT service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SENTIMENT_SERVICE_URL}/health")
            results["finbert_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
    except httpx.RequestError:
        results["finbert_service"] = {"status": "unhealthy", "details": None}
    
    # Check LLaMA service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLAMA_SERVICE_URL}/health")
            results["llama_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
    except httpx.RequestError:
        results["llama_service"] = {"status": "unhealthy", "details": None}
    
    # Overall status
    results["overall_status"] = "healthy" if (
        results.get("finbert_service", {}).get("status") == "healthy" or 
        results.get("llama_service", {}).get("status") == "healthy"
    ) else "unhealthy"
    
    return results
