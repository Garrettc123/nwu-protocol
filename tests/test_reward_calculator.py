"""Tests for Reward Calculator service."""

import pytest
from nwu_protocol.services.reward_calculator import RewardCalculator


def test_calculate_reward_basic():
    """Test basic reward calculation."""
    calculator = RewardCalculator()
    
    reward = calculator.calculate_reward(
        quality_score=80.0,
        contribution_type="code"
    )
    
    assert reward > 0
    assert isinstance(reward, float)


def test_calculate_reward_with_reputation():
    """Test reward calculation with reputation bonus."""
    calculator = RewardCalculator()
    
    reward_without_bonus = calculator.calculate_reward(
        quality_score=80.0,
        contribution_type="code",
        reputation_bonus=0.0
    )
    
    reward_with_bonus = calculator.calculate_reward(
        quality_score=80.0,
        contribution_type="code",
        reputation_bonus=0.5
    )
    
    assert reward_with_bonus > reward_without_bonus


def test_calculate_reward_quality_scaling():
    """Test that higher quality scores yield higher rewards."""
    calculator = RewardCalculator()
    
    reward_low = calculator.calculate_reward(
        quality_score=50.0,
        contribution_type="code"
    )
    
    reward_high = calculator.calculate_reward(
        quality_score=95.0,
        contribution_type="code"
    )
    
    assert reward_high > reward_low


def test_calculate_reward_type_multiplier():
    """Test that contribution type affects reward."""
    calculator = RewardCalculator()
    
    reward_code = calculator.calculate_reward(
        quality_score=80.0,
        contribution_type="code"
    )
    
    reward_doc = calculator.calculate_reward(
        quality_score=80.0,
        contribution_type="document"
    )
    
    assert reward_code > reward_doc  # Code has higher multiplier


def test_calculate_reputation_bonus():
    """Test reputation bonus calculation."""
    calculator = RewardCalculator()
    
    bonus = calculator.calculate_reputation_bonus(
        total_contributions=50,
        average_quality=80.0,
        reputation_score=5.0
    )
    
    assert 0 <= bonus <= 1.0
    assert bonus > 0


def test_invalid_quality_score():
    """Test that invalid quality scores return 0 reward."""
    calculator = RewardCalculator()
    
    reward = calculator.calculate_reward(
        quality_score=150.0,  # Invalid: > 100
        contribution_type="code"
    )
    
    assert reward == 0.0
