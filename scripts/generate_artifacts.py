"""
Artifact generation script for Epiphany Protocol smart contracts.
Compiles Solidity source files and saves the resulting ABI and bytecode to JSON files.
"""
import os
import json
from solcx import install_solc, get_installed_solc_versions, compile_standard

def get_compiled_contracts():
    """
    Reads Solidity source files and compiles them using solc standard JSON.
    Returns the compiled contract data.
    """
    files = {
        "ProvenanceLedger.sol": "src/contracts/ProvenanceLedger.sol",
        "ProvenanceRegistry.sol": "src/contracts/ProvenanceRegistry.sol",
        "DataAssetRegistry.sol": "src/contracts/DataAssetRegistry.sol"
    }

    sources = {}
    for name, path in files.items():
        with open(path, "r", encoding="utf-8") as f:
            sources[name] = {"content": f.read()}

    node_modules_path = os.path.abspath("node_modules")

    return compile_standard({
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "remappings": [
                f"@openzeppelin/={node_modules_path}/@openzeppelin/"
            ],
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    }, solc_version="0.8.26", allow_paths=node_modules_path)

def generate_artifacts():
    """
    Main function to compile contracts and generate artifact JSON files.
    """
    if "0.8.26" not in get_installed_solc_versions():
        install_solc("0.8.26")

    compiled_sol = get_compiled_contracts()

    output_dir = "artifacts/contracts/latest"
    os.makedirs(output_dir, exist_ok=True)

    contract_mapping = {
        "ProvenanceLedger.sol": "ProvenanceLedger",
        "ProvenanceRegistry.sol": "ProvenanceRegistry",
        "DataAssetRegistry.sol": "DataAssetRegistry"
    }

    for file_name, contract_name in contract_mapping.items():
        contract_data = compiled_sol["contracts"][file_name][contract_name]
        artifact = {
            "abi": contract_data["abi"],
            "bytecode": contract_data["evm"]["bytecode"]["object"]
        }
        with open(os.path.join(output_dir, f"{contract_name}.json"), "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2)

    print(f"Artifacts generated in {output_dir}")

if __name__ == "__main__":
    generate_artifacts()
