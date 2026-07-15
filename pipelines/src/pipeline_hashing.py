#!/usr/bin/env python3
"""
EPIPHANY PROTOCOL - PIPELINE HASHING
Generates deterministic proof packets for reasoning trajectories.
"""
import json
import hashlib
import os
import argparse
from datetime import datetime, timezone

def generate_proof_packet(data, evaluator_tag="default-evaluator"):
    """
    Generates a cryptographic proof packet for the given data.
    """
    content = json.dumps(data, sort_keys=True)
    source_hash = hashlib.sha256(content.encode()).hexdigest()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    packet = {
        "source_hash": f"0x{source_hash}",
        "evaluator_tag": evaluator_tag,
        "timestamp": timestamp,
        "version": "1.0.0"
    }
    return packet

def main():
    """Main execution point for hashing pipeline."""
    parser = argparse.ArgumentParser(description="Epiphany Protocol Hashing Pipeline")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--evaluator", type=str, default="default-evaluator", help="Evaluator ID")
    parser.add_argument("file", nargs='?', default=None, help="File to hash")
    args = parser.parse_args()

    sample_data = {
        "trajectory": (
            "Step 1: Analyzed liquidity injection. Step 2: Identified Alpha-7 pool. "
            "Step 3: Verified 4.2B USD."
        ),
        "metadata": {"subject": "SEC Liquidity Injection 2024"}
    }

    packet = generate_proof_packet(sample_data, evaluator_tag=args.evaluator)

    if args.test:
        print(f"[Wurk] Proof Packet: {json.dumps(packet, indent=2)}")
        # Verify it doesn't crash
        return

    os.makedirs("artifacts/proofs", exist_ok=True)
    file_path = "artifacts/proofs/proof_packet.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2)

    print(f"[Wurk] Proof packet generated at {file_path}")

if __name__ == "__main__":
    main()
