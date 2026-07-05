# Epiphany Liquid Economy - Decentralized Command Center

This repository houses the core protocol stack for the Epiphany Liquid Economy. The protocol transforms high-density AI training data, agentic trajectories, and structural logic chains into liquid financial assets settled in native **Epiphany Intelligence Tokens (EIT)**.

---

## Core Architecture

The protocol operates as a secure bridge between off-chain dynamic evaluation and on-chain ledger settlement:
* **Dynamic Appraisal Engine ([scripts/appraisal_engine.py](scripts/appraisal_engine.py)):** Programmatically values text trajectories using the multi-variable formula:
  $$\text{Price} = \text{Base Cost} \times \text{Information Density} \times \text{Scarcity Metric} \times \text{Demand Vector}$$
* **Smart Contract Registry ([src/contracts/DataAssetRegistry.sol](src/contracts/DataAssetRegistry.sol)):** Verifies EIP-712 appraisal signatures, manages native EIT token settlement, and triggers cross-contract Data NFT license minting while enforcing dynamic circuit breakers to prevent oracle manipulation.
* **Deterministic Hashing ([pipelines/src/pipeline_hashing.py](pipelines/src/pipeline_hashing.py)):** Generates memory-efficient, chunked SHA-256 hashes of data assets and archives structured proof packets.

---

## Agentic Development & Copilot Playbook

To maintain our strict development standards (such as compiling under Solidity \`0.8.26\` and enforcing a **10/10 Pylint score**), we utilize GitHub Copilot's multi-model runtime environment. Developers and autonomous agents should route tasks to the specific models optimized for each domain:

### 1. Cryptographic Auditing & Solidity Security
* **Recommended Model:** \`Claude Sonnet 5\` or \`Claude Opus 4.8\`
* **Optimal Tasks:** Auditing EIP-712 signature parsing, verifying the Checks-Effects-Interactions (CEI) state modifications, and analyzing the registry's ReentrancyGuard limits.
* **Why:** High reasoning capability and precise parsing of complex EVM safety invariants.

### 2. Fast Scripting & Pylint Hygiene (10/10 Compliance)
* **Recommended Model:** \`GPT-5.3-Codex\` or \`GPT-5 mini\`
* **Optimal Tasks:** Generating modular Python boilerplate, clearing minor syntax lints, and writing standard unit tests.
* **Why:** Optimized for rapid auto-completion, low-latency generation, and clean refactoring of syntax errors.

### 3. Data Analytics & Oracle Optimization
* **Recommended Model:** \`Gemini 3.1 Pro\` or \`GPT-5.5\`
* **Optimal Tasks:** Tuning the multi-variable appraisal coefficients, designing n-gram perplexity algorithms, and verifying statistical distributions of data scarcity metrics.
* **Why:** Strong quantitative analytical capabilities and large context windows for processing comprehensive historical datasets.

---

## Getting Started

### Prerequisites
* Python \`3.12+\`
* Node.js \`20.x\`
* Hardhat / Foundry

### Installation
Initialize the secure workspace and install dependencies cleanly using our idempotent setup pipeline:
\`\`\`bash
chmod +x setup.sh
./setup.sh
\`\`\`

### Local Verification
Run the integrated end-to-end cryptographic and transaction routing test suite:
\`\`\`bash
python3 scripts/verify_integration.py
\`\`\`
