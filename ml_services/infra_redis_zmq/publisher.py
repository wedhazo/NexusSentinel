import zmq
import time
import json
import random
import logging
import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zmq-publisher")

# Sample stock symbols
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "INTC", "NFLX"]

# Sample tweets with different sentiments
SAMPLE_TWEETS = [
    # Positive tweets
    "{symbol} just announced record earnings! Stock is going to soar.",
    "Analysts have upgraded {symbol} to a strong buy rating. Bullish!",
    "{symbol} product launch exceeded all expectations. This is huge for shareholders.",
    "Just heard {symbol} is planning a stock buyback program. Great news!",
    "{symbol} crushed earnings estimates by 15%. Market is reacting positively.",
    
    # Neutral tweets
    "{symbol} announced new leadership today. Impact remains to be seen.",
    "Interesting developments at {symbol} - monitoring the situation closely.",
    "{symbol} revenue was in line with expectations. No surprises.",
    "Attended {symbol} investor day. Company sticking to existing strategy.",
    "{symbol} trading sideways on low volume today. Waiting for catalyst.",
    
    # Negative tweets
    "{symbol} missed earnings estimates. Stock taking a hit in after-hours.",
    "Regulatory investigation announced for {symbol}. This could be bad.",
    "Disappointing product launch from {symbol}. Sales projections lowered.",
    "{symbol} cutting 5% of workforce amid restructuring. Concerning trend.",
    "Insider selling at {symbol} has me worried about future prospects."
]

# Market news headlines
MARKET_NEWS = [
    "Fed raises interest rates by 25 basis points",
    "Inflation data comes in higher than expected",
    "Tech sector leading market rally today",
    "Oil prices surge amid Middle East tensions",
    "Market volatility increases as earnings season begins",
    "Economic indicators point to potential slowdown",
    "Treasury yields hit new highs amid inflation concerns",
    "Market breadth improving as small caps outperform",
    "Sector rotation continues as investors seek value",
    "Global markets mixed as Asian stocks decline overnight"
]

class StockMessagePublisher:
    """ZeroMQ publisher for stock-related messages"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5556):
        """Initialize the ZeroMQ publisher"""
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.bind_address = f"tcp://{host}:{port}"
        self.message_count = 0
        
        # Connect and bind
        try:
            self.socket.bind(self.bind_address)
            logger.info(f"Publisher bound to {self.bind_address}")
        except zmq.ZMQError as e:
            logger.error(f"Failed to bind publisher: {e}")
            raise
    
    def generate_stock_tweet(self) -> Dict[str, Any]:
        """Generate a random stock tweet"""
        symbol = random.choice(SYMBOLS)
        tweet_template = random.choice(SAMPLE_TWEETS)
        tweet = tweet_template.format(symbol=symbol)
        
        return {
            "type": "tweet",
            "symbol": symbol,
            "tweet": tweet,
            "timestamp": datetime.datetime.now().isoformat(),
            "user": f"trader_{random.randint(1000, 9999)}",
            "likes": random.randint(0, 100),
            "retweets": random.randint(0, 50)
        }
    
    def generate_market_news(self) -> Dict[str, Any]:
        """Generate a random market news item"""
        headline = random.choice(MARKET_NEWS)
        affected_symbols = random.sample(SYMBOLS, k=random.randint(1, 3))
        
        return {
            "type": "market_news",
            "headline": headline,
            "timestamp": datetime.datetime.now().isoformat(),
            "source": random.choice(["Bloomberg", "Reuters", "CNBC", "WSJ", "Financial Times"]),
            "affected_symbols": affected_symbols,
            "importance": random.randint(1, 5)  # 1-5 scale of importance
        }
    
    def generate_price_update(self) -> Dict[str, Any]:
        """Generate a random price update"""
        symbol = random.choice(SYMBOLS)
        price = round(random.uniform(50, 500), 2)
        prev_close = price * random.uniform(0.95, 1.05)
        prev_close = round(prev_close, 2)
        percent_change = round((price - prev_close) / prev_close * 100, 2)
        
        return {
            "type": "price_update",
            "symbol": symbol,
            "price": price,
            "change": round(price - prev_close, 2),
            "percent_change": percent_change,
            "timestamp": datetime.datetime.now().isoformat(),
            "volume": random.randint(10000, 1000000)
        }
    
    def generate_message(self) -> Dict[str, Any]:
        """Generate a random message of any type"""
        message_type = random.choices(
            ["tweet", "market_news", "price_update"], 
            weights=[0.5, 0.2, 0.3],  # Higher weight for tweets
            k=1
        )[0]
        
        if message_type == "tweet":
            return self.generate_stock_tweet()
        elif message_type == "market_news":
            return self.generate_market_news()
        else:
            return self.generate_price_update()
    
    def publish_message(self, message: Dict[str, Any]) -> None:
        """Publish a message to the ZeroMQ socket"""
        try:
            self.socket.send_json(message)
            self.message_count += 1
            logger.info(f"Published message #{self.message_count}: {message['type']} - {message.get('symbol', 'N/A')}")
        except zmq.ZMQError as e:
            logger.error(f"Failed to publish message: {e}")
    
    def run(self, interval: float = 2.0, max_messages: int = None) -> None:
        """Run the publisher, sending messages at the specified interval"""
        logger.info(f"Starting publisher with {interval}s interval")
        
        try:
            while max_messages is None or self.message_count < max_messages:
                message = self.generate_message()
                self.publish_message(message)
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Publisher stopped by user")
        except Exception as e:
            logger.error(f"Publisher error: {e}")
        finally:
            self.socket.close()
            self.context.term()
            logger.info(f"Publisher shut down after sending {self.message_count} messages")

if __name__ == "__main__":
    publisher = StockMessagePublisher()
    # Run with 2-second interval between messages
    publisher.run(interval=2.0)
