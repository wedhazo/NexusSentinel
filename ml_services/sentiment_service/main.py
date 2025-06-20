from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import redis
import json
from functools import lru_cache

app = FastAPI(title="NexusSentinel FinBERT Sentiment Service")

# Connect to Redis
try:
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    r.ping()  # Test connection
except redis.ConnectionError:
    print("Warning: Redis connection failed. Caching will be disabled.")
    r = None

# Load FinBERT model with caching
@lru_cache(maxsize=1)
def load_finbert_model():
    """Load the FinBERT model with caching to improve performance"""
    return pipeline(
        "text-classification",
        model="yiyanghkust/finbert-tone",
        tokenizer="yiyanghkust/finbert-tone"
    )

# Get the model
finbert = load_finbert_model()

class TextInput(BaseModel):
    text: str
    cache: bool = True

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model": "finbert-tone"}

@app.post("/sentiment")
def analyze_sentiment(data: TextInput):
    """
    Analyze the sentiment of financial text using FinBERT
    
    Returns sentiment label (positive, negative, neutral) and confidence score
    """
    # Normalize input text
    text = data.text.strip()
    
    # Check cache if enabled
    if data.cache and r is not None:
        cache_key = f"sentiment:{text.lower()}"
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    
    # Perform sentiment analysis
    try:
        result = finbert(text)[0]
        response = {
            "text": text,
            "sentiment": result["label"],
            "confidence": float(result["score"]),
            "model": "finbert-tone"
        }
        
        # Cache result if enabled
        if data.cache and r is not None:
            r.setex(cache_key, 3600, json.dumps(response))
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference error: {str(e)}")

@app.post("/batch-sentiment")
def analyze_batch_sentiment(data: list[TextInput]):
    """Analyze sentiment for multiple texts in a single request"""
    results = []
    for item in data:
        result = analyze_sentiment(item)
        results.append(result)
    return results
