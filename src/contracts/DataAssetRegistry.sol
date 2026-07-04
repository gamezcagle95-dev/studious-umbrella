// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title DataAssetRegistry
 * @dev Handles the purchase of data assets using EIP-712 appraised signatures and EIT tokens.
 */
interface IProvenanceRegistry {
    function mintDataNFT(address recipient, string calldata ipfsCid) external returns (uint256);
}

contract DataAssetRegistry is EIP712, Ownable, ReentrancyGuard {
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

    mapping(address => bool) public isAppraiser;
    mapping(bytes32 => bool) public usedAppraisals;
    mapping(address => mapping(bytes32 => bool)) public accessGrants;
    mapping(bytes32 => string) public assetCids;

    event AssetUnlocked(bytes32 indexed dataHash, address indexed buyer, uint256 price);
    event AppraiserStatusChanged(address indexed appraiser, bool status);

    error InvalidSignature();
    error AppraisalExpired();
    error AppraisalAlreadyUsed();
    error UnauthorizedAppraiser();
    error TransferFailed();

    constructor(address _eitToken, address _provenanceRegistry)
        EIP712("DataAssetRegistry", "1")
        Ownable(msg.sender)
    {
        eitToken = IERC20(_eitToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);
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
     * @param appraisal The appraisal details.
     * @param signature The EIP-712 signature from an authorized appraiser.
     */
    function purchaseAsset(Appraisal calldata appraisal, bytes calldata signature) external nonReentrant {
        if (block.timestamp > appraisal.expiry) revert AppraisalExpired();

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
