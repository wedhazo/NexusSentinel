from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import pipeline
import redis
import json
import logging
import os
import time
from typing import Dict, Any, Optional
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sentiment_service")

# Initialize FastAPI app
app = FastAPI(
    title="FinBERT Sentiment Analysis API",
    description="Financial sentiment analysis using FinBERT model",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 hour default
MODEL_CACHE_SIZE = int(os.getenv("MODEL_CACHE_SIZE", "100"))

# Redis connection with retry mechanism
def get_redis_connection():
    max_retries = 5
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_timeout=5,
            )
            r.ping()  # Test connection
            logger.info("Successfully connected to Redis")
            return r
        except redis.RedisError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Redis connection failed (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Redis connection failed after {max_retries} attempts: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Redis service unavailable: {str(e)}"
                )

# Load FinBERT model with caching
@lru_cache(maxsize=1)
def get_finbert_model():
    logger.info("Loading FinBERT model...")
    try:
        model = pipeline(
            "text-classification",
            model="yiyanghkust/finbert-tone",
            tokenizer="yiyanghkust/finbert-tone"
        )
        logger.info("FinBERT model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load FinBERT model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Model initialization failed: {str(e)}"
        )

# Input and output models
class TextInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=1024, description="Text to analyze for sentiment")
    cache: bool = Field(True, description="Whether to use cache for this request")

class SentimentResponse(BaseModel):
    label: str
    score: float
    source: str = "cache"  # "cache" or "model"
    processing_time: float

# Health check endpoint
@app.get("/health")
async def health_check():
    start_time = time.time()
    health_status = {"status": "healthy", "components": {}}
    
    # Check Redis
    try:
        redis_conn = get_redis_connection()
        redis_conn.ping()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # Check model
    try:
        # Just check if model can be loaded, don't actually load it here
        if "finbert_model" in app.state.__dict__:
            health_status["components"]["model"] = "healthy"
        else:
            # Try to access the model to trigger loading if needed
            _ = get_finbert_model()
            health_status["components"]["model"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["model"] = {"status": "unhealthy", "error": str(e)}
    
    health_status["response_time"] = time.time() - start_time
    
    return health_status

# Sentiment analysis endpoint
@app.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(
    data: TextInput,
    background_tasks: BackgroundTasks
):
    start_time = time.time()
    text = data.text.strip()
    
    # Try to get from cache if caching is enabled
    if data.cache:
        try:
            redis_conn = get_redis_connection()
            cache_key = f"sentiment:{text.lower()}"
            cached_result = redis_conn.get(cache_key)
            
            if cached_result:
                result = json.loads(cached_result)
                logger.info(f"Cache hit for text: {text[:50]}...")
                return SentimentResponse(
                    label=result["label"],
                    score=result["score"],
                    source="cache",
                    processing_time=time.time() - start_time
                )
        except Exception as e:
            logger.warning(f"Redis error (continuing with model): {e}")
    
    # If not in cache or cache disabled, use the model
    try:
        finbert = get_finbert_model()
        model_result = finbert(text)[0]
        
        result = {
            "label": model_result["label"],
            "score": float(model_result["score"])
        }
        
        # Store in cache in the background
        if data.cache:
            background_tasks.add_task(
                cache_result,
                text=text,
                result=result
            )
        
        logger.info(f"Model inference for text: {text[:50]}...")
        return SentimentResponse(
            label=result["label"],
            score=result["score"],
            source="model",
            processing_time=time.time() - start_time
        )
    except Exception as e:
        logger.error(f"Model inference error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis failed: {str(e)}"
        )

# Function to cache results in the background
def cache_result(text: str, result: Dict[str, Any]):
    try:
        redis_conn = get_redis_connection()
        cache_key = f"sentiment:{text.lower()}"
        redis_conn.setex(
            cache_key,
            REDIS_CACHE_TTL,
            json.dumps(result)
        )
        logger.debug(f"Cached result for text: {text[:50]}...")
    except Exception as e:
        logger.error(f"Failed to cache result: {e}")

# Batch processing endpoint
@app.post("/sentiment/batch")
async def batch_analyze_sentiment(
    data: list[TextInput],
    background_tasks: BackgroundTasks
):
    if len(data) > 50:
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds maximum of 50 items"
        )
    
    results = []
    for item in data:
        result = await analyze_sentiment(item, background_tasks)
        results.append({"text": item.text, "sentiment": result})
    
    return {"results": results}

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting sentiment analysis service")
    # Pre-load model in memory
    app.state.finbert_model = get_finbert_model()
    
    # Test Redis connection
    try:
        redis_conn = get_redis_connection()
        redis_conn.ping()
    except Exception as e:
        logger.warning(f"Redis unavailable at startup: {e}. Service will run in degraded mode.")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down sentiment analysis service")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
