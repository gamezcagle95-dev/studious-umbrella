import os
import json
from solcx import compile_standard, install_solc, get_installed_solc_versions

def generate_artifacts():
    if not get_installed_solc_versions():
        install_solc("0.8.26")

    with open("src/contracts/ProvenanceLedger.sol", "r") as f:
        ledger_src = f.read()
    with open("src/contracts/ProvenanceRegistry.sol", "r") as f:
        registry_src = f.read()

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
    }, solc_version="0.8.26", allow_paths=node_modules_path)

    with open("artifacts/ProvenanceLedger.json", "w") as f:
        json.dump(compiled_sol["contracts"]["ProvenanceLedger.sol"]["ProvenanceLedger"], f)

    with open("artifacts/ProvenanceRegistry.json", "w") as f:
        json.dump(compiled_sol["contracts"]["ProvenanceRegistry.sol"]["ProvenanceRegistry"], f)

    print("Artifacts generated in artifacts/")

if __name__ == "__main__":
    generate_artifacts()
