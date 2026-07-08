// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IProvenanceRegistry {
    function mintDataNFT(address recipient, string calldata ipfsCID) external;
}

/**
 * @title DataAssetRegistry
 * @dev Manages the purchasing, unlocking, and anchoring of high-density training data.
 * Settles payments in native EIT tokens and verifies EIP-712 structured appraisals.
 */
contract DataAssetRegistry is AccessControl, EIP712, ReentrancyGuard {
    using ECDSA for bytes32;

    // Roles (Aligned with existing codebase configurations)
    bytes32 public constant SENIOR_INVESTIGATOR_ROLE = keccak256("SENIOR_INVESTIGATOR_ROLE");
    bytes32 public constant APPRAISER_ROLE = keccak256("APPRAISER_ROLE");

    // EIP-712 Struct Type Hash
    bytes32 public constant ASSET_APPRAISAL_TYPEHASH = keccak256(
        "AssetAppraisal(bytes32 assetHash,uint256 price,string ipfsCID,uint256 nonce,uint256 expiry,address creator)"
    );

    // External dependencies
    IERC20 public immutable paymentToken; // Epiphany Intelligence Token (EIT)
    IProvenanceRegistry public immutable provenanceRegistry;

    // Asset state structure
    struct AssetDetails {
        bytes32 assetHash;
        uint256 price;
        string ipfsCID;
        address creator;
        bool registered;
    }

    // Mappings
    mapping(bytes32 => AssetDetails) public registeredAssets;
    mapping(address => mapping(bytes32 => bool)) public accessGrants;
    mapping(bytes32 => bool) public usedNonces; // Prevents appraisal replay attacks

    // Circuit Breaker State Variables
    bool public isPaused;
    uint256 public maxPricePerTokenInEIT; // Sanity limit (maximum allowed EIT per token)
    uint256 public lastPauseTimestamp; // Track when the circuit breaker was triggered

    // Events
    event AssetAppraisalRegistered(
        bytes32 indexed assetHash,
        uint256 price,
        string ipfsCID,
        address indexed creator
    );
    event AssetUnlocked(
        bytes32 indexed assetHash,
        address indexed buyer,
        uint256 pricePaid,
        string ipfsCID
    );
    event CircuitBreakerTriggered(
        bytes32 indexed assetHash,
        uint256 price,
        uint256 estimatedTokens,
        uint256 timestamp
    );

    // EIP-712 Mirror Struct
    struct AssetAppraisal {
        bytes32 assetHash;
        uint256 price;
        string ipfsCID;
        uint256 nonce;
        uint256 expiry;
        address creator;
    }

    modifier whenNotPaused() {
        require(!isPaused, "Circuit Breaker: Contract is currently paused");
        _;
    }

    constructor(
        address _paymentToken,
        address _provenanceRegistry,
        address _seniorInvestigator,
        uint256 _maxPricePerTokenInEIT
    ) EIP712("DataAssetRegistry", "1") {
        require(_paymentToken != address(0), "Invalid payment token");
        require(_provenanceRegistry != address(0), "Invalid registry");
        require(_seniorInvestigator != address(0), "Invalid investigator");

        paymentToken = IERC20(_paymentToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);
        maxPricePerTokenInEIT = _maxPricePerTokenInEIT;

        // Grant default admin and senior investigator roles to the coordinator
        _grantRole(DEFAULT_ADMIN_ROLE, _seniorInvestigator);
        _grantRole(SENIOR_INVESTIGATOR_ROLE, _seniorInvestigator);
    }

    /**
     * @dev Allows an authorized Senior Investigator to manage approved appraisers.
     */
    function authorizeAppraiser(address appraiser) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        _grantRole(APPRAISER_ROLE, appraiser);
    }

    function revokeAppraiser(address appraiser) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        _revokeRole(APPRAISER_ROLE, appraiser);
    }

    /**
     * @dev Admin recovery interface to pause/resume contract after anomalous price spike.
     */
    function setPaused(bool _paused) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        isPaused = _paused;
        if (_paused) {
            lastPauseTimestamp = block.timestamp;
        }
    }

    /**
     * @dev Updates the circuit breaker threshold.
     */
    function setMaxPricePerToken(uint256 _newMax) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        maxPricePerTokenInEIT = _newMax;
    }

    /**
     * @dev Purchases training access to an appraised data asset.
     * Verifies EIP-712 appraisal metrics, transfers EIT tokens, and triggers NFT mint.
     */
    function purchaseAsset(
        AssetAppraisal calldata appraisal,
        bytes calldata signature,
        uint256 estimatedTokens
    ) external whenNotPaused nonReentrant {
        // 1. Cryptographic Verification (EIP-712) - EXECUTE FIRST to prevent DoS
        bytes32 structHash = keccak256(abi.encode(
            ASSET_APPRAISAL_TYPEHASH,
            appraisal.assetHash,
            appraisal.price,
            keccak256(bytes(appraisal.ipfsCID)),
            appraisal.nonce,
            appraisal.expiry,
            appraisal.creator
        ));

        bytes32 digest = _hashTypedDataV4(structHash);
        address recoveredSigner = digest.recover(signature);
        require(hasRole(APPRAISER_ROLE, recoveredSigner), "Invalid signature: Appraiser not authorized");

        // 2. Invariant & Replay Protection Checks
        require(block.timestamp <= appraisal.expiry, "Appraisal signature has expired");

        bytes32 nonceKey = keccak256(abi.encodePacked(appraisal.creator, appraisal.nonce));
        require(!usedNonces[nonceKey], "Appraisal nonce has already been consumed");

        // 3. Dynamic Appraisal Sanity Check (The Circuit Breaker / Kill-Switch)
        if (estimatedTokens > 0) {
            require(estimatedTokens >= 10, "Minimum token count not met");
            uint256 pricePerToken = (appraisal.price * 10**18) / estimatedTokens;
            if (pricePerToken > maxPricePerTokenInEIT) {
                isPaused = true;
                lastPauseTimestamp = block.timestamp;
                emit CircuitBreakerTriggered(
                    appraisal.assetHash,
                    appraisal.price,
                    estimatedTokens,
                    block.timestamp
                );
                revert("Anomaly Detected: Price-per-token exceeds limit. Circuit breaker triggered.");
            }
        }

        // 4. Effects (Checks-Effects-Interactions)
        usedNonces[nonceKey] = true;
        accessGrants[msg.sender][appraisal.assetHash] = true;

        AssetDetails storage asset = registeredAssets[appraisal.assetHash];
        if (!asset.registered) {
            asset.assetHash = appraisal.assetHash;
            asset.price = appraisal.price;
            asset.ipfsCID = appraisal.ipfsCID;
            asset.creator = appraisal.creator;
            asset.registered = true;

            emit AssetAppraisalRegistered(
                appraisal.assetHash,
                appraisal.price,
                appraisal.ipfsCID,
                appraisal.creator
            );
        } else {
            require(asset.price == appraisal.price, "Price mismatch: Asset already registered with a different rate");
        }

        // 5. Interactions (External Calls)
        // Pull EIT ERC-20 tokens from the buyer directly to the creator
        bool success = paymentToken.transferFrom(msg.sender, appraisal.creator, appraisal.price);
        require(success, "EIT token settlement transfer failed");

        // Mint Data NFT License
        provenanceRegistry.mintDataNFT(msg.sender, appraisal.ipfsCID);

        emit AssetUnlocked(
            appraisal.assetHash,
            msg.sender,
            appraisal.price,
            appraisal.ipfsCID
        );
    }
}
