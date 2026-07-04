// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title DataAssetRegistry
 * @dev Handles the purchase of data assets using EIP-712 appraised signatures and EIT tokens.
 * Includes an on-chain circuit breaker and price sanity boundaries.
 */
interface IProvenanceRegistry {
    function mintDataNFT(address recipient, string calldata ipfsCid) external returns (uint256);
}

contract DataAssetRegistry is EIP712, Ownable, ReentrancyGuard, Pausable {
    using ECDSA for bytes32;

    struct Appraisal {
        bytes32 dataHash;
        uint256 price;
        string ipfsCID;
        uint256 nonce;
        uint256 expiry;
        address creator;
    }

    bytes32 public constant APPRAISAL_TYPEHASH = keccak256(
        "Appraisal(bytes32 dataHash,uint256 price,string ipfsCID,uint256 nonce,uint256 expiry,address creator)"
    );

    IERC20 public immutable eitToken;
    IProvenanceRegistry public immutable provenanceRegistry;

    // Sanity boundaries (Circuit Breaker)
    uint256 public maxPricePerAsset = 1_000_000 * 10**18; // Default 1M EIT tokens

    mapping(address => bool) public isAppraiser;
    mapping(bytes32 => bool) public usedAppraisals;
    mapping(address => mapping(bytes32 => bool)) public accessGrants;
    mapping(bytes32 => string) public assetCids;

    event AssetUnlocked(bytes32 indexed dataHash, address indexed buyer, uint256 price);
    event AppraiserStatusChanged(address indexed appraiser, bool status);
    event MaxPriceUpdated(uint256 oldMax, uint256 newMax);

    error InvalidSignature();
    error AppraisalExpired();
    error AppraisalAlreadyUsed();
    error UnauthorizedAppraiser();
    error TransferFailed();
    error PriceExceedsSanityBoundary(uint256 requested, uint256 maxAllowed);

    constructor(address _eitToken, address _provenanceRegistry)
        EIP712("DataAssetRegistry", "1")
        Ownable(msg.sender)
    {
        eitToken = IERC20(_eitToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);
    }

    /**
     * @dev Emergency stop: Pauses all purchase transactions.
     */
    function setPaused(bool status) external onlyOwner {
        if (status) {
            _pause();
        } else {
            _unpause();
        }
    }

    /**
     * @dev Updates the global maximum price allowed per asset appraisal.
     */
    function setMaxPricePerAsset(uint256 _maxPrice) external onlyOwner {
        emit MaxPriceUpdated(maxPricePerAsset, _maxPrice);
        maxPricePerAsset = _maxPrice;
    }

    /**
     * @dev Authorizes or revokes an appraiser address.
     */
    function setAppraiser(address appraiser, bool status) external onlyOwner {
        isAppraiser[appraiser] = status;
        emit AppraiserStatusChanged(appraiser, status);
    }

    /**
     * @dev Unlocks a data asset by verifying an appraiser's signature and processing payment.
     * Enforces the on-chain circuit breaker (price sanity check and pause state).
     * @param appraisal The appraisal details.
     * @param signature The EIP-712 signature from an authorized appraiser.
     */
    function purchaseAsset(Appraisal calldata appraisal, bytes calldata signature)
        external
        nonReentrant
        whenNotPaused
    {
        if (block.timestamp > appraisal.expiry) revert AppraisalExpired();

        // Circuit Breaker: Enforce price sanity boundary
        if (appraisal.price > maxPricePerAsset) {
            revert PriceExceedsSanityBoundary(appraisal.price, maxPricePerAsset);
        }

        bytes32 structHash = keccak256(abi.encode(
            APPRAISAL_TYPEHASH,
            appraisal.dataHash,
            appraisal.price,
            keccak256(bytes(appraisal.ipfsCID)),
            appraisal.nonce,
            appraisal.expiry,
            appraisal.creator
        ));

        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = hash.recover(signature);

        if (!isAppraiser[signer]) revert UnauthorizedAppraiser();

        // Unique ID for the appraisal to prevent replay attacks
        bytes32 appraisalId = keccak256(abi.encode(appraisal.dataHash, appraisal.nonce));
        if (usedAppraisals[appraisalId]) revert AppraisalAlreadyUsed();
        usedAppraisals[appraisalId] = true;

        // Execute payment: Buyer -> Creator
        if (!eitToken.transferFrom(msg.sender, appraisal.creator, appraisal.price)) {
            revert TransferFailed();
        }

        // Grant access and store metadata
        accessGrants[msg.sender][appraisal.dataHash] = true;
        assetCids[appraisal.dataHash] = appraisal.ipfsCID;

        // Mint Data NFT via ProvenanceRegistry
        provenanceRegistry.mintDataNFT(msg.sender, appraisal.ipfsCID);

        emit AssetUnlocked(appraisal.dataHash, msg.sender, appraisal.price);
    }
}
