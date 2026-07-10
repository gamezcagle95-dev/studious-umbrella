"""
deploy.py - Epiphany Protocol Smart Contract Compiler and Deployer

Programmatically deploys the full protocol stack (ProvenanceLedger, ProvenanceRegistry,
and DataAssetRegistry), configures on-chain AccessControl roles, and writes
verified deployed contract addresses to public/settlement.json.
"""

import os
import sys
import json
from dataclasses import dataclass
from typing import Dict, Any
from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

OUTPUT_ARTIFACT_PATH = "public/settlement.json"


@dataclass
class EnvConfig:
    """Stores shell environment configurations securely."""
    rpc_url: str
    chain_id: int
    private_key: str
    deployer_address: str
    senior_investigator: str


@dataclass
class BaseProtocolsConfig:
    """Stores the deployed contract addresses of our base protocol layer."""
    ledger_address: str
    registry_address: str


@dataclass
class MarketConfig:
    """Stores configuration parameters for the DataAssetRegistry contract."""
    payment_token: str
    provenance_registry: str
    senior_investigator: str
    max_price_per_token: int


def get_env_config() -> EnvConfig:
    """
    Parses and checksums active environment variables from .env.
    Returns a structured EnvConfig dataclass.
    """
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    chain_id = int(os.getenv("CHAIN_ID", "1337"))

    private_key = os.getenv("APPRAISER_PRIVATE_KEY")
    if not private_key:
        print("[Wurk] Error: APPRAISER_PRIVATE_KEY is missing from .env.", file=sys.stderr)
        sys.exit(1)

    try:
        # Derive deployer address programmatically from the private key
        # pylint: disable=no-value-for-parameter
        deployer_acc = Account.from_key(private_key)
        deployer_address = Web3.to_checksum_address(deployer_acc.address)
    except ValueError as err:
        print(f"[Wurk] Error: Invalid private key format: {err}", file=sys.stderr)
        sys.exit(1)

    senior_investigator = os.getenv("SENIOR_INVESTIGATOR_ADDRESS", str(deployer_address))
    checksummed_investigator = Web3.to_checksum_address(senior_investigator)

    return EnvConfig(
        rpc_url=rpc_url,
        chain_id=chain_id,
        private_key=private_key,
        deployer_address=deployer_address,
        senior_investigator=checksummed_investigator
    )


def load_compiled_artifact(contract_name: str) -> Dict[str, Any]:
    """Loads ABI and Bytecode from our latest standardized compiler directory."""
    artifact_path = os.path.join("artifacts/contracts/latest", f"{contract_name}.json")
    if not os.path.exists(artifact_path):
        print(f"[Wurk] Error: Compiled artifact not found at {artifact_path}.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(artifact_path, "r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except (json.JSONDecodeError, IOError) as err:
        print(f"[Wurk] Error reading compiler artifact: {err}", file=sys.stderr)
        sys.exit(1)


def build_eip1559_transaction(w3: Web3, tx_params: Dict[str, Any]) -> Dict[str, Any]:
    """Appends EIP-1559 fee fields (maxFeePerGas, maxPriorityFeePerGas) to transaction."""
    try:
        priority_fee = w3.eth.max_priority_fee
        base_fee = w3.eth.get_block('latest')['baseFeePerGas']
        max_fee = (base_fee * 2) + priority_fee

        tx_params.update({
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee
        })
    except (ValueError, KeyError, TransactionNotFound):
        # Fallback to legacy type-0 gas pricing if EIP-1559 fields are rejected by the RPC node
        tx_params.update({
            "gasPrice": w3.eth.gas_price
        })
    return tx_params


def deploy_base_protocols(w3: Web3, env: EnvConfig) -> BaseProtocolsConfig:
    """Deploys ProvenanceLedger and ProvenanceRegistry sequentially."""
    nonce = w3.eth.get_transaction_count(env.deployer_address)

    # 1. Deploy ProvenanceLedger (EIT Payment Token)
    print("[Wurk] Deploying ProvenanceLedger...")
    artifact = load_compiled_artifact("ProvenanceLedger")
    contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])

    tx_params = build_eip1559_transaction(w3, {
        "chainId": env.chain_id,
        "from": env.deployer_address,
        "nonce": nonce
    })
    construct_tx = contract.constructor(env.senior_investigator).build_transaction(tx_params)
    signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=env.private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    ledger_address = receipt.contractAddress
    print(f"[Wurk] ProvenanceLedger deployed successfully to: {ledger_address}")
    nonce += 1

    # 2. Deploy ProvenanceRegistry (Minter Registry)
    print("[Wurk] Deploying ProvenanceRegistry...")
    artifact = load_compiled_artifact("ProvenanceRegistry")
    contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])

    tx_params = build_eip1559_transaction(w3, {
        "chainId": env.chain_id,
        "from": env.deployer_address,
        "nonce": nonce
    })
    construct_tx = contract.constructor(ledger_address).build_transaction(tx_params)
    signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=env.private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    registry_address = receipt.contractAddress
    print(f"[Wurk] ProvenanceRegistry deployed successfully to: {registry_address}")

    return BaseProtocolsConfig(
        ledger_address=ledger_address,
        registry_address=registry_address
    )


def deploy_market_clearinghouse(w3: Web3, env: EnvConfig, base: BaseProtocolsConfig) -> str:
    """Deploys DataAssetRegistry contract on-chain."""
    nonce = w3.eth.get_transaction_count(env.deployer_address)
    artifact = load_compiled_artifact("DataAssetRegistry")
    contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])

    # Configure 100 EIT standard circuit breaker price boundary
    max_price_per_token = 100 * 10**18

    tx_params = build_eip1559_transaction(w3, {
        "chainId": env.chain_id,
        "from": env.deployer_address,
        "nonce": nonce
    })

    construct_tx = contract.constructor(
        base.ledger_address,
        base.registry_address,
        env.senior_investigator,
        max_price_per_token
    ).build_transaction(tx_params)

    signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=env.private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[Wurk] DataAssetRegistry deployed successfully to: {receipt.contractAddress}")
    return receipt.contractAddress


def delegate_minter_role(w3: Web3, env: EnvConfig, base: BaseProtocolsConfig,
                         dar_address: str) -> None:
    """Grants the MINTER_ROLE on ProvenanceRegistry to the DataAssetRegistry address."""
    nonce = w3.eth.get_transaction_count(env.deployer_address)
    registry_artifact = load_compiled_artifact("ProvenanceRegistry")
    registry_instance = w3.eth.contract(address=base.registry_address, abi=registry_artifact["abi"])

    minter_role_hash = Web3.keccak(text="MINTER_ROLE")

    tx_params = build_eip1559_transaction(w3, {
        "chainId": env.chain_id,
        "from": env.deployer_address,
        "nonce": nonce
    })

    grant_tx = registry_instance.functions.grantRole(
        minter_role_hash,
        dar_address
    ).build_transaction(tx_params)

    signed_grant_tx = w3.eth.account.sign_transaction(grant_tx, private_key=env.private_key)
    grant_hash = w3.eth.send_raw_transaction(signed_grant_tx.raw_transaction)

    # Wait for the receipt and assert success status explicitly (Resolves silent fail bug)
    receipt = w3.eth.wait_for_transaction_receipt(grant_hash)
    if receipt.status != 1:
        raise RuntimeError(f"AccessControl role-grant transaction failed: {grant_hash.hex()}")
    print(f"[Wurk] Successfully granted MINTER_ROLE on Registry to DAR. Hash: {grant_hash.hex()}")


def run_deployment_loop() -> None:
    """Orchestrates contract deployment pipeline and role configurations."""
    print("[Wurk] Initializing production deployment loop...")
    env = get_env_config()

    # 1. Establish Web3 Provider Connection
    w3 = Web3(Web3.HTTPProvider(env.rpc_url))
    if not w3.is_connected():
        # Fallback to local simulation mode with clearly invalid sentinel addresses
        print("[Wurk] RPC offline. Initializing local deployment simulation...")
        address_manifest = {
            "contracts": {
                "Intelligence_Ledger": "0x0000000000000000000000000000000000000001",
                "Provenance_Registry": "0x0000000000000000000000000000000000000002",
                "Data_Asset_Registry": "0x0000000000000000000000000000000000000003"
            }
        }
        os.makedirs(os.path.dirname(OUTPUT_ARTIFACT_PATH), exist_ok=True)
        with open(OUTPUT_ARTIFACT_PATH, "w", encoding="utf-8") as out_file:
            json.dump(address_manifest, out_file, indent=2)

        # Write to deployments.json in the root
        deployments_manifest = {
            "contracts": address_manifest["contracts"],
            "DATA_ASSET_REGISTRY_ADDRESS": address_manifest["contracts"].get("Data_Asset_Registry")
        }
        with open("deployments.json", "w", encoding="utf-8") as dep_file:
            json.dump(deployments_manifest, dep_file, indent=2)

        print(f"[Wurk] Simulation complete. Mock addresses saved to: {OUTPUT_ARTIFACT_PATH}")
os.makedirs(os.path.dirname(os.path.abspath('deployments.json')), exist_ok=True)
with open('deployments.json', 'w', encoding='utf-8') as dep_file:
    json.dump(deployments_manifest, dep_file, indent=2)

    # 2. Sequential Deployments
    base_config = deploy_base_protocols(w3, env)
    dar_address = deploy_market_clearinghouse(w3, env, base_config)

    # 3. Grant Minter Roles
    delegate_minter_role(w3, env, base_config, dar_address)

    # 4. Write verified addresses to manifest using the nested JSON format
    address_manifest = {
        "contracts": {
            "Intelligence_Ledger": base_config.ledger_address,
            "Provenance_Registry": base_config.registry_address,
            "Data_Asset_Registry": dar_address
        }
    }

    os.makedirs(os.path.dirname(OUTPUT_ARTIFACT_PATH), exist_ok=True)
    with open(OUTPUT_ARTIFACT_PATH, "w", encoding="utf-8") as out_file:
        json.dump(address_manifest, out_file, indent=2)

    # Write to deployments.json in the root
    deployments_manifest = {
        "contracts": address_manifest["contracts"],
        "DATA_ASSET_REGISTRY_ADDRESS": address_manifest["contracts"].get("Data_Asset_Registry")
    }
    with open("deployments.json", "w", encoding="utf-8") as dep_file:
        json.dump(deployments_manifest, dep_file, indent=2)

    print(f"[Wurk] Deployment complete. Address manifest saved to: {OUTPUT_ARTIFACT_PATH}")


if __name__ == "__main__":
    run_deployment_loop()
