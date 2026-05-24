"""
Intent Mapper — Neural Embedding → Symbolic Atom Grounding.

Maps high-dimensional vector embeddings to first-order logic predicates
(atoms) using L2-normalised cosine similarity — the LTN-style approach
identified as most mature by the SOTA survey (arXiv:2403.05440).

Truth-value assignment (fuzzy, not classical):
    TRUE   similarity ≥ 0.70
    FUZZY  0.40 ≤ similarity < 0.70
    FALSE  similarity < 0.40

Drift guard (per arXiv:2403.05440):
    If the spread of the top-10 similarity scores is ≤ 0.02 the embeddings
    are near-constant and cosine similarity is meaningless.  A GroundingWarning
    is raised so callers can log and take action.

Termux / edge compatibility: stdlib + numpy only.  No torch, no sentence-
transformers required in the critical path.
"""

import logging
import math
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class TruthValue(Enum):
    TRUE = "true"
    FUZZY = "fuzzy"
    FALSE = "false"


class GroundingWarning(UserWarning):
    """Raised when embedding drift renders cosine similarity unreliable."""


@dataclass
class Atom:
    """A named symbolic predicate with an associated prototype embedding."""
    name: str
    vector: np.ndarray          # stored L2-normalised
    domain: str = "general"
    description: str = ""

    def __post_init__(self) -> None:
        # Always normalise at construction time
        norm = np.linalg.norm(self.vector)
        if norm < 1e-12:
            raise ValueError(f"Atom '{self.name}': zero-norm embedding is not valid")
        object.__setattr__(self, "vector", self.vector / norm)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        return isinstance(other, Atom) and self.name == other.name


@dataclass
class MappingResult:
    """The similarity of one atom to a query embedding."""
    atom: Atom
    similarity: float
    truth_value: TruthValue


# ---------------------------------------------------------------------------
# Intent Mapper
# ---------------------------------------------------------------------------

_TRUE_THRESHOLD = 0.70
_FUZZY_THRESHOLD = 0.40
_DRIFT_SPREAD_MIN = 0.02   # minimum spread; below this → GroundingWarning
_DRIFT_TOP_K = 10


class IntentMapper:
    """
    Maps raw neural embeddings to symbolic atoms.

    Usage::

        mapper = IntentMapper()
        mapper.register_atom(Atom("deploy_service", np.array([0.1, 0.9, ...])))
        mapper.register_atom(Atom("halt_process",   np.array([0.8, 0.1, ...])))

        results = mapper.map(some_embedding, top_k=5)
        grounded = mapper.ground(some_embedding, threshold=0.70)
    """

    def __init__(
        self,
        true_threshold: float = _TRUE_THRESHOLD,
        fuzzy_threshold: float = _FUZZY_THRESHOLD,
    ):
        self._atoms: Dict[str, Atom] = {}
        self._true_threshold = true_threshold
        self._fuzzy_threshold = fuzzy_threshold

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    def register_atom(self, atom: Atom) -> None:
        """Register (or replace) a named atom."""
        self._atoms[atom.name] = atom
        logger.debug("IntentMapper: registered atom '%s' (domain=%s)", atom.name, atom.domain)

    def deregister_atom(self, name: str) -> None:
        self._atoms.pop(name, None)

    def atom_names(self) -> List[str]:
        return list(self._atoms.keys())

    # ------------------------------------------------------------------
    # Core mapping
    # ------------------------------------------------------------------

    def map(self, embedding: np.ndarray, top_k: int = 5) -> List[MappingResult]:
        """
        Compute cosine similarity between *embedding* and every registered atom.

        Returns up to *top_k* results, sorted by descending similarity.
        Raises GroundingWarning if drift is detected.
        """
        if not self._atoms:
            return []

        vec = self._l2_normalize(embedding)
        results: List[MappingResult] = []

        for atom in self._atoms.values():
            sim = float(np.dot(vec, atom.vector))
            sim = max(-1.0, min(1.0, sim))   # numerical safety
            tv = self._truth_value(sim)
            results.append(MappingResult(atom=atom, similarity=sim, truth_value=tv))

        results.sort(key=lambda r: r.similarity, reverse=True)

        # Drift guard
        self._check_drift(results)

        return results[:top_k]

    def ground(
        self,
        embedding: np.ndarray,
        threshold: Optional[float] = None,
    ) -> List[Atom]:
        """
        Return atoms whose similarity to *embedding* meets *threshold*.

        Defaults to the TRUE threshold (0.70) when *threshold* is None.
        """
        thr = threshold if threshold is not None else self._true_threshold
        results = self.map(embedding, top_k=len(self._atoms))
        return [r.atom for r in results if r.similarity >= thr]

    def ground_with_scores(
        self,
        embedding: np.ndarray,
        threshold: Optional[float] = None,
    ) -> List[MappingResult]:
        """Like ground() but returns full MappingResult objects."""
        thr = threshold if threshold is not None else self._true_threshold
        results = self.map(embedding, top_k=len(self._atoms))
        return [r for r in results if r.similarity >= thr]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _l2_normalize(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        if norm < 1e-12:
            raise ValueError("Cannot normalise a zero-norm embedding")
        return v / norm

    def _truth_value(self, similarity: float) -> TruthValue:
        if similarity >= self._true_threshold:
            return TruthValue.TRUE
        if similarity >= self._fuzzy_threshold:
            return TruthValue.FUZZY
        return TruthValue.FALSE

    def _check_drift(self, results: List[MappingResult]) -> None:
        """
        Warn if the top-K similarities are suspiciously uniform.
        A spread ≤ _DRIFT_SPREAD_MIN suggests all embeddings are near-constant,
        making cosine similarity meaningless (arXiv:2403.05440).
        """
        top = results[:_DRIFT_TOP_K]
        if len(top) < 2:
            return
        sims = [r.similarity for r in top]
        spread = max(sims) - min(sims)
        if spread <= _DRIFT_SPREAD_MIN:
            warnings.warn(
                f"IntentMapper drift detected: top-{len(top)} cosine similarities span "
                f"only {spread:.4f} (threshold {_DRIFT_SPREAD_MIN}). "
                "Embeddings may be near-constant; re-calibrate the embedding model.",
                GroundingWarning,
                stacklevel=3,
            )
