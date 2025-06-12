#!/usr/bin/env python
"""
NexusSentinel API - Development Server Runner

This script provides a convenient way to run the NexusSentinel API
in development mode with hot-reloading enabled.

Usage:
    python run_server.py [options]

Options:
    --host HOST         Host to bind the server to (default: from .env or 0.0.0.0)
    --port PORT         Port to bind the server to (default: from .env or 8000)
    --reload            Enable auto-reload on code changes (default: True)
    --workers WORKERS   Number of worker processes (default: from .env or 1)
    --log-level LEVEL   Logging level (default: from .env or info)
"""

import argparse
import logging
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add the current directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("nexussentinel")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the NexusSentinel API development server")
    
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind the server to (default: from .env or 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", 8000)),
        help="Port to bind the server to (default: from .env or 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("API_RELOAD", "True").lower() in ("true", "1", "t"),
        help="Enable auto-reload on code changes (default: from .env or True)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("API_WORKERS", 1)),
        help="Number of worker processes (default: from .env or 1)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "info").lower(),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: from .env or info)"
    )
    
    return parser.parse_args()


def main():
    """Run the development server."""
    args = parse_args()
    
    # Configure uvicorn logger
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Log startup information
    logger.info(f"Starting NexusSentinel API development server")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Reload: {args.reload}")
    logger.info(f"Log level: {args.log_level}")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level,
        log_config=log_config
    )


if __name__ == "__main__":
    main()
