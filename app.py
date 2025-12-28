"""Main FastAPI application entrypoint for nwu-protocol."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="NWU Protocol API",
    description="Enterprise-grade API for NWU Protocol system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "timestamp": "2025-12-28T11:56:00Z"
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


@app.on_event("startup")
async def startup_event():
    """Handle startup events."""
    logger.info("NWU Protocol API starting up...")
    logger.info("API available at http://0.0.0.0:8000")
    logger.info("Documentation at http://0.0.0.0:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Handle shutdown events."""
    logger.info("NWU Protocol API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
