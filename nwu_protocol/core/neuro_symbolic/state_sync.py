"""
UEEP Cross-Session State Synchronisation.

Provides a serialisable, validatable state block that can be:
    - Saved to / loaded from a JSON file between sessions
    - Injected as a formatted header into LLM context windows
    - Validated for required-field completeness

Insert `StateSync.to_context_header()` at the start of any new thread or
agent session to re-establish UEEP platform context.

[SYSTEM STATE SYNC]
Platform: UEEP (Unified Enterprise Execution Platform)
Core Architecture: Recursive Hierarchical Network System (RHNS)
Current Module: Neuro-Symbolic Integration
Constraints: High-security enterprise environment, edge computing, manual override required.
Knowledge Cutoff Sync: 2026-05-24
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {"platform", "core_architecture", "current_module", "constraints", "knowledge_cutoff"}

STATE_SYNC_BLOCK: Dict[str, str] = {
    "platform": "UEEP (Unified Enterprise Execution Platform)",
    "core_architecture": "Recursive Hierarchical Network System (RHNS)",
    "current_module": "Neuro-Symbolic Integration",
    "constraints": (
        "High-security enterprise environment, edge computing, "
        "manual override required, ≤50 agents per cluster"
    ),
    "knowledge_cutoff": "2026-05-24",
    "nsr_components": (
        "SymbolicKnowledgeVault, IntentMapper, PolicyResolver, "
        "DualOverride, RHNSLayer"
    ),
    "sota_references": (
        "IBM/LNN, LTNtorch, DeepProbLog, Scallop, "
        "Deontic Defeasible Logic (arXiv:2409.11780)"
    ),
}


@dataclass
class StateSync:
    """Serialisable cross-session state for the UEEP NSR module."""

    platform: str = STATE_SYNC_BLOCK["platform"]
    core_architecture: str = STATE_SYNC_BLOCK["core_architecture"]
    current_module: str = STATE_SYNC_BLOCK["current_module"]
    constraints: str = STATE_SYNC_BLOCK["constraints"]
    knowledge_cutoff: str = STATE_SYNC_BLOCK["knowledge_cutoff"]
    nsr_components: str = STATE_SYNC_BLOCK["nsr_components"]
    sota_references: str = STATE_SYNC_BLOCK["sota_references"]
    session_timestamp: float = field(default_factory=time.time)
    extra: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Serialise state to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)
        logger.info("StateSync saved to %s", p)

    @classmethod
    def load(cls, path: str) -> "StateSync":
        """Deserialise state from a JSON file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"StateSync file not found: {p}")
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        extra = {k: v for k, v in data.items() if k not in cls.__dataclass_fields__}
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        obj = cls(**known)
        obj.extra = extra
        logger.info("StateSync loaded from %s", p)
        return obj

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Return True if all required fields are non-empty."""
        d = asdict(self)
        missing = [f for f in _REQUIRED_FIELDS if not d.get(f)]
        if missing:
            logger.warning("StateSync validation failed — missing fields: %s", missing)
            return False
        return True

    # ------------------------------------------------------------------
    # Context header generation
    # ------------------------------------------------------------------

    def to_context_header(self) -> str:
        """
        Return a formatted string suitable for injection at the top of
        an LLM prompt or agent context window.
        """
        lines = [
            "[SYSTEM STATE SYNC]",
            f"Platform: {self.platform}",
            f"Core Architecture: {self.core_architecture}",
            f"Current Module: {self.current_module}",
            f"Constraints: {self.constraints}",
            f"Knowledge Cutoff Sync: {self.knowledge_cutoff}",
            f"NSR Components: {self.nsr_components}",
            f"SOTA References: {self.sota_references}",
        ]
        if self.extra:
            for k, v in self.extra.items():
                lines.append(f"{k}: {v}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return asdict(self)


def get_default_sync() -> StateSync:
    """Return a pre-populated StateSync with UEEP defaults."""
    return StateSync()
