"""
deploy.py - Epiphany Protocol Smart Contract Compiler and Deployer

Programmatically deploys the full protocol stack (ProvenanceLedger, ProvenanceRegistry,
and DataAssetRegistry), configures on-chain AccessControl roles, and writes
verified deployed contract addresses to public/settlement.json.
Includes a simulation fallback for local development and dry-runs.
"""

import os
import sys
import json
from typing import Dict, Any
from web3 import Web3
from dotenv import load_dotenv

# Load workspace configuration parameters
load_dotenv()

OUTPUT_ARTIFACT_PATH = "public/settlement.json"


def load_compiled_artifact(contract_name: str) -> Dict[str, Any]:
    """
    Loads ABI and Bytecode from our latest standardized compiler directory.
    """
    artifact_path = os.path.join("artifacts/contracts/latest", f"{contract_name}.json")
    if not os.path.exists(artifact_path):
        print(f"[Wurk] Error: Compiled artifact not found at {artifact_path}.", file=sys.stderr)
        print("[Wurk] Please run 'bin/build.contracts.sh' before deploying.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(artifact_path, "r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except (json.JSONDecodeError, IOError) as err:
        print(f"[Wurk] Error reading compiler artifact: {err}", file=sys.stderr)
        sys.exit(1)


def save_settlement_manifest(ledger: str, registry: str, clearing: str, is_sim: bool = False):
    """
    Synchronizes deployment addresses to public/settlement.json.
    """
    address_manifest = {
        "contracts": {
            "Intelligence_Ledger": ledger,
            "Provenance_Registry": registry,
            "Data_Asset_Registry": clearing
        }
    }

    os.makedirs(os.path.dirname(OUTPUT_ARTIFACT_PATH), exist_ok=True)
    with open(OUTPUT_ARTIFACT_PATH, "w", encoding="utf-8") as out_file:
        json.dump(address_manifest, out_file, indent=2)

    msg = "Simulation mode" if is_sim else "Deployment complete"
    print(f"✓ {msg} manifest saved to: {OUTPUT_ARTIFACT_PATH}")


def deploy_contract(w3: Web3, account: Any, pkey: str, name: str, args: list) -> str:
    """Deploys a single contract and returns its address."""
    artifact = load_compiled_artifact(name)
    contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
    nonce = w3.eth.get_transaction_count(account.address)

    tx = contract.constructor(*args).build_transaction({
        "chainId": w3.eth.chain_id,
        "from": account.address,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=pkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"[Wurk] Transmitted transaction for {name}. Hash: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[Wurk] {name} deployed successfully to: {receipt.contractAddress}")
    return receipt.contractAddress


# pylint: disable=too-many-locals
def deploy_and_permission_contracts() -> Dict[str, str]:
    """
    Executes the sequential broadcast of smart contract bytecodes,
    and configures on-chain AccessControl permissions for minters.
    """
    print("[Wurk] Initializing on-chain deployment loop...")

    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    deployer_pkey = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

    if not deployer_pkey:
        print("⚠️  Warning: DEPLOYER_PRIVATE_KEY or PRIVATE_KEY not set.")
        print("💡 Simulation Mode: Mocking configuration outputs.")
        save_settlement_manifest(
            "0x4c0883a69102937d6231471b5dbb6204fe302702fd307ce2304598dcf3e346d1",
            "0x71C7656EC7ab88b098defB751B7401B5f6d147a3",
            "0x1234567890123456789012345678901234567890",
            is_sim=True
        )
        return {}

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"[Wurk] Error: Failed to connect to RPC node at {rpc_url}", file=sys.stderr)
        sys.exit(1)

    deployer = w3.eth.account.from_key(deployer_pkey)
    print(f"[Wurk] Connected to Chain ID: {w3.eth.chain_id}. Deployer: {deployer.address}")

    # 1. Deploy ProvenanceLedger
    ledger_addr = deploy_contract(
        w3, deployer, deployer_pkey, "ProvenanceLedger", [deployer.address]
    )

    # 2. Deploy ProvenanceRegistry
    reg_addr = deploy_contract(w3, deployer, deployer_pkey, "ProvenanceRegistry", [ledger_addr])

    # 3. Deploy DataAssetRegistry
    max_price = 100 * 10**18
    args = [ledger_addr, reg_addr, deployer.address, max_price]
    clearing_addr = deploy_contract(w3, deployer, deployer_pkey, "DataAssetRegistry", args)

    # 4. Grant MINTER_ROLE
    print("[Wurk] Configuring dynamic AccessControl roles...")
    reg_artifact = load_compiled_artifact("ProvenanceRegistry")
    registry = w3.eth.contract(address=reg_addr, abi=reg_artifact["abi"])
    minter_role = Web3.keccak(text="MINTER_ROLE")

    tx = registry.functions.grantRole(minter_role, clearing_addr).build_transaction({
        "chainId": w3.eth.chain_id,
        "from": deployer.address,
        "nonce": w3.eth.get_transaction_count(deployer.address),
        "gasPrice": w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=deployer_pkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[Wurk] Granted MINTER_ROLE. Hash: {tx_hash.hex()}")

    save_settlement_manifest(ledger_addr, reg_addr, clearing_addr)
    return {
        "Intelligence_Ledger": ledger_addr,
        "Provenance_Registry": reg_addr,
        "Data_Asset_Registry": clearing_addr
    }


if __name__ == "__main__":
    deploy_and_permission_contracts()
