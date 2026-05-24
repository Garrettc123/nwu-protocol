"""
Recursive Hierarchical Network System (RHNS).

Integrates the Symbolic Knowledge Vault, Intent Mapper, Policy Resolver, and
Dual Override into a layered hierarchy of symbolic-gating layers.

Layer depths (convention):
    0 — leaf agents (individual workers)
    1 — team clusters
    2 — domain coordinators
    3 — global / master layer

Each layer owns its own SKV instance so that circuit-breaker trips at one
depth do not automatically propagate upward — escalation is explicit.

Intent processing pipeline per layer::

    raw_embedding
        ↓  IntentMapper.ground()
    symbolic atoms
        ↓  SKV.validate()
    validation result
        ↓  if conflicts → PolicyResolver.resolve()
    resolution
        ↓  PASSED / BLOCKED / OVERRIDE_REQUIRED
    RHNSResult

If a layer is BLOCKED and the DualOverride is active, the result is
OVERRIDE_ACTIVE (execution proceeds with audit trail).
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from .dual_override import DualOverride
from .intent_mapper import Atom, IntentMapper
from .policy_resolver import NormativePosition, PolicyResolver, ResolutionOutcome
from .symbolic_knowledge_vault import SKVState, SymbolicKnowledgeVault

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class RHNSOutcome(Enum):
    PASSED          = "passed"           # all checks clear
    BLOCKED         = "blocked"          # SKV/policy blocked
    OVERRIDE_ACTIVE = "override_active"  # bypassed via DualOverride
    NO_ATOMS        = "no_atoms"         # embedding produced no grounded atoms
    ERROR           = "error"            # unexpected exception


@dataclass
class RHNSResult:
    outcome: RHNSOutcome
    agent_id: str
    layer_id: str
    depth: int
    grounded_atoms: List[str]
    skv_state: SKVState
    resolution: str
    escalated: bool = False
    override_active: bool = False
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# RHNSLayer — per-cluster symbolic gate
# ---------------------------------------------------------------------------

class RHNSLayer:
    """
    A single depth-level symbolic gate within the RHNS hierarchy.

    Parameters
    ----------
    layer_id : str
        Human-readable identifier (e.g. "team-alpha", "global").
    depth : int
        Depth in the hierarchy (0 = leaf, 3 = global).
    skv : SymbolicKnowledgeVault
        Circuit breaker for this layer.
    intent_mapper : IntentMapper
        Embedding-to-atom mapper.
    policy_resolver : PolicyResolver
        Multi-agent conflict resolver.
    override : DualOverride
        Dual-button bypass.
    """

    def __init__(
        self,
        layer_id: str,
        depth: int,
        skv: SymbolicKnowledgeVault,
        intent_mapper: IntentMapper,
        policy_resolver: PolicyResolver,
        override: DualOverride,
    ) -> None:
        self.layer_id = layer_id
        self.depth = depth
        self._skv = skv
        self._mapper = intent_mapper
        self._resolver = policy_resolver
        self._override = override
        self._parent: Optional["RHNSLayer"] = None
        self._agent_ids: List[str] = []

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    def register_agent(self, agent_id: str) -> None:
        if agent_id not in self._agent_ids:
            self._agent_ids.append(agent_id)

    def set_parent(self, parent: "RHNSLayer") -> None:
        self._parent = parent

    # ------------------------------------------------------------------
    # Intent processing
    # ------------------------------------------------------------------

    def process_intent(self, agent_id: str, raw_embedding: np.ndarray) -> RHNSResult:
        """
        Run the full NSR pipeline for one agent intent.

        Steps
        -----
        1. Ground embedding → atoms via IntentMapper
        2. Validate atoms via SKV (deontic circuit breaker)
        3. On conflict → PolicyResolver for CSP resolution
        4. If blocked and override active → OVERRIDE_ACTIVE
        5. Otherwise → PASSED or BLOCKED
        """
        try:
            # Step 1 — Grounding
            grounded = self._mapper.ground(raw_embedding)
            atom_names = [a.name for a in grounded]

            if not atom_names:
                logger.debug(
                    "RHNS[%s]: no atoms grounded for agent=%s — NO_ATOMS",
                    self.layer_id, agent_id,
                )
                return RHNSResult(
                    outcome=RHNSOutcome.NO_ATOMS,
                    agent_id=agent_id,
                    layer_id=self.layer_id,
                    depth=self.depth,
                    grounded_atoms=[],
                    skv_state=self._skv.state,
                    resolution="NO_ATOMS",
                )

            # Step 2 — SKV validation
            validation = self._skv.validate(agent_id, atom_names)

            if validation.passed:
                return RHNSResult(
                    outcome=RHNSOutcome.PASSED,
                    agent_id=agent_id,
                    layer_id=self.layer_id,
                    depth=self.depth,
                    grounded_atoms=atom_names,
                    skv_state=validation.breaker_state,
                    resolution=validation.resolution,
                )

            # Step 3 — Policy resolution for conflicts
            if validation.conflicts:
                for atom_name in atom_names:
                    pol_resolution = self._resolver.resolve(agent_id, atom_name)
                    if pol_resolution.outcome == ResolutionOutcome.PERMITTED:
                        logger.info(
                            "RHNS[%s]: policy resolver permitted agent=%s action=%s",
                            self.layer_id, agent_id, atom_name,
                        )
                        return RHNSResult(
                            outcome=RHNSOutcome.PASSED,
                            agent_id=agent_id,
                            layer_id=self.layer_id,
                            depth=self.depth,
                            grounded_atoms=atom_names,
                            skv_state=validation.breaker_state,
                            resolution=f"POLICY_RESOLVED:{pol_resolution.reasoning}",
                        )

            # Step 4 — Check override
            if self._override.is_active():
                logger.critical(
                    "RHNS[%s]: DualOverride ACTIVE — bypassing symbolic gate for agent=%s",
                    self.layer_id, agent_id,
                )
                return RHNSResult(
                    outcome=RHNSOutcome.OVERRIDE_ACTIVE,
                    agent_id=agent_id,
                    layer_id=self.layer_id,
                    depth=self.depth,
                    grounded_atoms=atom_names,
                    skv_state=validation.breaker_state,
                    resolution="OVERRIDE_ACTIVE",
                    override_active=True,
                )

            # Step 5 — Blocked; escalate if parent exists
            result = RHNSResult(
                outcome=RHNSOutcome.BLOCKED,
                agent_id=agent_id,
                layer_id=self.layer_id,
                depth=self.depth,
                grounded_atoms=atom_names,
                skv_state=validation.breaker_state,
                resolution=validation.resolution,
            )
            return self.escalate(result)

        except Exception as exc:
            logger.exception("RHNS[%s]: unexpected error for agent=%s", self.layer_id, agent_id)
            return RHNSResult(
                outcome=RHNSOutcome.ERROR,
                agent_id=agent_id,
                layer_id=self.layer_id,
                depth=self.depth,
                grounded_atoms=[],
                skv_state=SKVState.OPEN,
                resolution="ERROR",
                error=str(exc),
            )

    def escalate(self, result: RHNSResult) -> RHNSResult:
        """Propagate a blocked intent to the parent layer for re-evaluation."""
        if self._parent is not None:
            logger.info(
                "RHNS[%s]: escalating blocked intent (agent=%s) to layer %s",
                self.layer_id, result.agent_id, self._parent.layer_id,
            )
            escalated = self._parent.process_intent(
                result.agent_id,
                np.zeros(1),   # parent re-evaluates symbolically without re-mapping
            )
            escalated.escalated = True
            return escalated

        result.escalated = False
        return result

    def get_status(self) -> Dict:
        return {
            "layer_id": self.layer_id,
            "depth": self.depth,
            "registered_agents": len(self._agent_ids),
            "skv": self._skv.get_status(),
            "override": self._override.get_status(),
            "has_parent": self._parent is not None,
        }


# ---------------------------------------------------------------------------
# RHNS — top-level orchestrator
# ---------------------------------------------------------------------------

class RHNS:
    """
    Top-level Recursive Hierarchical Network System.

    Manages a set of RHNSLayer instances keyed by depth.
    Agents are registered to a specific depth; intents are routed to
    that depth's layer automatically.

    Usage::

        rhns = RHNS()
        rhns.add_layer(RHNSLayer("leaf", 0, skv0, mapper, resolver, override))
        rhns.add_layer(RHNSLayer("global", 3, skv3, mapper, resolver, override))
        rhns.register_agent("agent-007", layer_depth=0)
        result = rhns.submit_intent("agent-007", embedding)
    """

    def __init__(self) -> None:
        self._layers: Dict[int, RHNSLayer] = {}
        self._agent_layer: Dict[str, int] = {}

    def add_layer(self, layer: RHNSLayer) -> None:
        self._layers[layer.depth] = layer
        logger.info("RHNS: added layer '%s' at depth %d", layer.layer_id, layer.depth)

    def register_agent(self, agent_id: str, layer_depth: int = 0) -> None:
        """Assign *agent_id* to a specific depth layer."""
        if layer_depth not in self._layers:
            raise ValueError(f"No layer at depth {layer_depth}; add it first with add_layer()")
        self._layers[layer_depth].register_agent(agent_id)
        self._agent_layer[agent_id] = layer_depth
        logger.debug("RHNS: registered agent '%s' at depth %d", agent_id, layer_depth)

    def submit_intent(self, agent_id: str, embedding: np.ndarray) -> RHNSResult:
        """Route *agent_id*'s intent to the correct layer and return the result."""
        depth = self._agent_layer.get(agent_id)
        if depth is None:
            # Default to shallowest layer
            if not self._layers:
                raise RuntimeError("RHNS has no layers configured")
            depth = min(self._layers)
            logger.warning(
                "RHNS: agent '%s' not registered; routing to default depth %d", agent_id, depth
            )

        layer = self._layers[depth]
        return layer.process_intent(agent_id, embedding)

    def get_status(self) -> Dict:
        return {
            "layer_count": len(self._layers),
            "registered_agents": len(self._agent_layer),
            "layers": {
                depth: layer.get_status()
                for depth, layer in self._layers.items()
            },
        }

    @classmethod
    def build_default(
        cls,
        secret: bytes = b"change-me-use-kms-in-production",
        override_window: float = 30.0,
    ) -> "RHNS":
        """
        Factory: create a single-layer RHNS with default components.

        For production, build layers explicitly and supply a KMS-backed secret.
        """
        from .dual_override import DualOverride
        from .intent_mapper import IntentMapper
        from .policy_resolver import PolicyResolver
        from .symbolic_knowledge_vault import SymbolicKnowledgeVault

        skv      = SymbolicKnowledgeVault()
        mapper   = IntentMapper()
        resolver = PolicyResolver()
        override = DualOverride(secret=secret, window_seconds=override_window)

        layer = RHNSLayer(
            layer_id="default",
            depth=0,
            skv=skv,
            intent_mapper=mapper,
            policy_resolver=resolver,
            override=override,
        )

        rhns = cls()
        rhns.add_layer(layer)
        return rhns
