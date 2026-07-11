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
        owner = address(this);
        nonOwner = address(0x999);
        recipient = address(0x123);
        asset = new ForensicAsset("https://metadata.epiphany.network/api/item/{id}.json");
    }

    function test_MintAndHashAnchoring() public {
        uint256 id = 1;
        uint256 amount = 100;
        bytes32 datasetHash = keccak256("test_dataset_payload");

        // Mint as owner
        asset.mint(recipient, id, amount, datasetHash, 1000, ""); // 10% royalty

        // Verify balance
        assertEq(asset.balanceOf(recipient, id), amount);

        // Verify dataset hash mapping integrity (immutability check)
        assertEq(asset.datasetHashes(id), datasetHash);
    }

    function test_RoyaltyCalculation() public {
        uint256 id = 1;
        bytes32 datasetHash = keccak256("test_dataset_payload");

        // Mint with 10% royalty (1000 basis points)
        asset.mint(recipient, id, 100, datasetHash, 1000, "");

        // Query royalty for sale of 10000 Wei (should be 1000 Wei)
        (address royaltyRecipient, uint256 royaltyAmount) = asset.royaltyInfo(id, 10000);

        assertEq(royaltyRecipient, recipient);
        assertEq(royaltyAmount, 1000);
    }

    function test_UnauthorizedMintFails() public {
        uint256 id = 2;
        bytes32 datasetHash = keccak256("unauthorized_dataset");

        // Expect revert when non-owner tries to mint
        vm.prank(nonOwner);
        vm.expectRevert(); // Standard Ownable Unauthorized check
        asset.mint(recipient, id, 100, datasetHash, 1000, "");
    }
}
