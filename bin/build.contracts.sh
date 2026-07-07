#!/bin/bash
# ==============================================================================
# EPIPHANY PROTOCOL BUILD COMPONENT - CONTRACT COMPILER TARGETS
# System Profile: Epiphany Protocol
# ==============================================================================
set -e

echo "⚙️  Building contract target pipelines..."

# Execute programmatic compilation via scripts/generate_artifacts.py
# This produces combined ABI/bytecode JSON files in artifacts/contracts/latest/
PYTHONPATH=. python3 scripts/generate_artifacts.py

echo "✓ Compilation artifact caching complete."
