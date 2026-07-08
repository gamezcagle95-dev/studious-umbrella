# ==============================================================================
# EPIPHANY WEB3 SETTLEMENT MACHINE - DUAL-CONTRACT DEPLOYMENT ENGINE
# Profile Context: Epiphany Protocol
# ==============================================================================
"""
Deterministic contract deployment engine for the Epiphany Protocol.
Handles sequential deployment of the ProvenanceLedger and ProvenanceRegistry.
"""
import os
import json
import sys
from dataclasses import dataclass
from typing import List, Any
from web3 import Web3
from solcx import install_solc
from dotenv import load_dotenv
from scripts.shared_compiler import get_compiled_contracts

@dataclass
class DeploymentConfig:
    """Container for deployment parameters to reduce function argument count."""
    file_name: str
    contract_name: str
    account: str
    pkey: str
    args: List[Any]

load_dotenv()

def run_deployment_loop():
    """
    Main orchestration loop for deploying protocol contracts.
    """
    print("⛓️  Initializing state machine compiler pipelines...")

    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("PRIVATE_KEY")
    account_address = os.getenv("ACCOUNT_ADDRESS")

    if not private_key or not account_address:
        print("⚠️  Warning: PRIVATE_KEY or ACCOUNT_ADDRESS not set in environment.")
        print("💡 Simulation Mode: Mocking configuration outputs to public/settlement.json")
        mock_deployment_output(
            "0x4c0883a69102937d6231471b5dbb6204fe302702fd307ce2304598dcf3e346d1",
            "0x71C7656EC7ab88b098defB751B7401B5f6d147a3"
        )
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"❌ Connection Error: Node target offline at {rpc_url}")
        sys.exit(1)

    print(f"✓ Linked to network ledger. Chain ID: {w3.eth.chain_id}")
    install_solc("0.8.26")

    # Compile files in a single pass using shared compiler
    compiled_sol = get_compiled_contracts()

    # 1. Deploy ProvenanceLedger
    ledger_config = DeploymentConfig(
        file_name="ProvenanceLedger.sol",
        contract_name="ProvenanceLedger",
        account=account_address,
        pkey=private_key,
        args=[account_address]
    )
    ledger_address = deploy_contract(w3, compiled_sol, ledger_config)
    print(f"✅ LEDGER DEPLOYED: {ledger_address}")

    # 2. Deploy ProvenanceRegistry (Passing Ledger Address to Constructor)
    registry_config = DeploymentConfig(
        file_name="ProvenanceRegistry.sol",
        contract_name="ProvenanceRegistry",
        account=account_address,
        pkey=private_key,
        args=[ledger_address]
    )
    registry_address = deploy_contract(w3, compiled_sol, registry_config)
    print(f"✅ REGISTRY DEPLOYED: {registry_address}")

    mock_deployment_output(ledger_address, registry_address)

def deploy_contract(w3, compiled_sol, config: DeploymentConfig):
    """
    Executes a contract deployment transaction.
    """
    abi = compiled_sol["contracts"][config.file_name][config.contract_name]["abi"]
    evm_data = compiled_sol["contracts"][config.file_name][config.contract_name]["evm"]
    bytecode = evm_data["bytecode"]["object"]

    nonce = w3.eth.get_transaction_count(config.account)
    contract_obj = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx = contract_obj.constructor(*config.args).build_transaction({
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": config.account,
        "nonce": nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=config.pkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress

def mock_deployment_output(ledger_addr, registry_addr):
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

    with open(settlement_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✓ Configuration map synchronized in {settlement_path}")

if __name__ == "__main__":
    run_deployment_loop()
