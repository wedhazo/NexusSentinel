from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import numpy as np
import os
import pickle
import logging
import joblib
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("signal-generator")

# Initialize FastAPI app
app = FastAPI(title="NexusSentinel Trading Signal Generator")

# Define input model
class FeatureInput(BaseModel):
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

class BatchFeatureInput(BaseModel):
    features: List[FeatureInput]
    symbols: Optional[List[str]] = None

class SignalResponse(BaseModel):
    signal: str
    confidence: float
    timestamp: str
    features_used: Dict[str, float]

# Model path - will be used when a real model is trained
MODEL_PATH = os.environ.get("MODEL_PATH", "model/lgbm_model.pkl")

# Dummy model for initial implementation
class DummyModel:
    """Placeholder model until a real LightGBM model is trained"""
    
    def __init__(self):
        logger.info("Initializing dummy trading signal model")
    
    def predict(self, features):
        """
        Generate trading signals based on input features
        
        This is a simple rule-based implementation that will be replaced
        with a trained LightGBM model later.
        """
        # Extract features from numpy array
        if len(features.shape) == 2:
            # Handle batch prediction
            results = []
            for i in range(features.shape[0]):
                results.append(self._predict_single(features[i, :]))
            return np.array(results)
        else:
            # Handle single prediction
            return np.array([self._predict_single(features)])
    
    def _predict_single(self, feature_vector):
        """Generate a single prediction based on rules"""
        # Extract individual features
        sentiment_score = feature_vector[0]
        sentiment_momentum = feature_vector[1]
        rsi_14 = feature_vector[2]
        volume_change = feature_vector[3]
        
        # Simple rule-based logic
        # High sentiment + oversold RSI + increasing volume = buy signal
        if sentiment_score > 0.6 and rsi_14 < 40 and volume_change > 1.0:
            return 0.9  # Strong buy
        
        # Positive sentiment + neutral RSI + some volume increase
        elif sentiment_score > 0.3 and 40 <= rsi_14 <= 60 and volume_change > 0.5:
            return 0.7  # Buy
        
        # Negative sentiment + overbought RSI = sell signal
        elif sentiment_score < -0.3 and rsi_14 > 70:
            return 0.2  # Sell (represented as low buy probability)
        
        # Default to hold
        else:
            return 0.5  # Hold

# Initialize model
try:
    if os.path.exists(MODEL_PATH):
        logger.info(f"Loading LightGBM model from {MODEL_PATH}")
        model = joblib.load(MODEL_PATH)
    else:
        logger.info("Using dummy model (no trained model found)")
        model = DummyModel()
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    logger.info("Falling back to dummy model")
    model = DummyModel()

# Helper function to convert model output to trading signal
def get_signal_from_probability(probability: float) -> Dict[str, Any]:
    """Convert model probability to a trading signal with confidence"""
    if probability > 0.9:
        signal = "STRONG_BUY"
    elif probability > 0.7:
        signal = "BUY"
    elif probability < 0.3:
        signal = "SELL"
    elif probability < 0.1:
        signal = "STRONG_SELL"
    else:
        signal = "HOLD"
    
    return {
        "signal": signal,
        "confidence": float(probability) if signal in ["BUY", "STRONG_BUY"] else float(1.0 - probability),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/signal", response_model=SignalResponse)
async def generate_signal(features: FeatureInput):
    """
    Generate a trading signal based on sentiment and technical indicators
    
    Returns a signal (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL) and confidence score
    """
    try:
        # Convert input to numpy array
        x = np.array([
            [
                features.sentiment_score,
                features.sentiment_momentum,
                features.rsi_14,
                features.volume_change,
                features.price_sma_20 if features.price_sma_20 is not None else 1.0,
                features.macd if features.macd is not None else 0.0
            ]
        ])
        
        # Generate prediction
        prob = model.predict(x)[0]
        
        # Convert to signal
        result = get_signal_from_probability(prob)
        
        # Add features used for reference
        result["features_used"] = {
            "sentiment_score": features.sentiment_score,
            "sentiment_momentum": features.sentiment_momentum,
            "rsi_14": features.rsi_14,
            "volume_change": features.volume_change
        }
        
        if features.price_sma_20 is not None:
            result["features_used"]["price_sma_20"] = features.price_sma_20
            
        if features.macd is not None:
            result["features_used"]["macd"] = features.macd
            
        return result
    
    except Exception as e:
        logger.error(f"Error generating signal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating trading signal: {str(e)}"
        )

@app.post("/batch-signal", response_model=List[SignalResponse])
async def generate_batch_signals(batch_request: BatchFeatureInput):
    """
    Generate trading signals for multiple feature sets in a single request
    
    Useful for analyzing multiple stocks or scenarios at once
    """
    try:
        # Check if symbols are provided and match features length
        symbols = batch_request.symbols
        if symbols and len(symbols) != len(batch_request.features):
            raise HTTPException(
                status_code=400,
                detail="Number of symbols must match number of feature sets"
            )
        
        # Prepare feature matrix
        feature_matrix = []
        for feature_set in batch_request.features:
            feature_matrix.append([
                feature_set.sentiment_score,
                feature_set.sentiment_momentum,
                feature_set.rsi_14,
                feature_set.volume_change,
                feature_set.price_sma_20 if feature_set.price_sma_20 is not None else 1.0,
                feature_set.macd if feature_set.macd is not None else 0.0
            ])
        
        # Generate predictions
        x = np.array(feature_matrix)
        probs = model.predict(x)
        
        # Convert to signals
        results = []
        for i, prob in enumerate(probs):
            result = get_signal_from_probability(prob)
            
            # Add features used
            feature_set = batch_request.features[i]
            result["features_used"] = {
                "sentiment_score": feature_set.sentiment_score,
                "sentiment_momentum": feature_set.sentiment_momentum,
                "rsi_14": feature_set.rsi_14,
                "volume_change": feature_set.volume_change
            }
            
            if feature_set.price_sma_20 is not None:
                result["features_used"]["price_sma_20"] = feature_set.price_sma_20
                
            if feature_set.macd is not None:
                result["features_used"]["macd"] = feature_set.macd
            
            # Add symbol if provided
            if symbols:
                result["symbol"] = symbols[i]
                
            results.append(result)
            
        return results
    
    except Exception as e:
        logger.error(f"Error generating batch signals: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating batch trading signals: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint to verify if the model is loaded and ready"""
    model_type = "LightGBM" if os.path.exists(MODEL_PATH) else "Dummy (rule-based)"
    
    return {
        "status": "healthy",
        "model_type": model_type,
        "features_supported": [
            "sentiment_score",
            "sentiment_momentum",
            "rsi_14",
            "volume_change",
            "price_sma_20",
            "macd"
        ]
    }

@app.get("/model-info")
async def model_info():
    """Get information about the current model"""
    is_dummy = isinstance(model, DummyModel)
    
    info = {
        "model_type": "Dummy (rule-based)" if is_dummy else "LightGBM",
        "is_production_model": not is_dummy,
        "model_path": MODEL_PATH if not is_dummy else None,
        "features_required": [
            "sentiment_score",
            "sentiment_momentum",
            "rsi_14",
            "volume_change"
        ],
        "features_optional": [
            "price_sma_20",
            "macd"
        ]
    }
    
    # Add model parameters if it's a real LightGBM model
    if not is_dummy and hasattr(model, 'params'):
        info["model_parameters"] = model.params
    
    return info
