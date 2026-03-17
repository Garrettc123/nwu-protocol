"""Auto-repair control data models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RepairMode(str, Enum):
    """Auto-repair aggressiveness mode."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class RepairEventType(str, Enum):
    """Type of auto-repair event."""
    LINTING = "linting"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    TEST_FIX = "test_fix"
    FILE_GENERATION = "file_generation"
    CODE_QUALITY = "code_quality"
    ROLLBACK = "rollback"


class RepairEventStatus(str, Enum):
    """Status of a repair event."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RepairConfig(BaseModel):
    """Configuration for the auto-repair system."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
                "mode": "moderate",
                "max_retries": 3,
                "auto_rollback": True,
                "require_approval": False,
                "allowed_repair_types": [
                    "linting", "dependency", "security",
                    "test_fix", "file_generation", "code_quality"
                ]
            }
        }
    )

    enabled: bool = Field(True, description="Whether auto-repair is enabled")
    mode: RepairMode = Field(
        RepairMode.MODERATE,
        description="Aggressiveness level of auto-repair"
    )
    max_retries: int = Field(3, ge=1, le=10, description="Maximum retry attempts per repair")
    auto_rollback: bool = Field(True, description="Automatically rollback failed repairs")
    require_approval: bool = Field(False, description="Require manual approval before applying")
    allowed_repair_types: list[RepairEventType] = Field(
        default_factory=lambda: list(RepairEventType),
        description="Types of repairs that are allowed to run"
    )


class RepairConfigUpdate(BaseModel):
    """Schema for updating auto-repair configuration."""
    enabled: Optional[bool] = None
    mode: Optional[RepairMode] = None
    max_retries: Optional[int] = Field(None, ge=1, le=10)
    auto_rollback: Optional[bool] = None
    require_approval: Optional[bool] = None
    allowed_repair_types: Optional[list[RepairEventType]] = None


class RepairEvent(BaseModel):
    """Record of a single auto-repair event."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "repair_abc123def456",
                "event_type": "linting",
                "status": "completed",
                "description": "Fixed formatting in 3 files",
                "files_affected": ["src/utils.ts", "src/api.ts", "src/index.ts"],
                "retry_count": 0,
                "created_at": "2026-03-17T10:00:00Z",
                "completed_at": "2026-03-17T10:00:05Z"
            }
        }
    )

    id: str = Field(..., description="Unique repair event ID")
    event_type: RepairEventType
    status: RepairEventStatus = RepairEventStatus.PENDING
    description: str = Field("", description="Human-readable description of the repair")
    files_affected: list[str] = Field(default_factory=list, description="Files modified by repair")
    retry_count: int = Field(0, ge=0, description="Number of retries attempted")
    error_message: Optional[str] = Field(None, description="Error message if repair failed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None, description="When the repair completed")


class RepairStatus(BaseModel):
    """Overall status of the auto-repair system."""
    enabled: bool
    paused: bool
    mode: RepairMode
    total_repairs: int = Field(0, description="Total repairs executed")
    successful_repairs: int = Field(0, description="Number of successful repairs")
    failed_repairs: int = Field(0, description="Number of failed repairs")
    last_repair_at: Optional[datetime] = Field(None, description="Timestamp of last repair")
    active_repairs: int = Field(0, description="Currently running repairs")
