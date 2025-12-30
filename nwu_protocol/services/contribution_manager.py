"""Contribution Manager Service - The Trunk."""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from nwu_protocol.models.contribution import (
    Contribution,
    ContributionCreate,
    ContributionStatus,
)

logger = logging.getLogger(__name__)


class ContributionManager:
    """Manages contribution ingestion and processing."""

    def __init__(self):
        """Initialize the contribution manager."""
        # In-memory storage for now (would be MongoDB in production)
        self._contributions: dict[str, Contribution] = {}
        logger.info("Contribution Manager initialized")

    def create_contribution(
        self,
        submitter: str,
        contribution_data: ContributionCreate
    ) -> Contribution:
        """
        Create a new contribution.

        Args:
            submitter: Ethereum address of the submitter
            contribution_data: Contribution creation data

        Returns:
            Created contribution object
        """
        contribution_id = f"contrib_{uuid4().hex[:12]}"

        contribution = Contribution(
            id=contribution_id,
            submitter=submitter,
            file_type=contribution_data.file_type,
            metadata=contribution_data.metadata,
            content_hash=contribution_data.content_hash,
            ipfs_hash=contribution_data.ipfs_hash,
            status=ContributionStatus.PENDING,
        )

        self._contributions[contribution_id] = contribution
        logger.info(f"Created contribution {contribution_id} by {submitter}")

        return contribution

    def get_contribution(self, contribution_id: str) -> Optional[Contribution]:
        """
        Get a contribution by ID.

        Args:
            contribution_id: ID of the contribution

        Returns:
            Contribution object or None if not found
        """
        return self._contributions.get(contribution_id)

    def list_contributions(
        self,
        submitter: Optional[str] = None,
        status: Optional[ContributionStatus] = None,
        limit: int = 100
    ) -> List[Contribution]:
        """
        List contributions with optional filters.

        Args:
            submitter: Filter by submitter address
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of contributions
        """
        contributions = list(self._contributions.values())

        if submitter:
            contributions = [c for c in contributions if c.submitter == submitter]

        if status:
            contributions = [c for c in contributions if c.status == status]

        # Sort by created_at descending
        contributions.sort(key=lambda x: x.created_at, reverse=True)

        return contributions[:limit]

    def update_contribution_status(
        self,
        contribution_id: str,
        status: ContributionStatus
    ) -> Optional[Contribution]:
        """
        Update the status of a contribution.

        Args:
            contribution_id: ID of the contribution
            status: New status

        Returns:
            Updated contribution or None if not found
        """
        contribution = self._contributions.get(contribution_id)
        if not contribution:
            return None

        contribution.status = status
        contribution.updated_at = datetime.now(timezone.utc)
        logger.info(f"Updated contribution {contribution_id} status to {status}")

        return contribution

    def update_quality_score(
        self,
        contribution_id: str,
        quality_score: float
    ) -> Optional[Contribution]:
        """
        Update the quality score of a contribution.

        Args:
            contribution_id: ID of the contribution
            quality_score: Quality score (0-100)

        Returns:
            Updated contribution or None if not found
        """
        contribution = self._contributions.get(contribution_id)
        if not contribution:
            return None

        contribution.quality_score = quality_score
        contribution.updated_at = datetime.now(timezone.utc)
        logger.info(f"Updated contribution {contribution_id} quality score to {quality_score}")

        return contribution

    def increment_verification_count(
        self,
        contribution_id: str
    ) -> Optional[Contribution]:
        """
        Increment the verification count for a contribution.

        Args:
            contribution_id: ID of the contribution

        Returns:
            Updated contribution or None if not found
        """
        contribution = self._contributions.get(contribution_id)
        if not contribution:
            return None

        contribution.verification_count += 1
        contribution.updated_at = datetime.now(timezone.utc)
        logger.info(f"Incremented verification count for contribution {contribution_id} to {contribution.verification_count}")

        return contribution

    @staticmethod
    def compute_content_hash(content: bytes) -> str:
        """
        Compute SHA-256 hash of content.

        Args:
            content: Content bytes to hash

        Returns:
            Hex string of hash
        """
        return hashlib.sha256(content).hexdigest()
