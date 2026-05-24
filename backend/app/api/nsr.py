"""NSR API — Neuro-Symbolic Reasoning endpoints for the UEEP / NWU Protocol."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from ..services.nsr_service import nsr_service

router = APIRouter(prefix="/api/v1/nsr", tags=["nsr"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class IntentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, description="Agent submitting the intent")
    embedding: List[float] = Field(..., min_length=1, description="Raw neural embedding vector")


class PolicyValidateRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    atoms: List[str] = Field(..., min_length=1, description="Symbolic atom names to validate")
    rules: Optional[List[Dict[str, Any]]] = Field(
        None,
        description=(
            "Transient deontic rules. Each dict: "
            "{rule_id, agent_id?, modality (OBLIGATION|PERMISSION|PROHIBITION), "
            "predicate, priority?, weight?}"
        ),
    )


class PolicyEntry(BaseModel):
    agent_id: str
    positions: Dict[str, str] = Field(
        ...,
        description="Map of action → normative position (OBLIGATED|PERMITTED|FORBIDDEN)",
    )
    priority: int = Field(1, ge=1)


class ConflictScanRequest(BaseModel):
    policies: List[PolicyEntry] = Field(..., min_length=1)


class OverrideActionRequest(BaseModel):
    key_id: str = Field(..., min_length=1, description="Operator key identifier")
    token: str = Field(..., min_length=1, description="HMAC-signed single-use token")


class NSRResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/status")
async def nsr_status():
    """
    Return NSR service availability and RHNS layer status.
    Does not require numpy to call — reports unavailable gracefully.
    """
    if not nsr_service.is_available():
        return {
            "available": False,
            "message": "numpy is not installed; NSR unavailable",
        }
    status_data = await nsr_service.get_system_status()
    return {"available": True, **status_data}


@router.get("/state-sync")
async def state_sync():
    """
    Return the UEEP STATE_SYNC_BLOCK for cross-session context injection.

    Insert the returned `context_header` string at the top of any new LLM
    thread or agent session to re-establish UEEP platform context.
    """
    _require_available()
    data = await nsr_service.get_state_sync()
    # Build the formatted header too
    from nwu_protocol.core.neuro_symbolic import get_default_sync
    header = get_default_sync().to_context_header()
    return {"state_sync": data, "context_header": header}


@router.post("/intent", response_model=NSRResponse, status_code=status.HTTP_200_OK)
async def process_intent(request: IntentRequest):
    """
    Submit a neural embedding for RHNS validation.

    The embedding is grounded to symbolic atoms, validated by the Symbolic
    Knowledge Vault (deontic circuit breaker), and policy-resolved if conflicts
    are detected.

    Outcomes: ``passed``, ``blocked``, ``override_active``, ``no_atoms``, ``error``.
    """
    _require_available()
    try:
        result = await nsr_service.process_intent(request.agent_id, request.embedding)
        return NSRResponse(success=True, data=result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/policy/validate", response_model=NSRResponse, status_code=status.HTTP_200_OK)
async def validate_policy(request: PolicyValidateRequest):
    """
    Validate symbolic atoms against transient deontic rules.

    Supply a list of deontic rules inline; a temporary SKV instance is used
    (does not mutate the live RHNS policy store).
    """
    _require_available()
    try:
        result = await nsr_service.validate_policy(
            request.agent_id, request.atoms, request.rules
        )
        return NSRResponse(success=result.get("success", False), data=result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/policy/conflicts", response_model=NSRResponse, status_code=status.HTTP_200_OK)
async def detect_conflicts(request: ConflictScanRequest):
    """
    Scan a set of agent policies for global O∧F deontic conflicts.

    Returns detected conflicts and CSP-resolved outcomes per action.
    Efficient for ≤ 50 agents per SOTA benchmarks (arXiv:2409.11780).
    """
    _require_available()
    try:
        policies_raw = [p.model_dump() for p in request.policies]
        result = await nsr_service.detect_policy_conflicts(policies_raw)
        return NSRResponse(success=True, data=result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/override/arm", response_model=NSRResponse, status_code=status.HTTP_200_OK)
async def arm_override(request: OverrideActionRequest):
    """
    First-key of the dual-button ignition sequence.

    Validates an HMAC-signed token and moves the override to ARMED state.
    The confirm window starts immediately; call ``/override/confirm`` within
    ``window_seconds`` (default 30 s) using a **different** key_id.
    """
    _require_available()
    try:
        result = await nsr_service.arm_override(request.key_id, request.token)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return NSRResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/override/confirm", response_model=NSRResponse, status_code=status.HTTP_200_OK)
async def confirm_override(request: OverrideActionRequest):
    """
    Second-key of the dual-button ignition sequence.

    Validates a second HMAC token from a **different** key_id and activates
    the DualOverride bypass.  The symbolic layer is suspended until the bypass
    is deactivated or the system is restarted.
    """
    _require_available()
    try:
        result = await nsr_service.confirm_override(request.key_id, request.token)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return NSRResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/override/status")
async def override_status():
    """Return current DualOverride state (IDLE / ARMED / CONFIRMED / EXPIRED / USED)."""
    _require_available()
    return await nsr_service.get_override_status()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _require_available() -> None:
    if not nsr_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NSR unavailable: numpy is not installed.",
        )
