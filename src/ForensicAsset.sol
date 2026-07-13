// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/**
 * @dev OpenZeppelin Contracts v4.9.0 imports.
 * These are standard, industry-recognized implementations that provide
 * secure, reusable, and audit-compliant contract patterns.
 */
import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ForensicAsset
 * @notice Standard contract for managing cryptographic forensic datasets as semi-fungible tokens.
 * @dev Implements the ERC-1155 standard for multi-token management, ERC-2981 for standard royalty distribution,
 * and OpenZeppelin's Ownable for secure role-based administrative control.
 *
 * Compliance Architecture:
 * - Forensic Document Auditing requires immutable hash anchoring to establish provenance.
 * - This contract anchors SHA-256 baseline hashes of datasets directly onto the ledger.
 * - Integrates ERC-2981 to support programmatic royalty sharing for forensic investigations.
 */
contract ForensicAsset is ERC1155, ERC2981, Ownable {

    /**
     * @notice Maps token ID to its immutable SHA-256 dataset hash.
     * @dev Dataset hash establishes off-chain metadata integrity and protects against retroactive tampering.
     */
    mapping(uint256 => bytes32) public datasetHashes;

    /**
     * @notice Emitted when a new dataset hash is anchored on-chain.
     * @param tokenId The unique identifier of the ERC-1155 token.
     * @param datasetHash The cryptographic SHA-256 fingerprint of the document/dataset.
     */
    event DatasetHashAnchored(uint256 indexed tokenId, bytes32 indexed datasetHash);

    /**
     * @notice Initializes the contract and sets the base metadata URI.
     * @dev Passes the metadata URI to the parent ERC1155 contract and assigns ownership to the deployer.
     * @param uri_ The base metadata URL string pointing to token schema JSON dossiers.
     */
    constructor(string memory uri_) ERC1155(uri_) Ownable(msg.sender) {
        // Ownership is assigned to msg.sender as the default administrative investigator.
    }

    /**
     * @notice Mints a forensic data asset token representing a verified investigation report.
     * @dev Restricted to the contract owner to prevent unauthorized forensic state tampering.
     * @param to The recipient address who receives the minted token.
     * @param id The unique token identifier being minted.
     * @param amount The quantity of tokens to mint (enables semi-fungibility).
     * @param datasetHash The immutable SHA-256 hash of the target forensic dataset.
     * @param royaltyFeeNumerator The royalty percentage expressed in basis points (e.g., 1000 = 10%).
     * @param data Additional arbitrary byte payload for secure off-chain logging or hooks.
     */
    function mint(
        address to,
        uint256 id,
        uint256 amount,
        bytes32 datasetHash,
        uint96 royaltyFeeNumerator,
        bytes calldata data
    ) external onlyOwner {
        // Execute token creation via parent ERC-1155 internal routine
        _mint(to, id, amount, data);

        // Immutable on-chain record mapping of the forensic evidence SHA-256 hash
        datasetHashes[id] = datasetHash;
        emit DatasetHashAnchored(id, datasetHash);

        // Set token royalty parameters dynamically if royalty numerator is specified
        if (royaltyFeeNumerator > 0) {
            _setTokenRoyalty(id, to, royaltyFeeNumerator);
        }
    }

    /**
     * @notice Queries supported interfaces of this smart contract.
     * @dev Overrides ERC1155 and ERC2981 interface support checks to resolve inheritance conflicts.
     * @param interfaceId The interface identifier byte signature to query.
     * @return True if the requested interface is supported, False otherwise.
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
