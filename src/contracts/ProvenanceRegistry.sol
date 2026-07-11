// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ProvenanceRegistry
 * @dev Mints Data NFTs representing verified forensic assets. 
 * Reconciled: Retains legacy ledger pointer for test compatibility with modern security errors.
 */
contract ProvenanceRegistry is ERC721URIStorage, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    
    uint256 public tokenCount;
    address public legacyLedgerAddress;

    // Custom security errors
    error InvalidAddress();

    event DataNFTMinted(uint256 indexed tokenId, string ipfsCID, address indexed creator);

    /**
     * @param _ledgerAddress Legacy address to ensure existing tests do not break.
     */
    constructor(address _ledgerAddress) ERC721("Epiphany Data Asset", "EDA") {
        if (_ledgerAddress == address(0)) revert InvalidAddress();
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, _ledgerAddress);
        
        legacyLedgerAddress = _ledgerAddress;
    }

    /**
     * @dev Mints a secure token pointer linking to a verified off-chain dataset.
     * @param recipient The wallet address receiving the token.
     * @param ipfsCID The immutable IPFS CID of the encrypted data file.
     * @return The unique uint256 ID of the minted data token.
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
     * @dev Required override for AccessControl and ERC721.
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721ERC721URIStorage, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
