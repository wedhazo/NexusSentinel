import json
import asyncio
import websockets
import httpx
import logging
import datetime
import random
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("websocket-signal-server")

# Config endpoints
SENTIMENT_API = "http://sentiment_service:8000/sentiment"
ENHANCED_SENTIMENT_API = "http://api:8000/api/v1/enhanced-sentiment/analyze-consensus"
SIGNAL_API = "http://signal_generator:8002/signal"
LLAMA_SENTIMENT_API = "http://llama3_sentiment_service:8001/llama-sentiment"

# Server configuration
HOST = "0.0.0.0"
PORT = 8004
HEARTBEAT_INTERVAL = 30  # seconds

# Global client tracking
connected_clients = set()

async def get_technical_indicators(symbol: str) -> Dict[str, float]:
    """
    Get technical indicators for a stock symbol.
    In a production environment, this would fetch real data from a market data provider.
    For now, we generate realistic mock data.
    """
    # Generate somewhat realistic mock data
    rsi = random.uniform(30, 70)
    volume_change = random.uniform(0.8, 1.5)
    
    # Make some symbols consistently bullish/bearish for demo purposes
    if symbol.lower() in ["aapl", "msft", "googl"]:
        sentiment_momentum = random.uniform(0.05, 0.2)  # Bullish
        rsi = random.uniform(45, 65)  # Neutral to bullish
    elif symbol.lower() in ["meta", "nflx"]:
        sentiment_momentum = random.uniform(-0.1, 0.1)  # Neutral
        rsi = random.uniform(40, 60)  # Neutral
    else:
        sentiment_momentum = random.uniform(-0.2, 0.05)  # Bearish
        rsi = random.uniform(35, 55)  # Neutral to bearish
    
    return {
        "rsi_14": rsi,
        "volume_change": volume_change,
        "sentiment_momentum": sentiment_momentum,
        "price_sma_20": random.uniform(0.9, 1.1),
        "macd": random.uniform(-0.1, 0.1)
    }

async def get_sentiment(tweet: str, use_enhanced: bool = True) -> Dict[str, Any]:
    """
    Get sentiment analysis for a tweet.
    If use_enhanced is True, uses the consensus endpoint that combines FinBERT and LLaMA.
    Otherwise, falls back to the basic FinBERT endpoint.
    """
    try:
        async with httpx.AsyncClient() as client:
            if use_enhanced:
                # Try enhanced sentiment first (consensus of FinBERT + LLaMA)
                response = await client.post(
                    ENHANCED_SENTIMENT_API,
                    json={"text": tweet},
                    timeout=60.0  # Longer timeout for LLaMA
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Convert sentiment label to score (-1 to 1)
                    sentiment_label = data.get("sentiment", "neutral")
                    confidence = data.get("confidence", 0.5)
                    
                    sentiment_score = 0.0  # Default neutral
                    if sentiment_label == "positive":
                        sentiment_score = confidence
                    elif sentiment_label == "negative":
                        sentiment_score = -confidence
                        
                    return {
                        "sentiment_score": sentiment_score,
                        "sentiment_label": sentiment_label,
                        "confidence": confidence,
                        "source": "consensus"
                    }
            
            # Fallback to basic FinBERT sentiment
            response = await client.post(
                SENTIMENT_API,
                json={"text": tweet},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                sentiment_label = data.get("sentiment", "neutral")
                confidence = data.get("confidence", 0.5)
                
                sentiment_score = 0.0  # Default neutral
                if sentiment_label == "positive":
                    sentiment_score = confidence
                elif sentiment_label == "negative":
                    sentiment_score = -confidence
                    
                return {
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "confidence": confidence,
                    "source": "finbert"
                }
            
            # If we get here, both attempts failed
            logger.error(f"Sentiment API error: {response.status_code} - {response.text}")
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.5,
                "source": "fallback",
                "error": f"API error: {response.status_code}"
            }
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to sentiment service: {str(e)}")
        return {
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
            "confidence": 0.5,
            "source": "fallback",
            "error": f"Connection error: {str(e)}"
        }

async def get_trading_signal(features: Dict[str, float]) -> Dict[str, Any]:
    """
    Get trading signal based on features.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SIGNAL_API,
                json=features,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            
            logger.error(f"Signal API error: {response.status_code} - {response.text}")
            return {
                "signal": "HOLD",
                "confidence": 0.5,
                "error": f"API error: {response.status_code}"
            }
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to signal service: {str(e)}")
        return {
            "signal": "HOLD",
            "confidence": 0.5,
            "error": f"Connection error: {str(e)}"
        }

async def send_heartbeat(websocket):
    """Send periodic heartbeats to keep connection alive"""
    while True:
        try:
            await websocket.send(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.datetime.now().isoformat()
            }))
            await asyncio.sleep(HEARTBEAT_INTERVAL)
        except websockets.exceptions.ConnectionClosed:
            break
        except Exception as e:
            logger.error(f"Heartbeat error: {str(e)}")
            break

async def handler(websocket):
    """Handle WebSocket connection and messages"""
    client_id = id(websocket)
    client_info = {"id": client_id, "connected_at": datetime.datetime.now().isoformat()}
    connected_clients.add(client_id)
    
    logger.info(f"Client connected: {client_id}")
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeat(websocket))
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "info",
            "message": "Connected to NexusSentinel WebSocket Signal Server",
            "client_id": client_id
        }))
        
        # Process incoming messages
        async for message in websocket:
            try:
                # Parse the message
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Check message type
                if "type" in data and data["type"] == "ping":
                    # Simple ping-pong for connection testing
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.datetime.now().isoformat()
                    }))
                    continue
                
                # Process trading signal request
                if "tweet" in data and "symbol" in data:
                    tweet = data["tweet"]
                    symbol = data["symbol"]
                    use_enhanced = data.get("use_enhanced", True)
                    
                    # Step 1: Get sentiment score
                    sentiment_data = await get_sentiment(tweet, use_enhanced)
                    sentiment_score = sentiment_data["sentiment_score"]
                    sentiment_label = sentiment_data["sentiment_label"]
                    
                    # Step 2: Get technical indicators
                    tech_indicators = await get_technical_indicators(symbol)
                    
                    # Step 3: Create features for signal generation
                    features = {
                        "sentiment_score": sentiment_score,
                        "sentiment_momentum": tech_indicators["sentiment_momentum"],
                        "rsi_14": tech_indicators["rsi_14"],
                        "volume_change": tech_indicators["volume_change"],
                        "price_sma_20": tech_indicators["price_sma_20"],
                        "macd": tech_indicators["macd"]
                    }
                    
                    # Step 4: Get trading signal
                    signal_data = await get_trading_signal(features)
                    
                    # Step 5: Send response to client
                    await websocket.send(json.dumps({
                        "type": "signal",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "symbol": symbol,
                        "tweet": tweet,
                        "sentiment": {
                            "label": sentiment_label,
                            "score": sentiment_score,
                            "confidence": sentiment_data["confidence"],
                            "source": sentiment_data["source"]
                        },
                        "technicals": tech_indicators,
                        "action": signal_data.get("signal", "HOLD"),
                        "confidence": signal_data.get("confidence", 0.5)
                    }))
                else:
                    # Invalid message format
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid message format. Expected {\"tweet\": \"...\", \"symbol\": \"...\"}"
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Error processing request: {str(e)}"
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Clean up
        heartbeat_task.cancel()
        connected_clients.discard(client_id)
        logger.info(f"Connection closed for client {client_id}")

async def health_handler(path, request_headers):
    """Handle health check requests on a separate port"""
    if path == "/health":
        return 200, {"Content-Type": "application/json"}, json.dumps({
            "status": "healthy",
            "connected_clients": len(connected_clients),
            "timestamp": datetime.datetime.now().isoformat()
        })
    return 404, {"Content-Type": "text/plain"}, "Not Found"

async def main():
    """Start the WebSocket server"""
    logger.info(f"Starting WebSocket Signal Server on {HOST}:{PORT}")
    
    # Start the main WebSocket server
    signal_server = await websockets.serve(handler, HOST, PORT)
    
    # Start a simple HTTP server for health checks on port 8005
    health_server = await websockets.serve(health_handler, HOST, 8005)
    
    logger.info("WebSocket Signal Server is running")
    logger.info("Health check endpoint available at http://localhost:8005/health")
    
    # Keep the server running
    await asyncio.gather(
        asyncio.Future(),  # Main WebSocket server
        asyncio.Future()   # Health check server
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
