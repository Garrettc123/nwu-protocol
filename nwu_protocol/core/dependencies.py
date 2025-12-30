"""Dependency injection for NWU Protocol services."""

from functools import lru_cache
from nwu_protocol.services.contribution_manager import ContributionManager
from nwu_protocol.services.verification_engine import VerificationEngine
from nwu_protocol.services.reward_calculator import RewardCalculator


@lru_cache()
def get_contribution_manager() -> ContributionManager:
    """Get or create the contribution manager singleton."""
    return ContributionManager()


@lru_cache()
def get_verification_engine() -> VerificationEngine:
    """Get or create the verification engine singleton."""
    return VerificationEngine(contribution_manager=get_contribution_manager())


@lru_cache()
def get_reward_calculator() -> RewardCalculator:
    """Get or create the reward calculator singleton."""
    return RewardCalculator()
