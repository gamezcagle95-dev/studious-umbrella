"""
EPIPHANY APPRAISAL ENGINE - DATA ASSET VALUATION & SIGNING
"""
import os
import json
import time
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
    expiry_seconds: int = 3600

class AppraisalEngine:
    """
    Engine for calculating data asset value and generating cryptographic signatures.
    """
    def __init__(self, appraiser_private_key, chain_id, contract_address):
        self.account = Account.from_key(appraiser_private_key)
        self.chain_id = chain_id
        self.contract_address = contract_address

    def calculate_valuation(self, metrics: AppraisalMetrics) -> float:
        """
        Calculates the final USD asset value using the formula: B * I * S * D.
        """
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

def run_engine_example():
    """
    Demonstrates the full appraisal workflow.
    """
    print("🚀 Initializing Epiphany Appraisal Engine...")

    # Configuration (use environment or defaults for testing)
    private_key = os.getenv("APPRAISER_PRIVATE_KEY", "0x" + "9" * 64)
    chain_id = int(os.getenv("CHAIN_ID", "1337"))
    # Use str type for default to satisfy Pylint
    default_addr = "0x" + "a" * 40
    contract_address = Web3.to_checksum_address(os.getenv("DATA_ASSET_REGISTRY_ADDRESS",
                                                         default_addr))

    engine = AppraisalEngine(private_key, chain_id, contract_address)

    # 1. Ingest Raw Data (Mocked for this example)
    raw_data = "Forensic analysis: Transaction 0xabc... reveals 4.2B unauthorized movement."
    data_hash = Web3.keccak(text=raw_data) # Keep as bytes
    print(f"✓ Data Ingested. Asset Hash: {data_hash.hex()}")

    # 2. Calculate Metrics (B * I * S * D)
    metrics = AppraisalMetrics(
        base_cost=100.0,
        information_density=1.8,
        scarcity_metric=2.5,
        demand_vector=1.5
    )

    valuation_usd = engine.calculate_valuation(metrics)
    price_eit_wei = engine.usd_to_eit_wei(valuation_usd)

    print(f"✓ Valuation Calculated: ${valuation_usd:,.2f} USD")
    print(f"✓ EIT Token Equivalent: {price_eit_wei} (10^18 units)")

    # 3. Generate Signed Appraisal
    ipfs_cid = "QmPK1s3pNYsjnu7wT2L7ck5nS1..."
    creator = Web3.to_checksum_address("0x71C7656EC7ab88b098defB751B7401B5f6d147a3")
    nonce = int(time.time())

    params = AppraisalParams(
        data_hash=data_hash,
        price_eit_wei=price_eit_wei,
        ipfs_cid=ipfs_cid,
        creator_address=creator,
        nonce=nonce
    )

    result = engine.generate_appraisal_signature(params)

    # Convert bytes to hex for JSON serialization in the print
    serializable_result = json.loads(json.dumps(result))
    serializable_result["appraisal"]["dataHash"] = "0x" + result["appraisal"]["dataHash"].hex()

    print("\n--- CRYPTOGRAPHIC APPRAISAL PROOF ---")
    print(json.dumps(serializable_result, indent=2))
    print("--------------------------------------\n")

if __name__ == "__main__":
    run_engine_example()
