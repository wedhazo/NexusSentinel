"""
NexusSentinel API - Main Application Module

This module initializes the FastAPI application, configures middleware,
sets up API routers, and handles startup/shutdown events.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any

# Import configuration and database modules
from app.config import settings
from app.database import init_db, close_db_connections, check_db_connection

# Import API routers (will be created in separate files)
from app.api.v1.router import api_router
from app.api.health import health_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("nexussentinel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info("Starting NexusSentinel API")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown: Close database connections
    logger.info("Shutting down NexusSentinel API")
    await close_db_connections()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=None,  # We'll customize the docs URL
    redoc_url=None,  # We'll customize the redoc URL
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# NOTE: SlowAPI-based rate limiting is disabled for now to keep
# the initial setup simple and avoid additional dependencies.
# -------------------------------------------------------------

# Include API routers
app.include_router(health_router, tags=["health"])
app.include_router(api_router, prefix=settings.API_PREFIX)

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with additional metadata."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
    )
    
    # Add custom metadata
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    # Add security schemes if authentication is implemented
    if hasattr(settings, "SECRET_KEY") and settings.SECRET_KEY:
        openapi_schema["components"] = {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI endpoint."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        title=f"{settings.API_TITLE} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc documentation endpoint."""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        title=f"{settings.API_TITLE} - API Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint that redirects to API documentation."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "documentation": "/docs",
        "health": "/health",
        "api_prefix": settings.API_PREFIX,
    }


@app.get("/health", tags=["health"], include_in_schema=False)
async def health_check():
    """Health check endpoint to verify API status and database connection."""
    db_status = await check_db_connection()
    
    status_code = status.HTTP_200_OK if db_status["status"] == "connected" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if db_status["status"] == "connected" else "unhealthy",
            "api_version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
        }
    )


if __name__ == "__main__":
    """Run the application using Uvicorn when executed directly."""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
