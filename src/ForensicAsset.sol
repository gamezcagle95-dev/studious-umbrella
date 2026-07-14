// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ForensicAsset
 * @dev Implements ERC-1155 with SHA-256 hash mapping and ERC-2981 royalties.
 */
contract ForensicAsset is ERC1155, ERC2981, Ownable {
    mapping(uint256 => bytes32) public datasetHashes;

    event DatasetHashAnchored(uint256 indexed tokenId, bytes32 indexed datasetHash);

    constructor(string memory uri_) ERC1155(uri_) Ownable(msg.sender) {}

    /**
     * @dev Mints a forensic data asset token.
     * @param to Recipient address.
     * @param id Token ID.
     * @param amount Amount to mint.
     * @param datasetHash The immutable SHA-256 hash of the forensic dataset.
     * @param royaltyFeeNumerator Royalty percentage in basis points (e.g. 1000 = 10%).
     * @param data Optional extra data.
     */
    function mint(
        address to,
        uint256 id,
        uint256 amount,
        bytes32 datasetHash,
        uint96 royaltyFeeNumerator,
        bytes calldata data
    ) external onlyOwner {
        _mint(to, id, amount, data);

        datasetHashes[id] = datasetHash;
        emit DatasetHashAnchored(id, datasetHash);

        if (royaltyFeeNumerator > 0) {
            _setTokenRoyalty(id, to, royaltyFeeNumerator);
        }
    }

    /**
     * @dev Required override to resolve interface conflicts.
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
