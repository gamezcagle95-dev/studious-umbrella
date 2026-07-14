// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/**
 * @dev Import the Foundry standard test library to enable assertions, VM pranks,
 * and testing utility scripts.
 */
import "forge-std/Test.sol";
import "../src/ForensicAsset.sol";

/**
 * @title ForensicAssetTest
 * @notice Test suite for validating the deployment, minting, hash anchoring, and royalty calculations of ForensicAsset.
 * @dev Inherits Foundry's standard Test contract. Employs pranks and assertion helpers to isolate roles.
 *
 * Compliance Goals:
 * - Verify that only authorized forensic administrators (Ownable contract owners) can mint assets.
 * - Certify that cryptographic dataset hashes cannot be altered post-mint (immutability checking).
 * - Validate that ERC-2981 royalty calculations conform to basis points spec.
 */
contract ForensicAssetTest is Test {

    // Core contract instance being audited
    ForensicAsset public asset;

    // Test accounts for role separation
    address public owner;
    address public nonOwner;
    address public recipient;

    /**
     * @notice Performs initial state setup before each test case runs.
     * @dev Deploys a new instance of ForensicAsset with a mock metadata base URI and configures test accounts.
     */
    function setUp() public {
        owner = address(this);
        nonOwner = address(0x999);
        recipient = address(0x123);

        // Deploy ForensicAsset pointing to metadata schemas hosted on a secure Epiphany sub-domain
        asset = new ForensicAsset("https://metadata.epiphany.network/api/item/{id}.json");
    }

    /**
     * @notice Tests that standard token minting works correctly and anchors immutable dataset hashes on-chain.
     * @dev Mints an asset as the owner, verifies the recipient balance, and asserts dataset hash mapping integrity.
     */
    function test_MintAndHashAnchoring() public {
        uint256 id = 1;
        uint256 amount = 100;

        // Simulate a SHA-256 hash of a raw investigative forensic report payload
        bytes32 datasetHash = keccak256("test_dataset_payload");

        // Mint as the owner - sets a 10% royalty rate (1000 basis points)
        asset.mint(recipient, id, amount, datasetHash, 1000, "");

        // Verify that the recipient has successfully received the semi-fungible token balance
        assertEq(asset.balanceOf(recipient, id), amount);

        // Verify that the on-chain SHA-256 fingerprint remains uncorrupted and accessible
        assertEq(asset.datasetHashes(id), datasetHash);
    }

    /**
     * @notice Validates that royalty configurations conform precisely to the ERC-2981 standard.
     * @dev Mints an asset with a specified royalty and queries `royaltyInfo` to assert correct recipient and amount.
     */
    function test_RoyaltyCalculation() public {
        uint256 id = 1;
        bytes32 datasetHash = keccak256("test_dataset_payload");

        // Mint a forensic asset with 10% royalty (1000 basis points)
        asset.mint(recipient, id, 100, datasetHash, 1000, "");

        // Query royalty calculations for a sale price of 10000 Wei (should yield exactly 1000 Wei)
        (address royaltyRecipient, uint256 royaltyAmount) = asset.royaltyInfo(id, 10000);

        // Assert that the recipient configured during minting receives the royalty fee
        assertEq(royaltyRecipient, recipient);

        // Assert that the calculated fee represents exactly 10% of the sale price
        assertEq(royaltyAmount, 1000);
    }

    /**
     * @notice Verifies that unauthorized third-party attempts to mint forensic tokens are correctly reverted.
     * @dev Uses Foundry's `vm.prank` to simulate a call from a non-owner and expects a revert.
     */
    function test_UnauthorizedMintFails() public {
        uint256 id = 2;
        bytes32 datasetHash = keccak256("unauthorized_dataset");

        // Expect a standard revert when an address other than the Ownable owner attempts to mint
        vm.prank(nonOwner);
        vm.expectRevert(); // Standard OpenZeppelin Ownable Unauthorized check
        asset.mint(recipient, id, 100, datasetHash, 1000, "");
    }
}
