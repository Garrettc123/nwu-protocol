// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./NWUDataToken.sol";
import "./NWUGovernance.sol";

/**
 * @title NWUProtocol
 * @dev Main protocol contract for managing contributions, verification, and rewards
 */
contract NWUProtocol is AccessControl, ReentrancyGuard, Pausable {
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    uint256 public constant SUBMISSION_FEE = 0.001 ether;
    uint256 public constant VERIFICATION_REWARD = 100 * 10**18; // 100 NWUG tokens

    struct Contribution {
        uint256 id;
        address contributor;
        string dataHash;
        string description;
        string category;
        uint256 timestamp;
        bool verified;
        uint256 nftTokenId;
    }

    NWUDataToken public dataToken;
    NWUGovernance public governanceToken;
    address public treasury;

    uint256 private nextContributionId;
    mapping(uint256 => Contribution) public contributions;
    mapping(address => uint256[]) public userContributions;
    
    uint256 public totalContributions;
    uint256 public totalVerifiedContributions;
    uint256 public totalRewardsDistributed;

    event ContributionSubmitted(
        uint256 indexed contributionId,
        address indexed contributor,
        string dataHash,
        uint256 timestamp
    );

    event ContributionVerified(
        uint256 indexed contributionId,
        address indexed contributor,
        uint256 nftTokenId,
        uint256 reward
    );

    event TreasuryAddressUpdated(
        address indexed oldAddress,
        address indexed newAddress
    );

    constructor(
        address _dataToken,
        address _governanceToken,
        address _treasury
    ) {
        require(_dataToken != address(0), "Invalid data token address");
        require(_governanceToken != address(0), "Invalid governance token address");
        require(_treasury != address(0), "Invalid treasury address");

        dataToken = NWUDataToken(_dataToken);
        governanceToken = NWUGovernance(_governanceToken);
        treasury = _treasury;

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    /**
     * @dev Submit a data contribution
     */
    function submitContribution(
        string memory dataHash,
        string memory description,
        string memory category
    ) external payable whenNotPaused returns (uint256) {
        require(msg.value >= SUBMISSION_FEE, "Insufficient submission fee");
        require(bytes(dataHash).length > 0, "Data hash required");
        require(bytes(description).length > 0, "Description required");

        uint256 contributionId = nextContributionId++;
        
        contributions[contributionId] = Contribution({
            id: contributionId,
            contributor: msg.sender,
            dataHash: dataHash,
            description: description,
            category: category,
            timestamp: block.timestamp,
            verified: false,
            nftTokenId: 0
        });

        userContributions[msg.sender].push(contributionId);
        totalContributions++;

        // Send fee to treasury
        (bool success, ) = treasury.call{value: msg.value}("");
        require(success, "Treasury transfer failed");

        emit ContributionSubmitted(
            contributionId,
            msg.sender,
            dataHash,
            block.timestamp
        );

        return contributionId;
    }

    /**
     * @dev Verify a contribution and mint NFT
     */
    function verifyContribution(
        uint256 contributionId,
        string memory tokenURI
    ) external onlyRole(VERIFIER_ROLE) nonReentrant {
        Contribution storage contribution = contributions[contributionId];
        require(contribution.id == contributionId, "Contribution does not exist");
        require(!contribution.verified, "Already verified");

        // Mint NFT to contributor
        uint256 tokenId = dataToken.safeMint(
            contribution.contributor,
            tokenURI
        );

        // Mint governance tokens as reward
        governanceToken.mint(
            contribution.contributor,
            VERIFICATION_REWARD
        );

        contribution.verified = true;
        contribution.nftTokenId = tokenId;
        totalVerifiedContributions++;
        totalRewardsDistributed += VERIFICATION_REWARD;

        emit ContributionVerified(
            contributionId,
            contribution.contributor,
            tokenId,
            VERIFICATION_REWARD
        );
    }

    /**
     * @dev Batch verify contributions
     */
    function batchVerifyContributions(
        uint256[] calldata contributionIds,
        string[] calldata tokenURIs
    ) external onlyRole(VERIFIER_ROLE) {
        require(
            contributionIds.length == tokenURIs.length,
            "Array length mismatch"
        );

        for (uint256 i = 0; i < contributionIds.length; i++) {
            verifyContribution(contributionIds[i], tokenURIs[i]);
        }
    }

    /**
     * @dev Get user statistics
     */
    function getUserStats(address user)
        external
        view
        returns (
            uint256 totalSubmissions,
            uint256 verifiedSubmissions,
            uint256 totalRewards
        )
    {
        uint256[] memory userContributionIds = userContributions[user];
        totalSubmissions = userContributionIds.length;
        
        for (uint256 i = 0; i < userContributionIds.length; i++) {
            if (contributions[userContributionIds[i]].verified) {
                verifiedSubmissions++;
            }
        }

        totalRewards = verifiedSubmissions * VERIFICATION_REWARD;
    }

    /**
     * @dev Get protocol statistics
     */
    function getProtocolStats()
        external
        view
        returns (
            uint256 _totalContributions,
            uint256 _totalVerifiedContributions,
            uint256 _totalRewardsDistributed,
            uint256 _treasuryBalance
        )
    {
        return (
            totalContributions,
            totalVerifiedContributions,
            totalRewardsDistributed,
            address(treasury).balance
        );
    }

    /**
     * @dev Update treasury address
     */
    function updateTreasuryAddress(address newTreasury)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        require(newTreasury != address(0), "Invalid treasury address");
        address oldTreasury = treasury;
        treasury = newTreasury;
        emit TreasuryAddressUpdated(oldTreasury, newTreasury);
    }

    /**
     * @dev Pause contract
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause contract
     */
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }
}
