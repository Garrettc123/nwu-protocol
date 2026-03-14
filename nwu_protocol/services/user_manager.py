"""User Manager Service."""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from nwu_protocol.models.user import User, UserCreate, UserStats
from nwu_protocol.models.contribution import ContributionStatus

logger = logging.getLogger(__name__)


class UserManager:
    """Manages user registration and statistics."""

    def __init__(self):
        """Initialize the user manager."""
        self._users: dict[str, User] = {}
        self._address_index: dict[str, str] = {}  # address -> user_id
        logger.info("User Manager initialized")

    def create_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user object

        Raises:
            ValueError: If address is already registered
        """
        if user_data.address in self._address_index:
            raise ValueError(f"Address {user_data.address} is already registered")

        user_id = f"user_{uuid4().hex[:12]}"
        user = User(
            id=user_id,
            address=user_data.address,
        )

        self._users[user_id] = user
        self._address_index[user_data.address] = user_id
        logger.info(f"Registered user {user_id} with address {user_data.address}")

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: ID of the user

        Returns:
            User object or None if not found
        """
        return self._users.get(user_id)

    def get_user_by_address(self, address: str) -> Optional[User]:
        """
        Get a user by Ethereum address.

        Args:
            address: Ethereum wallet address

        Returns:
            User object or None if not found
        """
        user_id = self._address_index.get(address)
        if user_id is None:
            return None
        return self._users.get(user_id)

    def list_users(self, limit: int = 100) -> List[User]:
        """
        List all users.

        Args:
            limit: Maximum number of results

        Returns:
            List of users sorted by join date descending
        """
        users = sorted(self._users.values(), key=lambda u: u.joined_at, reverse=True)
        return users[:limit]

    def get_user_stats(self, user_id: str, contributions: list) -> Optional[UserStats]:
        """
        Compute statistics for a user from their contributions.

        Args:
            user_id: ID of the user
            contributions: List of contributions belonging to the user

        Returns:
            UserStats object or None if user not found
        """
        user = self._users.get(user_id)
        if user is None:
            return None

        pending = sum(1 for c in contributions if c.status == ContributionStatus.PENDING)
        verified = sum(1 for c in contributions if c.status == ContributionStatus.VERIFIED)
        rejected = sum(1 for c in contributions if c.status == ContributionStatus.REJECTED)

        scores = [c.quality_score for c in contributions if c.quality_score is not None]
        average_quality = sum(scores) / len(scores) if scores else None

        rewards = sum(c.reward_amount or 0.0 for c in contributions)

        return UserStats(
            user_id=user_id,
            contributions_pending=pending,
            contributions_verified=verified,
            contributions_rejected=rejected,
            average_quality_score=average_quality,
            total_rewards=rewards,
            reputation_score=user.reputation_score,
        )

    def update_reputation(self, user_id: str, score: float) -> Optional[User]:
        """
        Update the reputation score of a user.

        Args:
            user_id: ID of the user
            score: New reputation score (>= 0)

        Returns:
            Updated user or None if not found
        """
        user = self._users.get(user_id)
        if user is None:
            return None

        user.reputation_score = max(0.0, score)
        user.last_active = datetime.now(timezone.utc)
        logger.info(f"Updated reputation for user {user_id} to {user.reputation_score}")

        return user
