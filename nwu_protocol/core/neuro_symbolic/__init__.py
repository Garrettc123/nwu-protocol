"""
Neuro-Symbolic Reasoning (NSR) core package for the UEEP / NWU Protocol.

[SYSTEM STATE SYNC]
Platform: UEEP (Unified Enterprise Execution Platform)
Core Architecture: Recursive Hierarchical Network System (RHNS)
Current Module: Neuro-Symbolic Integration
Constraints: High-security enterprise environment, edge computing, manual override required.
Knowledge Cutoff Sync: 2026-05-24

Components
----------
SymbolicKnowledgeVault  -- deontic circuit breaker between neural and execution planes
IntentMapper            -- cosine-similarity embedding → symbolic atom grounding
PolicyResolver          -- deontic defeasible logic + CSP conflict resolution (≤50 agents)
DualOverride            -- HMAC-signed dual-button ignition-sequence bypass
RHNSLayer / RHNS        -- recursive hierarchical integration of all NSR components
StateSync               -- cross-session state serialization and context-header generation

SOTA References (mid-2026)
--------------------------
- IBM/LNN (Logical Neural Networks) — ibm.github.io/LNN
- LTNtorch (Logic Tensor Networks) — github.com/logictensornetworks/LTNtorch
- Deontic Defeasible Logic — arXiv:2409.11780, arXiv:2501.05765
- Grounding drift guard — arXiv:2403.05440
"""

from .symbolic_knowledge_vault import (
    SymbolicKnowledgeVault,
    SKVState,
    DeonticRule,
    DeonticModality,
    ValidationResult,
    Conflict,
)
from .intent_mapper import (
    IntentMapper,
    Atom,
    TruthValue,
    MappingResult,
    GroundingWarning,
)
from .policy_resolver import (
    PolicyResolver,
    AgentPolicy,
    NormativePosition,
    PolicyConflict,
    Resolution,
)
from .dual_override import (
    DualOverride,
    OverrideState,
    OverrideBypassContext,
)
from .rhns import (
    RHNS,
    RHNSLayer,
    RHNSResult,
    RHNSOutcome,
)
from .state_sync import (
    StateSync,
    get_default_sync,
    STATE_SYNC_BLOCK,
)

__all__ = [
    # SKV
    "SymbolicKnowledgeVault", "SKVState", "DeonticRule", "DeonticModality",
    "ValidationResult", "Conflict",
    # Intent mapper
    "IntentMapper", "Atom", "TruthValue", "MappingResult", "GroundingWarning",
    # Policy resolver
    "PolicyResolver", "AgentPolicy", "NormativePosition", "PolicyConflict", "Resolution",
    # Dual override
    "DualOverride", "OverrideState", "OverrideBypassContext",
    # RHNS
    "RHNS", "RHNSLayer", "RHNSResult", "RHNSOutcome",
    # State sync
    "StateSync", "get_default_sync", "STATE_SYNC_BLOCK",
]
