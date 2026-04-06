"""Services module initialization."""

import logging as _logging

_logger = _logging.getLogger(__name__)

__all__: list[str] = []


def _try_import(names: list[str], from_mod: str) -> None:
    """Import *names* from *from_mod*, skipping silently on ImportError."""
    try:
        mod = __import__(from_mod, globals(), locals(), names, level=1)
        for name in names:
            globals()[name] = getattr(mod, name)
            __all__.append(name)
    except (ImportError, Exception) as exc:  # noqa: BLE001
        _logger.debug("Optional service %s unavailable: %s", from_mod, exc)


_try_import(['ipfs_service', 'IPFSService'], '.ipfs_service')
_try_import(['rabbitmq_service', 'RabbitMQService'], '.rabbitmq_service')
_try_import(['redis_service', 'RedisService'], '.redis_service')
_try_import(['auth_service', 'AuthService'], '.auth_service')
_try_import(['payment_service', 'PaymentService'], '.payment_service')
_try_import(['EngagementIterationService'], '.engagement_service')
_try_import(['ProgressiveAutomationEngine', 'WorkflowStage'], '.workflow_engine')
_try_import(['HaltProcessService'], '.halt_process_service')
