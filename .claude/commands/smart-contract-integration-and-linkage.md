---
name: smart-contract-integration-and-linkage
description: Workflow command scaffold for smart-contract-integration-and-linkage in studious-umbrella.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /smart-contract-integration-and-linkage

Use this workflow when working on **smart-contract-integration-and-linkage** in `studious-umbrella`.

## Goal

Integrate or revert integration between ProvenanceLedger and ProvenanceRegistry contracts, update deployment scripts, and generate new build artifacts.

## Common Files

- `src/contracts/ProvenanceLedger.sol`
- `src/contracts/ProvenanceRegistry.sol`
- `deploy.py`
- `artifacts/contracts/*/build-info.json`
- `artifacts/contracts/latest`
- `scripts/verify_integration.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Modify src/contracts/ProvenanceLedger.sol and/or src/contracts/ProvenanceRegistry.sol to add or remove integration logic.
- Update deploy.py to reflect new linkage or remove linkage logic.
- Generate new build artifacts in artifacts/contracts/ with timestamped build-info.json and update artifacts/contracts/latest.
- Optionally, add or remove scripts/verify_integration.py for ABI verification.
- Commit all related files together.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.