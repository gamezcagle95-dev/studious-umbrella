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
mkdir -p "$ARTIFACT_DIR/abi"
mkdir -p "$ARTIFACT_DIR/bytecode"

# Copy pre-configured contract schemas if available
if ls src/contracts/*.json >/dev/null 2>&1; then
    cp src/contracts/*.json "$ARTIFACT_DIR/abi/"
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
rm -f "$BASE_DIR/latest"
ln -s "./$TIMESTAMP" "$BASE_DIR/latest"

echo "✓ Compilation artifact caching complete: $ARTIFACT_DIR"
