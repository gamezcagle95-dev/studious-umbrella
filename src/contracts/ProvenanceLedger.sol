// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title ProvenanceLedger
 * @dev Core settlement layer for the Epiphany Investigative Protocol.
 * Handles intelligence anchoring, bounty distribution, and incentive alignment.
 */
contract ProvenanceLedger is ERC20, ERC20Permit, Pausable, ReentrancyGuard {
    using ECDSA for bytes32;

    address public seniorInvestigator;
    uint64 public bountyCount;
    uint256 public constant RECOVERY_FEE_BPS = 500; // 5% performance reward fee

    bytes32 private constant SECURE_TYPEHASH = keccak256("SecureAssets(address investigator)");

    error BountyAlreadyClaimed();
    error IntelligenceHashMismatch();
    error ReportAlreadyAnchored();
    error OnlySeniorInvestigator();
    error NoCreditsToSecure();
    error EtherTransferFailed();

    struct IntelligenceReport {
        uint128 identifiedLaunderedValue;
        address primaryInvestigator;
        bool isVerified;
        bool feeClaimed;
    }

    mapping(bytes32 => IntelligenceReport) public intelligenceLedger;
    mapping(address => uint256) public claimableCredits;

    struct Bounty {
        bytes32 targetHash;
        address creator;
        uint128 rewardAmount;
        bool isClaimed;
        string encryptedCid;
    }

    mapping(uint256 => Bounty) public bounties;

    event ProofAnchored(bytes32 indexed reportId, uint256 value, address indexed investigator);
    event IntelligenceVerified(bytes32 indexed reportId, address indexed auditor);
    event RewardDistributed(address indexed investigator, uint256 amount);
    event BountyTriggered(uint256 indexed bountyId, address indexed solver);

    constructor(address initialOwner)
        ERC20("Epiphany Intelligence Token", "EIT")
        ERC20Permit("Epiphany Ledger")
        ERC20Permit("Epiphany Intelligence Token")
    {
        seniorInvestigator = initialOwner;
    }

    /**
     * @dev Step 1: Anchor Forensic Findings onto the state machine.
     */
    function anchorIntelligenceReport(bytes32 reportId, uint128 launderedValue) external whenNotPaused {
        if (intelligenceLedger[reportId].primaryInvestigator != address(0)) revert ReportAlreadyAnchored();

        intelligenceLedger[reportId] = IntelligenceReport({
            identifiedLaunderedValue: launderedValue,
            primaryInvestigator: msg.sender,
            isVerified: false,
            feeClaimed: false
        });

        emit ProofAnchored(reportId, launderedValue, msg.sender);
    }

    /**
     * @dev Step 2: Protocol Weight Auditing & Verification.
     */
    function verifyIntelligenceReport(bytes32 reportId) external {
        if (msg.sender != seniorInvestigator) revert OnlySeniorInvestigator();
        IntelligenceReport storage report = intelligenceLedger[reportId];

        report.isVerified = true;

        // Programmatic incentive generation: 5% of targeted value added to pulling buffer
        uint256 reward = (report.identifiedLaunderedValue * RECOVERY_FEE_BPS) / 10000;
        claimableCredits[report.primaryInvestigator] += reward;

        emit IntelligenceVerified(reportId, msg.sender);
    }

    function triggerBounty(uint256 bountyId, string calldata submissionCid) external {
        Bounty storage bounty = bounties[bountyId];
        if (bounty.isClaimed) revert BountyAlreadyClaimed();

        bounty.isClaimed = true;
        claimableCredits[msg.sender] += bounty.rewardAmount;

        emit BountyTriggered(bountyId, msg.sender);
    }

    function claimCredits() external nonReentrant whenNotPaused {
        _secureAssets(msg.sender);
    }

    /**
     * @dev Meta-transaction support for gasless asset securing using EIP-712.
     * Allows a relayer to execute the state change if the investigator provides a valid signature.
     */
    function metaSecureAssets(address investigator, bytes memory signature) external nonReentrant whenNotPaused {
        bytes32 structHash = keccak256(abi.encode(SECURE_TYPEHASH, investigator));
        bytes32 hash = _hashTypedDataV4(structHash);

        address signer = ECDSA.recover(hash, signature);
        require(signer == investigator, "Invalid signature");

        _secureAssets(investigator);
    }

    function _secureAssets(address investigator) internal {
        uint256 amount = claimableCredits[investigator];
        if (amount == 0) revert NoCreditsToSecure();

        // Zero state out entirely before minting to prevent reentrancy manipulation vectors
        claimableCredits[investigator] = 0;
        _mint(investigator, amount);

        emit RewardDistributed(investigator, amount);
    }

    function reclaimNativeAssets() external {
        if (msg.sender != seniorInvestigator) revert OnlySeniorInvestigator();
        uint256 balance = address(this).balance;
        if (balance == 0) revert NoCreditsToSecure();

        (bool success, ) = msg.sender.call{value: balance}("");
        if (!success) revert EtherTransferFailed();
    }
}
