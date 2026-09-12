"""NWU Protocol - Decentralized Intelligence & Verified Truth Protocol API"""
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nwu_protocol.api.contributions import router as contributions_router
from nwu_protocol.api.verifications import router as verifications_router
from nwu_protocol.api.users import router as users_router
from nwu_protocol.api.payments import router as payments_router

SYSTEM = "nwu-protocol"
ROLE = "blockchain_protocol"
VERSION = "1.0.0"
CONTRACT_VERSION = "1.0.0"

app = FastAPI(
    title="NWU Protocol API",
    description="Decentralized Intelligence & Verified Truth Protocol - Enterprise-grade API",
    version=VERSION,
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

_events: deque[dict[str, Any]] = deque(maxlen=1000)
_counters: dict[str, int] = {
    "requests_total": 0,
    "health_checks": 0,
    "meta_checks": 0,
    "metrics_checks": 0,
    "events_checks": 0,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
def root():
    return {
        "service": "NWU Protocol API",
        "version": VERSION,
        "status": "healthy",
        "description": "Decentralized Intelligence & Verified Truth Protocol",
        "docs": "/docs",
        "timestamp": _now(),
    }


@app.get("/health")
def health():
    _counters["health_checks"] += 1
    _counters["requests_total"] += 1
    return {
        "status": "healthy",
        "system": SYSTEM,
        "version": VERSION,
        "timestamp": _now(),
    }


@app.get("/meta")
def meta():
    _counters["meta_checks"] += 1
    _counters["requests_total"] += 1
    return {
        "system": SYSTEM,
        "role": ROLE,
        "contract_version": CONTRACT_VERSION,
        "endpoints": ["/health", "/meta", "/metrics", "/events"],
        "event_bus_topic_schema": "garcar.{system}.{event_type}",
    }


@app.get("/metrics")
def metrics():
    _counters["metrics_checks"] += 1
    _counters["requests_total"] += 1
    return dict(_counters)


@app.get("/events")
def events():
    _counters["events_checks"] += 1
    _counters["requests_total"] += 1
    ev = list(_events)
    return {"events": ev, "total": len(ev)}


@app.get("/api/v1/status")
def api_status():
    return {
        "api": "NWU Protocol",
        "version": VERSION,
        "modules": ["contributions", "verifications", "payments", "users"],
        "status": "operational",
        "timestamp": _now(),
    }


@app.get("/api/v1/info")
def api_info():
    return {
        "name": "NWU Protocol",
        "version": VERSION,
        "description": "Decentralized Intelligence & Verified Truth Protocol",
        "endpoints": [
            "/api/v1/contributions",
            "/api/v1/verifications",
            "/api/v1/users",
            "/api/v1/payments",
        ],
    }
