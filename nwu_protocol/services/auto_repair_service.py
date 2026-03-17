"""Auto-Repair Control Service.

Manages the configuration, state, and history of the auto-repair system.
Provides control mechanisms to enable/disable, pause/resume, and configure
the automated code repair pipeline.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from nwu_protocol.models.auto_repair import (
    RepairConfig,
    RepairConfigUpdate,
    RepairEvent,
    RepairEventStatus,
    RepairEventType,
    RepairMode,
    RepairStatus,
)

logger = logging.getLogger(__name__)


class AutoRepairService:
    """Controls the auto-repair system lifecycle and configuration."""

    def __init__(self):
        """Initialize the auto-repair control service."""
        self._config = RepairConfig()
        self._paused = False
        self._events: dict[str, RepairEvent] = {}
        logger.info("Auto-Repair Control Service initialized")

    def get_config(self) -> RepairConfig:
        """
        Get the current auto-repair configuration.

        Returns:
            Current repair configuration
        """
        return self._config

    def update_config(self, update: RepairConfigUpdate) -> RepairConfig:
        """
        Update auto-repair configuration.

        Only fields provided in the update are changed; others remain as-is.

        Args:
            update: Partial configuration update

        Returns:
            Updated configuration
        """
        update_data = update.model_dump(exclude_unset=True)
        current_data = self._config.model_dump()
        current_data.update(update_data)
        self._config = RepairConfig(**current_data)
        logger.info(f"Auto-repair config updated: {update_data}")
        return self._config

    def pause(self) -> RepairStatus:
        """
        Pause the auto-repair system.

        Returns:
            Current repair status after pausing
        """
        self._paused = True
        logger.info("Auto-repair system paused")
        return self.get_status()

    def resume(self) -> RepairStatus:
        """
        Resume the auto-repair system.

        Returns:
            Current repair status after resuming
        """
        self._paused = False
        logger.info("Auto-repair system resumed")
        return self.get_status()

    def get_status(self) -> RepairStatus:
        """
        Get the current status of the auto-repair system.

        Returns:
            Current system status with statistics
        """
        events = list(self._events.values())
        completed = [e for e in events if e.status == RepairEventStatus.COMPLETED]
        failed = [
            e for e in events
            if e.status in (RepairEventStatus.FAILED, RepairEventStatus.ROLLED_BACK)
        ]
        active = [
            e for e in events
            if e.status in (RepairEventStatus.PENDING, RepairEventStatus.IN_PROGRESS)
        ]

        last_repair_at = None
        if events:
            sorted_events = sorted(events, key=lambda e: e.created_at, reverse=True)
            last_repair_at = sorted_events[0].created_at

        return RepairStatus(
            enabled=self._config.enabled,
            paused=self._paused,
            mode=self._config.mode,
            total_repairs=len(events),
            successful_repairs=len(completed),
            failed_repairs=len(failed),
            last_repair_at=last_repair_at,
            active_repairs=len(active),
        )

    def get_history(
        self,
        event_type: Optional[RepairEventType] = None,
        status: Optional[RepairEventStatus] = None,
        limit: int = 50,
    ) -> List[RepairEvent]:
        """
        Get repair event history with optional filters.

        Args:
            event_type: Filter by event type
            status: Filter by event status
            limit: Maximum number of results

        Returns:
            List of repair events
        """
        events = list(self._events.values())

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        if status is not None:
            events = [e for e in events if e.status == status]

        events.sort(key=lambda e: e.created_at, reverse=True)
        return events[:limit]

    def record_event(
        self,
        event_type: RepairEventType,
        description: str,
        files_affected: Optional[List[str]] = None,
    ) -> RepairEvent:
        """
        Record a new auto-repair event.

        Returns an event in PENDING status if the system is active, or raises
        if the system is disabled or paused.

        Args:
            event_type: Type of repair
            description: Human-readable description
            files_affected: List of affected file paths

        Returns:
            Created repair event

        Raises:
            RuntimeError: If the system is disabled or paused
        """
        if not self._config.enabled:
            raise RuntimeError("Auto-repair system is disabled")

        if self._paused:
            raise RuntimeError("Auto-repair system is paused")

        if event_type not in self._config.allowed_repair_types:
            raise RuntimeError(
                f"Repair type '{event_type}' is not allowed in the current configuration"
            )

        event_id = f"repair_{uuid4().hex[:12]}"
        event = RepairEvent(
            id=event_id,
            event_type=event_type,
            status=RepairEventStatus.IN_PROGRESS,
            description=description,
            files_affected=files_affected or [],
        )

        self._events[event_id] = event
        logger.info(f"Repair event {event_id} recorded: {description}")
        return event

    def complete_event(self, event_id: str) -> Optional[RepairEvent]:
        """
        Mark a repair event as completed.

        Args:
            event_id: ID of the repair event

        Returns:
            Updated event or None if not found
        """
        event = self._events.get(event_id)
        if not event:
            return None

        event.status = RepairEventStatus.COMPLETED
        event.completed_at = datetime.now(timezone.utc)
        logger.info(f"Repair event {event_id} completed")
        return event

    def fail_event(
        self,
        event_id: str,
        error_message: str,
    ) -> Optional[RepairEvent]:
        """
        Mark a repair event as failed.

        If auto_rollback is enabled the event is marked as ROLLED_BACK instead.

        Args:
            event_id: ID of the repair event
            error_message: Description of the failure

        Returns:
            Updated event or None if not found
        """
        event = self._events.get(event_id)
        if not event:
            return None

        if self._config.auto_rollback:
            event.status = RepairEventStatus.ROLLED_BACK
            logger.info(f"Repair event {event_id} rolled back: {error_message}")
        else:
            event.status = RepairEventStatus.FAILED
            logger.info(f"Repair event {event_id} failed: {error_message}")

        event.error_message = error_message
        event.completed_at = datetime.now(timezone.utc)
        return event

    def get_event(self, event_id: str) -> Optional[RepairEvent]:
        """
        Get a repair event by ID.

        Args:
            event_id: ID of the repair event

        Returns:
            Repair event or None if not found
        """
        return self._events.get(event_id)
