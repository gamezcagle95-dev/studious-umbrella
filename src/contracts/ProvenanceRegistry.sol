// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

/**
 * @title ProvenanceRegistry
 * @dev Mints unique Data NFTs representing verified intellectual forensic assets.
 * Integrates directly with the core Epiphany Investigative Protocol settlement layer.
 */
contract ProvenanceRegistry is ERC721URIStorage {
    uint256 public tokenCount;
    address public immutable ledgerAddress;

    // Custom security errors
    error OnlyLedgerAllowed();
    error InvalidAddress();

    // Verification logging
    event DataNFTMinted(uint256 indexed tokenId, string ipfsCid, address indexed creator);

    modifier onlyLedger() {
        if (msg.sender != ledgerAddress) revert OnlyLedgerAllowed();
        _;
    }

    /**
     * @dev Initializes the Data NFT factory, locking it to a single financial settlement clearinghouse.
     * @param _ledgerAddress The deployed coordinate of the ProvenanceLedger contract.
     */
    constructor(address _ledgerAddress) ERC721("Epiphany Data Asset", "EDA") {
        if (_ledgerAddress == address(0)) revert InvalidAddress();
        ledgerAddress = _ledgerAddress;
    }

    /**
     * @dev Mints a secure token pointer linking directly to a verified off-chain dataset.
     * Can only be called by the coupled ledger contract to enforce programmatic royalty distribution.
     * @param recipient The destination wallet address receiving data token ownership rights.
     * @param ipfsCid The immutable IPFS Content Identifier hash pointing to the raw encrypted data file.
     * @return The unique uint256 ID of the newly minted cryptographic data token.
     */
    function mintDataNFT(address recipient, string calldata ipfsCid)
        external
        onlyLedger
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
}
