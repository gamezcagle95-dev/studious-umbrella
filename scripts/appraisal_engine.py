# ==============================================================================
# EPIPHANY DYNAMIC APPRAISAL ENGINE - CRYPTOGRAPHIC VALUATION CORE
# Profile Context: Epiphany Protocol
# ==============================================================================
"""
Off-chain valuation engine that programmatically calculates data asset prices
and generates EIP-712 compliant signatures for on-chain settlement.
"""
import time
from dataclasses import dataclass
from typing import Dict, Any
from eth_account import Account
from eth_account.messages import encode_typed_data as encode_structured_data
from web3 import Web3

@dataclass
class AppraisalMetrics:
    """Quantitative inputs for the multi-variable valuation formula."""
    base_cost: float
    information_density: float
    scarcity_metric: float
    demand_vector: float

@dataclass
class AppraisalParams:
    """Parameters required for EIP-712 signing."""
    data_hash: bytes
    price_eit_wei: int
    ipfs_cid: str
    creator_address: str
    nonce: int
    expiry_delta: int = 3600

class AppraisalEngine:
    """
    Orchestrates the conversion of raw data metrics into verifiable on-chain appraisals.
    """
    def __init__(self, private_key: str, chain_id: int, contract_address: str):
        # pylint: disable=no-value-for-parameter
        self.account = Account.from_key(private_key=private_key)
        self.chain_id = chain_id
        self.contract_address = Web3.to_checksum_address(contract_address)

    def calculate_valuation(self, metrics: AppraisalMetrics, raw_data: str) -> float:
        """
        Calculates price = Base Cost * Density * Scarcity * Demand.
        Includes an off-chain guardrail to reject low-quality or noise data.
        """
        # Off-chain guardrail: Minimum length and entropy check (simulated)
        if len(raw_data) < 20:
            return 0.0

        valuation = (metrics.base_cost *
                     metrics.information_density *
                     metrics.scarcity_metric *
                     metrics.demand_vector)
        return round(valuation, 2)

    def usd_to_eit_wei(self, usd_amount: float) -> int:
        """
        Converts USD valuation to EIT tokens in Wei.
        Fixed exchange rate for simulation: 1 EIT = 100 USD.
        """
        eit_amount = usd_amount / 100.0
        return int(eit_amount * 10**18)

    def generate_appraisal_signature(self, params: AppraisalParams) -> Dict[str, Any]:
        """
        Generates an EIP-712 signature for the DataAssetRegistry.
        """
        expiry = int(time.time()) + params.expiry_delta

        domain_data = {
            "name": "DataAssetRegistry",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": self.contract_address,
        }

        # Updated to ipfsCID
        message = {
            "assetHash": params.data_hash,
            "price": params.price_eit_wei,
            "ipfsCID": params.ipfs_cid,
            "nonce": params.nonce,
            "expiry": expiry,
            "creator": Web3.to_checksum_address(params.creator_address),
        }

        types = {
            "AssetAppraisal": [
                {"name": "assetHash", "type": "bytes32"},
                {"name": "price", "type": "uint256"},
                {"name": "ipfsCID", "type": "string"},
                {"name": "nonce", "type": "uint256"},
                {"name": "expiry", "type": "uint256"},
                {"name": "creator", "type": "address"},
            ],
        }

        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                **types
            },
            "primaryType": "AssetAppraisal",
            "domain": domain_data,
            "message": message,
        }

        # pylint: disable=no-value-for-parameter
        signable_msg = encode_structured_data(full_message=structured_data)
        signed_msg = Account.sign_message(signable_message=signable_msg,
                                          private_key=self.account.key)

        return {
            "appraisal": message,
            "signature": signed_msg.signature.hex()
        }

if __name__ == "__main__":
    # Internal component test
    TEST_KEY_VAL = "0x" + "1" * 64
    engine_obj = AppraisalEngine(TEST_KEY_VAL, 1, "0x" + "2" * 40)
    test_metrics = AppraisalMetrics(1000.0, 1.2, 1.5, 1.1)
    val_res = engine_obj.calculate_valuation(test_metrics, "Valid forensic dataset analysis...")
    print(f"Test Valuation: {val_res} USD")
