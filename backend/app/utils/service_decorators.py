"""Decorators for common service patterns."""
import functools
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def auto_reconnect(connect_attr: str = 'connect', client_attr: str = 'client'):
    """
    Decorator to automatically reconnect if client is not connected.

    Args:
        connect_attr: Name of the connect method (default: 'connect')
        client_attr: Name of the client attribute (default: 'client')

    Usage:
        @auto_reconnect()
        async def get(self, key: str):
            return await self.client.get(key)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            client = getattr(self, client_attr, None)
            if not client:
                connect_method = getattr(self, connect_attr)
                await connect_method()
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def handle_service_errors(
    error_message: str,
    return_value: Any = None,
    log_level: str = 'error'
):
    """
    Decorator to handle service errors with logging.

    Args:
        error_message: Error message template (can use {e} for exception)
        return_value: Value to return on error (default: None)
        log_level: Log level for errors (default: 'error')

    Usage:
        @handle_service_errors("Failed to get from Redis: {e}")
        async def get(self, key: str):
            return await self.client.get(key)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log_func = getattr(logger, log_level)
                log_func(error_message.format(e=e))
                return return_value
        return wrapper
    return decorator


def ensure_connection_and_handle_errors(
    error_message: str,
    return_value: Any = None,
    connect_attr: str = 'connect',
    client_attr: str = 'client'
):
    """
    Combined decorator for auto-reconnect and error handling.

    Args:
        error_message: Error message template
        return_value: Value to return on error
        connect_attr: Name of the connect method
        client_attr: Name of the client attribute

    Usage:
        @ensure_connection_and_handle_errors("Failed to get from Redis: {e}")
        async def get(self, key: str):
            return await self.client.get(key)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                # Auto-reconnect
                client = getattr(self, client_attr, None)
                if not client:
                    connect_method = getattr(self, connect_attr)
                    await connect_method()

                # Execute function
                return await func(self, *args, **kwargs)
            except Exception as e:
                logger.error(error_message.format(e=e))
                return return_value
        return wrapper
    return decorator
