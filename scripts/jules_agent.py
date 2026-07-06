"""
jules_agent.py - Real-World Autonomous Developer Agent

Natively executes the Epiphany Protocol development loop:
1. Environment Initialization (setup.sh)
2. Contract Compilation (bin/build.contracts.sh)
3. Pylint Compliance checks (Enforcing 10/10)
4. Cryptographic Integration verification
5. Safe Git Commit execution upon successful validation
"""

import sys
import subprocess
import os


def run_process(command_list, description):
    """Executes a terminal process and captures output."""
    print(f"\n[Jules] Action: {description}...")

    # Ensure we use the virtual environment's python/pylint if available
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    venv_bin = os.path.join(os.getcwd(), "venv", "bin")
    if os.path.exists(venv_bin):
        env["PATH"] = venv_bin + os.pathsep + env["PATH"]

    try:
        result = subprocess.run(
            command_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            env=env
        )
        print(f"[Jules] Success: {result.stdout.strip()[:200]}")
        if len(result.stdout) > 200:
            print("        ... [Output Truncated]")
        return True
    except subprocess.CalledProcessError as err:
        print(f"\n[Jules] FAILURE: Error during {description}.", file=sys.stderr)
        print(f"[Jules] Error Output:\n{err.stderr.strip()}", file=sys.stderr)
        return False


def execute_agentic_loop():
    """
    Orchestrates the full Epiphany Protocol development loop.
    """
    print("======================================================================")
    print("         Jules - Autonomous Developer Agent - Active Session")
    print("======================================================================")

    # Step 1: Environment Setup Verification
    if not run_process(["/bin/bash", "./setup.sh"], "Running workspace initialization"):
        sys.exit(1)

    # Step 2: Compile Solidity Smart Contracts via Native Build Script
    if not run_process(["/bin/bash", "bin/build.contracts.sh"],
                       "Compiling Solidity contracts via build script"):
        sys.exit(1)

    # Step 3: Run Pylint Checks (Targeting 10/10)
    pylint_cmd = [
        "pylint",
        "scripts/appraisal_engine.py",
        "scripts/verify_integration.py",
        "scripts/jules_agent.py",
        "scripts/generate_trust_report.py",
        "pipelines/src/pipeline_hashing.py"
    ]
    if not run_process(pylint_cmd, "Checking Python style compliance"):
        print("[Jules] Warning: Pylint checks did not pass cleanly.", file=sys.stderr)
        sys.exit(1)

    # Step 4: Run Cryptographic and Settlement Integration Tests
    integration_cmd = ["python3", "scripts/verify_integration.py"]
    if not run_process(integration_cmd,
                       "Executing end-to-end cryptographic and token settlement test"):
        sys.exit(1)

    # Step 5: Run Forensic Trust Audit
    audit_cmd = ["python3", "scripts/generate_trust_report.py", "."]
    if not run_process(audit_cmd, "Generating Forensic Trust Report"):
        sys.exit(1)

    # Step 6: Safe Git Commit and Push preparation
    print("\n[Jules] All quality gates successfully passed.")
    print("[Jules] Preparing workspace commit...")

    try:
        status_check = subprocess.run(
            ["git", "status", "--porcelain"],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        if not status_check.stdout.strip():
            print("[Jules] No changes detected in workspace. Commit skipped.")
            return

        print("[Jules] Changes detected. Auto-staging and committing...")
        run_process(["git", "add", "."], "Staging modified and new files")

        commit_msg = "feat: implement forensic trust report generator and integrate into CI gate"
        run_process(["git", "commit", "-m", commit_msg], "Executing Git commit")

        print("\n[Jules] Session Complete. Progress saved and cryptographically verified.")

    except subprocess.SubprocessError as err:
        print(f"[Jules] Critical error during Git operations: {err}", file=sys.stderr)


if __name__ == "__main__":
    execute_agentic_loop()
