// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Snapshot.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title NWUGovernance
 * @dev ERC20 governance token with vesting and voting capabilities
 */
contract NWUGovernance is
    ERC20,
    ERC20Burnable,
    ERC20Votes,
    ERC20Snapshot,
    AccessControl,
    Pausable
{
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant SNAPSHOT_ROLE = keccak256("SNAPSHOT_ROLE");

    uint256 public constant MAX_SUPPLY = 1000000000 * 10**18; // 1 billion tokens
    uint256 public constant INITIAL_SUPPLY = 100000000 * 10**18; // 100 million tokens

    bool public transfersEnabled;
    mapping(address => bool) public whitelist;

    struct VestingSchedule {
        uint256 totalAmount;
        uint256 releasedAmount;
        uint256 startTime;
        uint256 duration;
        bool revoked;
    }

    mapping(address => VestingSchedule) public vestingSchedules;

    event VestingScheduleCreated(
        address indexed beneficiary,
        uint256 amount,
        uint256 duration
    );

    event TokensReleased(address indexed beneficiary, uint256 amount);
    event TransfersEnabled();
    event AddressWhitelisted(address indexed account);
    event AddressRemovedFromWhitelist(address indexed account);

    constructor() ERC20("NWU Governance", "NWUG") ERC20Permit("NWU Governance") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(SNAPSHOT_ROLE, msg.sender);

        // Mint initial supply
        _mint(msg.sender, INITIAL_SUPPLY);
        
        // Whitelist deployer
        whitelist[msg.sender] = true;
    }

    /**
     * @dev Mint new tokens
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
    }

    /**
     * @dev Create vesting schedule
     */
    function createVestingSchedule(
        address beneficiary,
        uint256 amount,
        uint256 duration
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(beneficiary != address(0), "Invalid beneficiary");
        require(amount > 0, "Amount must be > 0");
        require(duration > 0, "Duration must be > 0");
        require(
            vestingSchedules[beneficiary].totalAmount == 0,
            "Schedule already exists"
        );

        vestingSchedules[beneficiary] = VestingSchedule({
            totalAmount: amount,
            releasedAmount: 0,
            startTime: block.timestamp,
            duration: duration,
            revoked: false
        });

        _transfer(msg.sender, address(this), amount);

        emit VestingScheduleCreated(beneficiary, amount, duration);
    }

    /**
     * @dev Release vested tokens
     */
    function releaseVestedTokens() external {
        VestingSchedule storage schedule = vestingSchedules[msg.sender];
        require(schedule.totalAmount > 0, "No vesting schedule");
        require(!schedule.revoked, "Schedule revoked");

        uint256 vestedAmount = _computeVestedAmount(schedule);
        uint256 releasableAmount = vestedAmount - schedule.releasedAmount;
        
        require(releasableAmount > 0, "No tokens to release");

        schedule.releasedAmount += releasableAmount;
        _transfer(address(this), msg.sender, releasableAmount);

        emit TokensReleased(msg.sender, releasableAmount);
    }

    /**
     * @dev Compute vested amount
     */
    function _computeVestedAmount(VestingSchedule memory schedule)
        private
        view
        returns (uint256)
    {
        if (block.timestamp < schedule.startTime) {
            return 0;
        }

        uint256 elapsed = block.timestamp - schedule.startTime;
        
        if (elapsed >= schedule.duration) {
            return schedule.totalAmount;
        }

        return (schedule.totalAmount * elapsed) / schedule.duration;
    }

    /**
     * @dev Enable transfers
     */
    function enableTransfers() external onlyRole(DEFAULT_ADMIN_ROLE) {
        transfersEnabled = true;
        emit TransfersEnabled();
    }

    /**
     * @dev Add address to whitelist
     */
    function addToWhitelist(address account)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        whitelist[account] = true;
        emit AddressWhitelisted(account);
    }

    /**
     * @dev Remove address from whitelist
     */
    function removeFromWhitelist(address account)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        whitelist[account] = false;
        emit AddressRemovedFromWhitelist(account);
    }

    /**
     * @dev Create snapshot for voting
     */
    function snapshot() external onlyRole(SNAPSHOT_ROLE) returns (uint256) {
        return _snapshot();
    }

    /**
     * @dev Pause transfers
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause transfers
     */
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // Override transfer restrictions
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20, ERC20Snapshot) whenNotPaused {
        if (from != address(0) && to != address(0)) {
            require(
                transfersEnabled || whitelist[from] || whitelist[to],
                "Transfers not enabled"
            );
        }
        super._beforeTokenTransfer(from, to, amount);
    }

    function _afterTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20, ERC20Votes) {
        super._afterTokenTransfer(from, to, amount);
    }

    function _mint(address to, uint256 amount)
        internal
        override(ERC20, ERC20Votes)
    {
        super._mint(to, amount);
    }

    function _burn(address account, uint256 amount)
        internal
        override(ERC20, ERC20Votes)
    {
        super._burn(account, amount);
    }
}
