"""Reward Calculator Service."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RewardCalculator:
    """Computes contributor rewards based on quality and complexity."""

    def __init__(self):
        """Initialize the reward calculator."""
        self.base_reward = 10.0  # Base NWU tokens
        self.max_quality_multiplier = 2.0  # Max multiplier for quality
        self.complexity_weights = {
            "code": 1.5,
            "dataset": 1.3,
            "document": 1.0,
            "other": 1.0
        }
        logger.info("Reward Calculator initialized")

    def calculate_reward(
        self,
        quality_score: float,
        contribution_type: str,
        reputation_bonus: float = 0.0
    ) -> float:
        """
        Calculate reward amount for a contribution.

        Formula: base_reward * quality_multiplier * complexity_weight * (1 + reputation_bonus)

        Args:
            quality_score: Quality score (0-100)
            contribution_type: Type of contribution
            reputation_bonus: Bonus multiplier based on user reputation (0-1)

        Returns:
            Calculated reward amount in NWU tokens
        """
        if not 0 <= quality_score <= 100:
            logger.warning(f"Invalid quality score: {quality_score}")
            return 0.0

        # Convert quality score to multiplier (0-100 -> 0.5-2.0)
        quality_multiplier = 0.5 + (quality_score / 100) * 1.5

        # Get complexity weight
        complexity_weight = self.complexity_weights.get(contribution_type, 1.0)

        # Calculate base reward
        reward = self.base_reward * quality_multiplier * complexity_weight

        # Apply reputation bonus (0-100% increase)
        if reputation_bonus > 0:
            reward *= (1 + min(reputation_bonus, 1.0))

        logger.info(
            f"Calculated reward: {reward:.2f} NWU "
            f"(quality={quality_score}, type={contribution_type}, "
            f"reputation_bonus={reputation_bonus})"
        )

        return round(reward, 2)

    def calculate_reputation_bonus(
        self,
        total_contributions: int,
        average_quality: float,
        reputation_score: float
    ) -> float:
        """
        Calculate reputation bonus multiplier.

        Args:
            total_contributions: Total number of contributions
            average_quality: Average quality score
            reputation_score: User reputation score

        Returns:
            Bonus multiplier (0-1)
        """
        # Contribution count bonus (0-0.3)
        count_bonus = min(total_contributions / 100, 0.3)

        # Quality bonus (0-0.4)
        quality_bonus = (average_quality / 100) * 0.4

        # Reputation bonus (0-0.3)
        reputation_bonus = min(reputation_score / 10, 0.3)

        total_bonus = count_bonus + quality_bonus + reputation_bonus

        return min(total_bonus, 1.0)
