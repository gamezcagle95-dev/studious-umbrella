// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

interface IProvenanceRegistry {
    function mintDataNFT(address recipient, string calldata ipfsCID) external returns (uint256);
}

contract DataAssetRegistry is AccessControl, EIP712, ReentrancyGuard, Pausable {
    using ECDSA for bytes32;

    bytes32 public constant SENIOR_INVESTIGATOR_ROLE = keccak256("SENIOR_INVESTIGATOR_ROLE");
    bytes32 public constant APPRAISER_ROLE = keccak256("APPRAISER_ROLE");

    bytes32 public constant ASSET_APPRAISAL_TYPEHASH = keccak256(
        "AssetAppraisal(bytes32 assetHash,uint256 price,uint256 estimatedTokens,string ipfsCID,uint256 nonce,uint256 expiry,address creator)"
    );

    IERC20 public immutable paymentToken;
    IProvenanceRegistry public immutable provenanceRegistry;
    uint256 public maxPricePerTokenInEIT;

    struct AssetAppraisal {
        bytes32 assetHash;
        uint256 price;
        uint256 estimatedTokens;
        string ipfsCID;
        uint256 nonce;
        uint256 expiry;
        address creator;
    }

    mapping(bytes32 => bool) public usedNonces;
    mapping(address => mapping(bytes32 => bool)) public accessGrants;
    bool private _anomalyDetected;

    event AssetUnlocked(bytes32 indexed assetHash, address indexed buyer, uint256 price, string ipfsCID);
    event CircuitBreakerTriggered(bytes32 indexed assetHash, uint256 price, uint256 estimatedTokens);

    constructor(
        address _paymentToken,
        address _provenanceRegistry,
        address _seniorInvestigator,
        uint256 _maxPricePerTokenInEIT
    ) EIP712("DataAssetRegistry", "1") {
        paymentToken = IERC20(_paymentToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);
        maxPricePerTokenInEIT = _maxPricePerTokenInEIT;
        _grantRole(DEFAULT_ADMIN_ROLE, _seniorInvestigator);
        _grantRole(SENIOR_INVESTIGATOR_ROLE, _seniorInvestigator);
    }

    function setPaused(bool _paused) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        _paused ? _pause() : _unpause();
    }

    function setMaxPricePerAsset(uint256 _maxPricePerAsset) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        maxPricePerTokenInEIT = _maxPricePerAsset;
    }

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

        if (appraisal.estimatedTokens > 0) {
            uint256 pricePerToken = (appraisal.price * 10**18) / appraisal.estimatedTokens;
            if (pricePerToken > maxPricePerTokenInEIT) {
                if (!_anomalyDetected) {
                    _anomalyDetected = true;
                    _pause();
                    emit CircuitBreakerTriggered(appraisal.assetHash, appraisal.price, appraisal.estimatedTokens);
                }
                return;
            }
        }

        require(paymentToken.transferFrom(msg.sender, appraisal.creator, appraisal.price), "Transfer Failed");
        provenanceRegistry.mintDataNFT(msg.sender, appraisal.ipfsCID);
        
        accessGrants[msg.sender][appraisal.assetHash] = true;
        emit AssetUnlocked(appraisal.assetHash, msg.sender, appraisal.price, appraisal.ipfsCID);
    }
}
