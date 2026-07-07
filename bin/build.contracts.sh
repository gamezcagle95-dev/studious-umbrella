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

# Execute programmatic compilation via Python helper
python3 scripts/generate_artifacts.py

# Move newly generated artifacts to versioned directory for archiving
# Note: scripts/generate_artifacts.py writes to artifacts/contracts/latest/
# We want to keep latest as a symlink to the timestamped directory.
# So we move the files from latest (if it's a real dir) or just let generate_artifacts
# handle it and we symlink the timestamped one.

# Let's refine the strategy:
# 1. generate_artifacts writes to artifacts/contracts/latest (if it's a dir)
# 2. We move artifacts/contracts/latest contents to ARTIFACT_DIR
# 3. We recreate the symlink

if [ -d "$BASE_DIR/latest" ] && [ ! -L "$BASE_DIR/latest" ]; then
    mv "$BASE_DIR/latest/"* "$ARTIFACT_DIR/"
    rmdir "$BASE_DIR/latest"
else
    # If latest is already a symlink, generate_artifacts followed the link
    # or created a new dir. If it created a new dir, move it.
    if [ -d "$BASE_DIR/latest" ]; then
         cp -r "$BASE_DIR/latest/." "$ARTIFACT_DIR/"
    fi
fi

# Populate standardized build metadata manifest
cat <<metadata > "$ARTIFACT_DIR/build-info.json"
{
  "target": "$TARGET",
  "timestamp": "$TIMESTAMP",
  "version": "1.0.0",
  "compiler": "solc-0.8.26",
  "profile": "Epiphany Protocol"
}
metadata

# Update rolling 'latest' shortcut via relative symlink
echo "🔗 Synchronizing 'latest' build reference pointer..."
rm -f "$BASE_DIR/latest"
ln -s "./$TIMESTAMP" "$BASE_DIR/latest"

echo "✓ Compilation artifact caching complete: $ARTIFACT_DIR"
