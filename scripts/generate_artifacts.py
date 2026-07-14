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
    # Programmatically install solc version 0.8.26 if it is missing
    if "0.8.26" not in [str(v) for v in get_installed_solc_versions()]:
        install_solc("0.8.26")

    # Get the programmatically compiled Solidity files using shared_compiler
    compiled_sol = get_compiled_contracts()

    # Establish the standard latest contract build directory
    output_dir = "artifacts/contracts/latest"
    if os.path.islink(output_dir):
        os.unlink(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Establish contract naming and mapping dictionary
    contract_mapping = {
        "ProvenanceLedger.sol": "ProvenanceLedger",
        "ProvenanceRegistry.sol": "ProvenanceRegistry",
        "DataAssetRegistry.sol": "DataAssetRegistry"
    }

    # Loop and extract combined ABI / Bytecode files for downstream tools and scripts
    for file_name, contract_name in contract_mapping.items():
        contract_data = compiled_sol["contracts"][file_name][contract_name]
        artifact = {
            "abi": contract_data["abi"],
            "bytecode": contract_data["evm"]["bytecode"]["object"]
        }
        # Safely save the extracted ABI and bytecode JSON payload to the workspace artifacts path
        with open(os.path.join(output_dir, f"{contract_name}.json"), "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2)

    print(f"Artifacts generated in {output_dir}")

if __name__ == "__main__":
    generate_artifacts()
