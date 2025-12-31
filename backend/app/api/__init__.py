"""API routes initialization."""

from .contributions import router as contributions_router
from .users import router as users_router
from .verifications import router as verifications_router

__all__ = [
    'contributions_router',
    'users_router',
    'verifications_router'
]
