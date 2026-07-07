#!/bin/bash
# ==============================================================================
# EPIPHANY PROTOCOL BUILD COMPONENT - CONTRACT COMPILER TARGETS
# System Profile: Epiphany Protocol
# ==============================================================================
set -e

TARGET="contracts"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BASE_DIR="artifacts/$TARGET"
ARTIFACT_DIR="$BASE_DIR/$TIMESTAMP"

echo "⚙️  Building contract target pipelines..."

# Establish strict artifact standard directory layouts
mkdir -p "$ARTIFACT_DIR"

# Compile contracts using Python script and output to the timestamped directory
python3 scripts/generate_artifacts.py

# Move generated artifacts to the timestamped directory
mv artifacts/ProvenanceLedger.json "$ARTIFACT_DIR/ProvenanceLedger.json"
mv artifacts/ProvenanceRegistry.json "$ARTIFACT_DIR/ProvenanceRegistry.json"
mv artifacts/DataAssetRegistry.json "$ARTIFACT_DIR/DataAssetRegistry.json"

# Populate standardized build metadata manifest
cat <<MANIFEST_EOF > "$ARTIFACT_DIR/build-info.json"
{
  "target": "$TARGET",
  "timestamp": "$TIMESTAMP",
  "version": "1.0.0",
  "compiler": "solc-0.8.26",
  "profile": "Epiphany Protocol"
}
MANIFEST_EOF

# Update rolling 'latest' shortcut via relative symlink
echo "🔗 Synchronizing 'latest' build reference pointer..."
rm -f "$BASE_DIR/latest"
ln -s "./$TIMESTAMP" "$BASE_DIR/latest"

echo "✓ Compilation artifact caching complete: $ARTIFACT_DIR"
