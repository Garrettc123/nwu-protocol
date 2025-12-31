// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title NWUDataToken
 * @dev ERC721 NFT representing verified data contribution certificates
 */
contract NWUDataToken is 
    ERC721,
    ERC721URIStorage,
    ERC721Burnable,
    ERC2981,
    AccessControl,
    Pausable
{
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    uint256 private _nextTokenId;
    uint256 public maxSupply = 1000000;
    
    struct TokenInfo {
        address creator;
        uint256 mintTime;
    }

    mapping(uint256 => TokenInfo) public tokenInfo;
    mapping(address => uint256[]) private _ownedTokens;

    event TokenMinted(uint256 indexed tokenId, address indexed to, string uri);

    constructor() ERC721("NWU Data Certificate", "NWUDC") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);

        // Set default royalty to 2.5% (250 basis points)
        _setDefaultRoyalty(msg.sender, 250);
    }

    /**
     * @dev Mint a new NFT
     */
    function safeMint(address to, string memory uri)
        external
        onlyRole(MINTER_ROLE)
        whenNotPaused
        returns (uint256)
    {
        require(_nextTokenId < maxSupply, "Max supply reached");
        
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);

        tokenInfo[tokenId] = TokenInfo({
            creator: to,
            mintTime: block.timestamp
        });

        _ownedTokens[to].push(tokenId);

        emit TokenMinted(tokenId, to, uri);
        return tokenId;
    }

    /**
     * @dev Batch mint NFTs
     */
    function batchMint(
        address[] calldata recipients,
        string[] calldata uris
    ) external onlyRole(MINTER_ROLE) returns (uint256[] memory) {
        require(
            recipients.length == uris.length,
            "Array length mismatch"
        );

        uint256[] memory tokenIds = new uint256[](recipients.length);
        
        for (uint256 i = 0; i < recipients.length; i++) {
            tokenIds[i] = safeMint(recipients[i], uris[i]);
        }

        return tokenIds;
    }

    /**
     * @dev Get token information
     */
    function getTokenInfo(uint256 tokenId)
        external
        view
        returns (
            address owner,
            address creator,
            string memory uri,
            uint256 mintTime
        )
    {
        require(_exists(tokenId), "Token does not exist");
        
        TokenInfo memory info = tokenInfo[tokenId];
        return (
            ownerOf(tokenId),
            info.creator,
            tokenURI(tokenId),
            info.mintTime
        );
    }

    /**
     * @dev Get all tokens owned by an address
     */
    function tokensOfOwner(address owner)
        external
        view
        returns (uint256[] memory)
    {
        return _ownedTokens[owner];
    }

    /**
     * @dev Pause minting
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause minting
     */
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // The following functions are overrides required by Solidity.

    function _burn(uint256 tokenId)
        internal
        override(ERC721, ERC721URIStorage)
    {
        super._burn(tokenId);
        _resetTokenRoyalty(tokenId);
    }

    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721URIStorage, ERC2981, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function _exists(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }
}
