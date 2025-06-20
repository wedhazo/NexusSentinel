import zmq
import json
import logging
import time
import datetime
from typing import Dict, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zmq-subscriber")

class StockMessageSubscriber:
    """ZeroMQ subscriber for stock-related messages"""
    
    def __init__(self, host: str = "publisher", port: int = 5556):
        """Initialize the ZeroMQ subscriber"""
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.connect_address = f"tcp://{host}:{port}"
        self.message_count = 0
        self.handlers = {
            "tweet": self.handle_tweet,
            "market_news": self.handle_market_news,
            "price_update": self.handle_price_update
        }
        
        # Connect to publisher
        try:
            self.socket.connect(self.connect_address)
            # Subscribe to all messages
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
            logger.info(f"Subscriber connected to {self.connect_address}")
        except zmq.ZMQError as e:
            logger.error(f"Failed to connect subscriber: {e}")
            raise
    
    def handle_tweet(self, message: Dict[str, Any]) -> None:
        """Handle tweet messages"""
        symbol = message.get("symbol", "UNKNOWN")
        tweet = message.get("tweet", "")
        user = message.get("user", "anonymous")
        likes = message.get("likes", 0)
        
        logger.info(f"TWEET [{symbol}] from {user} ({likes} likes): {tweet}")
        
        # In a real implementation, you might:
        # 1. Store the tweet in a database
        # 2. Analyze sentiment
        # 3. Generate trading signals
        # 4. Notify users
        
        # Example of additional processing
        if "bullish" in tweet.lower() or "soar" in tweet.lower():
            logger.info(f"Detected positive sentiment for {symbol}")
        elif "bearish" in tweet.lower() or "miss" in tweet.lower():
            logger.info(f"Detected negative sentiment for {symbol}")
    
    def handle_market_news(self, message: Dict[str, Any]) -> None:
        """Handle market news messages"""
        headline = message.get("headline", "")
        source = message.get("source", "unknown")
        importance = message.get("importance", 1)
        affected_symbols = message.get("affected_symbols", [])
        
        symbols_str = ", ".join(affected_symbols) if affected_symbols else "none specified"
        
        logger.info(f"NEWS [Importance: {importance}/5] from {source}: {headline}")
        logger.info(f"Affected symbols: {symbols_str}")
        
        # In a real implementation, you might:
        # 1. Store the news in a database
        # 2. Analyze impact on affected symbols
        # 3. Update market context for trading algorithms
        # 4. Send alerts for high-importance news
        
        if importance >= 4:
            logger.warning(f"HIGH IMPORTANCE NEWS: {headline}")
    
    def handle_price_update(self, message: Dict[str, Any]) -> None:
        """Handle price update messages"""
        symbol = message.get("symbol", "UNKNOWN")
        price = message.get("price", 0.0)
        change = message.get("change", 0.0)
        percent_change = message.get("percent_change", 0.0)
        volume = message.get("volume", 0)
        
        change_sign = "+" if change >= 0 else ""
        logger.info(f"PRICE [{symbol}]: ${price} ({change_sign}{change}, {change_sign}{percent_change}%) Vol: {volume}")
        
        # In a real implementation, you might:
        # 1. Update price database
        # 2. Check for price alerts
        # 3. Update technical indicators
        # 4. Trigger trading algorithms on significant moves
        
        # Example of additional processing
        if abs(percent_change) > 2.0:
            logger.warning(f"SIGNIFICANT MOVE: {symbol} moved {percent_change}%")
    
    def process_message(self, message: Dict[str, Any]) -> None:
        """Process a message based on its type"""
        message_type = message.get("type")
        
        if message_type in self.handlers:
            self.handlers[message_type](message)
        else:
            logger.warning(f"Unknown message type: {message_type}")
            logger.debug(f"Message content: {message}")
    
    def run(self, max_messages: Optional[int] = None, timeout_ms: int = 1000) -> None:
        """Run the subscriber, processing messages as they arrive"""
        logger.info("Starting subscriber...")
        
        try:
            while max_messages is None or self.message_count < max_messages:
                try:
                    # Use poll to avoid blocking indefinitely
                    if self.socket.poll(timeout_ms):
                        message = self.socket.recv_json()
                        self.message_count += 1
                        logger.debug(f"Received message #{self.message_count}")
                        
                        # Process the message
                        self.process_message(message)
                    else:
                        # No message received within timeout
                        logger.debug("No message received, still listening...")
                except zmq.ZMQError as e:
                    logger.error(f"ZMQ error: {e}")
                    # Attempt to reconnect
                    self._reconnect()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        except KeyboardInterrupt:
            logger.info("Subscriber stopped by user")
        finally:
            self.socket.close()
            self.context.term()
            logger.info(f"Subscriber shut down after processing {self.message_count} messages")
    
    def _reconnect(self) -> None:
        """Attempt to reconnect to the publisher"""
        logger.info(f"Attempting to reconnect to {self.connect_address}...")
        try:
            # Close existing socket
            self.socket.close()
            
            # Create new socket
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(self.connect_address)
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
            
            logger.info("Reconnection successful")
        except zmq.ZMQError as e:
            logger.error(f"Reconnection failed: {e}")
            # Wait before next attempt
            time.sleep(5)

if __name__ == "__main__":
    subscriber = StockMessageSubscriber()
    # Run indefinitely
    subscriber.run()
