// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IProvenanceRegistry {
    function mintDataNFT(address recipient, string calldata ipfsCID) external returns (uint256);
}

/**
 * @title DataAssetRegistry
 * @dev Handles EIP-712 based appraisal verification and data asset settlement.
 */
contract DataAssetRegistry is EIP712, ReentrancyGuard, Pausable, Ownable {
    using ECDSA for bytes32;

    IERC20 public immutable eitToken;
    IProvenanceRegistry public immutable provenanceRegistry;

    bytes32 private constant APPRAISAL_TYPEHASH = keccak256(
        "Appraisal(bytes32 dataHash,uint256 price,string ipfsCID,uint256 nonce,uint256 expiry,address creator)"
    );

    mapping(address => bool) public isAppraiser;
    mapping(uint256 => bool) public usedNonces;
    uint256 public maxPricePerAsset = 100000 * 10**18; // 100k EIT limit

    error InvalidSignature();
    error AppraisalExpired();
    error NonceAlreadyUsed();
    error PriceExceedsLimit();
    error UnauthorizedAppraiser();
    error InvalidAddress();

    event AssetPurchased(
        bytes32 indexed dataHash,
        address indexed buyer,
        address indexed creator,
        uint256 price,
        uint256 tokenId
    );
    event AppraiserStatusChanged(address indexed appraiser, bool allowed);
    event MaxPriceUpdated(uint256 newMaxPrice);

    constructor(address _eitToken, address _provenanceRegistry)
        EIP712("DataAssetRegistry", "1")
        Ownable(msg.sender)
    {
        if (_eitToken == address(0) || _provenanceRegistry == address(0)) revert InvalidAddress();
        eitToken = IERC20(_eitToken);
        provenanceRegistry = IProvenanceRegistry(_provenanceRegistry);
    }

    function setAppraiser(address appraiser, bool allowed) external onlyOwner {
        if (appraiser == address(0)) revert InvalidAddress();
        isAppraiser[appraiser] = allowed;
        emit AppraiserStatusChanged(appraiser, allowed);
    }

    function setMaxPrice(uint256 newMax) external onlyOwner {
        maxPricePerAsset = newMax;
        emit MaxPriceUpdated(newMax);
    }

    function purchaseAsset(
        bytes32 dataHash,
        uint256 price,
        string calldata ipfsCID,
        uint256 nonce,
        uint256 expiry,
        address creator,
        bytes calldata signature
    ) external nonReentrant whenNotPaused {
        if (block.timestamp > expiry) revert AppraisalExpired();
        if (usedNonces[nonce]) revert NonceAlreadyUsed();
        if (price > maxPricePerAsset) revert PriceExceedsLimit();
        if (creator == address(0)) revert InvalidAddress();

        bytes32 structHash = keccak256(
            abi.encode(APPRAISAL_TYPEHASH, dataHash, price, keccak256(bytes(ipfsCID)), nonce, expiry, creator)
        );
        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = hash.recover(signature);

        if (!isAppraiser[signer]) revert UnauthorizedAppraiser();

        usedNonces[nonce] = true;

        // Execute settlement: Transfer EIT from buyer (msg.sender) to creator
        bool success = eitToken.transferFrom(msg.sender, creator, price);
        require(success, "EIT transfer failed");

        // Mint Data NFT to the buyer
        uint256 tokenId = provenanceRegistry.mintDataNFT(msg.sender, ipfsCID);

        emit AssetPurchased(dataHash, msg.sender, creator, price, tokenId);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}
