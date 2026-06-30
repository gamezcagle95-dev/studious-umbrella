# ==============================================================================
# EPIPHANY WEB3 SETTLEMENT MACHINE - DUAL-CONTRACT DEPLOYMENT ENGINE
# Profile Context: Susan D. Cagle <gamezcagle95@gmail.com>
# ==============================================================================
"""
Deterministic contract deployment engine for the Epiphany Protocol.
Handles sequential deployment of the ProvenanceLedger and ProvenanceRegistry.
"""
import os
import json
import sys
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

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

    # Compile files in a single pass
    compiled_sol = compile_files()

    # 1. Deploy ProvenanceLedger
    ledger_address = deploy_contract(
        w3, compiled_sol, "ProvenanceLedger.sol", "ProvenanceLedger",
        account_address, private_key, [account_address]
    )
    print(f"✅ LEDGER DEPLOYED: {ledger_address}")

    # 2. Deploy ProvenanceRegistry (Passing Ledger Address to Constructor)
    registry_address = deploy_contract(
        w3, compiled_sol, "ProvenanceRegistry.sol", "ProvenanceRegistry",
        account_address, private_key, [ledger_address]
    )
    print(f"✅ REGISTRY DEPLOYED: {registry_address}")

    mock_deployment_output(ledger_address, registry_address)

def compile_files():
    """
    Compiles Solidity source files using the solc standard JSON input.
    """
    with open("src/contracts/ProvenanceLedger.sol", "r", encoding="utf-8") as f:
        ledger_src = f.read()
    with open("src/contracts/ProvenanceRegistry.sol", "r", encoding="utf-8") as f:
        registry_src = f.read()

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

def deploy_contract(w3, compiled_sol, file_name, contract_name, account, pkey, args):
    """
    Executes a contract deployment transaction.
    """
    abi = compiled_sol["contracts"][file_name][contract_name]["abi"]
    bytecode = compiled_sol["contracts"][file_name][contract_name]["evm"]["bytecode"]["object"]

    nonce = w3.eth.get_transaction_count(account)
    contract_obj = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx = contract_obj.constructor(*args).build_transaction({
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": account,
        "nonce": nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=pkey)
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
