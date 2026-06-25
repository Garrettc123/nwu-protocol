"""NWU Protocol - Decentralized Intelligence & Verified Truth Protocol API"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from nwu_protocol.api.contributions import router as contributions_router
from nwu_protocol.api.verifications import router as verifications_router
from nwu_protocol.api.users import router as users_router
from nwu_protocol.api.payments import router as payments_router

app = FastAPI(
    title="NWU Protocol API",
    description="Decentralized Intelligence & Verified Truth Protocol - Enterprise-grade API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contributions_router)
app.include_router(verifications_router)
app.include_router(users_router)
app.include_router(payments_router)


@app.get("/")
def root():
    return {
        "service": "NWU Protocol API",
        "version": "1.0.0",
        "status": "healthy",
        "description": "Decentralized Intelligence & Verified Truth Protocol",
        "docs": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "system": "NWU Protocol",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/status")
def api_status():
    return {
        "api": "NWU Protocol",
        "version": "1.0.0",
        "modules": ["contributions", "verifications", "payments", "users"],
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/info")
def api_info():
    return {
        "name": "NWU Protocol",
        "version": "1.0.0",
        "description": "Decentralized Intelligence & Verified Truth Protocol",
        "endpoints": [
            "/api/v1/contributions",
            "/api/v1/verifications",
            "/api/v1/users",
            "/api/v1/payments",
        ],
    }
