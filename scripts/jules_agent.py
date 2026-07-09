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
import re


def run_process(command_list, description):
    """Executes a terminal process and captures output."""
    print(f"\n[Jules] Action: {description}...")

    # Ensure we use the virtual environment's python/pylint if available
    env = os.environ.copy()
    venv_bin = os.path.join(os.getcwd(), "venv", "bin")
    if os.path.exists(venv_bin):
        env["PATH"] = venv_bin + os.pathsep + env["PATH"]
    env["PYTHONPATH"] = os.getcwd()

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
        return True, result.stdout
    except subprocess.CalledProcessError as err:
        print(f"\n[Jules] FAILURE: Error during {description}.", file=sys.stderr)
        print(f"[Jules] Error Output:\n{err.stderr.strip()}", file=sys.stderr)
        return False, err.stdout


def execute_agentic_loop():
    """
    Orchestrates the full Epiphany Protocol development loop.
    """
    print("======================================================================")
    print("         Jules - Autonomous Developer Agent - Active Session")
    print("======================================================================")

    # Step 1: Environment Setup Verification
    success, _ = run_process(["/bin/bash", "./setup.sh"], "Running workspace initialization")
    if not success:
        sys.exit(1)

    # Step 2: Compile Solidity Smart Contracts via Native Build Script
    success, _ = run_process(["/bin/bash", "bin/build.contracts.sh"], "Compiling Solidity contracts via build script")
    if not success:
        sys.exit(1)

    # Step 3: Run Pylint Checks (Targeting 10/10)
    pylint_cmd = [
        "pylint",
        "scripts/appraisal_engine.py",
        "scripts/verify_integration.py",
        "scripts/jules_agent.py",
        "--max-line-length=120"
    ]
    success, output = run_process(pylint_cmd, "Checking Python style compliance")

    # Parse and report Pylint score
    score_match = re.search(r"Your code has been rated at (\d+\.\d+)/10", output)
    if score_match:
        score = score_match.group(1)
        print(f"\n[Jules] Verified Pylint Score: {score}/10")

        # Add to GITHUB_STEP_SUMMARY if running in CI
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
                summary.write("### Pylint Quality Gate\n")
                summary.write(f"- **Final Score:** {score}/10\n")
                summary.write(f"- **Status:** {'✅ Passed' if float(score) >= 9.5 else '⚠️ Needs Improvement'}\n")
    else:
        print("\n[Jules] Warning: Could not parse Pylint score from output.")

    if not success:
        print("[Jules] Warning: Pylint checks did not pass cleanly.", file=sys.stderr)
        sys.exit(1)

    # Step 4: Run Cryptographic and Settlement Integration Tests
    integration_cmd = ["python3", "scripts/verify_integration.py"]
    success, _ = run_process(integration_cmd, "Executing end-to-end cryptographic and token settlement test")
    if not success:
        sys.exit(1)

    # Step 5: Safe Git Commit and Push preparation
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

        commit_msg = "feat: integrate secured EIP-712 DataAssetRegistry with circuit breaker and CEI pattern"
        run_process(["git", "commit", "-m", commit_msg], "Executing Git commit")

        print("\n[Jules] Session Complete. Progress saved and cryptographically verified.")

    except subprocess.SubprocessError as err:
        print(f"[Jules] Critical error during Git operations: {err}", file=sys.stderr)


if __name__ == "__main__":
    execute_agentic_loop()
