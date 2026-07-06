#!/usr/bin/env python3
"""
EPIPHANY PROTOCOL - DYNAMIC APPRAISAL ENGINE
Values text trajectories and signs EIP-712 envelopes.
"""
from dataclasses import dataclass
from eth_account import Account
from eth_account.messages import encode_typed_data as encode_structured_data

@dataclass
class AppraisalParams:
    """Container for EIP-712 signing parameters."""
    data_hash: str
    price: int
    ipfs_cid: str
    nonce: int
    expiry: int
    creator: str

class AppraisalEngine:
    """Multi-variable valuation engine for reasoning trajectories."""

    def __init__(self, eit_rate: float = 0.10):
        self.eit_rate = eit_rate  # 1 EIT = $0.10 USD

    def calculate_valuation(self, trajectory: str) -> float:
        """
        Price = Base Cost × Information Density × Scarcity Metric × Demand Vector
        """
        base_cost = 100.0  # $100 USD base
        info_density = min(len(trajectory) / 100.0, 2.5)  # Max 2.5x
        scarcity = 1.2     # Default 1.2x
        demand = 1.5       # Default 1.5x

        usd_price = base_cost * info_density * scarcity * demand
        return usd_price

    def usd_to_eit(self, usd_amount: float) -> int:
        """Converts USD to EIT tokens (scaled to 18 decimals)."""
        eit_amount = usd_amount / self.eit_rate
        return int(eit_amount * 10**18)

    def sign_appraisal_eip712(self, params: AppraisalParams, private_key: str,
                              chain_id: int, contract_address: str):
        """Signs the appraisal using EIP-712 structured data."""
        domain_data = {
            "name": "DataAssetRegistry",
            "version": "1",
            "chainId": chain_id,
            "verifyingContract": contract_address
        }

        message_types = {
            "Appraisal": [
                {"name": "dataHash", "type": "bytes32"},
                {"name": "price", "type": "uint256"},
                {"name": "ipfsCID", "type": "string"},
                {"name": "nonce", "type": "uint256"},
                {"name": "expiry", "type": "uint256"},
                {"name": "creator", "type": "address"},
            ]
        }

        dh = params.data_hash
        if isinstance(dh, str) and dh.startswith("0x"):
            dh = bytes.fromhex(dh[2:])
        elif isinstance(dh, str):
            dh = bytes.fromhex(dh)

        message = {
            "dataHash": dh,
            "price": params.price,
            "ipfsCID": params.ipfs_cid,
            "nonce": params.nonce,
            "expiry": params.expiry,
            "creator": params.creator
        }

        # pylint: disable=no-value-for-parameter
        structured_msg = encode_structured_data(
            domain_data=domain_data,
            message_types=message_types,
            message_data=message
        )

        signed_msg = Account.sign_message(signable_message=structured_msg, private_key=private_key)
        return signed_msg.signature.hex()

def main():
    """Main entry point for appraisal engine demonstration."""
    engine = AppraisalEngine()

    # Mock data for demonstration
    trajectory = "SEC Liquidity Injection 2024 analysis..."
    usd_price = engine.calculate_valuation(trajectory)
    eit_price = engine.usd_to_eit(usd_price)

    print(f"[Wurk] Valuation: ${usd_price:.2f} USD -> {eit_price / 10**18:.2f} EIT")

if __name__ == "__main__":
    main()
