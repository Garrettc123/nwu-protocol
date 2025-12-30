"""Main FastAPI application entrypoint for nwu-protocol."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
from datetime import datetime

# Import API routers
from nwu_protocol.api import contributions, verifications

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info("NWU Protocol API starting up...")
    logger.info("API available at http://0.0.0.0:8000")
    logger.info("Documentation at http://0.0.0.0:8000/docs")
    yield
    # Shutdown
    logger.info("NWU Protocol API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="NWU Protocol API",
    description="Decentralized Intelligence & Verified Truth Protocol - Enterprise-grade API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contributions.router)
app.include_router(verifications.router)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint - Health check and API info."""
    return {
        "status": "healthy",
        "service": "NWU Protocol API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "nwu-protocol"}


@app.get("/api/v1/status")
async def api_status() -> Dict[str, Any]:
    """API status endpoint."""
    return {
        "status": "operational",
        "api_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/v1/info")
async def api_info() -> Dict[str, Any]:
    """API information endpoint."""
    return {
        "name": "NWU Protocol",
        "description": "Enterprise unified network protocol",
        "version": "1.0.0",
        "endpoints": [
            "/",
            "/health",
            "/api/v1/status",
            "/api/v1/info",
            "/docs",
            "/redoc"
        ]
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
