from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import torch
import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("price-forecast-service")

# Initialize FastAPI app
app = FastAPI(title="NexusSentinel Price Forecast Service")

# Model path
MODEL_PATH = os.environ.get("MODEL_PATH", "model/tft_best.ckpt")

# Define input/output models
class TimeSeriesPoint(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    sentiment_score: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-06-15T09:30:00",
                "open": 150.25,
                "high": 152.75,
                "low": 149.80,
                "close": 151.50,
                "volume": 1250000,
                "sentiment_score": 0.65,
                "rsi_14": 58.5,
                "macd": 0.75
            }
        }

class ForecastInput(BaseModel):
    stock_id: str = Field(..., description="Stock ticker symbol")
    historic_features: List[TimeSeriesPoint] = Field(..., description="Historical time series data")
    forecast_horizon: int = Field(5, description="Number of periods to forecast")
    
    class Config:
        schema_extra = {
            "example": {
                "stock_id": "AAPL",
                "historic_features": [
                    {
                        "timestamp": "2025-06-14T09:30:00",
                        "open": 150.25,
                        "high": 152.75,
                        "low": 149.80,
                        "close": 151.50,
                        "volume": 1250000,
                        "sentiment_score": 0.65,
                        "rsi_14": 58.5,
                        "macd": 0.75
                    }
                ],
                "forecast_horizon": 5
            }
        }

class ForecastOutput(BaseModel):
    stock_id: str
    forecast_generated_at: str
    forecast_values: List[Dict[str, Any]]
    model_version: str
    confidence_intervals: Optional[Dict[str, List[float]]] = None

# Dummy model for initial implementation or when real model is not available
class DummyTFTModel:
    """Placeholder model when TFT model file is not available"""
    
    def __init__(self):
        logger.info("Initializing dummy TFT forecasting model")
    
    def predict(self, data, mode="prediction", return_x=False, return_index=False):
        """
        Generate dummy forecasts based on simple rules
        
        This is a placeholder that mimics the TFT model's predict method
        but uses simple trend continuation + noise
        """
        # Extract the last few values to establish a trend
        if isinstance(data, pd.DataFrame):
            # Get the last 5 close prices if available
            if 'close' in data.columns:
                recent_prices = data['close'].values[-5:]
                last_price = recent_prices[-1]
                
                # Calculate a simple trend
                if len(recent_prices) > 1:
                    trend = np.mean(np.diff(recent_prices))
                else:
                    trend = 0
                
                # Generate forecast with trend + noise
                forecast_length = 5  # Default forecast length
                forecast = np.array([last_price + trend * i + np.random.normal(0, last_price * 0.01) 
                                    for i in range(1, forecast_length + 1)])
                
                return forecast
        
        # Fallback: just return random values around the last known value
        return np.random.normal(100, 5, 5)  # 5 predictions around $100

# Try to load the TFT model
try:
    if os.path.exists(MODEL_PATH):
        logger.info(f"Loading TFT model from {MODEL_PATH}")
        # Import here to avoid dependency issues if not needed
        from pytorch_forecasting import TemporalFusionTransformer
        model = TemporalFusionTransformer.load_from_checkpoint(MODEL_PATH)
        model_version = "TFT-" + os.path.basename(MODEL_PATH)
    else:
        logger.warning(f"TFT model not found at {MODEL_PATH}, using dummy model")
        model = DummyTFTModel()
        model_version = "dummy-v1.0"
except Exception as e:
    logger.error(f"Error loading TFT model: {str(e)}")
    logger.info("Falling back to dummy model")
    model = DummyTFTModel()
    model_version = "dummy-v1.0"

@app.post("/forecast", response_model=ForecastOutput)
async def forecast_price(data: ForecastInput):
    """
    Generate price forecasts using Temporal Fusion Transformer
    
    Takes historical time series data and generates future price predictions
    """
    try:
        # Convert input data to dataframe
        df = pd.DataFrame([item.dict() for item in data.historic_features])
        
        # Convert timestamp strings to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp to ensure chronological order
        df = df.sort_values('timestamp')
        
        # Generate prediction
        prediction = model.predict(df)
        
        # Convert prediction to list format
        if isinstance(prediction, np.ndarray):
            predicted_values = prediction.tolist()
        else:
            # Handle TFT-specific output format
            predicted_values = prediction.tolist() if hasattr(prediction, 'tolist') else prediction
        
        # Generate forecast timestamps (daily forecast)
        last_timestamp = pd.to_datetime(data.historic_features[-1].timestamp)
        forecast_timestamps = [
            (last_timestamp + timedelta(days=i+1)).strftime("%Y-%m-%dT%H:%M:%S")
            for i in range(len(predicted_values) if isinstance(predicted_values, list) else data.forecast_horizon)
        ]
        
        # Format the response
        forecast_values = []
        for i, val in enumerate(predicted_values if isinstance(predicted_values, list) else range(data.forecast_horizon)):
            if isinstance(predicted_values, list):
                price = val
            else:
                # Dummy model might return a single value
                price = predicted_values[i] if i < len(predicted_values) else predicted_values
                
            forecast_values.append({
                "timestamp": forecast_timestamps[i],
                "predicted_close": float(price),
                "confidence": 0.8  # Placeholder confidence value
            })
        
        return {
            "stock_id": data.stock_id,
            "forecast_generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "forecast_values": forecast_values,
            "model_version": model_version,
            "confidence_intervals": {
                "lower_95": [float(val * 0.95) for val in predicted_values] if isinstance(predicted_values, list) else None,
                "upper_95": [float(val * 1.05) for val in predicted_values] if isinstance(predicted_values, list) else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating price forecast: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint to verify if the model is loaded and ready"""
    model_type = "TFT" if not isinstance(model, DummyTFTModel) else "Dummy (rule-based)"
    
    return {
        "status": "healthy",
        "model_type": model_type,
        "model_version": model_version,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

@app.get("/model-info")
async def model_info():
    """Get information about the current forecasting model"""
    is_dummy = isinstance(model, DummyTFTModel)
    
    info = {
        "model_type": "Dummy (rule-based)" if is_dummy else "Temporal Fusion Transformer",
        "is_production_model": not is_dummy,
        "model_path": MODEL_PATH if not is_dummy else None,
        "model_version": model_version,
        "input_features": [
            "timestamp",
            "open",
            "high",
            "low", 
            "close",
            "volume"
        ],
        "optional_features": [
            "sentiment_score",
            "rsi_14",
            "macd"
        ]
    }
    
    # Add model parameters if it's a real TFT model
    if not is_dummy and hasattr(model, 'hparams'):
        info["model_parameters"] = {
            "hidden_size": getattr(model.hparams, 'hidden_size', 'unknown'),
            "lstm_layers": getattr(model.hparams, 'lstm_layers', 'unknown'),
            "attention_head_size": getattr(model.hparams, 'attention_head_size', 'unknown')
        }
    
    return info
