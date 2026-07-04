"""
EPIPHANY PIPELINE HASHING - CRYPTOGRAPHIC CONTRACT VERIFICATION
"""
import os
import sys
import hashlib
import json
import datetime
import argparse

def generate_proof_packet(file_path, evaluator):
    """
    Generates a cryptographic proof packet for a target file.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        sys.exit(1)

    with open(file_path, "rb") as f:
        content = f.read()
        sha256_hash = hashlib.sha256(content).hexdigest()

    timestamp = datetime.datetime.now(datetime.timezone.utc)
    proof_packet = {
        "version": "1.0.0",
        "target": os.path.basename(file_path),
        "sha256": sha256_hash,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "evaluator": evaluator,
        "status": "STATICALLY_VERIFIED"
    }

    output_dir = "artifacts/proofs"
    os.makedirs(output_dir, exist_ok=True)

    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
    output_name = f"proof_{os.path.basename(file_path)}_{timestamp_str}.json"
    output_path = os.path.join(output_dir, output_name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(proof_packet, f, indent=2)

    print("\n[Wurk] Proof Packet Generated Successfully.")
    print(f"Target: {file_path}")
    print(f"SHA256: {sha256_hash}")
    print(f"Output: {output_path}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Epiphany Pipeline Hashing Tool")
    parser.add_argument("file", help="Path to the file to hash")
    parser.add_argument("--evaluator", default="LexTrinity-Alpha", help="Evaluator identity")

    args = parser.parse_args()
    generate_proof_packet(args.file, args.evaluator)
