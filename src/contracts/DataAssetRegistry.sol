// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title IProvenanceRegistry
 * @dev Interface for interacting with the ProvenanceRegistry smart contract to trigger programmatic minting of Data NFTs.
 */
interface IProvenanceRegistry {
    /**
     * @dev Triggers programmatic minting of an ERC-721 token representing a data license.
     * @param recipient The buyer's address.
     * @param ipfsCID The immutable IPFS CID of the encrypted dataset.
     */
    function mintDataNFT(address recipient, string calldata ipfsCID) external returns (uint256);
}

/**
 * @title DataAssetRegistry
 * @dev Core settlement and access management registry for high-throughput data licensing.
 * Streamlined to handle direct Appraise-Purchase-Mint interactions without forensic report anchoring logic.
 */
contract DataAssetRegistry is AccessControl, EIP712, ReentrancyGuard, Pausable {
    using ECDSA for bytes32;

    // Roles and permissions management
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant APPRAISER_ROLE = keccak256("APPRAISER_ROLE");

    // EIP-712 Structured Appraisal Typehash
    bytes32 public constant ASSET_APPRAISAL_TYPEHASH = keccak256(
        "AssetAppraisal(bytes32 assetHash,uint256 price,uint256 estimatedTokens,string ipfsCID,uint256 nonce,uint256 expiry,address creator)"
    );

    // Immutable components for payment settlement and license minting
    IERC20 public immutable paymentToken;
    IProvenanceRegistry public immutable provenanceRegistry;

    // On-chain circuit breaker parameters
    uint256 public maxPricePerTokenInEIT;

    /**
     * @dev Structured payload representing a cryptographically locked data asset appraisal.
     */
    struct AssetAppraisal {
        bytes32 assetHash;        // SHA-256 or Keccak-256 reference hash of the dataset
        uint256 price;            // Settlement price in standard payment token (EIT) units
        uint256 estimatedTokens;  // Estimated token count for valuation validation
        string ipfsCID;           // IPFS CID containing the secure dataset index
        uint256 nonce;            // Cryptographic nonce to prevent transaction replay
        uint256 expiry;           // Expiry timestamp of the appraisal
        address creator;          // Creator/recipient of the royalty/purchase settlement
    }

    // Mapping to track used nonces and prevent replay attacks
    mapping(bytes32 => bool) public usedNonces;

    // Mapping to manage access grants for buyers
    mapping(address => mapping(bytes32 => bool)) public accessGrants;

    // Operational events
    event AssetUnlocked(bytes32 indexed assetHash, address indexed buyer, uint256 price, string ipfsCID);
    event CircuitBreakerTriggered(bytes32 indexed assetHash, uint256 price, uint256 estimatedTokens);

    /**
     * @dev Constructor to initialize the contract with core dependencies and the circuit breaker threshold.
     * @param _paymentToken The ERC-20 payment token address used for settlements.
     * @param _provenanceRegistry The ProvenanceRegistry contract address for minting Data NFTs.
     * @param _admin The administrative account address managing thresholds and Appraisers.
     * @param _maxPricePerTokenInEIT The circuit breaker threshold price per estimated token in EIT.
     */
    constructor(
        address _paymentToken,
        address _provenanceRegistry,
        address _admin,
        uint256 _maxPricePerTokenInEIT
    ) EIP712("DataAssetRegistry", "1") {
        require(_paymentToken != address(0), "Invalid payment token");
        require(_provenanceRegistry != address(0), "Invalid registry");
        require(_admin != address(0), "Invalid admin");

        paymentToken = IERC20(_paymentToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);
        maxPricePerTokenInEIT = _maxPricePerTokenInEIT;

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
    }

    /**
     * @dev Pauses or unpauses contract interactions. Restricted to ADMIN_ROLE.
     * @param _paused True to pause operations; false to unpause.
     */
    function setPaused(bool _paused) external onlyRole(ADMIN_ROLE) {
        _paused ? _pause() : _unpause();
    }

    /**
     * @dev Purchases access to a data asset, settlements payment, and mints a licensing Data NFT.
     * Performs EIP-712 signature verification, replay checks, and circuit-breaker verification.
     * @param appraisal The structured asset appraisal payload.
     * @param signature The cryptographic signature signed by an authorized Appraiser.
     */
    function purchaseAsset(AssetAppraisal calldata appraisal, bytes calldata signature)
        external
        nonReentrant
        whenNotPaused
    {
        require(block.timestamp <= appraisal.expiry, "Expired");
        bytes32 nonceKey = keccak256(abi.encodePacked(appraisal.creator, appraisal.nonce));
        require(!usedNonces[nonceKey], "Replay");
        usedNonces[nonceKey] = true;

        bytes32 structHash = keccak256(abi.encode(
            ASSET_APPRAISAL_TYPEHASH,
            appraisal.assetHash,
            appraisal.price,
            appraisal.estimatedTokens,
            keccak256(bytes(appraisal.ipfsCID)),
            appraisal.nonce,
            appraisal.expiry,
            appraisal.creator
        ));

        address recoveredSigner = _hashTypedDataV4(structHash).recover(signature);
        require(hasRole(APPRAISER_ROLE, recoveredSigner), "Unauthorized Appraiser");

        // Circuit breaker check
        if (appraisal.estimatedTokens > 0) {
            uint256 pricePerToken = (appraisal.price * 10**18) / appraisal.estimatedTokens;
            if (pricePerToken > maxPricePerTokenInEIT) {
                _pause();
                emit CircuitBreakerTriggered(appraisal.assetHash, appraisal.price, appraisal.estimatedTokens);
                return;
            }
        }

        // Token Settlement
        require(paymentToken.transferFrom(msg.sender, appraisal.creator, appraisal.price), "Transfer Failed");

        // Programmatic Minting
        provenanceRegistry.mintDataNFT(msg.sender, appraisal.ipfsCID);
        
        // Grant digital access
        accessGrants[msg.sender][appraisal.assetHash] = true;
        emit AssetUnlocked(appraisal.assetHash, msg.sender, appraisal.price, appraisal.ipfsCID);
    }
}
