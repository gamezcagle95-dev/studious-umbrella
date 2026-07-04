// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ProvenanceRegistry
 * @dev Manages the cryptographic proof of AI interaction datasets and mints Data NFTs.
 */
contract ProvenanceRegistry is ERC721URIStorage, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    uint256 public tokenCount;
    address public legacyLedgerAddress;

    // Emitted when a new dataset hash is anchored/minted
    event DataNFTMinted(uint256 indexed tokenId, string ipfsCID, address indexed creator);

    /**
     * @param _ledgerAddress Legacy address to ensure existing tests do not break.
     */
    constructor(address _ledgerAddress) ERC721("Epiphany Data Asset", "EDA") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);

        _grantRole(MINTER_ROLE, _ledgerAddress);
        legacyLedgerAddress = _ledgerAddress;
    }

    /**
     * @dev Mints a Data NFT representation (Option B / License Token).
     * @param recipient The address receiving the license token.
     * @param ipfsCID The IPFS Content Identifier of the underlying trajectory data.
     */
    function mintDataNFT(address recipient, string calldata ipfsCID)
        external
        onlyRole(MINTER_ROLE)
        returns (uint256)
    {
        tokenCount++;
        uint256 newTokenId = tokenCount;

        _safeMint(recipient, newTokenId);
        _setTokenURI(newTokenId, ipfsCID);

        emit DataNFTMinted(newTokenId, ipfsCID, recipient);
        return newTokenId;
    }

    /**
     * @dev Explicit override for supportsInterface to resolve inheritance conflict.
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
