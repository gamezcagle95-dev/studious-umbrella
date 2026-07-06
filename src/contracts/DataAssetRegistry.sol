// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

/**
 * @file DataAssetRegistry.sol
 * @dev Manages the purchasing and registration of forensic data assets.
 * Implements EIP-712 for verifiable off-chain appraisals.
 */

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";

interface IProvenanceRegistry {
    /**
     * @dev Mints a Data NFT for a verified asset.
     */
    function mintDataNFT(address recipient, string calldata ipfsCID) external returns (uint256);
}

/**
 * @title DataAssetRegistry
 * @dev Core registry for data asset purchases with circuit breaker protection.
 */
contract DataAssetRegistry is AccessControl, Pausable, ReentrancyGuard, EIP712 {
    using ECDSA for bytes32;

    bytes32 public constant APPRAISER_ROLE = keccak256("APPRAISER_ROLE");
    bytes32 public constant GOVERNOR_ROLE = keccak256("GOVERNOR_ROLE");

    IERC20 public immutable eitToken;
    IProvenanceRegistry public immutable provenanceRegistry;

    uint256 public maxPricePerTokenInEIT;

    /**
     * @dev Structured appraisal data for EIP-712 signing.
     */
    struct Appraisal {
        bytes32 assetHash;
        uint256 price;
        string ipfsCID;
        uint256 nonce;
        uint256 expiry;
        address creator;
    }

    bytes32 private constant APPRAISAL_TYPEHASH = keccak256(
        "AssetAppraisal(bytes32 assetHash,uint256 price,string ipfsCID,uint256 nonce,uint256 expiry,address creator)"
    );

    mapping(bytes32 => bool) public assetRegistered;
    mapping(address => mapping(bytes32 => bool)) public accessGrants;
    mapping(uint256 => bool) public usedNonces;

    event AssetPurchased(bytes32 indexed assetHash, address indexed buyer, uint256 price);
    event AppraiserStatusChanged(address indexed appraiser, bool status);
    event MaxPriceUpdated(uint256 newMaxPrice);

    /**
     * @dev Initializes the registry with token and registry dependencies.
     */
    constructor(address _eitToken, address _provenanceRegistry)
        EIP712("DataAssetRegistry", "1")
    {
        if (_eitToken == address(0) || _provenanceRegistry == address(0)) revert("Invalid address");
        eitToken = IERC20(_eitToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(GOVERNOR_ROLE, msg.sender);

        maxPricePerTokenInEIT = 5000 * 10**18; // Default circuit breaker at 5000 EIT
    }

    /**
     * @dev Authorizes or revokes an appraiser address.
     */
    function setAppraiser(address appraiser, bool status) external onlyRole(GOVERNOR_ROLE) {
        if (status) {
            _grantRole(APPRAISER_ROLE, appraiser);
        } else {
            _revokeRole(APPRAISER_ROLE, appraiser);
        }
        emit AppraiserStatusChanged(appraiser, status);
    }

    /**
     * @dev Updates the circuit breaker maximum price.
     */
    function setMaxPricePerAsset(uint256 _maxPrice) external onlyRole(GOVERNOR_ROLE) {
        maxPricePerTokenInEIT = _maxPrice;
        emit MaxPriceUpdated(_maxPrice);
    }

    /**
     * @dev Executes a purchase of a forensic data asset using a verified appraisal signature.
     */
    function purchaseAsset(Appraisal calldata appraisal, bytes calldata signature)
        external
        whenNotPaused
        nonReentrant
    {
        if (block.timestamp > appraisal.expiry) revert("Appraisal expired");
        if (usedNonces[appraisal.nonce]) revert("Nonce already used");
        if (appraisal.price > maxPricePerTokenInEIT) revert("Price exceeds circuit breaker");

        bytes32 structHash = keccak256(abi.encode(
            APPRAISAL_TYPEHASH,
            appraisal.assetHash,
            appraisal.price,
            keccak256(bytes(appraisal.ipfsCID)),
            appraisal.nonce,
            appraisal.expiry,
            appraisal.creator
        ));

        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = hash.recover(signature);

        if (!hasRole(APPRAISER_ROLE, signer)) revert("Invalid appraiser signature");

        usedNonces[appraisal.nonce] = true;
        accessGrants[msg.sender][appraisal.assetHash] = true;

        // CEI: Interactions
        require(eitToken.transferFrom(msg.sender, appraisal.creator, appraisal.price), "Payment failed");

        provenanceRegistry.mintDataNFT(msg.sender, appraisal.ipfsCID);

        emit AssetPurchased(appraisal.assetHash, msg.sender, appraisal.price);
    }

    /**
     * @dev Pauses the registry.
     */
    function pause() external onlyRole(GOVERNOR_ROLE) {
        _pause();
    }

    /**
     * @dev Unpauses the registry.
     */
    function unpause() external onlyRole(GOVERNOR_ROLE) {
        _unpause();
    }
}
