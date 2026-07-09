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

echo "✓ Compilation artifact caching complete: $ARTIFACT_DIR"
