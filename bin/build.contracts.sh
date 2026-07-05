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

# Compile contracts and generate JSON artifacts
python3 <<PYEOF
import os
import json
import solcx

def build():
    # Ensure solc is installed
    if '0.8.26' not in solcx.get_installed_solc_versions():
        solcx.install_solc("0.8.26")
    solcx.set_solc_version("0.8.26")

    files = [
        "src/contracts/ProvenanceLedger.sol",
        "src/contracts/ProvenanceRegistry.sol",
        "src/contracts/DataAssetRegistry.sol"
    ]

    sources = {}
    for file in files:
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                sources[os.path.basename(file)] = {"content": f.read()}

    compiled = solcx.compile_standard({
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "optimizer": {"enabled": True, "runs": 200},
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}},
            "remappings": ["@openzeppelin/=node_modules/@openzeppelin/"]
        }
    }, allow_paths=os.getcwd())

    for source_file, contracts in compiled['contracts'].items():
        for contract_name, data in contracts.items():
            # Skip OpenZeppelin internal contracts
            if source_file.startswith("node_modules"):
                continue

            # Save ABI
            abi_path = os.path.join("$ARTIFACT_DIR", "abi", f"{contract_name}.json")
            with open(abi_path, "w") as f:
                json.dump(data['abi'], f, indent=2)

            # Save Bytecode
            bin_path = os.path.join("$ARTIFACT_DIR", "bytecode", f"{contract_name}.bin")
            with open(bin_path, "w") as f:
                f.write(data['evm']['bytecode']['object'])

build()
PYEOF

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
