"""NSR Guardian Agent — BaseAgent subclass for neuro-symbolic policy enforcement."""

import logging
from typing import Any, Dict, Optional

from .base_agent import BaseAgent
from .agent_orchestrator import AgentType

logger = logging.getLogger(__name__)


class NSRGuardianAgent(BaseAgent):
    """
    NSR Guardian Agent — validates neural intents via the Symbolic Knowledge Vault
    before they reach the execution plane.

    Supported task types
    --------------------
    validate_intent     — run an embedding through the RHNS pipeline
    resolve_policy      — detect and resolve deontic conflicts in a policy set
    fact_gate           — gate a claim through the SKV before forwarding
    emergency_override  — arm or confirm the DualOverride bypass
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(agent_id, AgentType.NSR_GUARDIAN, config)

    async def initialize(self) -> None:
        logger.info("NSR Guardian Agent %s initialising...", self.agent_id)
        from .nsr_service import nsr_service
        if not nsr_service.is_available():
            logger.warning(
                "NSR Guardian Agent %s: numpy not available — tasks will fail until installed.",
                self.agent_id,
            )
        else:
            logger.info("NSR Guardian Agent %s ready.", self.agent_id)

    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        from .nsr_service import nsr_service

        dispatch = {
            "validate_intent":   self._validate_intent,
            "resolve_policy":    self._resolve_policy,
            "fact_gate":         self._fact_gate,
            "emergency_override": self._emergency_override,
        }
        handler = dispatch.get(task_type)
        if handler is None:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
        return await handler(task_data, nsr_service)

    # ------------------------------------------------------------------
    # Task handlers
    # ------------------------------------------------------------------

    async def _validate_intent(self, data: Dict, svc) -> Dict:
        embedding = data.get("embedding")
        agent_id  = data.get("agent_id", self.agent_id)
        if embedding is None:
            return {"success": False, "error": "Missing 'embedding' field"}
        try:
            result = await svc.process_intent(agent_id, embedding)
            return {"success": True, **result}
        except Exception as exc:
            logger.error("NSR Guardian %s validate_intent failed: %s", self.agent_id, exc)
            return {"success": False, "error": str(exc)}

    async def _resolve_policy(self, data: Dict, svc) -> Dict:
        policies = data.get("policies")
        if not policies:
            return {"success": False, "error": "Missing 'policies' list"}
        try:
            return await svc.detect_policy_conflicts(policies)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _fact_gate(self, data: Dict, svc) -> Dict:
        agent_id = data.get("agent_id", self.agent_id)
        atoms    = data.get("atoms", [])
        rules    = data.get("rules")
        if not atoms:
            return {"success": False, "error": "Missing 'atoms' list"}
        try:
            return await svc.validate_policy(agent_id, atoms, rules)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _emergency_override(self, data: Dict, svc) -> Dict:
        action   = data.get("action")   # "arm" | "confirm" | "status"
        key_id   = data.get("key_id")
        token    = data.get("token")

        if action == "arm":
            if not key_id or not token:
                return {"success": False, "error": "arm requires key_id and token"}
            return await svc.arm_override(key_id, token)
        elif action == "confirm":
            if not key_id or not token:
                return {"success": False, "error": "confirm requires key_id and token"}
            return await svc.confirm_override(key_id, token)
        elif action == "status":
            return await svc.get_override_status()
        else:
            return {"success": False, "error": "action must be 'arm', 'confirm', or 'status'"}
