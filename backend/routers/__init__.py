"""Subscription billing router package.

Imports are deferred to avoid pulling in the full ``app.api`` package
initialiser (which has external dependencies) when only plan constants
are needed.
"""


def __getattr__(name):
    if name == "subscriptions_router":
        from app.api.subscriptions import router
        return router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["subscriptions_router"]
