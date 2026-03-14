"""
Middleware for API key authentication and usage metering.

Validates the ``X-API-Key`` header on every request that carries it,
increments the per-day usage counter for the key, and blocks the request
with HTTP 429 when the daily quota is exceeded.

Requests that do **not** carry an ``X-API-Key`` header pass through
unchanged so that JWT-authenticated endpoints continue to work normally.
"""

import logging
from datetime import date, datetime

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..database import SessionLocal
from ..models import APIKey, APIKeyUsage, SubscriptionTier, TIER_DAILY_LIMITS
from ..services.payment_service import payment_service

logger = logging.getLogger(__name__)

# Header name used to pass the raw API key
API_KEY_HEADER = "X-API-Key"


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that:

    1. Checks for an ``X-API-Key`` request header.
    2. Validates the key against the database (hashed comparison).
    3. Enforces the tier's daily request quota.
    4. Increments the per-day usage counter.
    5. Attaches the resolved :class:`APIKey` instance to ``request.state``
       as ``request.state.api_key`` for downstream use.

    Requests without the header are forwarded untouched.
    """

    async def dispatch(self, request: Request, call_next):
        raw_key = request.headers.get(API_KEY_HEADER)

        if not raw_key:
            # No API key – let normal JWT auth (or unauthenticated) routes handle it
            return await call_next(request)

        db = SessionLocal()
        try:
            # ---------- 1. Validate the key ----------
            api_key_record = await payment_service.verify_api_key(db, raw_key)

            if api_key_record is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "Invalid or expired API key", "status_code": 401},
                )

            # ---------- 2. Quota enforcement ----------
            daily_limit = TIER_DAILY_LIMITS.get(api_key_record.tier.value, 0)

            if daily_limit != -1:  # -1 means unlimited (enterprise)
                today = date.today()
                usage_record = (
                    db.query(APIKeyUsage)
                    .filter(
                        APIKeyUsage.api_key_id == api_key_record.id,
                        APIKeyUsage.usage_date == today,
                    )
                    .first()
                )

                current_count = usage_record.request_count if usage_record else 0

                if current_count >= daily_limit:
                    logger.warning(
                        "API key %d quota exceeded (%d/%d)",
                        api_key_record.id,
                        current_count,
                        daily_limit,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Daily quota exceeded",
                            "status_code": 429,
                            "quota": daily_limit,
                            "used": current_count,
                        },
                    )

            # ---------- 3. Increment usage counter ----------
            _increment_usage(db, api_key_record.id)

            # ---------- 4. Expose key on request state ----------
            request.state.api_key = api_key_record

        except Exception as e:
            logger.error("Error in APIKeyAuthMiddleware: %s", e, exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error", "status_code": 500},
            )
        finally:
            db.close()

        return await call_next(request)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _increment_usage(db, api_key_id: int) -> None:
    """Upsert today's usage record and increment the request counter."""
    today = date.today()
    usage_record = (
        db.query(APIKeyUsage)
        .filter(
            APIKeyUsage.api_key_id == api_key_id,
            APIKeyUsage.usage_date == today,
        )
        .first()
    )

    if usage_record:
        usage_record.request_count += 1
        usage_record.updated_at = datetime.utcnow()
    else:
        usage_record = APIKeyUsage(
            api_key_id=api_key_id,
            usage_date=today,
            request_count=1,
        )
        db.add(usage_record)

    db.commit()
