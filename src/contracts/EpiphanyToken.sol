// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title EpiphanyToken
 * @dev Standard ERC-20 token contract to act as the standard paymentToken for decentralized asset licensing.
 * This contract replaces the legacy forensic bounty ledger and focuses purely on standard token transfers.
 *
 * Requirements:
 * - Decoupled from forensic dependencies and reporting mechanisms.
 * - Provides high-throughput standard EIP-20 transactions compliant with Monad.
 */
contract EpiphanyToken is ERC20, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    /**
     * @dev Constructor that mints an initial supply to the creator and sets up AccessControl.
     * @param initialOwner The address that gets initial administrative control and roles.
     */
    constructor(address initialOwner) ERC20("Epiphany Intelligence Token", "EIT") {
        require(initialOwner != address(0), "Invalid owner address");
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
        _grantRole(MINTER_ROLE, initialOwner);
        _mint(initialOwner, 1_000_000 * 10**decimals());
    }

    /**
     * @dev Mint new EIT tokens. Restricted to MINTER_ROLE.
     * @param to The address receiving the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }
}
