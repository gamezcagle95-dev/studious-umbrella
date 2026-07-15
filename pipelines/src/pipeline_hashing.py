"""
pipeline_hashing.py - Provenance Hashing and Proof Packet Generator

Calculates SHA-256 hashes of weights or datasets and constructs verified
proof packets to certify data and model asset integrity.
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass


@dataclass
class ProofPacket:
    """Represents a cryptographic proof packet for AI pipeline artifacts."""
    file_path: str
    sha256_hash: str
    file_size_bytes: int
    evaluator: str
    timestamp: str


def calculate_file_hash(file_path: str, chunk_size: int = 65536) -> str:
    """
    Calculates the SHA-256 hash of a file in chunks to optimize memory.

    Args:
        file_path (str): The system path to the target file.
        chunk_size (int): The size of chunks to read into memory.

    Returns:
        str: The hex representation of the SHA-256 hash.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file_handle:
        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def save_proof_packet(packet: ProofPacket, output_dir: str) -> str:
    """
    Saves the generated proof packet metadata to the specified artifacts directory.

    Args:
        packet (ProofPacket): The populated metadata dataclass.
        output_dir (str): Target directory for artifact persistence.

    Returns:
        str: The path to the created JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "proof_packet.json")

    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(asdict(packet), file_handle, indent=4)

    return output_path


def process_file(file_path: str, evaluator: str, output_dir: str) -> None:
    """
    Validates and hashes a file, then writes its metadata proof packet.

    Args:
        file_path (str): Path of the file to process.
        evaluator (str): Cryptographic identity of the evaluator.
        output_dir (str): Directory where output artifacts are written.
    """
    try:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Target path '{file_path}' is not a valid file.")

        file_size = os.path.getsize(file_path)

        print(f"[Wurk] Processing asset: {file_path} ({file_size} bytes)")
        sha256_hash = calculate_file_hash(file_path)
        print(f"[Wurk] Calculated SHA-256: {sha256_hash}")

        timestamp = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat().replace("+00:00", "Z")

        packet = ProofPacket(
            file_path=os.path.abspath(file_path),
            sha256_hash=sha256_hash,
            file_size_bytes=file_size,
            evaluator=evaluator,
            timestamp=timestamp
        )

        saved_path = save_proof_packet(packet, output_dir)
        print(f"[Wurk] Proof packet saved successfully: {saved_path}")

    except FileNotFoundError as err:
        print(f"[Wurk] Error: {err}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"[Wurk] Error: Insufficient permissions to read file '{file_path}'", file=sys.stderr)
        sys.exit(1)
    except IOError as err:
        print(f"[Wurk] Critical I/O Error processing file: {err}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main execution entry point analyzing CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate cryptographic proof packets for AI weights and data assets."
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to the input file (e.g., weights.bin, dataset.csv) to be hashed."
    )
    parser.add_argument(
        "--evaluator",
        default="LexTrinity-Alpha",
        help="The cryptographic identity of the evaluator (defaults to 'LexTrinity-Alpha')."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Execute an isolated test run using temporary dummy weights."
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts",
        help="Directory where the output proof packet should be saved (defaults to 'artifacts')."
    )

    args = parser.parse_args()

    # Enforce standard execution bounds
    if not args.test and not args.file_path:
        parser.error(
            "The input file_path argument is required unless running in test mode with --test."
        )

    if args.test:
        print("[Wurk] Initializing isolated pipeline test run...")
        # Create a self-cleaning temporary file to simulate dummy training weights
        with tempfile.NamedTemporaryFile(delete=True) as temp_weights:
            temp_weights.write(b"MOCK_MODEL_WEIGHTS_TRAINING_STATE_DATA_010101")
import tempfile
import os

if args.test:
    print("[Wurk] Initializing isolated pipeline test run...")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
    try:
        tmp.write(b"MOCK_MODEL_WEIGHTS_TRAINING_STATE_DATA_010101")
        tmp.flush()
        tmp.close()
        process_file(tmp.name, args.evaluator, args.output_dir)
    finally:
        os.unlink(tmp.name)
    print("[Wurk] Test run completed. Temporary assets have been garbage-collected.")

            # Process the temporary file
            process_file(temp_weights.name, args.evaluator, args.output_dir)
        print("[Wurk] Test run completed. Temporary assets have been garbage-collected.")
    else:
        process_file(args.file_path, args.evaluator, args.output_dir)


if __name__ == "__main__":
    main()
