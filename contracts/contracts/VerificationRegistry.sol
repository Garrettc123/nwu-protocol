// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title VerificationRegistry
 * @dev Stores verification results on-chain
 */
contract VerificationRegistry is Ownable, ReentrancyGuard {
    struct Verification {
        bytes32 ipfsHash;
        uint8 qualityScore;
        uint256 timestamp;
        address contributor;
        bool verified;
        bool exists;
    }
    
    mapping(bytes32 => Verification) public verifications;
    mapping(address => bytes32[]) public contributorVerifications;
    
    mapping(address => bool) public verifiers;
    
    event VerificationRecorded(
        bytes32 indexed contributionId,
        bytes32 ipfsHash,
        uint8 qualityScore,
        address indexed contributor,
        uint256 timestamp
    );
    
    event VerifierAdded(address indexed verifier);
    event VerifierRemoved(address indexed verifier);
    
    constructor() {
        verifiers[msg.sender] = true;
    }
    
    /**
     * @dev Add a verifier address (e.g., backend service)
     */
    function addVerifier(address verifier) external onlyOwner {
        require(verifier != address(0), "Invalid verifier address");
        verifiers[verifier] = true;
        emit VerifierAdded(verifier);
    }
    
    /**
     * @dev Remove a verifier address
     */
    function removeVerifier(address verifier) external onlyOwner {
        verifiers[verifier] = false;
        emit VerifierRemoved(verifier);
    }
    
    /**
     * @dev Record a verification result
     */
    function recordVerification(
        bytes32 contributionId,
        bytes32 ipfsHash,
        uint8 qualityScore,
        address contributor
    ) external nonReentrant {
        require(verifiers[msg.sender], "Not authorized verifier");
        require(contributor != address(0), "Invalid contributor address");
        require(qualityScore <= 100, "Invalid quality score");
        require(!verifications[contributionId].exists, "Verification already exists");
        
        verifications[contributionId] = Verification({
            ipfsHash: ipfsHash,
            qualityScore: qualityScore,
            timestamp: block.timestamp,
            contributor: contributor,
            verified: qualityScore >= 70, // Minimum threshold
            exists: true
        });
        
        contributorVerifications[contributor].push(contributionId);
        
        emit VerificationRecorded(
            contributionId,
            ipfsHash,
            qualityScore,
            contributor,
            block.timestamp
        );
    }
    
    /**
     * @dev Get verification details
     */
    function getVerification(bytes32 contributionId) 
        external 
        view 
        returns (
            bytes32 ipfsHash,
            uint8 qualityScore,
            uint256 timestamp,
            address contributor,
            bool verified
        ) 
    {
        require(verifications[contributionId].exists, "Verification not found");
        Verification memory v = verifications[contributionId];
        return (v.ipfsHash, v.qualityScore, v.timestamp, v.contributor, v.verified);
    }
    
    /**
     * @dev Get all verifications for a contributor
     */
    function getContributorVerifications(address contributor) 
        external 
        view 
        returns (bytes32[] memory) 
    {
        return contributorVerifications[contributor];
    }
    
    /**
     * @dev Get contributor statistics
     */
    function getContributorStats(address contributor) 
        external 
        view 
        returns (
            uint256 totalContributions,
            uint256 verifiedContributions,
            uint256 averageScore
        ) 
    {
        bytes32[] memory contributions = contributorVerifications[contributor];
        totalContributions = contributions.length;
        
        if (totalContributions == 0) {
            return (0, 0, 0);
        }
        
        uint256 totalScore = 0;
        verifiedContributions = 0;
        
        for (uint256 i = 0; i < totalContributions; i++) {
            Verification memory v = verifications[contributions[i]];
            totalScore += v.qualityScore;
            if (v.verified) {
                verifiedContributions++;
            }
        }
        
        averageScore = totalScore / totalContributions;
    }
}
