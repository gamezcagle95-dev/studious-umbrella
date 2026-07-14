// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import "../src/ForensicAsset.sol";

contract ForensicAssetTest is Test {
    ForensicAsset public asset;
    address public owner;
    address public nonOwner;
    address public recipient;

    function setUp() public {
        // Assign roles to standard test entities to ensure zero-PII security
        owner = address(this);
        nonOwner = address(0x999);
        recipient = address(0x123);
        // Initialize the ForensicAsset ERC-1155 contract with standard metadata URI
        asset = new ForensicAsset("https://metadata.epiphany.network/api/item/{id}.json");
    }

    /**
     * @dev Verifies that the owner can successfully mint tokens and anchor
     * the immutable SHA-256 hash representation of the forensic dataset.
     */
    function test_MintAndHashAnchoring() public {
        uint256 id = 1;
        uint256 amount = 100;
        bytes32 datasetHash = keccak256("test_dataset_payload");

        // Mint asset tokens as owner, configured with 10% royalty (1000 bps)
        asset.mint(recipient, id, amount, datasetHash, 1000, "");

        // Assert recipient balance matches expected minted allocation amount
        assertEq(asset.balanceOf(recipient, id), amount);

        // Assert dataset hashes map deterministically to ensure immutable audit trails
        assertEq(asset.datasetHashes(id), datasetHash);
    }

    /**
     * @dev Verifies the correctness of the EIP-2981 royalty calculations.
     * Computes the basis points payout for secondary market clearinghouse routing.
     */
    function test_RoyaltyCalculation() public {
        uint256 id = 1;
        bytes32 datasetHash = keccak256("test_dataset_payload");

        // Mint token with 10% royalty mapping configured during mint function execution
        asset.mint(recipient, id, 100, datasetHash, 1000, "");

        // Programmatically query ERC-2981 royaltyInfo for a mock sale of 10,000 Wei
        (address royaltyRecipient, uint256 royaltyAmount) = asset.royaltyInfo(id, 10000);

        // Assert royalty recipient is correctly routed to token creator
        assertEq(royaltyRecipient, recipient);
        // Assert royalty payment matches expected 10% payout of 1,000 Wei
        assertEq(royaltyAmount, 1000);
    }

    /**
     * @dev Validates security boundary: ensures non-owner accounts cannot
     * invoke restricted mint operations, raising standard Ownable exceptions.
     */
    function test_UnauthorizedMintFails() public {
        uint256 id = 2;
        bytes32 datasetHash = keccak256("unauthorized_dataset");

        // Set message sender context to unauthorized non-owner
        vm.prank(nonOwner);
        // Assert that execution reverts cleanly due to standard ownership guards
        vm.expectRevert();
        asset.mint(recipient, id, 100, datasetHash, 1000, "");
    }
}
