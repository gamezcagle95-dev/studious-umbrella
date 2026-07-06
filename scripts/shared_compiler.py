"""
Shared compilation logic for Epiphany Protocol smart contracts.
Used by deployment and artifact generation scripts.
"""
import os
from solcx import compile_standard

def get_compiled_contracts():
    """
    Reads Solidity source files and compiles them using solc standard JSON.
    Returns the compiled contract data.
    """
    with open("src/contracts/ProvenanceLedger.sol", "r", encoding="utf-8") as f:
        ledger_src = f.read()
    with open("src/contracts/ProvenanceRegistry.sol", "r", encoding="utf-8") as f:
        registry_src = f.read()

    node_modules_path = os.path.abspath("node_modules")

    return compile_standard({
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
