"""
Health check endpoints for NexusSentinel API.

This module provides endpoints for monitoring the health and status
of the API and its dependencies, including database connectivity,
external services, and system resources.
"""

import platform
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db, check_db_connection
from app.config import settings


# Create router
health_router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    """Schema for health status response."""
    status: str
    timestamp: datetime
    version: str
    environment: str


class DetailedHealthStatus(HealthStatus):
    """Schema for detailed health status response."""
    uptime: float
    components: Dict[str, Dict[str, Any]]
    system_info: Dict[str, Any]


class ComponentCheck(BaseModel):
    """Schema for component health check."""
    status: str
    details: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    last_checked: datetime


@health_router.get("/", summary="Health check")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Basic health check endpoint.
    
    Returns status of the API and its critical dependencies.
    Returns 200 if healthy, 503 if unhealthy.
    """
    # Check database connection
    db_status = await check_db_connection()
    
    # Determine overall health status
    is_healthy = db_status["status"] == "connected"
    
    # Set appropriate status code
    response.status_code = (
        status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    # Return a minimal JSON payload understood by Swagger UI
    return {"status": "ok" if is_healthy else "unhealthy"}


@health_router.get("/detailed", response_model=DetailedHealthStatus)
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check endpoint.
    
    Returns comprehensive status of the API and all its dependencies,
    including system information and resource usage.
    """
    start_time = time.time()
    
    # Check database connection
    db_status = await check_db_connection()
    db_latency = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Check system resources
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "cpu_usage_percent": psutil.cpu_percent(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "memory_used_percent": psutil.virtual_memory().percent,
        "disk_usage": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent
        }
    }
    
    # Check components
    components = {
        "database": {
            "status": "healthy" if db_status["status"] == "connected" else "unhealthy",
            "details": db_status,
            "latency_ms": db_latency,
            "last_checked": datetime.now()
        }
    }
    
    # Add external service checks if configured
    if settings.SENTIMENT_API_KEY:
        # Mock check for now, would be replaced with actual API call
        components["sentiment_api"] = {
            "status": "healthy",
            "details": {"endpoint": "sentiment-analysis"},
            "latency_ms": 0.0,
            "last_checked": datetime.now()
        }
    
    if settings.MARKET_DATA_API_URL:
        # Mock check for now, would be replaced with actual API call
        components["market_data_api"] = {
            "status": "healthy",
            "details": {"endpoint": str(settings.MARKET_DATA_API_URL)},
            "latency_ms": 0.0,
            "last_checked": datetime.now()
        }
    
    # Determine overall health status
    is_healthy = all(component["status"] == "healthy" for component in components.values())
    
    # Calculate uptime (mock value for now)
    uptime = 3600.0  # Would be replaced with actual uptime calculation
    
    # Set appropriate status code
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(
        content=DetailedHealthStatus(
            status="healthy" if is_healthy else "unhealthy",
            timestamp=datetime.now(),
            version=settings.API_VERSION,
            environment=settings.ENVIRONMENT,
            uptime=uptime,
            components=components,
            system_info=system_info
        ).model_dump_json(),
        media_type="application/json",
        status_code=status_code
    )


@health_router.get("/database", response_model=ComponentCheck)
async def database_health_check():
    """
    Database-specific health check endpoint.
    
    Returns detailed information about the database connection.
    """
    start_time = time.time()
    db_status = await check_db_connection()
    db_latency = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    status_code = status.HTTP_200_OK if db_status["status"] == "connected" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(
        content=ComponentCheck(
            status="healthy" if db_status["status"] == "connected" else "unhealthy",
            details=db_status,
            latency_ms=db_latency,
            last_checked=datetime.now()
        ).model_dump_json(),
        media_type="application/json",
        status_code=status_code
    )


@health_router.get("/system", response_model=Dict[str, Any])
async def system_info():
    """
    System information endpoint.
    
    Returns detailed information about the system resources and environment.
    """
    # Get system information
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    system_info = {
        "hardware": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_physical_count": psutil.cpu_count(logical=False),
            "cpu_percent": cpu_percent,
            "cpu_freq": {
                "current": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "min": psutil.cpu_freq().min if psutil.cpu_freq() else None,
                "max": psutil.cpu_freq().max if psutil.cpu_freq() else None
            }
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        },
        "software": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "os_name": platform.system(),
            "os_version": platform.version(),
            "api_version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT
        },
        "network": {
            "hostname": platform.node(),
            "ip_address": "127.0.0.1"  # Would be replaced with actual IP detection
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return system_info
