"""
Symbolic Knowledge Vault (SKV) — Deontic Circuit Breaker.

Acts as the logical 'circuit breaker' between the neural inference layer and
the execution plane in the RHNS.  Every neural intent must pass through the
SKV before it reaches actuators or downstream agents.

Circuit breaker states (after Nygard 2007):
    CLOSED   — normal operation; intents validated and passed through
    OPEN     — policy violation detected; all intents blocked until reset
    HALF_OPEN — recovery probe; a single intent is tested before fully closing

Deontic operators (after Governatori & Rotolo 2004; arXiv:2409.11780):
    O(a, φ)  — agent a is OBLIGATED to achieve φ
    P(a, φ)  — agent a is PERMITTED to do φ
    F(a, φ)  — agent a is FORBIDDEN from doing φ

Conflict: O(a, φ) ∧ F(a, φ) → circuit breaker trips to OPEN.
Resolution: priority(rule_1) × weight(rule_1) vs priority(rule_2) × weight(rule_2).
Tie → ABSTAIN (conservative default).

Deadlock detection: Tarjan's SCC on the policy dependency graph catches cyclic
obligation chains before they are committed to the vault.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & dataclasses
# ---------------------------------------------------------------------------

class SKVState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class DeonticModality(Enum):
    OBLIGATION = "O"   # must achieve
    PERMISSION = "P"   # may do
    PROHIBITION = "F"  # must not do


@dataclass
class DeonticRule:
    """A single deontic policy rule."""
    rule_id: str
    agent_id: str                   # "*" matches any agent
    modality: DeonticModality
    predicate: str                  # symbolic atom name this rule applies to
    priority: int = 1               # higher wins; ties go to ABSTAIN
    weight: float = 1.0             # multiplied with priority for scoring
    depends_on: List[str] = field(default_factory=list)  # rule_ids this rule implies


@dataclass
class Conflict:
    """An O ∧ F conflict detected for a given (agent, predicate) pair."""
    agent_id: str
    predicate: str
    obligation_rule: DeonticRule
    prohibition_rule: DeonticRule


@dataclass
class ValidationResult:
    """Outcome of an SKV validation call."""
    passed: bool
    agent_id: str
    intent_atoms: List[str]
    conflicts: List[Conflict]
    resolution: str           # "PASS", "BLOCKED", "ABSTAIN", "OVERRIDE_REQUIRED"
    breaker_state: SKVState
    timestamp: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Symbolic Knowledge Vault
# ---------------------------------------------------------------------------

class SymbolicKnowledgeVault:
    """
    Deontic circuit breaker for the RHNS.

    Usage::

        skv = SymbolicKnowledgeVault(failure_threshold=3, recovery_timeout=60)
        skv.register_rule(DeonticRule("r1", "agent-1", DeonticModality.OBLIGATION,
                                      "deploy_service", priority=2))
        skv.register_rule(DeonticRule("r2", "agent-1", DeonticModality.PROHIBITION,
                                      "deploy_service", priority=1))
        result = skv.validate("agent-1", ["deploy_service"])
        # → conflict detected; breaker may trip
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ):
        self._rules: Dict[str, DeonticRule] = {}
        self._state: SKVState = SKVState.CLOSED
        self._failure_count: int = 0
        self._failure_threshold: int = failure_threshold
        self._recovery_timeout: float = recovery_timeout
        self._open_since: Optional[float] = None
        self._used_tokens: Set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> SKVState:
        self._maybe_recover()
        return self._state

    def register_rule(self, rule: DeonticRule) -> None:
        """Add a deontic rule to the vault."""
        self._rules[rule.rule_id] = rule
        logger.debug("SKV registered rule %s (%s %s %s)",
                     rule.rule_id, rule.modality.value, rule.agent_id, rule.predicate)
        # Run deadlock check after every structural change
        cycles = self._scc_deadlock_check()
        if cycles:
            logger.warning("SKV: cyclic dependency detected in policy graph: %s", cycles)

    def deregister_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def validate(self, agent_id: str, intent_atoms: List[str]) -> ValidationResult:
        """
        Validate a list of symbolic atoms for a given agent.

        Returns a ValidationResult describing whether the intent may proceed.
        Trips the circuit breaker when the failure threshold is exceeded.
        """
        self._maybe_recover()

        if self._state == SKVState.OPEN:
            return ValidationResult(
                passed=False,
                agent_id=agent_id,
                intent_atoms=intent_atoms,
                conflicts=[],
                resolution="BLOCKED",
                breaker_state=self._state,
            )

        conflicts: List[Conflict] = []
        for atom in intent_atoms:
            obligations = self._rules_for(agent_id, atom, DeonticModality.OBLIGATION)
            prohibitions = self._rules_for(agent_id, atom, DeonticModality.PROHIBITION)
            conflicts.extend(self._detect_conflicts(agent_id, atom, obligations, prohibitions))

        if not conflicts:
            if self._state == SKVState.HALF_OPEN:
                self.reset()
            return ValidationResult(
                passed=True,
                agent_id=agent_id,
                intent_atoms=intent_atoms,
                conflicts=[],
                resolution="PASS",
                breaker_state=self._state,
            )

        # Attempt resolution
        resolution_str = self._resolve_conflicts(conflicts)
        passed = resolution_str == "PASS"

        if not passed:
            self._failure_count += 1
            logger.warning(
                "SKV validation failed for agent=%s atoms=%s conflicts=%d failures=%d",
                agent_id, intent_atoms, len(conflicts), self._failure_count,
            )
            if self._failure_count >= self._failure_threshold:
                self.trip()

        return ValidationResult(
            passed=passed,
            agent_id=agent_id,
            intent_atoms=intent_atoms,
            conflicts=conflicts,
            resolution=resolution_str,
            breaker_state=self._state,
        )

    def trip(self) -> None:
        """Open the circuit breaker."""
        logger.error("SKV circuit breaker OPEN — blocking all intents")
        self._state = SKVState.OPEN
        self._open_since = time.time()

    def half_open(self) -> None:
        """Put the circuit into half-open probe state."""
        logger.info("SKV circuit breaker HALF_OPEN — probe mode")
        self._state = SKVState.HALF_OPEN

    def reset(self) -> None:
        """Close the circuit breaker and reset failure counter."""
        logger.info("SKV circuit breaker CLOSED — normal operation")
        self._state = SKVState.CLOSED
        self._failure_count = 0
        self._open_since = None

    def get_rules(self) -> List[DeonticRule]:
        return list(self._rules.values())

    def get_status(self) -> Dict:
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self._failure_threshold,
            "rule_count": len(self._rules),
            "open_since": self._open_since,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _maybe_recover(self) -> None:
        """Auto-transition OPEN → HALF_OPEN after recovery_timeout."""
        if (
            self._state == SKVState.OPEN
            and self._open_since is not None
            and time.time() - self._open_since >= self._recovery_timeout
        ):
            self.half_open()

    def _rules_for(
        self,
        agent_id: str,
        predicate: str,
        modality: DeonticModality,
    ) -> List[DeonticRule]:
        """Return rules that apply to (agent_id, predicate, modality)."""
        return [
            r for r in self._rules.values()
            if r.modality == modality
            and r.predicate == predicate
            and (r.agent_id == agent_id or r.agent_id == "*")
        ]

    def _detect_conflicts(
        self,
        agent_id: str,
        predicate: str,
        obligations: List[DeonticRule],
        prohibitions: List[DeonticRule],
    ) -> List[Conflict]:
        """Return Conflict objects for every O ∧ F pair."""
        conflicts = []
        for ob in obligations:
            for pr in prohibitions:
                conflicts.append(Conflict(
                    agent_id=agent_id,
                    predicate=predicate,
                    obligation_rule=ob,
                    prohibition_rule=pr,
                ))
        return conflicts

    def _resolve_conflicts(self, conflicts: List[Conflict]) -> str:
        """
        Priority × weight cascade:
        - obligation score > prohibition score → PASS (obligation wins)
        - prohibition score > obligation score → BLOCKED
        - tie → ABSTAIN (conservative)
        """
        for conflict in conflicts:
            ob_score = conflict.obligation_rule.priority * conflict.obligation_rule.weight
            pr_score = conflict.prohibition_rule.priority * conflict.prohibition_rule.weight

            if ob_score > pr_score:
                continue          # obligation wins for this conflict — keep checking
            elif pr_score > ob_score:
                return "BLOCKED"
            else:
                return "ABSTAIN"  # tie → conservative block

        return "PASS"

    def _scc_deadlock_check(self) -> List[List[str]]:
        """
        Tarjan's Strongly Connected Components on the rule dependency graph.
        Returns a list of cycles (each cycle is a list of rule_ids).
        A non-trivial SCC (size > 1) indicates a cyclic obligation chain.
        """
        graph: Dict[str, List[str]] = {r: rule.depends_on for r, rule in self._rules.items()}
        index_counter = [0]
        stack: List[str] = []
        lowlink: Dict[str, int] = {}
        index: Dict[str, int] = {}
        on_stack: Set[str] = set()
        sccs: List[List[str]] = []

        def strongconnect(v: str) -> None:
            index[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack.add(v)

            for w in graph.get(v, []):
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink.get(w, lowlink[v]))
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], index[w])

            if lowlink[v] == index[v]:
                scc: List[str] = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == v:
                        break
                if len(scc) > 1:
                    sccs.append(scc)

        for node in list(graph.keys()):
            if node not in index:
                strongconnect(node)

        return sccs
