#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Polygon.io Daily OHLCV Data Collector

This script fetches daily OHLCV (Open, High, Low, Close, Volume) data
from the Polygon.io API for all tickers tracked in the database and
stores it in the PostgreSQL database.

Usage:
    python -m data_collectors.polygon.fetch_daily_data

Environment Variables:
    POLYGON_API_KEY: API key for Polygon.io
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx
from sqlalchemy import Column, Date, Float, BigInteger, Integer, String, UniqueConstraint, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Assuming app.config and app.database are accessible
# In a real project, these would be imported from the main app structure
# For this standalone script, we'll define minimal necessary config and db setup
# or assume they are available in the environment.

# --- Minimal Config and DB Setup (for standalone execution/testing) ---
# In a full NexusSentinel integration, these would come from app.config and app.database
# For the purpose of this single file generation, we'll define them here.

import os

class Settings:
    POLYGON_API_KEY: Optional[str] = os.environ.get("POLYGON_API_KEY")
    DB_HOST: str = os.environ.get("DB_HOST", "localhost")
    DB_PORT: int = int(os.environ.get("DB_PORT", 5432))
    DB_USER: str = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "password")
    DB_NAME: str = os.environ.get("DB_NAME", "nexussentinel")

settings = Settings()

DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """Provides an async database session."""
    async with AsyncSessionLocal() as session:
        yield session

# --- End Minimal Config and DB Setup ---


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("polygon_data_collector.log")
    ]
)
logger = logging.getLogger(__name__)

# --- PostgreSQL Table Definition ---
# This model corresponds to the user-provided CREATE TABLE statement.
# In a larger project, this would typically reside in app/models/
class OHLCVData(Base):
    __tablename__ = "ohlcv_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)

    __table_args__ = (UniqueConstraint('symbol', 'date', name='uq_symbol_date'),)

    def __repr__(self):
        return f"<OHLCVData(symbol='{self.symbol}', date='{self.date}', close={self.close})>"

async def create_ohlcv_table_if_not_exists():
    """Ensures the ohlcv_data table exists in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Ensured 'ohlcv_data' table exists.")

# --- Polygon.io API Client ---
class PolygonClient:
    """Client for fetching data from Polygon.io API."""
    BASE_URL = "https://api.polygon.io"
    MAX_RETRIES = 5
    RETRY_DELAY_SECONDS = 5
    RATE_LIMIT_DELAY_SECONDS = 12  # Polygon.io free tier is 5 requests per minute (12 seconds per request)

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Polygon.io API key is not provided.")
        self.api_key = api_key
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0)

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Helper to make requests to Polygon.io API with retry logic."""
        params["apiKey"] = self.api_key
        for attempt in range(self.MAX_RETRIES):
            try:
                await asyncio.sleep(self.RATE_LIMIT_DELAY_SECONDS) # Respect rate limits
                response = await self.client.get(endpoint, params=params)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                return response.json()
            except httpx.RequestError as exc:
                logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
            except httpx.HTTPStatusError as exc:
                logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
                if exc.response.status_code == 429: # Too Many Requests
                    logger.warning(f"Rate limit hit. Retrying in {self.RETRY_DELAY_SECONDS} seconds (attempt {attempt + 1}/{self.MAX_RETRIES})...")
                    await asyncio.sleep(self.RETRY_DELAY_SECONDS)
                    continue
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
            
            if attempt < self.MAX_RETRIES - 1:
                logger.info(f"Retrying {endpoint} (attempt {attempt + 1}/{self.MAX_RETRIES})...")
                await asyncio.sleep(self.RETRY_DELAY_SECONDS)
        logger.error(f"Failed to fetch data from {endpoint} after {self.MAX_RETRIES} attempts.")
        return None

    async def get_daily_ohlcv(self, symbol: str, from_date: date, to_date: date) -> List[Dict[str, Any]]:
        """
        Fetches daily OHLCV data for a given symbol and date range.
        Polygon.io aggregates endpoint: /v2/aggs/ticker/{stockTicker}/range/{multiplier}/{timespan}/{from}/{to}
        """
        endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{from_date.isoformat()}/{to_date.isoformat()}"
        logger.info(f"Fetching OHLCV for {symbol} from {from_date} to {to_date}")
        
        data = await self._make_request(endpoint, {})
        
        if data and data.get("results"):
            ohlcv_records = []
            for result in data["results"]:
                ohlcv_records.append({
                    "symbol": symbol,
                    "date": datetime.fromtimestamp(result["t"] / 1000).date(), # Convert milliseconds to date
                    "open": result["o"],
                    "high": result["h"],
                    "low": result["l"],
                    "close": result["c"],
                    "volume": result["v"],
                })
            logger.info(f"Fetched {len(ohlcv_records)} OHLCV records for {symbol}.")
            return ohlcv_records
        else:
            logger.info(f"No OHLCV data found for {symbol} from {from_date} to {to_date}.")
            return []

# --- Data Fetcher and Storage Logic ---
class PolygonDataFetcher:
    """Manages fetching and storing Polygon.io data."""
    def __init__(self, db_session_factory: sessionmaker, polygon_client: PolygonClient):
        self.db_session_factory = db_session_factory
        self.polygon_client = polygon_client

    async def get_all_tracked_tickers(self) -> List[str]:
        """
        Fetches all unique ticker symbols currently tracked in the StocksCore table.
        This assumes StocksCore model is available and has a 'symbol' column.
        """
        # This import needs to be here to avoid circular dependencies if StocksCore is in app.models
        try:
            from app.models.stocks_core import StocksCore
        except ImportError:
            logger.warning("StocksCore model not found. Using a dummy list of tickers. "
                           "Ensure app.models.stocks_core is available or provide tickers manually.")
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"] # Dummy tickers for testing

        async with self.db_session_factory() as session:
            result = await session.execute(text("SELECT DISTINCT symbol FROM stocks_core"))
            tickers = [row[0] for row in result.scalars().all()]
            logger.info(f"Found {len(tickers)} tracked tickers in the database.")
            return tickers

    async def get_last_fetched_date(self, session: AsyncSession, symbol: str) -> Optional[date]:
        """Gets the last date for which OHLCV data was fetched for a given symbol."""
        result = await session.execute(
            text(f"SELECT MAX(date) FROM ohlcv_data WHERE symbol = '{symbol}'")
        )
        last_date = result.scalar_one_or_none()
        return last_date if last_date else None

    async def insert_ohlcv_data(self, session: AsyncSession, data: List[Dict[str, Any]]) -> int:
        """
        Inserts OHLCV data into the database.
        Uses ON CONFLICT DO NOTHING to handle unique constraint violations.
        """
        if not data:
            return 0

        inserted_count = 0
        for record in data:
            try:
                # Using PostgreSQL's ON CONFLICT DO NOTHING for efficient upsert-like behavior
                stmt = pg_insert(OHLCVData).values(record)
                on_conflict_stmt = stmt.on_conflict_do_nothing(
                    index_elements=['symbol', 'date']
                )
                await session.execute(on_conflict_stmt)
                inserted_count += 1
            except Exception as e:
                logger.error(f"Error inserting OHLCV data for {record.get('symbol')} on {record.get('date')}: {e}")
        
        await session.commit()
        logger.info(f"Inserted/attempted to insert {inserted_count} OHLCV records.")
        return inserted_count

    async def fetch_and_store_daily_data(self):
        """Main function to orchestrate fetching and storing daily OHLCV data."""
        logger.info("Starting daily OHLCV data ingestion from Polygon.io.")
        await create_ohlcv_table_if_not_exists()

        tickers = await self.get_all_tracked_tickers()
        if not tickers:
            logger.warning("No tickers found to track. Exiting.")
            return

        today = date.today()
        
        for ticker in tickers:
            async with self.db_session_factory() as session:
                last_fetched = await self.get_last_fetched_date(session, ticker)
                
                start_date = last_fetched + timedelta(days=1) if last_fetched else date(2020, 1, 1) # Start from 2020-01-01 if no data
                
                if start_date > today:
                    logger.info(f"Data for {ticker} is already up to date. Skipping.")
                    continue
                
                # Fetch data up to yesterday to ensure full day's data is available
                end_date = today - timedelta(days=1)
                if start_date > end_date:
                    logger.info(f"No new full day's data to fetch for {ticker}. Skipping.")
                    continue

                logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
                ohlcv_data = await self.polygon_client.get_daily_ohlcv(ticker, start_date, end_date)
                
                if ohlcv_data:
                    inserted_count = await self.insert_ohlcv_data(session, ohlcv_data)
                    logger.info(f"Inserted {inserted_count} new OHLCV records for {ticker}.")
                
                # Add a small delay between tickers to avoid rate limiting
                await asyncio.sleep(1)

        logger.info("Daily OHLCV data ingestion completed.")

async def main():
    """Main entry point for the script."""
    if not settings.POLYGON_API_KEY:
        logger.error("POLYGON_API_KEY environment variable is not set. Exiting.")
        return

    try:
        # Initialize Polygon client
        polygon_client = PolygonClient(settings.POLYGON_API_KEY)
        
        # Initialize data fetcher
        data_fetcher = PolygonDataFetcher(AsyncSessionLocal, polygon_client)
        
        # Fetch and store data
        await data_fetcher.fetch_and_store_daily_data()
        
    except Exception as e:
        logger.error(f"An error occurred during data collection: {e}")
        raise

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
