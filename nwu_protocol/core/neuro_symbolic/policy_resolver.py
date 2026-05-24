"""
Policy Resolver — Deontic Defeasible Logic + CSP.

Resolves multi-agent normative conflicts using:
    1. Per-agent normative positions (OBLIGATED / PERMITTED / FORBIDDEN)
    2. Priority cascade for pairwise conflicts (higher priority wins; tie → ABSTAIN)
    3. Constraint Satisfaction scan for global conflict detection

SOTA basis:
    - Deontic Defeasible Logic (Governatori & Rotolo 2004; arXiv:2409.11780)
    - Normative Multi-Agent Systems (Dagstuhl Seminar 23151)
    - Deontic Temporal Logic for AI Ethics (arXiv:2501.05765)

Scale constraint (from ISPASS 2024 benchmarks):
    Efficient for ≤ 50 agents.  A scale warning is logged — not raised — when
    the policy store exceeds this limit.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

_SCALE_WARN_THRESHOLD = 50


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class NormativePosition(Enum):
    OBLIGATED = "obligated"   # O(a, φ)
    PERMITTED = "permitted"   # P(a, φ)
    FORBIDDEN = "forbidden"   # F(a, φ)


class ResolutionOutcome(Enum):
    PERMITTED = "permitted"   # action is allowed
    BLOCKED   = "blocked"     # action is explicitly prohibited
    ABSTAIN   = "abstain"     # tie / no coverage — conservative block


@dataclass
class AgentPolicy:
    """Normative policy for a single agent."""
    agent_id: str
    # Maps action/predicate name → NormativePosition
    positions: Dict[str, NormativePosition]
    priority: int = 1          # higher priority wins pairwise conflicts


@dataclass
class PolicyConflict:
    """An O ∧ F conflict across one or more agents for a specific action."""
    action: str
    agent_ids: List[str]
    conflicting_positions: List[Tuple[str, NormativePosition]]  # (agent_id, position)


@dataclass
class Resolution:
    """Outcome of a resolve() call."""
    agent_id: str
    action: str
    outcome: ResolutionOutcome
    reasoning: str
    winning_policy: Optional[AgentPolicy] = None


# ---------------------------------------------------------------------------
# Policy Resolver
# ---------------------------------------------------------------------------

class PolicyResolver:
    """
    Multi-agent deontic conflict resolver.

    Usage::

        resolver = PolicyResolver()
        resolver.add_policy(AgentPolicy("agent-1", {"deploy": NormativePosition.OBLIGATED}, priority=2))
        resolver.add_policy(AgentPolicy("agent-2", {"deploy": NormativePosition.FORBIDDEN}, priority=1))

        result = resolver.resolve("agent-1", "deploy")
        # → Resolution(outcome=PERMITTED, ...) because agent-1 has higher priority
    """

    def __init__(self) -> None:
        self._policies: Dict[str, AgentPolicy] = {}

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    def add_policy(self, policy: AgentPolicy) -> None:
        self._policies[policy.agent_id] = policy
        if len(self._policies) > _SCALE_WARN_THRESHOLD:
            logger.warning(
                "PolicyResolver: policy store has %d agents (SOTA efficient limit is %d). "
                "Consider partitioning the swarm into clusters.",
                len(self._policies), _SCALE_WARN_THRESHOLD,
            )
        logger.debug("PolicyResolver: registered policy for agent '%s'", policy.agent_id)

    def remove_policy(self, agent_id: str) -> None:
        self._policies.pop(agent_id, None)

    def agent_ids(self) -> List[str]:
        return list(self._policies.keys())

    # ------------------------------------------------------------------
    # Per-agent resolution
    # ------------------------------------------------------------------

    def resolve(self, agent_id: str, action: str) -> Resolution:
        """
        Determine whether *agent_id* may perform *action*.

        Checks the agent's own policy first, then checks for global conflicts
        with other agents' policies and runs the priority cascade.
        """
        own = self._policies.get(agent_id)
        own_position = own.positions.get(action) if own else None

        # Gather conflicting positions from all agents for this action
        all_positions: List[Tuple[AgentPolicy, NormativePosition]] = []
        for pol in self._policies.values():
            pos = pol.positions.get(action)
            if pos is not None:
                all_positions.append((pol, pos))

        if not all_positions:
            # No policy coverage → ABSTAIN (open-world: unknown is blocked)
            return Resolution(
                agent_id=agent_id,
                action=action,
                outcome=ResolutionOutcome.ABSTAIN,
                reasoning="No policy covers this (agent, action) pair — conservative abstain.",
            )

        obligations  = [(p, pos) for p, pos in all_positions if pos == NormativePosition.OBLIGATED]
        prohibitions = [(p, pos) for p, pos in all_positions if pos == NormativePosition.FORBIDDEN]

        if not prohibitions:
            return Resolution(
                agent_id=agent_id,
                action=action,
                outcome=ResolutionOutcome.PERMITTED,
                reasoning="Action is obligated or permitted with no prohibition.",
                winning_policy=own,
            )

        if not obligations:
            return Resolution(
                agent_id=agent_id,
                action=action,
                outcome=ResolutionOutcome.BLOCKED,
                reasoning="Action is forbidden with no countervailing obligation.",
            )

        # Conflict — run priority cascade
        return self._priority_cascade(agent_id, action, obligations, prohibitions)

    # ------------------------------------------------------------------
    # Global conflict detection
    # ------------------------------------------------------------------

    def detect_global_conflicts(self) -> List[PolicyConflict]:
        """
        Scan all registered policies for O ∧ F conflicts across agents.

        Returns a list of PolicyConflict objects; empty list means no conflicts.
        """
        # Build maps: action → set of agents with each position
        obligated: Dict[str, List[str]] = {}
        forbidden: Dict[str, List[str]] = {}

        for pol in self._policies.values():
            for action, pos in pol.positions.items():
                if pos == NormativePosition.OBLIGATED:
                    obligated.setdefault(action, []).append(pol.agent_id)
                elif pos == NormativePosition.FORBIDDEN:
                    forbidden.setdefault(action, []).append(pol.agent_id)

        conflicts: List[PolicyConflict] = []
        for action in set(obligated) & set(forbidden):
            affected = list(set(obligated[action]) | set(forbidden[action]))
            conflicting = (
                [(a, NormativePosition.OBLIGATED) for a in obligated[action]]
                + [(a, NormativePosition.FORBIDDEN) for a in forbidden[action]]
            )
            conflicts.append(PolicyConflict(
                action=action,
                agent_ids=affected,
                conflicting_positions=conflicting,
            ))

        if conflicts:
            logger.warning(
                "PolicyResolver: %d global O∧F conflict(s) detected: %s",
                len(conflicts), [c.action for c in conflicts],
            )
        return conflicts

    def csp_resolve(
        self,
        conflicts: Optional[List[PolicyConflict]] = None,
    ) -> Dict[str, Resolution]:
        """
        Run a constraint-satisfaction pass over detected conflicts.

        Returns a per-action Resolution dict using the priority cascade.
        If *conflicts* is None, detect_global_conflicts() is called first.
        """
        if conflicts is None:
            conflicts = self.detect_global_conflicts()

        result: Dict[str, Resolution] = {}
        for conflict in conflicts:
            # Find the highest-priority agent in the conflict and use its position
            agents_in_conflict = [
                self._policies[aid]
                for aid in conflict.agent_ids
                if aid in self._policies
            ]
            if not agents_in_conflict:
                continue

            obligations = [
                (p, NormativePosition.OBLIGATED)
                for p in agents_in_conflict
                if p.positions.get(conflict.action) == NormativePosition.OBLIGATED
            ]
            prohibitions = [
                (p, NormativePosition.FORBIDDEN)
                for p in agents_in_conflict
                if p.positions.get(conflict.action) == NormativePosition.FORBIDDEN
            ]

            resolution = self._priority_cascade(
                "swarm", conflict.action, obligations, prohibitions
            )
            result[conflict.action] = resolution

        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _priority_cascade(
        self,
        agent_id: str,
        action: str,
        obligations: List[Tuple[AgentPolicy, NormativePosition]],
        prohibitions: List[Tuple[AgentPolicy, NormativePosition]],
    ) -> Resolution:
        """Higher priority wins; exact tie → ABSTAIN."""
        max_ob  = max((p.priority for p, _ in obligations),  default=0)
        max_pr  = max((p.priority for p, _ in prohibitions), default=0)

        winning_ob_policy = next(
            (p for p, _ in obligations if p.priority == max_ob), None
        )

        if max_ob > max_pr:
            return Resolution(
                agent_id=agent_id,
                action=action,
                outcome=ResolutionOutcome.PERMITTED,
                reasoning=(
                    f"Obligation priority {max_ob} > prohibition priority {max_pr} "
                    "— obligation wins."
                ),
                winning_policy=winning_ob_policy,
            )
        elif max_pr > max_ob:
            return Resolution(
                agent_id=agent_id,
                action=action,
                outcome=ResolutionOutcome.BLOCKED,
                reasoning=(
                    f"Prohibition priority {max_pr} > obligation priority {max_ob} "
                    "— prohibition wins."
                ),
            )
        else:
            logger.warning(
                "PolicyResolver: exact priority tie for action='%s' — ABSTAIN (conservative).",
                action,
            )
            return Resolution(
                agent_id=agent_id,
                action=action,
                outcome=ResolutionOutcome.ABSTAIN,
                reasoning=(
                    f"Obligation priority {max_ob} == prohibition priority {max_pr} "
                    "— tie resolved conservatively as ABSTAIN."
                ),
            )
