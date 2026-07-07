"""
Artifact generation utility for Epiphany Protocol.
"""
import os
import json
from solcx import compile_standard, install_solc, get_installed_solc_versions

def generate_artifacts():
    """
    Compiles protocol contracts and generates artifacts.
    """
    if "0.8.26" not in [str(v) for v in get_installed_solc_versions()]:
        install_solc("0.8.26")

    with open("src/contracts/ProvenanceLedger.sol", "r", encoding="utf-8") as f:
        ledger_src = f.read()
    with open("src/contracts/ProvenanceRegistry.sol", "r", encoding="utf-8") as f:
        registry_src = f.read()
    with open("src/contracts/DataAssetRegistry.sol", "r", encoding="utf-8") as f:
        dar_src = f.read()

    node_modules_path = os.path.abspath("node_modules")

    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {
            "ProvenanceLedger.sol": {"content": ledger_src},
            "ProvenanceRegistry.sol": {"content": registry_src},
            "DataAssetRegistry.sol": {"content": dar_src}
        },
        "settings": {
            "remappings": [
                f"@openzeppelin/={node_modules_path}/@openzeppelin/"
            ],
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    }, solc_version="0.8.26", allow_paths=node_modules_path)

    os.makedirs("artifacts", exist_ok=True)

    with open("artifacts/ProvenanceLedger.json", "w", encoding="utf-8") as f:
        json.dump(compiled_sol["contracts"]["ProvenanceLedger.sol"]["ProvenanceLedger"], f)

    with open("artifacts/ProvenanceRegistry.json", "w", encoding="utf-8") as f:
        json.dump(compiled_sol["contracts"]["ProvenanceRegistry.sol"]["ProvenanceRegistry"], f)

    with open("artifacts/DataAssetRegistry.json", "w", encoding="utf-8") as f:
        json.dump(compiled_sol["contracts"]["DataAssetRegistry.sol"]["DataAssetRegistry"], f)

    print("Artifacts generated in artifacts/")

if __name__ == "__main__":
    generate_artifacts()
