"""Verification Engine Service - The Nervous System.

NOTE: This module is configured for AUTO-APPROVE mode.
Consensus threshold is set to 0.0, meaning all contributions with at least
one verification are automatically approved. This is intentional behavior
per system requirements.
"""

import logging
from typing import Optional, List
from uuid import uuid4

from nwu_protocol.models.verification import (
    Verification,
    VerificationCreate,
    VerificationVote,
)
from nwu_protocol.models.contribution import ContributionStatus

logger = logging.getLogger(__name__)


class VerificationEngine:
    """Orchestrates the AI verification workflow."""

    def __init__(self, contribution_manager=None):
        """Initialize the verification engine."""
        self._verifications: dict[str, Verification] = {}
        self._contribution_manager = contribution_manager
        self.consensus_threshold = 0.0  # Auto-approve everything (0% threshold)
        self.min_verifications = 1  # Minimum verifications before consensus
        logger.info("Verification Engine initialized (auto-approve mode)")

    def submit_verification(
        self,
        verification_data: VerificationCreate
    ) -> Verification:
        """
        Submit a new verification from an agent.

        Args:
            verification_data: Verification data

        Returns:
            Created verification object
        """
        verification_id = f"verif_{uuid4().hex[:12]}"

        verification = Verification(
            id=verification_id,
            contribution_id=verification_data.contribution_id,
            agent_id=verification_data.agent_id,
            vote=verification_data.vote,
            score=verification_data.score,
            reasoning=verification_data.reasoning,
            details=verification_data.details,
        )

        self._verifications[verification_id] = verification
        
        # Increment verification count
        if self._contribution_manager:
            self._contribution_manager.increment_verification_count(
                verification_data.contribution_id
            )
        
        logger.info(
            f"Verification {verification_id} submitted for "
            f"contribution {verification_data.contribution_id}"
        )

        # Check if consensus is reached
        self._check_consensus(verification_data.contribution_id)

        return verification

    def get_verification(self, verification_id: str) -> Optional[Verification]:
        """Get a verification by ID."""
        return self._verifications.get(verification_id)

    def get_verifications_for_contribution(
        self,
        contribution_id: str
    ) -> List[Verification]:
        """Get all verifications for a contribution."""
        return [
            v for v in self._verifications.values()
            if v.contribution_id == contribution_id
        ]

    def calculate_consensus(self, contribution_id: str) -> dict:
        """
        Calculate consensus for a contribution.

        Args:
            contribution_id: ID of the contribution

        Returns:
            Dictionary with consensus results
        """
        verifications = self.get_verifications_for_contribution(contribution_id)

        if not verifications:
            return {
                "consensus_reached": False,
                "total_verifications": 0,
                "approval_rate": 0.0,
                "average_score": 0.0,
                "status": "pending"
            }

        total = len(verifications)
        approvals = sum(1 for v in verifications if v.vote == VerificationVote.APPROVE)
        approval_rate = approvals / total

        scores = [v.score for v in verifications if v.vote != VerificationVote.ABSTAIN]
        average_score = sum(scores) / len(scores) if scores else 0.0

        # Auto-approve: consensus always reached if we have minimum verifications
        consensus_reached = total >= self.min_verifications

        # Always verified (auto-approve mode)
        status = "verified" if total >= self.min_verifications else "pending"

        return {
            "consensus_reached": consensus_reached,
            "total_verifications": total,
            "approval_rate": approval_rate,
            "average_score": average_score,
            "status": status
        }

    def _check_consensus(self, contribution_id: str) -> None:
        """Check if consensus is reached and update contribution status."""
        if not self._contribution_manager:
            return

        consensus = self.calculate_consensus(contribution_id)

        if consensus["consensus_reached"]:
            self._contribution_manager.update_contribution_status(
                contribution_id,
                ContributionStatus.VERIFIED
            )
            self._contribution_manager.update_quality_score(
                contribution_id,
                consensus["average_score"]
            )
            logger.info(f"Consensus reached for contribution {contribution_id}")
        elif consensus["total_verifications"] >= self.min_verifications:
            self._contribution_manager.update_contribution_status(
                contribution_id,
                ContributionStatus.REJECTED
            )
            logger.info(f"Contribution {contribution_id} rejected")
