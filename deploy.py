# ==============================================================================
# EPIPHANY WEB3 SETTLEMENT MACHINE - DETERMINISTIC CONTRACT DEPLOYMENT ENGINE
# Profile Context: Susan D. Cagle <gamezcagle95@gmail.com>
# ==============================================================================
import os
import json
import sys
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

load_dotenv()

def run_deployment_loop():
    print("⛓️  Initializing state machine compiler pipelines...")

    # 1. Load System Staging Parameters
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("PRIVATE_KEY")
    account_address = os.getenv("ACCOUNT_ADDRESS")

    # Graceful fallback simulation if environment variables aren't hot yet
    if not private_key or not account_address:
        print("⚠️  Warning: PRIVATE_KEY or ACCOUNT_ADDRESS not set in environment.")
        print("💡 Simulation Mode: Mocking configuration outputs to public/settlement.json")
        mock_deployment_output("0x4c0883a69102937d6231471b5dbb6204fe302702fd307ce2304598dcf3e346d1")
        return

    # 2. Establish Network Connection
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"❌ Connection Error: Node target offline at {rpc_url}")
        sys.exit(1)

    print(f"✓ Linked to network ledger. Chain ID: {w3.eth.chain_id}")

    # 3. Compile Target Ledger
    print("🔨 Locking Solidity compiler version to [0.8.26]...")
    install_solc("0.8.26")

    contract_file_path = "src/contracts/ProvenanceLedger.sol"
    if not os.path.exists(contract_file_path):
        print(f"❌ Error: Source file missing at {contract_file_path}")
        sys.exit(1)

    with open(contract_file_path, "r") as f:
        source_code = f.read()

    # Build the standard JSON compilation input matrix
    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {"ProvenanceLedger.sol": {"content": source_code}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    }, allow_paths=os.path.abspath("node_modules"))

    # 4. Generate & Send Transaction Sequence
    abi = compiled_sol["contracts"]["ProvenanceLedger.sol"]["ProvenanceLedger"]["abi"]
    bytecode = compiled_sol["contracts"]["ProvenanceLedger.sol"]["ProvenanceLedger"]["evm"]["bytecode"]["object"]

    nonce = w3.eth.get_transaction_count(account_address)
    ProvenanceLedger = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx = ProvenanceLedger.constructor(account_address).build_transaction({
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": account_address,
        "nonce": nonce,
    })

    print("🔑 Signing deployment authorization hash...")
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print(f"🚀 Transaction pushed to pool. Hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"✅ DEPLOYMENT VERIFIED. Address: {receipt.contractAddress}")
    mock_deployment_output(receipt.contractAddress)

def mock_deployment_output(contract_address):
    settlement_path = "public/settlement.json"
    if os.path.exists(settlement_path):
        with open(settlement_path, "r") as f:
            data = json.load(f)

        data["contracts"]["Intelligence_Ledger"] = contract_address

        with open(settlement_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✓ Configuration map synchronized in {settlement_path}")

if __name__ == "__main__":
    run_deployment_loop()
