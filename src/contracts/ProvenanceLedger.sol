// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ProvenanceLedger
 * @dev Core settlement layer for the Epiphany Investigative Protocol.
 * Handles intelligence anchoring, bounty distribution, and incentive alignment.
 */
contract ProvenanceLedger is ERC20, ERC20Permit, Pausable, ReentrancyGuard, AccessControl {
    using ECDSA for bytes32;

    bytes32 public constant SENIOR_INVESTIGATOR_ROLE = keccak256("SENIOR_INVESTIGATOR_ROLE");
    bytes32 public constant INVESTIGATOR_ROLE = keccak256("INVESTIGATOR_ROLE");

    uint64 public bountyCount;
    uint256 public constant RECOVERY_FEE_BPS = 500; // 5% performance reward fee

    bytes32 private constant SECURE_TYPEHASH = keccak256("SecureAssets(address investigator,uint256 nonce)");

    error BountyAlreadyClaimed();
    error ReportAlreadyAnchored();
    error NoCreditsToSecure();
    error EtherTransferFailed();
    error InvalidAddress();
    error InvalidSignature();

    struct IntelligenceReport {
        uint128 identifiedLaunderedValue;
        address primaryInvestigator;
        bool isVerified;
        bool feeClaimed;
        string ipfsCID;
    }

    mapping(bytes32 => IntelligenceReport) public intelligenceLedger;
    mapping(address => uint256) public claimableCredits;
    mapping(address => uint256) public nonces;

    struct Bounty {
        bytes32 targetHash;
        address creator;
        uint128 rewardAmount;
        bool isClaimed;
        string encryptedCID;
    }

    mapping(uint256 => Bounty) public bounties;

    event ProofAnchored(bytes32 indexed reportId, uint256 value, address indexed investigator, string ipfsCID);
    event IntelligenceVerified(bytes32 indexed reportId, address indexed auditor);
    event RewardDistributed(address indexed investigator, uint256 amount);
    event BountyTriggered(uint256 indexed bountyId, address indexed solver);
    event BountyCreated(uint256 indexed bountyId, bytes32 indexed targetHash, uint128 rewardAmount);

    constructor(address initialOwner)
        ERC20("Epiphany Intelligence Token", "EIT")
        ERC20Permit("Epiphany Ledger")
    {
        if (initialOwner == address(0)) revert InvalidAddress();
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
        _grantRole(SENIOR_INVESTIGATOR_ROLE, initialOwner);
        _grantRole(INVESTIGATOR_ROLE, initialOwner);
    }

    /**
     * @dev Step 1: Anchor Forensic Findings onto the state machine.
     */
    function anchorIntelligenceReport(
        bytes32 reportId,
        uint128 launderedValue,
        string calldata ipfsCID
    ) external onlyRole(INVESTIGATOR_ROLE) whenNotPaused {
        if (intelligenceLedger[reportId].primaryInvestigator != address(0)) revert ReportAlreadyAnchored();

        intelligenceLedger[reportId] = IntelligenceReport({
            identifiedLaunderedValue: launderedValue,
            primaryInvestigator: msg.sender,
            isVerified: false,
            feeClaimed: false,
            ipfsCID: ipfsCID
        });

        emit ProofAnchored(reportId, launderedValue, msg.sender, ipfsCID);
    }

    /**
     * @dev Step 2: Protocol Weight Auditing & Verification.
     */
    function verifyIntelligenceReport(bytes32 reportId) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        IntelligenceReport storage report = intelligenceLedger[reportId];
        if (report.primaryInvestigator == address(0)) revert InvalidAddress();
        if (report.isVerified) return; // Already verified

        report.isVerified = true;

        // Programmatic incentive generation: 5% of targeted value
        uint256 reward = (uint256(report.identifiedLaunderedValue) * RECOVERY_FEE_BPS) / 10000;
        claimableCredits[report.primaryInvestigator] += reward;

        emit IntelligenceVerified(reportId, msg.sender);
    }

    /**
     * @dev Create a new bounty for specific evidence.
     */
    function createBounty(
        bytes32 targetHash,
        uint128 rewardAmount,
        string calldata encryptedCID
    ) external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        bountyCount++;
        bounties[bountyCount] = Bounty({
            targetHash: targetHash,
            creator: msg.sender,
            rewardAmount: rewardAmount,
            isClaimed: false,
            encryptedCID: encryptedCID
        });

        emit BountyCreated(bountyCount, targetHash, rewardAmount);
    }

    function triggerBounty(uint256 bountyId, string calldata submissionCID) external whenNotPaused {
        Bounty storage bounty = bounties[bountyId];
        if (bounty.rewardAmount == 0) revert InvalidAddress(); // Bounty doesn't exist
        if (bounty.isClaimed) revert BountyAlreadyClaimed();

        // Check submissionCID is provided
        if (bytes(submissionCID).length == 0) revert InvalidAddress();

        bounty.isClaimed = true;
        claimableCredits[msg.sender] += bounty.rewardAmount;

        emit BountyTriggered(bountyId, msg.sender);
    }

    function claimCredits() external nonReentrant whenNotPaused {
        _secureAssets(msg.sender);
    }

    /**
     * @dev Meta-transaction support for gasless asset securing using EIP-712.
     */
    function metaSecureAssets(
        address investigator,
        bytes calldata signature
    ) external nonReentrant whenNotPaused {
        uint256 nonce = nonces[investigator];
        bytes32 structHash = keccak256(abi.encode(SECURE_TYPEHASH, investigator, nonce));
        bytes32 hash = _hashTypedDataV4(structHash);

        address signer = hash.recover(signature);
        if (signer != investigator) revert InvalidSignature();

        nonces[investigator]++;
        _secureAssets(investigator);
    }

    function _secureAssets(address investigator) internal {
        uint256 amount = claimableCredits[investigator];
        if (amount == 0) revert NoCreditsToSecure();

        // Zero state out entirely before minting (CEI pattern)
        claimableCredits[investigator] = 0;
        _mint(investigator, amount);

        emit RewardDistributed(investigator, amount);
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    function reclaimNativeAssets() external onlyRole(SENIOR_INVESTIGATOR_ROLE) {
        uint256 balance = address(this).balance;
        if (balance == 0) revert NoCreditsToSecure();

        // CEI: No state changes here, but good practice to keep transfer last
        (bool success, ) = msg.sender.call{value: balance}("");
        if (!success) revert EtherTransferFailed();
    }
}
