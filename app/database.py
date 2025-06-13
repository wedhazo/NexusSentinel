"""
Database connection module for NexusSentinel API.

This module sets up SQLAlchemy async database connection using asyncpg.
It provides database session management, connection pooling, and
proper async context managers.
"""

from typing import AsyncGenerator, Any, Dict
import logging
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import inspect, text  # `text` used for raw SQL execution

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=30,
    future=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Create declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Yields:
        AsyncSession: SQLAlchemy async session
        
    Example:
        ```python
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            items = await db.execute(select(Item))
            return items.scalars().all()
        ```
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """
    Initialize database - create tables, indexes, etc.
    Should be called during application startup.
    """
    try:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            # Uncomment the line below to create tables automatically
            # await conn.run_sync(Base.metadata.create_all)
            pass
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def close_db_connections() -> None:
    """
    Close database connections.
    Should be called during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")


async def check_db_connection() -> Dict[str, Any]:
    """
    Check database connection and return status.
    
    Returns:
        Dict[str, Any]: Connection status information
    """
    try:
        async with engine.connect() as conn:
            # Use `text()` to wrap raw SQL strings so SQLAlchemy can compile them
            await conn.execute(text("SELECT 1"))
            return {
                "status": "connected",
                "details": {
                    "database": settings.DB_NAME,
                    "host": settings.DB_HOST,
                    "port": settings.DB_PORT,
                    "user": settings.DB_USER,
                    "pool_size": settings.DB_POOL_SIZE,
                    "max_overflow": settings.DB_MAX_OVERFLOW,
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "details": {
                "database": settings.DB_NAME,
                "host": settings.DB_HOST,
                "port": settings.DB_PORT,
            }
        }
