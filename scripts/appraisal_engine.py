"""
appraisal_engine.py - EIP-712 Appraisal Valuation and Signing Engine

Calculates dynamic data values (B * I * S * D) and outputs verified EIP-712 signatures.
"""

import math
from dataclasses import dataclass
from eth_account import Account
# pylint: disable=no-name-in-module
from eth_account.messages import encode_typed_data as encode_structured_data

EIT_USD_RATE = 0.10  # 1 EIT = $0.10 USD


@dataclass
class AppraisalParams:
    """Dataclass to hold appraisal signing parameters."""
    # pylint: disable=too-many-instance-attributes
    asset_hash_hex: str
    price_eit_base: int
    ipfs_cid: str
    nonce: int
    expiry: int
    creator_address: str
    private_key: str
    contract_address: str
    chain_id: int = 1337


def usd_to_eit_base_units(usd_value: float) -> int:
    """Converts USD appraisal into EIT base units (18 decimals)."""
    eit_amount = usd_value / EIT_USD_RATE
    return int(eit_amount * 10**18)


def calculate_shannon_entropy(text: str) -> float:
    """Calculates character-level Shannon Entropy of the text."""
    if not text:
        return 0.0
    freqs = {}
    for char in text:
        freqs[char] = freqs.get(char, 0) + 1

    entropy = 0.0
    total_chars = len(text)
    for count in freqs.values():
        p = count / total_chars
        entropy -= p * math.log2(p)
    return entropy


def get_information_density(text: str) -> float:
    """Normalizes Shannon Entropy into a density multiplier."""
    entropy = calculate_shannon_entropy(text)
    return round(max(0.1, entropy / 4.5), 3)


def get_scarcity_metric(text: str) -> float:
    """Simulates semantic scarcity based on vocabulary variance."""
    if not text:
        return 0.5
    unique_chars = len(set(text))
    total_chars = len(text)
    diversity_ratio = unique_chars / total_chars
    return round(max(0.5, math.exp(diversity_ratio * 2.0)), 3)


def calculate_appraisal(text: str, base_cost: float, demand_multiplier: float) -> float:
    """
    Computes final valuation using the multi-variable formula:
    Price = Base Cost * Information Density * Scarcity * Demand
    """
    info_density = get_information_density(text)
    scarcity = get_scarcity_metric(text)
    return round(base_cost * info_density * scarcity * demand_multiplier, 6)


def sign_appraisal_eip712(params: AppraisalParams) -> str:
    """Constructs and signs an EIP-712 compliant AssetAppraisal struct."""
    eip712_payload = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"}
            ],
            "AssetAppraisal": [
                {"name": "assetHash", "type": "bytes32"},
                {"name": "price", "type": "uint256"},
                {"name": "ipfsCID", "type": "string"},
                {"name": "nonce", "type": "uint256"},
                {"name": "expiry", "type": "uint256"},
                {"name": "creator", "type": "address"}
            ]
        },
        "primaryType": "AssetAppraisal",
        "domain": {
            "name": "DataAssetRegistry",
            "version": "1",
            "chainId": params.chain_id,
            "verifyingContract": params.contract_address
        },
        "message": {
            "assetHash": bytes.fromhex(
                params.asset_hash_hex.replace("0x", "")
            ),
            "price": params.price_eit_base,
            "ipfsCID": params.ipfs_cid,
            "nonce": params.nonce,
            "expiry": params.expiry,
            "creator": params.creator_address
        }
    }

    structured_msg = encode_structured_data(full_message=eip712_payload)
    # pylint: disable=no-value-for-parameter
    signed_msg = Account.sign_message(
        signable_message=structured_msg, private_key=params.private_key
    )
    return signed_msg.signature.hex()
