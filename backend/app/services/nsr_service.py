"""NSR Service — async wrapper over the UEEP neuro-symbolic core."""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _numpy_available() -> bool:
    try:
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


class NSRService:
    """
    Thin async facade over nwu_protocol.core.neuro_symbolic.

    Follows the same pattern as PerplexityService: lazy initialisation,
    is_available() guard, global singleton at module bottom.
    """

    def __init__(self) -> None:
        self._ready = False
        self._rhns = None
        self._override = None
        self._state_sync = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return _numpy_available()

    def _ensure_ready(self) -> None:
        if self._ready:
            return
        if not self.is_available():
            raise RuntimeError("NSR requires numpy — install it first.")

        # Import here to avoid circular deps at module load time
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        from nwu_protocol.core.neuro_symbolic import RHNS, get_default_sync

        secret = os.environ.get("NSR_OVERRIDE_SECRET", "change-me-use-kms").encode()
        self._rhns = RHNS.build_default(secret=secret)
        self._override = list(self._rhns._layers.values())[0]._override
        self._state_sync = get_default_sync()
        self._ready = True
        logger.info("NSRService initialised (RHNS ready)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_system_status(self) -> Dict[str, Any]:
        if not self.is_available():
            return {"available": False, "reason": "numpy not installed"}
        self._ensure_ready()
        return {
            "available": True,
            "rhns": self._rhns.get_status(),
            "override": self._override.get_status(),
        }

    async def get_state_sync(self) -> Dict[str, Any]:
        self._ensure_ready()
        return self._state_sync.to_dict()

    async def process_intent(
        self,
        agent_id: str,
        embedding: List[float],
    ) -> Dict[str, Any]:
        """Run an embedding through the RHNS pipeline."""
        self._ensure_ready()
        import numpy as np
        vec = np.array(embedding, dtype=float)
        result = self._rhns.submit_intent(agent_id, vec)
        return {
            "outcome": result.outcome.value,
            "agent_id": result.agent_id,
            "layer_id": result.layer_id,
            "depth": result.depth,
            "grounded_atoms": result.grounded_atoms,
            "skv_state": result.skv_state.value,
            "resolution": result.resolution,
            "escalated": result.escalated,
            "override_active": result.override_active,
            "timestamp": result.timestamp,
            "error": result.error,
        }

    async def validate_policy(
        self,
        agent_id: str,
        atoms: List[str],
        rules: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Validate symbolic atoms directly against the SKV.
        Optionally register transient deontic rules first.
        """
        self._ensure_ready()
        from nwu_protocol.core.neuro_symbolic import (
            DeonticModality, DeonticRule, SymbolicKnowledgeVault,
        )

        skv = SymbolicKnowledgeVault()
        if rules:
            for r in rules:
                try:
                    skv.register_rule(DeonticRule(
                        rule_id=r["rule_id"],
                        agent_id=r.get("agent_id", agent_id),
                        modality=DeonticModality[r["modality"].upper()],
                        predicate=r["predicate"],
                        priority=int(r.get("priority", 1)),
                        weight=float(r.get("weight", 1.0)),
                    ))
                except (KeyError, ValueError) as exc:
                    return {"success": False, "error": f"Invalid rule: {exc}"}

        result = skv.validate(agent_id, atoms)
        return {
            "success": True,
            "passed": result.passed,
            "resolution": result.resolution,
            "breaker_state": result.breaker_state.value,
            "conflicts": [
                {
                    "predicate": c.predicate,
                    "obligation_rule": c.obligation_rule.rule_id,
                    "prohibition_rule": c.prohibition_rule.rule_id,
                }
                for c in result.conflicts
            ],
        }

    async def detect_policy_conflicts(
        self,
        policies: List[Dict],
    ) -> Dict[str, Any]:
        """Scan a list of agent policies for global O∧F conflicts."""
        self._ensure_ready()
        from nwu_protocol.core.neuro_symbolic import (
            AgentPolicy, NormativePosition, PolicyResolver,
        )

        resolver = PolicyResolver()
        for p in policies:
            positions = {
                action: NormativePosition[pos.upper()]
                for action, pos in p.get("positions", {}).items()
            }
            resolver.add_policy(AgentPolicy(
                agent_id=p["agent_id"],
                positions=positions,
                priority=int(p.get("priority", 1)),
            ))

        conflicts = resolver.detect_global_conflicts()
        resolutions = resolver.csp_resolve(conflicts)

        return {
            "success": True,
            "conflict_count": len(conflicts),
            "conflicts": [
                {
                    "action": c.action,
                    "agent_ids": c.agent_ids,
                }
                for c in conflicts
            ],
            "resolutions": {
                action: {
                    "outcome": res.outcome.value,
                    "reasoning": res.reasoning,
                }
                for action, res in resolutions.items()
            },
        }

    async def arm_override(self, key_id: str, token: str) -> Dict[str, Any]:
        self._ensure_ready()
        result = self._override.arm(key_id, token)
        return {
            "success": result.success,
            "state": result.state.value,
            "message": result.message,
            "expires_at": result.expires_at,
        }

    async def confirm_override(self, key_id: str, token: str) -> Dict[str, Any]:
        self._ensure_ready()
        result = self._override.confirm(key_id, token)
        return {
            "success": result.success,
            "state": result.state.value,
            "message": result.message,
        }

    async def get_override_status(self) -> Dict[str, Any]:
        self._ensure_ready()
        return self._override.get_status()

    def generate_override_token(self, key_id: str) -> str:
        """Generate a test token (uses the service's own secret)."""
        self._ensure_ready()
        return self._override.generate_token(key_id)


# Global singleton
nsr_service = NSRService()
