"""
Epiphany Web3 Settlement Machine - Dual-Contract Deployment Engine.

This module handles automatic compilation via solcx and deployments of both the
ProvenanceLedger and ProvenanceRegistry smart contracts.
"""

import os
import json
import sys
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

load_dotenv()


def run_deployment_loop():
    """Executes the primary deployment cycle for both smart contracts."""
    print("⛓️  Initializing state machine compiler pipelines...")

    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("PRIVATE_KEY")
    account_address = os.getenv("ACCOUNT_ADDRESS")

    if not private_key or not account_address:
        print("⚠️  Warning: PRIVATE_KEY or ACCOUNT_ADDRESS not set in environment.")
        print("💡 Simulation Mode: Mocking configurations in public/settlement.json")
        mock_deployment_output(
            "0x4c0883a69102937d6231471b5dbb6204fe302702fd307ce2304598dcf3e346d1",
            "0x71C7656EC7ab88b098defB751B7401B5f6d147a3"
        )
        return

    w3_conn = Web3(Web3.HTTPProvider(rpc_url))
    if not w3_conn.is_connected():
        print(f"❌ Connection Error: Node target offline at {rpc_url}")
        sys.exit(1)

    print(f"✓ Linked to network ledger. Chain ID: {w3_conn.eth.chain_id}")
    install_solc("0.8.26")

    compiled_sol = compile_files()

    # 1. Deploy ProvenanceLedger
    ledger_args = [account_address]
    ledger_address = deploy_contract(
        w3_conn, compiled_sol, "ProvenanceLedger.sol",
        "ProvenanceLedger", account_address, private_key, ledger_args
    )
    print(f"✅ LEDGER DEPLOYED: {ledger_address}")

    # 2. Deploy ProvenanceRegistry (Passing Ledger Address to Constructor)
    registry_args = [ledger_address]
    registry_address = deploy_contract(
        w3_conn, compiled_sol, "ProvenanceRegistry.sol",
        "ProvenanceRegistry", account_address, private_key, registry_args
    )
    print(f"✅ REGISTRY DEPLOYED: {registry_address}")

    mock_deployment_output(ledger_address, registry_address)


def compile_files():
    """Reads contract source code and runs standard Solidity compilation."""
    with open("src/contracts/ProvenanceLedger.sol", "r", encoding="utf-8") as file_in:
        ledger_src = file_in.read()
    with open("src/contracts/ProvenanceRegistry.sol", "r", encoding="utf-8") as file_in:
        registry_src = file_in.read()

    return compile_standard({
        "language": "Solidity",
        "sources": {
            "ProvenanceLedger.sol": {"content": ledger_src},
            "ProvenanceRegistry.sol": {"content": registry_src}
        },
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    }, allow_paths=os.path.abspath("node_modules"))


# pylint: disable=too-many-arguments,too-many-positional-arguments
def deploy_contract(w3_conn, compiled_sol, file_name, contract_name, account, pkey, args):
    """Signs and transmits raw deployment transactions to the target node."""
    abi = compiled_sol["contracts"][file_name][contract_name]["abi"]
    bytecode = compiled_sol["contracts"][file_name][contract_name]["evm"]["bytecode"]["object"]

    nonce = w3_conn.eth.get_transaction_count(account)
    contract_obj = w3_conn.eth.contract(abi=abi, bytecode=bytecode)

    tx_data = contract_obj.constructor(*args).build_transaction({
        "chainId": w3_conn.eth.chain_id,
        "gasPrice": w3_conn.eth.gas_price,
        "from": account,
        "nonce": nonce,
    })

    signed_tx = w3_conn.eth.account.sign_transaction(tx_data, private_key=pkey)
    tx_hash = w3_conn.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3_conn.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress


def mock_deployment_output(ledger_addr, registry_addr):
    """Updates the public JSON state configuration file with deployed addresses."""
    settlement_path = "public/settlement.json"
    data = {"contracts": {}}

    if os.path.exists(settlement_path):
        try:
            with open(settlement_path, "r", encoding="utf-8") as file_in:
                data = json.load(file_in)
        except json.JSONDecodeError:
            pass

    data["contracts"]["Intelligence_Ledger"] = ledger_addr
    data["contracts"]["Provenance_Registry"] = registry_addr

    with open(settlement_path, "w", encoding="utf-8") as file_out:
        json.dump(data, file_out, indent=2)
    print(f"✓ Configuration map synchronized in {settlement_path}")


if __name__ == "__main__":
    run_deployment_loop()
