"""
Artifact generation script for Epiphany Protocol smart contracts.
Compiles Solidity source files and saves the resulting ABI and bytecode to JSON files.
"""
import os
import json
from solcx import install_solc, get_installed_solc_versions
from scripts.shared_compiler import get_compiled_contracts

def generate_artifacts():
    """
    Main function to compile contracts and generate artifact JSON files.
    """
    if not get_installed_solc_versions():
        install_solc("0.8.26")

    print("[Epiphany] Compiling contracts...")
    compiled_sol = get_compiled_contracts()

    # Define the standardized output directory
    output_dir = "artifacts/contracts/latest"
    os.makedirs(output_dir, exist_ok=True)

    contracts_to_generate = [
        ("ProvenanceLedger.sol", "ProvenanceLedger"),
        ("ProvenanceRegistry.sol", "ProvenanceRegistry"),
        ("DataAssetRegistry.sol", "DataAssetRegistry")
    ]

    for file_name, contract_name in contracts_to_generate:
        contract_data = compiled_sol["contracts"][file_name][contract_name]

        # Combine ABI and Bytecode into a single standardized artifact
        artifact = {
            "abi": contract_data["abi"],
            "bytecode": contract_data["evm"]["bytecode"]["object"]
        }

        artifact_path = os.path.join(output_dir, f"{contract_name}.json")
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2)
        print(f"[Epiphany] Artifact generated: {artifact_path}")

if __name__ == "__main__":
    generate_artifacts()
