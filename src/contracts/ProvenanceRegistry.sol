// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ProvenanceRegistry
 * @dev Mints unique Data NFTs representing verified intellectual forensic assets.
 * Integrates directly with the core Epiphany Investigative Protocol settlement layer.
 * Updated to support automated linkage and NFT minting via ProvenanceLedger.
 */
contract ProvenanceRegistry is ERC721URIStorage, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    uint256 public tokenCount;

    // Custom security errors
    error InvalidAddress();

    // Verification logging
    event DataNFTMinted(uint256 indexed tokenId, string ipfsCid, address indexed creator);

    /**
     * @dev Initializes the Data NFT factory, locking it to a single financial settlement clearinghouse.
     * @param _ledgerAddress The deployed coordinate of the ProvenanceLedger contract.
     */
    constructor(address _ledgerAddress) ERC721("Epiphany Data Asset", "EDA") {
        if (_ledgerAddress == address(0)) revert InvalidAddress();

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, _ledgerAddress);
    }

    /**
     * @dev Mints a secure token pointer linking directly to a verified off-chain dataset.
     * Can only be called by an address with the MINTER_ROLE.
     * @param recipient The destination wallet address receiving data token ownership rights.
     * @param ipfsCid The immutable IPFS Content Identifier hash pointing to the raw encrypted data file.
     * @return The unique uint256 ID of the newly minted cryptographic data token.
     */
    function mintDataNFT(address recipient, string calldata ipfsCid)
        external
        onlyRole(MINTER_ROLE)
        returns (uint256)
    {
        if (recipient == address(0)) revert InvalidAddress();

        tokenCount++;
        uint256 newTokenId = tokenCount;

        _mint(recipient, newTokenId);
        _setTokenURI(newTokenId, ipfsCid);

        emit DataNFTMinted(newTokenId, ipfsCid, recipient);
        return newTokenId;
    }

    /**
     * @dev Required override for AccessControl and ERC721.
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
