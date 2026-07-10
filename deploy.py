# ==============================================================================
# EPIPHANY WEB3 SETTLEMENT MACHINE - DUAL-CONTRACT DEPLOYMENT ENGINE
# Profile Context: Epiphany Protocol
# ==============================================================================
"""
Deterministic contract deployment engine for the Epiphany Protocol.
Handles sequential deployment of ProvenanceLedger, ProvenanceRegistry, and DataAssetRegistry.
"""
import os
import json
import sys
from dataclasses import dataclass
from typing import List, Any
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

@dataclass
class DeploymentConfig:
    """Container for deployment parameters to reduce function argument count."""
    file_name: str
    contract_name: str
    account: str
    pkey: str
    args: List[Any]

@dataclass
class RoleParams:
    """Container for role delegation parameters."""
    registry_addr: str
    dar_addr: str
    account_address: str
    private_key: str

load_dotenv()

def get_env_config():
    """Retrieves and validates environment configuration."""
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    p_key = os.getenv("PRIVATE_KEY")
    acc_addr = os.getenv("ACCOUNT_ADDRESS")
    return rpc_url, p_key, acc_addr

def delegate_minter_role(w3, r_params: RoleParams, compiled_sol):
    """Grants MINTER_ROLE on ProvenanceRegistry to DataAssetRegistry."""
    print("[Wurk] ⏳ Delegating MINTER_ROLE to DataAssetRegistry...")
    registry_abi = compiled_sol["contracts"]["ProvenanceRegistry.sol"]["ProvenanceRegistry"]["abi"]
    registry_contract = w3.eth.contract(address=r_params.registry_addr, abi=registry_abi)
    minter_role = w3.keccak(text="MINTER_ROLE")

    nonce = w3.eth.get_transaction_count(r_params.account_address)
    tx_params = {
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": r_params.account_address,
        "nonce": nonce,
    }
    tx = registry_contract.functions.grantRole(
        minter_role, r_params.dar_addr
    ).build_transaction(tx_params)
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=r_params.private_key)
    w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print("[Wurk] ✓ MINTER_ROLE granted.")

def run_deployment_loop():
    """
    Main orchestration loop for deploying protocol contracts.
    """
    print("[Wurk] ⛓️  Initializing state machine compiler pipelines...")
    rpc_url, private_key, account_address = get_env_config()

    if not private_key or not account_address:
        print("[Wurk] ⚠️  Warning: PRIVATE_KEY or ACCOUNT_ADDRESS not set in environment.")
        print("[Wurk] 💡 Simulation Mode: Mocking configuration outputs to public/settlement.json")
        mock_deployment_output(
            "0x4c0883a69102937d6231471b5dbb6204fe302702fd307ce2304598dcf3e346d1",
            "0x71C7656EC7ab88b098defB751B7401B5f6d147a3",
            "0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"
        )
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"[Wurk] ❌ Connection Error: Node target offline at {rpc_url}")
        sys.exit(1)

    print(f"[Wurk] ✓ Linked to network ledger. Chain ID: {w3.eth.chain_id}")
    install_solc("0.8.26")
    compiled_sol = compile_files()

    # 1. Deploy ProvenanceLedger
    l_cfg = DeploymentConfig("ProvenanceLedger.sol", "ProvenanceLedger",
                             account_address, private_key, [account_address])
    ledger_address = deploy_contract(w3, compiled_sol, l_cfg)
    print(f"[Wurk] ✅ LEDGER DEPLOYED: {ledger_address}")

    # 2. Deploy ProvenanceRegistry
    r_cfg = DeploymentConfig("ProvenanceRegistry.sol", "ProvenanceRegistry",
                             account_address, private_key, [ledger_address])
    registry_address = deploy_contract(w3, compiled_sol, r_cfg)
    print(f"[Wurk] ✅ REGISTRY DEPLOYED: {registry_address}")

    # 3. Deploy DataAssetRegistry
    d_cfg = DeploymentConfig("DataAssetRegistry.sol", "DataAssetRegistry",
                             account_address, private_key, [ledger_address, registry_address])
    dar_address = deploy_contract(w3, compiled_sol, d_cfg)
    print(f"[Wurk] ✅ DATA ASSET REGISTRY DEPLOYED: {dar_address}")

    # 4. Role Delegation
    r_params = RoleParams(registry_address, dar_address, account_address, private_key)
    delegate_minter_role(w3, r_params, compiled_sol)

    mock_deployment_output(ledger_address, registry_address, dar_address)

def compile_files():
    """
    Compiles Solidity source files using the solc standard JSON input.
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

    return compile_standard({
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    }, allow_paths=os.path.abspath("node_modules"))

def deploy_contract(w3, compiled_sol, config: DeploymentConfig):
    """
    Executes a contract deployment transaction.
    """
    contract_data = compiled_sol["contracts"][config.file_name][config.contract_name]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    nonce = w3.eth.get_transaction_count(config.account)
    contract_obj = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx_params = {
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": config.account,
        "nonce": nonce,
    }
    tx = contract_obj.constructor(*config.args).build_transaction(tx_params)

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=config.pkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress

def mock_deployment_output(ledger_addr, registry_addr, dar_addr):
    """
    Synchronizes deployment addresses to public/settlement.json for frontend mapping.
    """
    settlement_path = "public/settlement.json"
    data = {"contracts": {}}

    if os.path.exists(settlement_path):
        try:
            with open(settlement_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    data["contracts"]["Intelligence_Ledger"] = ledger_addr
    data["contracts"]["Provenance_Registry"] = registry_addr
    data["contracts"]["Data_Asset_Registry"] = dar_addr

    with open(settlement_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[Wurk] ✓ Configuration map synchronized in {settlement_path}")

if __name__ == "__main__":
    run_deployment_loop()
