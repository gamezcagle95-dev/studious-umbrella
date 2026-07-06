// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ProvenanceRegistry
 * @dev Mints unique Data NFTs representing verified intellectual forensic assets.
 * Integrates directly with the core Epiphany Investigative Protocol settlement layer.
 */
contract ProvenanceRegistry is ERC721URIStorage, AccessControl, ReentrancyGuard {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    uint256 public tokenCount;

    // Custom security errors
    error InvalidAddress();

    // Verification logging
    event DataNFTMinted(uint256 indexed tokenId, string ipfsCID, address indexed creator);

    /**
     * @dev Initializes the Data NFT factory.
     * @param _admin The address granted the default admin role.
     */
    constructor(address _admin) ERC721("Epiphany Data Asset", "EDA") {
        if (_admin == address(0)) revert InvalidAddress();
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
    }

    /**
     * @dev Mints a secure token pointer linking directly to a verified off-chain dataset.
     * Can only be called by addresses with the MINTER_ROLE.
     * @param recipient The destination wallet address receiving data token ownership rights.
     * @param ipfsCID The immutable IPFS Content Identifier hash pointing to the raw encrypted data file.
     * @return The unique uint256 ID of the newly minted cryptographic data token.
     */
    function mintDataNFT(address recipient, string calldata ipfsCID)
        external
        nonReentrant
        onlyRole(MINTER_ROLE)
        returns (uint256)
    {
        if (recipient == address(0)) revert InvalidAddress();

        tokenCount++;
        uint256 newTokenId = tokenCount;

        _safeMint(recipient, newTokenId);
        _setTokenURI(newTokenId, ipfsCID);

        emit DataNFTMinted(newTokenId, ipfsCID, recipient);
        return newTokenId;
    }

    /**
     * @dev Overrides supportsInterface to resolve conflicts between ERC721 and AccessControl.
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721URIStorage, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
