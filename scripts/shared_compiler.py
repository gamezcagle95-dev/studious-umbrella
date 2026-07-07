"""
Shared compilation logic for Epiphany Protocol smart contracts.
Used by deployment and artifact generation scripts.
"""
import os
from solcx import compile_standard

def get_compiled_contracts(node_modules_path=None):
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

    if node_modules_path is None:
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
