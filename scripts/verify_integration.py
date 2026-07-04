
import os
import sys
import json
import solcx
from solcx import compile_standard, install_solc

def test_integration():
    print("🚀 Starting integration test...")

    try:
        solcx.install_solc("0.8.26")
    except Exception as e:
        print(f"Solc installation note: {e}")

    solc_version = "0.8.26"

    with open("src/contracts/ProvenanceLedger.sol", "r", encoding="utf-8") as f:
        ledger_src = f.read()
    with open("src/contracts/ProvenanceRegistry.sol", "r", encoding="utf-8") as f:
        registry_src = f.read()

    # Need to handle remappings for OpenZeppelin
    node_modules_path = os.path.abspath("node_modules")

    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {
            "ProvenanceLedger.sol": {"content": ledger_src},
            "ProvenanceRegistry.sol": {"content": registry_src}
        },
        "settings": {
            "remappings": [
                f"@openzeppelin/={node_modules_path}/@openzeppelin/"
            ],
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    }, allow_paths=node_modules_path, solc_version=solc_version)

    # Verify that the ABI contains the new functions
    ledger_abi = compiled_sol["contracts"]["ProvenanceLedger.sol"]["ProvenanceLedger"]["abi"]

    has_set_registry = any(f["name"] == "setRegistryAddress" for f in ledger_abi if f.get("type") == "function")
    has_registry_addr = any(f["name"] == "registryAddress" for f in ledger_abi if f.get("type") == "function")

    print(f"✓ ProvenanceLedger has setRegistryAddress: {has_set_registry}")
    print(f"✓ ProvenanceLedger has registryAddress: {has_registry_addr}")

    anchor_func = next(f for f in ledger_abi if f.get("name") == "anchorIntelligenceReport")
    has_cid_param = any(p["name"] == "ipfsCid" for p in anchor_func["inputs"])
    print(f"✓ anchorIntelligenceReport has ipfsCid parameter: {has_cid_param}")

    if not (has_set_registry and has_registry_addr and has_cid_param):
        print("❌ Integration check failed!")
        sys.exit(1)

    print("✅ Integration logic verified successfully (static analysis).")

if __name__ == "__main__":
    test_integration()
