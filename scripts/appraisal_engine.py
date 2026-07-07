"""
EPIPHANY APPRAISAL ENGINE - DATA ASSET VALUATION & SIGNING
"""
import os
import json
import time
import math
from collections import Counter
from dataclasses import dataclass
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
    # pylint: disable=invalid-name
    data_hash: bytes
    price_eit_wei: int
    ipfsCID: str
    creator_address: str
    nonce: int
    expiry_seconds: int = 3600

class AppraisalEngine:
    """
    Engine for calculating data asset value and generating cryptographic signatures.
    """
    def __init__(self, appraiser_private_key, chain_id, contract_address):
        # pylint: disable=no-value-for-parameter
        self.account = Account.from_key(appraiser_private_key)
        self.chain_id = chain_id
        self.contract_address = contract_address

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

    def generate_appraisal_signature(self, params: AppraisalParams):
        """
        Generates an EIP-712 structured signature for the appraisal.
        """
        expiry = int(time.time()) + params.expiry_seconds

        # EIP-712 Domain
        domain_data = {
            "name": "DataAssetRegistry",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": self.contract_address,
        }

        # EIP-712 Types
        message_types = {
            "Appraisal": [
                {"name": "dataHash", "type": "bytes32"},
                {"name": "price", "type": "uint256"},
                {"name": "ipfsCID", "type": "string"},
                {"name": "nonce", "type": "uint256"},
                {"name": "expiry", "type": "uint256"},
                {"name": "creator", "type": "address"},
            ],
        }

        # The Appraisal Payload
        appraisal_data = {
            "dataHash": params.data_hash,
            "price": params.price_eit_wei,
            "ipfsCID": params.ipfsCID,
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

def run_engine_example():
    """
    Demonstrates the full appraisal workflow with entropy guardrails.
    """
    print("🚀 Initializing Epiphany Appraisal Engine with Guardrails...")

    # Configuration
    p_key = os.getenv("APPRAISER_PRIVATE_KEY", "0x" + "9" * 64)
    c_id = int(os.getenv("CHAIN_ID", "1337"))
    c_addr = Web3.to_checksum_address(os.getenv("DATA_ASSET_REGISTRY_ADDRESS", "0x" + "a" * 40))

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
    creator = Web3.to_checksum_address("0x71C7656EC7ab88b098defB751B7401B5f6d147a3")
    params = AppraisalParams(data_hash=d_hash, price_eit_wei=price_eit_wei,
                            ipfsCID="QmPK1s3pNYsjnu7wT2L7ck5nS1...", creator_address=creator,
                            nonce=int(time.time()))

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
