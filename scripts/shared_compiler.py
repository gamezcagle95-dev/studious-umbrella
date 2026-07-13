"""
Shared compilation logic for Epiphany Protocol smart contracts.
Used by deployment and artifact generation scripts.
This script compiles EpiphanyToken, ProvenanceRegistry, and DataAssetRegistry.
"""
import os
from solcx import compile_standard
from web3 import Web3

def get_compiled_contracts(node_modules_path=None):
    """
    Reads Solidity source files and compiles them using solc standard JSON.
    Returns the compiled contract data.

    Args:
        node_modules_path (str, optional): Custom path to node_modules for OpenZeppelin.

    Returns:
        dict: Standard solc output dictionary containing ABI and bytecode.
    """
    files = {
        "EpiphanyToken.sol": "src/contracts/EpiphanyToken.sol",
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


def predict_contract_address(deployer: str, nonce: int) -> str:
    """
    Predicts the checksummed contract address for a given deployer and nonce.
    This uses a pure python standard RLP list encoding for [address, nonce].
    """
    deployer_bytes = bytes.fromhex(deployer[2:]) if deployer.startswith("0x") else bytes.fromhex(deployer)
    if nonce == 0:
        nonce_bytes = b'\x80'
    elif nonce < 0x80:
        nonce_bytes = bytes([nonce])
    else:
        n_bytes = nonce.to_bytes((nonce.bit_length() + 7) // 8, 'big')
        nonce_bytes = bytes([0x80 + len(n_bytes)]) + n_bytes

    payload = b'\x94' + deployer_bytes + nonce_bytes
    rlp_encoded = bytes([0xc0 + len(payload)]) + payload
    # pylint: disable=no-value-for-parameter
    contract_hash = Web3.keccak(rlp_encoded)
    return Web3.to_checksum_address(contract_hash[-20:].hex())
