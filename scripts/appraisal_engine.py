"""
EPIPHANY APPRAISAL ENGINE - DATA ASSET VALUATION & SIGNING
"""
import os
import json
import time
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Hardcoded conversion rate: 1 EIT = $0.10 USD
# So 1 USD = 10 EIT tokens
USD_TO_EIT_RATE = 10
EIT_DECIMALS = 18

# Security Thresholds
MAX_ENTROPY_THRESHOLD = 5.0  # Threshold for noise filtering (bits per character)

@dataclass
class AppraisalMetrics:
    """Container for the B*I*S*D valuation metrics."""
    base_cost: float          # B: Base Cost
    information_density: float # I: Information Density
    scarcity_metric: float     # S: Scarcity Metric
    demand_vector: float       # D: Demand Vector

@dataclass
class AppraisalParams:
    """Container for appraisal signature parameters to satisfy Pylint."""
    data_hash: bytes
    price_eit_wei: int
    ipfs_cid: str
    creator_address: str
    nonce: int
    estimated_tokens: int = 0
    expiry_seconds: int = 3600

class AppraisalEngine:
    """
    Engine for calculating data asset value and generating cryptographic signatures.
    """
    def __init__(self, appraiser_private_key: str, chain_id: int,
                 contract_address: str) -> None:
        # pylint: disable=no-value-for-parameter
        self.account = Account.from_key(appraiser_private_key)
        self.chain_id = chain_id
        self.contract_address = Web3.to_checksum_address(contract_address)

    @staticmethod
    def calculate_entropy(data: str) -> float:
        """
        Calculates Shannon entropy of the input string to detect high-entropy noise.
        """
        if not data:
            return 0.0
        probabilities = [count / len(data) for count in Counter(data).values()]
        return -sum(p * math.log2(p) for p in probabilities)

    def calculate_valuation(self, metrics: AppraisalMetrics, raw_data: str) -> float:
        """
        Calculates the final USD asset value using the formula: B * I * S * D.
        Filters out high-entropy noise before calculation.
        """
        entropy = self.calculate_entropy(raw_data)

        # Guardrail: If entropy exceeds threshold, we treat it as noise and nullify value
        if entropy > MAX_ENTROPY_THRESHOLD:
            print(f"⚠️ Warning: High-entropy noise detected ({entropy:.2f}). Rejecting appraisal.")
            return 0.0

        return (
            metrics.base_cost *
            metrics.information_density *
            metrics.scarcity_metric *
            metrics.demand_vector
        )

    def usd_to_eit_wei(self, usd_value: float) -> int:
        """
        Converts a USD valuation into EIT token units (Wei-equivalent, 10^18).
        """
        eit_amount = usd_value * USD_TO_EIT_RATE
        return int(eit_amount * (10 ** EIT_DECIMALS))

    def generate_appraisal_signature(self, params: AppraisalParams) -> Dict[str, Any]:
        """
        Generates an EIP-712 structured signature for the appraisal.
        """
        expiry = int(time.time()) + params.expiry_seconds
        est_tokens = params.estimated_tokens if params.estimated_tokens > 0 else params.price_eit_wei

        # EIP-712 Domain
        domain_data = {
            "name": "DataAssetRegistry",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": self.contract_address,
        }

        # EIP-712 Types
        message_types = {
            "AssetAppraisal": [
                {"name": "assetHash", "type": "bytes32"},
                {"name": "price", "type": "uint256"},
                {"name": "estimatedTokens", "type": "uint256"},
                {"name": "ipfsCID", "type": "string"},
                {"name": "nonce", "type": "uint256"},
                {"name": "expiry", "type": "uint256"},
                {"name": "creator", "type": "address"},
            ],
        }

        # The Appraisal Payload
        appraisal_data = {
            "assetHash": params.data_hash,
            "price": params.price_eit_wei,
            "estimatedTokens": est_tokens,
            "ipfsCID": params.ipfs_cid,
            "nonce": params.nonce,
            "expiry": expiry,
            "creator": params.creator_address,
        }

        # Encode and Sign
        signable_message = encode_typed_data(
            domain_data=domain_data,
            message_types=message_types,
            message_data=appraisal_data
        )

        signed_message = self.account.sign_message(signable_message)

        return {
            "appraisal": appraisal_data,
            "signature": signed_message.signature.hex()
        }

def resolve_data_asset_registry_address() -> str:
    """
    Resolves and checksums the DataAssetRegistry address from environment
    or from the deployments.json fallback.
    """
    dar_env = os.getenv("DATA_ASSET_REGISTRY_ADDRESS")
    if dar_env:
        return Web3.to_checksum_address(dar_env)

    # Resolve path to deployments.json in the repository root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    deployments_path = os.path.join(root_dir, "deployments.json")
    if not os.path.exists(deployments_path):
        deployments_path = "deployments.json"

    try:
        with open(deployments_path, "r", encoding="utf-8") as dep_file:
            dep_data = json.load(dep_file)
        contracts = dep_data.get("contracts", {})
        dar_addr = contracts.get("Data_Asset_Registry") or dep_data.get("DATA_ASSET_REGISTRY_ADDRESS")
        if not dar_addr:
            raise ValueError("Data_Asset_Registry address not found in deployments.json")
        return Web3.to_checksum_address(dar_addr)
    except Exception as err:
        raise RuntimeError(f"Failed to load DATA_ASSET_REGISTRY_ADDRESS: {err}") from err


def run_engine_example() -> None:
    """
    Demonstrates the full appraisal workflow with entropy guardrails.
    """
    print("🚀 Initializing Epiphany Appraisal Engine with Guardrails...")

    # Configuration
    p_key = os.getenv("APPRAISER_PRIVATE_KEY", "0x" + "9" * 64)
    c_id = int(os.getenv("CHAIN_ID", "1337"))
    c_addr = resolve_data_asset_registry_address()

    engine = AppraisalEngine(p_key, c_id, c_addr)

    # 1. Ingest Raw Data
    raw_data = "Forensic analysis: Transaction 0xabc... reveals 4.2B unauthorized movement."
    d_hash = Web3.keccak(text=raw_data)
    print(f"✓ Data Ingested. Asset Hash: {d_hash.hex()}")

    # 2. Calculate Metrics (B * I * S * D)
    metrics = AppraisalMetrics(base_cost=100.0, information_density=1.8,
                              scarcity_metric=2.5, demand_vector=1.5)

    valuation_usd = engine.calculate_valuation(metrics, raw_data)
    price_eit_wei = engine.usd_to_eit_wei(valuation_usd)

    print(f"✓ Entropy Calculated: {engine.calculate_entropy(raw_data):.2f}")
    print(f"✓ Valuation Calculated: ${valuation_usd:,.2f} USD")

    if valuation_usd == 0:
        return

    # 3. Generate Signed Appraisal
    creator_raw = os.getenv("CREATOR_ADDRESS")
    if not creator_raw:
        raise ValueError("CREATOR_ADDRESS environment variable is required.")
    creator = Web3.to_checksum_address(creator_raw)
    params = AppraisalParams(data_hash=d_hash, price_eit_wei=price_eit_wei,
                            ipfs_cid=os.getenv("IPFS_CID", "QmPK1s3pNYsjnu7wT2L7ck5nS1..."),
                            creator_address=creator, nonce=int(time.time()))

    # pylint: disable=no-value-for-parameter
    result = engine.generate_appraisal_signature(params)

    # Manual conversion for HexBytes
    ser_app = result["appraisal"].copy()
    ser_app["dataHash"] = "0x" + ser_app["dataHash"].hex()
    ser_res = {"appraisal": ser_app, "signature": result["signature"]}

    print("\n--- CRYPTOGRAPHIC APPRAISAL PROOF ---")
    print(json.dumps(ser_res, indent=2))
    print("--------------------------------------\n")

if __name__ == "__main__":
    run_engine_example()
