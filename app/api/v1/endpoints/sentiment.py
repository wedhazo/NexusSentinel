"""
Sentiment Analysis endpoints for NexusSentinel API.

This module provides endpoints for analyzing sentiment in financial text, including:
- Text sentiment analysis with FinBERT/FinGPT
- Fallback to OpenAI for low-confidence results
- Entity extraction for companies, symbols, and financial instruments
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel, Field, validator
import logging
import time
from datetime import datetime

from app.config import settings
from app.services.sentiment_analysis import (
    SentimentAnalysisRequest, 
    SentimentAnalysisResponse,
    analyze_text_sentiment,
    SentimentLabel,
    Entity,
    EntityType
)

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# --- Pydantic Models for Request/Response ---

class SentimentAnalyzeRequest(BaseModel):
    """Schema for sentiment analysis request."""
    text: str = Field(..., description="Text to analyze for sentiment", min_length=1, max_length=5000)
    source: Optional[str] = Field(None, description="Source of the text (e.g., 'news', 'twitter', 'reddit')")
    extract_entities: bool = Field(True, description="Whether to extract entities from the text")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the request")
    
    @validator('text')
    def text_not_empty(cls, v):
        """Validate that text is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Text cannot be empty")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Apple's new product line exceeds analyst expectations, driving stock up 5%.",
                "source": "news",
                "extract_entities": True,
                "metadata": {"article_id": "12345", "publisher": "Financial Times"}
            }
        }


class EntityResponse(BaseModel):
    """Schema for entity in response."""
    text: str = Field(..., description="The extracted entity text")
    type: str = Field(..., description="Type of the entity")
    confidence: float = Field(..., description="Confidence score for the entity extraction", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the entity")


class SentimentAnalyzeResponse(BaseModel):
    """Schema for sentiment analysis response."""
    text: str = Field(..., description="Original text that was analyzed")
    sentiment: str = Field(..., description="Detected sentiment label")
    confidence: float = Field(..., description="Confidence score for the sentiment", ge=0.0, le=1.0)
    source: str = Field(..., description="Source of the analysis (e.g., 'finbert', 'openai')")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the sentiment classification")
    entities: List[EntityResponse] = Field(default_factory=list, description="Extracted entities from the text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the analysis")
    request_id: str = Field(..., description="Unique identifier for this request")
    processed_at: datetime = Field(..., description="Timestamp when the analysis was processed")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Apple's new product line exceeds analyst expectations, driving stock up 5%.",
                "sentiment": "positive",
                "confidence": 0.92,
                "source": "finbert",
                "reasoning": "The text indicates a positive financial outcome with stock price increase and exceeding expectations.",
                "entities": [
                    {
                        "text": "Apple",
                        "type": "company",
                        "confidence": 0.98,
                        "metadata": {"possible_symbols": ["AAPL"]}
                    }
                ],
                "metadata": {
                    "processing_time_ms": 156
                },
                "request_id": "f8d7e9c6-5b4a-4c3d-9e1f-2b3c4d5e6f7a",
                "processed_at": "2025-06-14T12:34:56.789Z"
            }
        }


# --- Endpoints ---

@router.post(
    "/analyze", 
    response_model=SentimentAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze sentiment in financial text",
    response_description="Sentiment analysis results with confidence score and extracted entities"
)
async def analyze_sentiment(
    request: SentimentAnalyzeRequest,
    confidence_threshold: Optional[float] = Query(
        None, 
        description="Confidence threshold for fallback to OpenAI (0.0-1.0)", 
        ge=0.0, 
        le=1.0
    ),
    background_tasks: BackgroundTasks = None
):
    """
    Analyze the sentiment of financial text using AI models.
    
    This endpoint processes the provided text to determine its financial sentiment:
    - First attempts analysis with FinBERT/FinGPT for fast, specialized financial sentiment
    - If confidence is below threshold, falls back to OpenAI for more nuanced analysis
    - Optionally extracts entities (companies, symbols, financial instruments) from the text
    
    The sentiment is classified as:
    - **positive**: Text indicates positive financial outcomes or bullish sentiment
    - **neutral**: Text is financially neutral or contains balanced positive/negative elements
    - **negative**: Text indicates negative financial outcomes or bearish sentiment
    
    When entity extraction is enabled, the response includes companies, stock symbols,
    and financial instruments mentioned in the text.
    
    Rate limits:
    - Standard tier: 100 requests per minute
    - Premium tier: 1000 requests per minute
    
    ## Example use cases:
    - Analyzing news headlines for market sentiment
    - Processing social media posts about stocks
    - Evaluating financial reports and press releases
    """
    # Generate request ID
    import uuid
    request_id = str(uuid.uuid4())
    
    # Log the incoming request
    logger.info(f"Processing sentiment analysis request {request_id}: {request.text[:100]}...")
    
    start_time = time.time()
    
    try:
        # Convert to internal request model
        internal_request = SentimentAnalysisRequest(
            text=request.text,
            source=request.source,
            extract_entities=request.extract_entities,
            metadata=request.metadata
        )
        
        # Process the request using our service
        result = await analyze_text_sentiment(
            request=internal_request,
            confidence_threshold=confidence_threshold
        )
        
        # Convert entities to response format
        entities = [
            EntityResponse(
                text=entity.text,
                type=entity.type,
                confidence=entity.confidence,
                metadata=entity.metadata
            )
            for entity in result.entities
        ]
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)  # in milliseconds
        
        # Update metadata with processing time if not already present
        if "processing_time_ms" not in result.metadata:
            result.metadata["processing_time_ms"] = processing_time
        
        # Log successful analysis
        logger.info(
            f"Completed sentiment analysis {request_id} in {processing_time}ms: "
            f"{result.sentiment} ({result.confidence:.2f}) from {result.source}"
        )
        
        # Schedule background task to store the result if needed
        if background_tasks and settings.ENABLE_SENTIMENT_HISTORY:
            background_tasks.add_task(
                store_sentiment_result,
                text=request.text,
                sentiment=result.sentiment,
                confidence=result.confidence,
                source=result.source
            )
        
        # Return the response
        return SentimentAnalyzeResponse(
            text=result.text,
            sentiment=result.sentiment,
            confidence=result.confidence,
            source=result.source,
            reasoning=result.reasoning,
            entities=entities,
            metadata=result.metadata,
            request_id=request_id,
            processed_at=datetime.utcnow()
        )
        
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error in sentiment analysis request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Error processing sentiment analysis request {request_id}: {str(e)}", exc_info=True)
        
        # Return a user-friendly error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the sentiment analysis request. Please try again later."
        )


# --- Background Tasks ---

async def store_sentiment_result(text: str, sentiment: str, confidence: float, source: str):
    """
    Store sentiment analysis result in database for historical tracking.
    
    This is a placeholder for future implementation.
    """
    # This would typically store the result in a database
    # For now, just log it
    logger.info(f"Would store sentiment result: {sentiment} ({confidence:.2f}) from {source}")
    pass
