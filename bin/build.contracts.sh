#!/bin/bash
# ==============================================================================
# EPIPHANY PROTOCOL BUILD COMPONENT - CONTRACT COMPILER TARGETS
# System Profile: Epiphany Protocol
# ==============================================================================
set -e

echo "⚙️  Building contract target pipelines..."

TARGET="contracts"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BASE_DIR="artifacts/$TARGET"
ARTIFACT_DIR="$BASE_DIR/$TIMESTAMP"

# Compile Solidity contracts programmatically using python compiler to artifacts/contracts/latest
PYTHONPATH=. python3 scripts/generate_artifacts.py

# Create timestamped directory and copy build artifacts
mkdir -p "$ARTIFACT_DIR"
if [ -d "artifacts/contracts/latest" ]; then
    cp -r artifacts/contracts/latest/* "$ARTIFACT_DIR/"
fi

# Populate standardized build metadata manifest
cat <<EOF > "$ARTIFACT_DIR/build-info.json"
{
  "target": "$TARGET",
  "timestamp": "$TIMESTAMP",
  "version": "1.0.0",
  "compiler": "solc-0.8.26",
  "profile": "Epiphany Protocol"
}
EOF

# Update rolling 'latest' shortcut via relative symlink
echo "🔗 Synchronizing 'latest' build reference pointer..."
rm -rf "$BASE_DIR/latest"
ln -s "./$TIMESTAMP" "$BASE_DIR/latest"

# Update deployments.json in the root directory from public/settlement.json
if [ -f "public/settlement.json" ]; then
    echo "Updating deployments.json in the root directory..."
    python3 -c '
import json
with open("public/settlement.json", "r", encoding="utf-8") as f:
    data = json.load(f)
contracts = data.get("contracts", {})
dar_addr = contracts.get("Data_Asset_Registry", "0x0000000000000000000000000000000000000003")
deployments = {
    "contracts": contracts,
    "DATA_ASSET_REGISTRY_ADDRESS": dar_addr
}
with open("deployments.json", "w", encoding="utf-8") as f:
    json.dump(deployments, f, indent=2)
'
fi

echo "✓ Compilation artifact caching complete: $ARTIFACT_DIR"
