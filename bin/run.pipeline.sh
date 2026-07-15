#!/bin/bash
set -e
clear
echo "======================================================================"
echo "      EPIPHANY ORACLE PROTOCOL - INTEGRATED AUTOMATION PIPELINE        "
echo "======================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

# Detect and activate isolated Python computational runtime environment
if [ -d "venv" ]; then
    echo "✓ Local virtual runtime found. Activating execution layer..."
    source venv/bin/activate
else
    echo "Initializing fresh runtime sandboxing environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
fi

echo -e "\n📦 [1/4] Building Artifacts..."
bash bin/build.contracts.sh

echo -e "\n🔍 [2/4] Off-Chain Evidence Fingerprinting..."
PYTHONPATH=. python3 pipelines/src/pipeline_hashing.py

echo -e "\n⛓️ [3/4] Deploying Protocol Layer..."
python3 deploy.py

echo -e "\n🧪 [4/4] End-to-End Verification..."
PYTHONPATH=scripts python3 scripts/verify_integration.py

echo -e "\n======================================================================"
echo "✅ PIPELINE COMPLETE"
echo "======================================================================"
