#!/bin/bash
# ==============================================================================
# EPIPHANY INVESTIGATIVE PROTOCOL - PIPELINE AUTOMATION RUNNER
# System Profile:
# Core Workspace: /app
# Target Remote: git@github.com:gamezcagle95-dev/dataset-tokenization-layer.git
# ==============================================================================
set -e

# Clear console terminal for clear data trace tracking
clear
echo "======================================================================"
echo "      EPIPHANY ORACLE PROTOCOL - INTEGRATED AUTOMATION PIPELINE        "
echo "======================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Identity:  "
echo "Workspace: /app"
echo "----------------------------------------------------------------------"

# ------------------------------------------------------------------------------
# STEP 1: Environment & Supply Chain Security Enforcements
# ------------------------------------------------------------------------------
echo "🔒 [1/4] Securing Local Software Supply Chain Layer..."

# Enforce script blocking configurations to neutralize node dependency vectors
echo "ignore-scripts=true" > .npmrc
echo "✓ Defensive supply-chain perimeter locked (.npmrc)."

# Initialize Node dependencies natively if missing inside /app
if [ ! -d "node_modules" ]; then
    echo "Installing baseline protocol packages..."
    npm install @openzeppelin/contracts@5.0.2 --quiet
fi

# Detect and activate isolated Python computational runtime environment
if [ -d "venv" ]; then
    echo "✓ Local virtual runtime found. Activating execution layer..."
    source venv/bin/activate
else
    echo "Initializing fresh runtime sandboxing environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install py-solc-x web3 python-dotenv --quiet
fi

# ------------------------------------------------------------------------------
# STEP 2: Structural Contract Compilation & Artifact Building
# ------------------------------------------------------------------------------
echo -e "\n📦 [2/4] Executing Master Solidity Compiler & Layout Matrix..."
if [ -f "bin/build.contracts.sh" ]; then
    bash bin/build.contracts.sh
else
    echo "CRITICAL ERROR: bin/build.contracts.sh not found."
    exit 1
fi

# ------------------------------------------------------------------------------
# STEP 3: Cryptographic Document Hashing & Evidence Processing
# ------------------------------------------------------------------------------
echo -e "\n🔍 [3/4] Triggering Off-Chain Evidence Fingerprint Extractions..."
if [ -f "anchor_real_evidence.js" ]; then
    node anchor_real_evidence.js
elif [ -f "scripts/anchor_evidence.js" ]; then
    node scripts/anchor_evidence.js
else
    echo "Warning: No primary baseline verification script detected. Skipping..."
fi

# ------------------------------------------------------------------------------
# STEP 4: On-Chain Deployment Simulation & State Alignment
# ------------------------------------------------------------------------------
echo -e "\n⛓️ [4/4] Activating Deterministic Smart Contract Deployment Vector..."
if [ -f "deploy.py" ]; then
    python3 deploy.py
else
    echo "CRITICAL ERROR: deploy.py deployment engine missing."
    exit 1
fi

echo -e "\n======================================================================"
echo "✅ PIPELINE COMPLETE: State Synchronized cleanly to public/settlement.json"
echo "======================================================================"
