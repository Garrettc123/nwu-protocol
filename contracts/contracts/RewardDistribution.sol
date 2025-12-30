// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./NWUToken.sol";

/**
 * @title RewardDistribution
 * @dev Handles reward distribution to contributors
 */
contract RewardDistribution is Ownable, ReentrancyGuard, Pausable {
    NWUToken public token;
    
    mapping(address => uint256) public pendingRewards;
    mapping(address => uint256) public claimedRewards;
    mapping(address => bool) public distributors;
    
    uint256 public totalDistributed;
    uint256 public constant MIN_QUALITY_SCORE = 70;
    uint256 public constant BASE_REWARD = 100 * 10**18; // 100 NWU tokens
    
    event RewardAllocated(address indexed contributor, uint256 amount, uint8 qualityScore);
    event RewardClaimed(address indexed contributor, uint256 amount);
    event DistributorAdded(address indexed distributor);
    event DistributorRemoved(address indexed distributor);
    
    constructor(address tokenAddress) {
        require(tokenAddress != address(0), "Invalid token address");
        token = NWUToken(tokenAddress);
        distributors[msg.sender] = true;
    }
    
    /**
     * @dev Add a distributor address (e.g., backend service)
     */
    function addDistributor(address distributor) external onlyOwner {
        require(distributor != address(0), "Invalid distributor address");
        distributors[distributor] = true;
        emit DistributorAdded(distributor);
    }
    
    /**
     * @dev Remove a distributor address
     */
    function removeDistributor(address distributor) external onlyOwner {
        distributors[distributor] = false;
        emit DistributorRemoved(distributor);
    }
    
    /**
     * @dev Calculate reward based on quality score
     */
    function calculateReward(uint8 qualityScore) public pure returns (uint256) {
        require(qualityScore >= MIN_QUALITY_SCORE, "Quality score too low");
        require(qualityScore <= 100, "Invalid quality score");
        
        // Reward formula: BASE_REWARD * (qualityScore / 70)
        // Score of 70 = 100 tokens, 100 = ~143 tokens
        uint256 reward = (BASE_REWARD * qualityScore) / MIN_QUALITY_SCORE;
        return reward;
    }
    
    /**
     * @dev Allocate reward to a contributor
     */
    function allocateReward(
        address contributor,
        uint8 qualityScore
    ) external nonReentrant whenNotPaused {
        require(distributors[msg.sender], "Not authorized distributor");
        require(contributor != address(0), "Invalid contributor address");
        
        uint256 reward = calculateReward(qualityScore);
        pendingRewards[contributor] += reward;
        
        emit RewardAllocated(contributor, reward, qualityScore);
    }
    
    /**
     * @dev Claim pending rewards
     */
    function claimRewards() external nonReentrant whenNotPaused {
        uint256 amount = pendingRewards[msg.sender];
        require(amount > 0, "No rewards to claim");
        
        pendingRewards[msg.sender] = 0;
        claimedRewards[msg.sender] += amount;
        totalDistributed += amount;
        
        require(token.transfer(msg.sender, amount), "Token transfer failed");
        
        emit RewardClaimed(msg.sender, amount);
    }
    
    /**
     * @dev Get contributor reward info
     */
    function getRewardInfo(address contributor) 
        external 
        view 
        returns (
            uint256 pending,
            uint256 claimed,
            uint256 total
        ) 
    {
        pending = pendingRewards[contributor];
        claimed = claimedRewards[contributor];
        total = pending + claimed;
    }
    
    /**
     * @dev Pause reward distribution
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause reward distribution
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Emergency withdraw tokens (owner only)
     */
    function emergencyWithdraw(uint256 amount) external onlyOwner {
        require(token.transfer(owner(), amount), "Transfer failed");
    }
    
    /**
     * @dev Get contract token balance
     */
    function getBalance() external view returns (uint256) {
        return token.balanceOf(address(this));
    }
}
