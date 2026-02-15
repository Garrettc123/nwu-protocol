"""Main FastAPI application for NWU Protocol Backend."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from .config import settings
from .database import init_db, engine
from .api import contributions_router, users_router, verifications_router, auth_router, websocket_router, payments_router
from .services import rabbitmq_service, redis_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting NWU Protocol Backend...")
    init_db()
    logger.info("Database initialized")
    
    try:
        await rabbitmq_service.connect()
        logger.info("RabbitMQ connected")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
    
    try:
        await redis_service.connect()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NWU Protocol Backend...")
    try:
        await rabbitmq_service.disconnect()
        logger.info("RabbitMQ disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting RabbitMQ: {e}")
    
    try:
        await redis_service.disconnect()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting Redis: {e}")


# Create FastAPI application
app = FastAPI(
    title="NWU Protocol API",
    description="Decentralized Intelligence & Verified Truth Protocol - Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contributions_router)
app.include_router(users_router)
app.include_router(verifications_router)
app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(payments_router)


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "NWU Protocol API",
        "description": "Decentralized Intelligence & Verified Truth Protocol",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check database
    db_healthy = False
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check IPFS
    from .services import ipfs_service
    ipfs_healthy = ipfs_service.is_connected()
    
    # Check RabbitMQ
    rabbitmq_healthy = await rabbitmq_service.is_connected()
    
    # Check Redis
    redis_healthy = await redis_service.is_connected()
    
    return {
        "status": "healthy" if all([db_healthy, ipfs_healthy, rabbitmq_healthy, redis_healthy]) else "degraded",
        "service": "nwu-protocol-backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_healthy,
            "ipfs": ipfs_healthy,
            "rabbitmq": rabbitmq_healthy,
            "redis": redis_healthy
        }
    }


@app.get("/api/v1/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "NWU Protocol API",
        "description": "Decentralized Intelligence & Verified Truth Protocol",
        "version": "1.0.0",
        "endpoints": {
            "contributions": "/api/v1/contributions",
            "users": "/api/v1/users",
            "verifications": "/api/v1/verifications",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
