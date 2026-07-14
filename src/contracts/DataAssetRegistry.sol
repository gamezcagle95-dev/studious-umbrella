// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @dev Interface to trigger our secure cryptographic anchor.
 */
interface IProvenanceRegistry {
    function mintDataNFT(address recipient, string calldata ipfsCID) external returns (uint256);
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
    IProvenanceRegistry public immutable provenanceRegistry; // Data NFT Factory

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

    // EIP-712 Mirror Struct
    struct AssetAppraisal {
        bytes32 assetHash;
        uint256 price;
        string ipfsCID;
        uint256 nonce;
        uint256 expiry;
        address creator;
    }

    /**
     * @dev Initializes the DataAssetRegistry with necessary dependencies.
     * @param _paymentToken The ERC20 token used for payments.
     * @param _provenanceRegistry The registry for minting Data NFTs.
     * @param _seniorInvestigator The address granted administrative roles.
     */
    constructor(
        address _paymentToken,
        address _provenanceRegistry,
        address _seniorInvestigator
    ) EIP712("DataAssetRegistry", "1") {
        require(_paymentToken != address(0), "Invalid payment token");
        require(_provenanceRegistry != address(0), "Invalid registry");
        require(_seniorInvestigator != address(0), "Invalid investigator");

        paymentToken = IERC20(_paymentToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);

        // Grant default admin and senior investigator roles to the coordinator
        _grantRole(DEFAULT_ADMIN_ROLE, _seniorInvestigator);
        _grantRole(SENIOR_INVESTIGATOR_ROLE, _seniorInvestigator);
    }

    /**
     * @dev Allows an authorized Senior Investigator to manage approved appraisers.
     * @param appraiser The address to authorize.
     */
    function authorizeAppraiser(address appraiser) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        _grantRole(APPRAISER_ROLE, appraiser);
    }

    /**
     * @dev Allows an authorized Senior Investigator to revoke approved appraisers.
     * @param appraiser The address to revoke.
     */
    function revokeAppraiser(address appraiser) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        _revokeRole(APPRAISER_ROLE, appraiser);
    }

    /**
     * @dev Purchases training access to an appraised data asset.
     * Verifies EIP-712 appraisal metrics, transfers EIT tokens, and anchors the hash.
     * @param appraisal The appraisal details including asset hash, price, and creator.
     * @param signature The appraiser's signature verifying the appraisal.
     */
    function purchaseAsset(
        AssetAppraisal calldata appraisal,
        bytes calldata signature
    ) external nonReentrant {
        // 1. Invariant & Replay Protection Checks
        require(block.timestamp <= appraisal.expiry, "Appraisal signature has expired");

        bytes32 nonceKey = keccak256(abi.encodePacked(appraisal.creator, appraisal.nonce));
        require(!usedNonces[nonceKey], "Appraisal nonce has already been consumed");
        usedNonces[nonceKey] = true;

// Move the mintDataNFT call AFTER the transferFrom, and restructure:

// 3. Register Asset state (no external calls yet)
AssetDetails storage asset = registeredAssets[appraisal.assetHash];
bool isNew = !asset.registered;
if (isNew) {
    asset.assetHash = appraisal.assetHash;
    asset.price     = appraisal.price;
    asset.ipfsCID   = appraisal.ipfsCID;
    asset.creator   = appraisal.creator;
    asset.registered = true;
} else {
    require(asset.price == appraisal.price, "Price mismatch");
}

// 4. Grant access state (no external calls yet)
accessGrants[msg.sender][appraisal.assetHash] = true;

// 5. Token settlement (external call #1)
bool success = paymentToken.transferFrom(msg.sender, appraisal.creator, appraisal.price);
require(success, "EIT token settlement transfer failed");

// 6. Mint NFT only on first purchase (external call #2 — last)
if (isNew) {
    provenanceRegistry.mintDataNFT(msg.sender, appraisal.ipfsCID);
    emit AssetAppraisalRegistered(appraisal.assetHash, appraisal.price, appraisal.ipfsCID, appraisal.creator);
}

emit AssetUnlocked(appraisal.assetHash, msg.sender, appraisal.price, appraisal.ipfsCID);
        // Note: For dynamically sized string (ipfsCID), we hash it on-chain per EIP-712 standard
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

        // 3. Register Asset (Run initial anchoring if first-time purchase)
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
            // Confirm the pricing parameters have not been altered
            require(asset.price == appraisal.price, "Price mismatch: Asset already registered with a different rate");
        }

        // 4. Grant API/Query Access to Buyer (Internal state update before external calls)
        accessGrants[msg.sender][appraisal.assetHash] = true;

        // 5. External Interactions
        // Trigger the minting of the Data NFT license directly to the buyer
        provenanceRegistry.mintDataNFT(msg.sender, appraisal.ipfsCID);

        // Transfers EIT tokens from the buyer to the verified creator
        bool success = paymentToken.transferFrom(msg.sender, appraisal.creator, appraisal.price);
        require(success, "EIT token settlement transfer failed");

        emit AssetUnlocked(
            appraisal.assetHash,
            msg.sender,
            appraisal.price,
            appraisal.ipfsCID
        );
    }
}
