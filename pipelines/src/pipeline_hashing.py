"""
EPIPHANY PIPELINE HASHING - CRYPTOGRAPHIC CONTRACT VERIFICATION
"""
import os
import sys
import hashlib
import json
import datetime
import argparse
import tempfile

def generate_proof_packet(file_path, evaluator):
    """
    Generates a cryptographic proof packet for a target file.
    """
    if not os.path.exists(file_path):
        print(f"[Wurk] ❌ Error: File not found at {file_path}")
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

    print("[Wurk] \n[Wurk] Proof Packet Generated Successfully.")
    print(f"[Wurk] Target: {file_path}")
    print(f"[Wurk] SHA256: {sha256_hash}")
    print(f"[Wurk] Output: {output_path}\n")
    return sha256_hash

def run_test_suite():
    """
    Executes a self-test of the hashing logic using a temporary file.
    """
    print("[Wurk] 🧪 Running Pipeline Hashing Self-Test...")
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write("Test content for Epiphany hashing")
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256("Test content for Epiphany hashing".encode()).hexdigest()
        actual_hash = generate_proof_packet(tmp_path, "Test-Evaluator")

        if expected_hash == actual_hash:
            print("[Wurk] ✨ Hashing Verification Passed.")
        else:
            print("[Wurk] ❌ Hashing Verification Failed.")
            sys.exit(1)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Epiphany Pipeline Hashing Tool")
    parser.add_argument("file", nargs="?", help="Path to the file to hash")
    parser.add_argument("--evaluator", default="LexTrinity-Alpha", help="Evaluator identity")
    parser.add_argument("--test", action="store_true", help="Run hashing logic self-test")

    args = parser.parse_args()

    if args.test:
        run_test_suite()
    elif args.file:
        generate_proof_packet(args.file, args.evaluator)
    else:
        parser.print_help()
