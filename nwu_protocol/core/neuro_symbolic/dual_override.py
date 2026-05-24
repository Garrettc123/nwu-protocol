"""
Dual-Button Manual Override — Physical Ignition Sequence.

Mimics a two-key nuclear ignition system:
    1. First operator calls arm(key_id, token)   → ARMED state + window starts
    2. Second operator calls confirm(key_id, token) → CONFIRMED (bypass active)

Security properties:
    - Both keys must be different (require_different_keys=True by default)
    - Both HMAC tokens must be valid (HMAC-SHA256, constant-time comparison)
    - The window closes after `window_seconds` (default 30 s)
    - Each token is single-use (nonce consumed immediately on first valid use)
    - Every attempt — success or failure — is appended to an audit log (JSONL)
    - The audit log write never raises; failures are logged but do not block override

Usage::

    override = DualOverride(secret=b"shared-secret", window_seconds=30)

    # Operator A
    token_a = override.generate_token("key-alpha", b"shared-secret")
    arm_result = override.arm("key-alpha", token_a)

    # Operator B (within 30 s)
    token_b = override.generate_token("key-beta", b"shared-secret")
    confirm_result = override.confirm("key-beta", token_b)

    if confirm_result.success:
        async with OverrideBypassContext(override):
            # SKV / RHNS bypass is active here
            ...

IMPORTANT: In production the *secret* MUST be loaded from a KMS-backed secret store
(e.g. AWS Secrets Manager) and rotated quarterly.  Hard-coded secrets invalidate the
entire trust chain.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

_AUDIT_LOG_PATH = "override_audit.jsonl"


# ---------------------------------------------------------------------------
# Enums & dataclasses
# ---------------------------------------------------------------------------

class OverrideState(Enum):
    IDLE      = "idle"
    ARMED     = "armed"
    CONFIRMED = "confirmed"
    EXPIRED   = "expired"
    USED      = "used"


@dataclass
class ArmResult:
    success: bool
    state: OverrideState
    message: str
    expires_at: Optional[float] = None


@dataclass
class ConfirmResult:
    success: bool
    state: OverrideState
    message: str


# ---------------------------------------------------------------------------
# DualOverride
# ---------------------------------------------------------------------------

class DualOverride:
    """
    Two-key ignition-sequence manual override for the SKV / RHNS.

    Parameters
    ----------
    secret : bytes
        Shared HMAC secret.  MUST come from a KMS in production.
    window_seconds : float
        How long (seconds) the armed state remains valid after arm().
    require_different_keys : bool
        If True (default), the key_id used in confirm() must differ from arm().
    audit_log_path : str
        Path to the append-only JSONL audit log.
    """

    def __init__(
        self,
        secret: bytes,
        window_seconds: float = 30.0,
        require_different_keys: bool = True,
        audit_log_path: str = _AUDIT_LOG_PATH,
    ) -> None:
        self._secret = secret
        self._window = window_seconds
        self._require_different_keys = require_different_keys
        self._audit_path = audit_log_path

        self._state: OverrideState = OverrideState.IDLE
        self._arm_key_id: Optional[str] = None
        self._arm_timestamp: Optional[float] = None
        self._used_nonces: set = set()
        self._bypass_active: bool = False

    # ------------------------------------------------------------------
    # Token generation
    # ------------------------------------------------------------------

    def generate_token(self, key_id: str, secret: Optional[bytes] = None) -> str:
        """
        Generate a single-use HMAC-SHA256 token for *key_id*.

        The message is ``key_id:nonce:timestamp`` where nonce is a
        32-byte URL-safe random string and timestamp is the current Unix time
        as an integer.  Returns ``nonce:timestamp:digest`` (colon-separated).
        """
        _secret = secret if secret is not None else self._secret
        nonce = secrets.token_urlsafe(32)
        ts = str(int(time.time()))
        message = f"{key_id}:{nonce}:{ts}".encode()
        digest = hmac.new(_secret, message, hashlib.sha256).hexdigest()
        return f"{nonce}:{ts}:{digest}"

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def arm(self, key_id: str, token: str) -> ArmResult:
        """
        First-key operation.  Validates *token* and moves to ARMED state.
        """
        self._expire_if_needed()

        if self._state not in (OverrideState.IDLE, OverrideState.EXPIRED):
            msg = f"Cannot arm: current state is {self._state.value}"
            self._audit("arm_rejected", key_id, False, msg)
            return ArmResult(False, self._state, msg)

        ok, nonce, msg = self._verify_token(key_id, token)
        if not ok:
            self._audit("arm_rejected", key_id, False, msg)
            return ArmResult(False, OverrideState.IDLE, msg)

        # Consume nonce immediately
        self._used_nonces.add(nonce)
        self._state = OverrideState.ARMED
        self._arm_key_id = key_id
        self._arm_timestamp = time.time()
        expires_at = self._arm_timestamp + self._window

        self._audit("arm_success", key_id, True, "Override armed")
        logger.warning("DualOverride ARMED by key_id='%s' — window closes in %.0fs", key_id, self._window)
        return ArmResult(True, OverrideState.ARMED, "Override armed successfully", expires_at)

    def confirm(self, key_id: str, token: str) -> ConfirmResult:
        """
        Second-key operation.  Validates *token* and activates the bypass.
        """
        self._expire_if_needed()

        if self._state != OverrideState.ARMED:
            msg = f"Cannot confirm: state is {self._state.value} (must be ARMED first)"
            self._audit("confirm_rejected", key_id, False, msg)
            return ConfirmResult(False, self._state, msg)

        # Enforce different-keys requirement
        if self._require_different_keys and key_id == self._arm_key_id:
            msg = "Confirm key_id must differ from arm key_id"
            self._audit("confirm_rejected", key_id, False, msg)
            return ConfirmResult(False, OverrideState.ARMED, msg)

        ok, nonce, msg = self._verify_token(key_id, token)
        if not ok:
            self._audit("confirm_rejected", key_id, False, msg)
            return ConfirmResult(False, OverrideState.ARMED, msg)

        # Consume nonce
        self._used_nonces.add(nonce)
        self._state = OverrideState.CONFIRMED
        self._bypass_active = True

        self._audit("confirm_success", key_id, True, "Override CONFIRMED — bypass ACTIVE")
        logger.critical(
            "DualOverride CONFIRMED by key_id='%s' after arm by key_id='%s' — "
            "symbolic layer BYPASSED",
            key_id, self._arm_key_id,
        )
        return ConfirmResult(True, OverrideState.CONFIRMED, "Override confirmed — bypass active")

    def deactivate(self) -> None:
        """Manually deactivate the bypass and reset to IDLE."""
        self._bypass_active = False
        self._state = OverrideState.USED
        self._arm_key_id = None
        self._arm_timestamp = None
        logger.warning("DualOverride deactivated — returning to IDLE")
        self._audit("deactivate", "system", True, "Override deactivated")
        self._state = OverrideState.IDLE

    def is_active(self) -> bool:
        """True when the bypass is confirmed and active."""
        self._expire_if_needed()
        return self._bypass_active and self._state == OverrideState.CONFIRMED

    def get_status(self) -> dict:
        self._expire_if_needed()
        return {
            "state": self._state.value,
            "bypass_active": self._bypass_active,
            "arm_key_id": self._arm_key_id,
            "window_seconds": self._window,
            "require_different_keys": self._require_different_keys,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _verify_token(self, key_id: str, token: str) -> tuple:
        """
        Verify a token produced by generate_token().

        Returns (ok: bool, nonce: str, message: str).
        Uses constant-time comparison to prevent timing attacks.
        """
        parts = token.split(":")
        if len(parts) != 3:
            return False, "", "Malformed token (expected nonce:timestamp:digest)"

        nonce, ts_str, provided_digest = parts

        # Reject replayed nonces
        if nonce in self._used_nonces:
            return False, nonce, "Token already used (nonce replay detected)"

        # Validate timestamp — tokens older than 5 × window are rejected outright
        try:
            ts = int(ts_str)
        except ValueError:
            return False, nonce, "Malformed timestamp in token"

        age = time.time() - ts
        if age > self._window * 5:
            return False, nonce, f"Token expired (age={age:.0f}s, max={self._window * 5:.0f}s)"

        # Recompute expected digest
        message = f"{key_id}:{nonce}:{ts_str}".encode()
        expected = hmac.new(self._secret, message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(provided_digest, expected):
            return False, nonce, "HMAC verification failed"

        return True, nonce, "OK"

    def _expire_if_needed(self) -> None:
        """Transition ARMED → EXPIRED if the window has elapsed."""
        if (
            self._state == OverrideState.ARMED
            and self._arm_timestamp is not None
            and time.time() - self._arm_timestamp > self._window
        ):
            logger.warning("DualOverride window expired — returning to IDLE")
            self._audit("window_expired", self._arm_key_id or "unknown", False, "Arm window expired")
            self._state = OverrideState.EXPIRED
            self._bypass_active = False
            self._arm_key_id = None
            self._arm_timestamp = None

    def _audit(self, event: str, key_id: str, success: bool, message: str) -> None:
        """Append an audit record to the JSONL log.  Never raises."""
        record = {
            "event": event,
            "key_id": key_id,
            "success": success,
            "message": message,
            "timestamp": time.time(),
            "state": self._state.value,
        }
        try:
            with open(self._audit_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except Exception as exc:  # pragma: no cover
            logger.error("DualOverride audit log write failed: %s", exc)


# ---------------------------------------------------------------------------
# Async context manager
# ---------------------------------------------------------------------------

class OverrideBypassContext:
    """
    Async context manager that activates the DualOverride bypass, yields,
    then auto-deactivates on exit.

    Usage::

        async with OverrideBypassContext(override):
            # symbolic checks are bypassed here
            await execute_emergency_action()
        # bypass automatically deactivated
    """

    def __init__(self, override: DualOverride) -> None:
        self._override = override

    async def __aenter__(self) -> "OverrideBypassContext":
        if not self._override.is_active():
            raise RuntimeError(
                "OverrideBypassContext: override is not in CONFIRMED state. "
                "Call arm() then confirm() first."
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._override.deactivate()
        return False   # do not suppress exceptions
