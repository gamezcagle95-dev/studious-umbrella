// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ProvenanceRegistry
 * @dev Manages the cryptographic proof of AI interaction datasets and mints Data NFTs.
 */
contract ProvenanceRegistry is AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    // Backward-compatibility hook for legacy ledger integrations
    address public legacyLedgerAddress;

    // Emitted when a new dataset hash is anchored/minted
    event DataNFTMinted(address indexed recipient, string ipfsCID, address indexed creator);

    /**
     * @param _ledgerAddress Legacy address to ensure existing tests do not break.
     */
    constructor(address _ledgerAddress) {
        // Grant the deployer the default admin and minter roles
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);

        // Grant the minter role to the legacy ledger address for backward compatibility
        _grantRole(MINTER_ROLE, _ledgerAddress);
        legacyLedgerAddress = _ledgerAddress;
    }

    /**
     * @dev Mints a Data NFT representation (Option B / License Token).
     * @param recipient The address receiving the license token.
     * @param ipfsCID The IPFS Content Identifier of the underlying trajectory data.
     */
    function mintDataNFT(address recipient, string calldata ipfsCID) external onlyRole(MINTER_ROLE) {
        emit DataNFTMinted(recipient, ipfsCID, msg.sender);
    }
}
