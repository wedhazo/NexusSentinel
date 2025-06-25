#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Polygon.io Data Collection Scheduler

This script sets up a scheduler to run the daily OHLCV data collection
from Polygon.io at 6 AM UTC every day.

Usage:
    python -m data_collectors.polygon.scheduler

Environment Variables:
    POLYGON_API_KEY: API key for Polygon.io
"""

import asyncio
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os

# Import the main function from fetch_daily_data.py
from data_collectors.polygon.fetch_daily_data import main as fetch_daily_data_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("polygon_scheduler.log")
    ]
)
logger = logging.getLogger(__name__)

def run_fetch_job():
    """Wrapper function to run the async fetch_daily_data_main in a new event loop."""
    logger.info(f"Starting scheduled data fetch job at {datetime.utcnow()} UTC...")
    try:
        # Create a new event loop for each job execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(fetch_daily_data_main())
        loop.close()
        logger.info("Scheduled data fetch job completed.")
    except Exception as e:
        logger.error(f"Error during scheduled data fetch job: {e}", exc_info=True)

def start_scheduler():
    """Starts the APScheduler to run the data fetching job."""
    scheduler = BlockingScheduler(timezone="UTC")

    # Schedule the job to run daily at 6 AM UTC
    scheduler.add_job(
        run_fetch_job,
        CronTrigger(hour=6, minute=0, second=0),
        id='polygon_daily_ohlcv_fetch',
        name='Daily Polygon.io OHLCV Fetch',
        replace_existing=True
    )
    logger.info("Scheduler initialized. Next run scheduled for 06:00 UTC daily.")
    logger.info("Press Ctrl+C to exit.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user.")
        scheduler.shutdown()
    except Exception as e:
        logger.critical(f"Scheduler encountered a critical error and stopped: {e}", exc_info=True)
        scheduler.shutdown()

if __name__ == "__main__":
    # Ensure environment variables are set for fetch_daily_data.py
    # In a real deployment, these would be managed by Docker/Kubernetes
    if not os.environ.get("POLYGON_API_KEY"):
        logger.warning("POLYGON_API_KEY environment variable not set. Data fetching will likely fail.")
    if not os.environ.get("DB_HOST"):
        logger.warning("DB_HOST environment variable not set. Database connection might fail.")

    start_scheduler()
