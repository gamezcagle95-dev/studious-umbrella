"""
Artifact generation script for Epiphany Protocol smart contracts.
Compiles Solidity source files and saves the resulting ABI and bytecode to JSON files.
"""
import json
from solcx import install_solc, get_installed_solc_versions
from scripts.shared_compiler import get_compiled_contracts

def generate_artifacts():
    """
    Main function to compile contracts and generate artifact JSON files.
    """
    if not get_installed_solc_versions():
        install_solc("0.8.26")

    compiled_sol = get_compiled_contracts()

    with open("artifacts/ProvenanceLedger.json", "w", encoding="utf-8") as f:
        json.dump(compiled_sol["contracts"]["ProvenanceLedger.sol"]["ProvenanceLedger"], f)

    with open("artifacts/ProvenanceRegistry.json", "w", encoding="utf-8") as f:
        json.dump(compiled_sol["contracts"]["ProvenanceRegistry.sol"]["ProvenanceRegistry"], f)

    print("Artifacts generated in artifacts/")

if __name__ == "__main__":
    generate_artifacts()
