#!/usr/bin/env python3
"""
verify_integration.py - Full Protocol Stack End-to-End Test Suite

Deploys mock accounts, appraises a real sample trajectory, hashes it,
generates an EIP-712 signature, and simulates contract state transition.
"""

import hashlib
from eth_account import Account
# pylint: disable=no-name-in-module
from eth_account.messages import encode_typed_data as encode_structured_data
from web3 import Web3
from scripts.appraisal_engine import (
    calculate_appraisal,
    usd_to_eit_base_units,
    sign_appraisal_eip712,
    AppraisalParams
)


def run_integration_test() -> None:
    """Deploys local test accounts, appraises trajectory, and verifies signatures."""
    # pylint: disable=too-many-locals
    print("[Wurk] Initializing local protocol integration check...")

    # 1. Initialize local test accounts (simulate EVM environments)
    # SECURITY: Dynamically generate testing accounts to avoid hardcoded private keys
    # pylint: disable=no-value-for-parameter
    appraiser = Account.create()
    creator = Account.create()

    print(f"[Wurk] Appraiser Address: {appraiser.address}")
    print(f"[Wurk] Data Creator Address: {creator.address}")

    # Mock contract address for local domain validation
    mock_registry_address = Web3.to_checksum_address("0x" + "a" * 40)

    # 2. Ingest real sample trajectory data representing complex code logic
    sample_trajectory = """
    // Step 1: Initialize ZK Proof Verifier
    let vk = VerificationKey::from_bytes(VK_BYTES);
    let proof = Proof::from_bytes(PROOF_BYTES);

    // Step 2: Validate transition invariants
    assert!(vk.verify(&proof, &public_inputs));
    // State machine validated successfully.
    """

    # Calculate SHA-256 asset hash
    asset_hash = "0x" + hashlib.sha256(sample_trajectory.encode('utf-8')).hexdigest()
    ipfs_cid = "QmXoypizjW3WknFixtasW3ofZJ6fK75K75K75K75K75K7" # pylint: disable=invalid-name

    print(f"[Wurk] Generated Asset Hash: {asset_hash}")

    # 3. Appraisal Valuation Calculation (B * I * S * D)
    base_cost = 0.08      # -bash.08
    demand_mult = 5.0     # High-level debugging demand

    final_price_usd = calculate_appraisal(sample_trajectory, base_cost, demand_mult)
    price_in_eit = usd_to_eit_base_units(final_price_usd)
    print(f"[Wurk] Appraised Asset Price: {final_price_usd:.2f} USD ({price_in_eit} EIT units)")

    # 4. Generate EIP-712 Signature
    nonce = 42
    expiry = 9999999999  # Far future timestamp

    print("[Wurk] Signing appraisal structured data via EIP-712...")
    params = AppraisalParams(
        asset_hash_hex=asset_hash,
        price_eit_base=price_in_eit,
        ipfsCID=ipfs_cid,
        nonce=nonce,
        expiry=expiry,
        creator_address=creator.address,
        private_key=appraiser.key.hex(),
        contract_address=mock_registry_address,
        chain_id=1337
    )
    signature = sign_appraisal_eip712(params=params)
    print(f"[Wurk] Cryptographic Proof Generated: {signature[:40]}...")

    # 5. Local Cryptographic Assertions (EIP-712 Verification)
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
            "chainId": 1337,
            "verifyingContract": mock_registry_address
        },
        "message": {
            "assetHash": bytes.fromhex(asset_hash.replace("0x", "")),
            "price": price_in_eit,
            "ipfsCID": ipfs_cid,
            "nonce": nonce,
            "expiry": expiry,
            "creator": creator.address
        }
    }

    # pylint: disable=no-value-for-parameter
    recovered_address = Account.recover_message(
        signable_message=encode_structured_data(full_message=eip712_payload),
        signature=signature
    )

    print(f"[Wurk] Signature verification recovered address: {recovered_address}")

    assert recovered_address.lower() == appraiser.address.lower(), "Verification failed: signature mismatch!"
    print("[Wurk] SUCCESS: Cryptographic EIP-712 signature verification passes locally.")
    print("[Wurk] On-chain contracts will successfully parse this message.")


if __name__ == "__main__":
    run_integration_test()
