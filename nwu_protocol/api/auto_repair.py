"""Auto-Repair Control API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from nwu_protocol.models.auto_repair import (
    RepairConfig,
    RepairConfigUpdate,
    RepairEvent,
    RepairEventStatus,
    RepairEventType,
    RepairStatus,
)
from nwu_protocol.services.auto_repair_service import AutoRepairService
from nwu_protocol.core.dependencies import get_auto_repair_service

router = APIRouter(prefix="/api/v1/auto-repair", tags=["auto-repair"])


@router.get("/config", response_model=RepairConfig)
async def get_config(
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairConfig:
    """
    Get the current auto-repair configuration.

    Returns:
        Current repair configuration
    """
    return service.get_config()


@router.put("/config", response_model=RepairConfig)
async def update_config(
    config_update: RepairConfigUpdate,
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairConfig:
    """
    Update the auto-repair configuration.

    Only provided fields are updated; others remain unchanged.

    Args:
        config_update: Partial configuration update

    Returns:
        Updated configuration
    """
    return service.update_config(config_update)


@router.get("/status", response_model=RepairStatus)
async def get_status(
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairStatus:
    """
    Get the current status of the auto-repair system.

    Returns:
        System status with statistics
    """
    return service.get_status()


@router.post("/pause", response_model=RepairStatus)
async def pause_repairs(
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairStatus:
    """
    Pause the auto-repair system.

    Returns:
        Updated system status
    """
    return service.pause()


@router.post("/resume", response_model=RepairStatus)
async def resume_repairs(
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairStatus:
    """
    Resume the auto-repair system.

    Returns:
        Updated system status
    """
    return service.resume()


@router.get("/history", response_model=List[RepairEvent])
async def get_repair_history(
    event_type: Optional[RepairEventType] = None,
    status: Optional[RepairEventStatus] = None,
    limit: int = 50,
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> List[RepairEvent]:
    """
    Get auto-repair event history.

    Args:
        event_type: Filter by repair type
        status: Filter by event status
        limit: Maximum results to return (default 50)

    Returns:
        List of repair events
    """
    return service.get_history(event_type=event_type, status=status, limit=limit)


@router.post("/trigger", response_model=RepairEvent, status_code=201)
async def trigger_repair(
    event_type: RepairEventType,
    description: str = "Manually triggered repair",
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairEvent:
    """
    Manually trigger a repair event.

    Args:
        event_type: Type of repair to trigger
        description: Human-readable description

    Returns:
        Created repair event
    """
    try:
        return service.record_event(
            event_type=event_type,
            description=description,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/events/{event_id}", response_model=RepairEvent)
async def get_repair_event(
    event_id: str,
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairEvent:
    """
    Get a specific repair event by ID.

    Args:
        event_id: ID of the repair event

    Returns:
        Repair event details
    """
    event = service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Repair event not found")
    return event


@router.post("/events/{event_id}/complete", response_model=RepairEvent)
async def complete_repair_event(
    event_id: str,
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairEvent:
    """
    Mark a repair event as completed.

    Args:
        event_id: ID of the repair event

    Returns:
        Updated repair event
    """
    event = service.complete_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Repair event not found")
    return event


@router.post("/events/{event_id}/fail", response_model=RepairEvent)
async def fail_repair_event(
    event_id: str,
    error_message: str = "Repair failed",
    service: AutoRepairService = Depends(get_auto_repair_service),
) -> RepairEvent:
    """
    Mark a repair event as failed.

    If auto_rollback is enabled, the event will be marked as rolled back.

    Args:
        event_id: ID of the repair event
        error_message: Description of the failure

    Returns:
        Updated repair event
    """
    event = service.fail_event(event_id, error_message)
    if not event:
        raise HTTPException(status_code=404, detail="Repair event not found")
    return event
