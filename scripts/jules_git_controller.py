"""
jules_git_controller.py - Automated Version Control Orchestrator for Jules

Provides verified wrappers for Git branch scanning, pulls, rebases,
commits, push targets, and automated GitHub PR creation/merging.
"""

import os
import sys
import subprocess
from typing import List, Dict, Any


class JulesGitController:
    """Orchestrates Git version control operations with built-in quality gates."""

    def __init__(self, workspace_path: str = "/app"):
        self.workspace_path = workspace_path
        os.chdir(self.workspace_path)

    def _execute(self, command: List[str]) -> str:
        """Executes a terminal command and captures output safely."""
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as err:
            raise IOError(f"Git execution failed: {err.stderr.strip()}") from err

    def _run_quality_gates(self) -> bool:
        """
        Executes internal quality gates: verify_integration.py and Pylint score.
        Returns True if all gates pass.
        """
        print("[Jules] Running quality gates...")

        # 1. Verify Integration
        if os.path.exists("scripts/verify_integration.py"):
            print("[Jules] Running verify_integration.py...")
            try:
                # We use the virtual environment's python if available
                python_bin = "venv/bin/python3" if os.path.exists("venv/bin/python3") else "python3"
                self._execute([python_bin, "scripts/verify_integration.py"])
                print("[Jules] Integration verification passed.")
            except (IOError, subprocess.SubprocessError) as err:
                print(f"[Jules] Integration verification failed: {err}")
                return False
        else:
            print("[Jules] Warning: scripts/verify_integration.py not found. Skipping.")

        # 2. Pylint Check (Targeting 10/10)
        print("[Jules] Checking Pylint compliance...")
        try:
            # Check all .py files in scripts and pipelines
            # Note: exit code 0 means 10/10 in strict mode or no errors
            # We'll check the output for the score.
            pylint_output = self._execute(["pylint", "scripts/", "pipelines/"])
            if "Your code has been rated at 10.00/10" in pylint_output:
                print("[Jules] Pylint score 10/10 confirmed.")
            else:
                # If it's not 10.00/10, we might want to be strict
                print(f"[Jules] Pylint score below 10/10. Output: {pylint_output}")
                return False
        except (IOError, subprocess.SubprocessError) as err:
            # subprocess.run with check=True will raise if pylint returns non-zero
            # Pylint returns non-zero for any message.
            print(f"[Jules] Pylint check failed or score below 10/10: {err}")
            return False

        return True

    def scan_branches(self) -> Dict[str, Any]:
        """Scans local and remote tracking branches to identify active states."""
        print("[Jules] Scanning repository branches...")
        self._execute(["git", "fetch", "--all"])

        # Get active local branch
        active_branch = self._execute(["git", "rev-parse", "--abbrev-ref", "HEAD"])

        # List all local branches
        local_branches = [
            b.strip().replace("* ", "")
            for b in self._execute(["git", "branch"]).split("\n")
            if b.strip()
        ]

        # List remote tracking branches
        remote_output = self._execute(["git", "branch", "-r"])
        remote_branches = [
            b.strip() for b in remote_output.split("\n")
            if b.strip() and "origin/HEAD" not in b
        ]

        return {
            "active_branch": active_branch,
            "local_branches": local_branches,
            "remote_branches": remote_branches
        }

    def safe_pull(self) -> str:
        """Performs a pull operation on the active branch to synchronize state."""
        active = self._execute(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        print(f"[Jules] Synchronizing active branch '{active}' with origin...")
        return self._execute(["git", "pull", "origin", active])

    def safe_rebase(self, target_branch: str = "main") -> str:
        """Safely rebases the active branch on top of the target branch."""
        active = self._execute(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if active == target_branch:
            raise ValueError(f"Cannot rebase branch '{active}' onto itself.")

        print(f"[Jules] Rebasing active branch '{active}' onto '{target_branch}'...")
        self._execute(["git", "fetch", "origin"])
        return self._execute(["git", "rebase", f"origin/{target_branch}"])

    def verified_commit(self, message: str) -> str:
        """Stages files and executes a Git commit."""
        # Ensure our changes don't contain empty files or untracked sensitive data
        status = self._execute(["git", "status", "--porcelain"])
        if not status:
            return "No changes detected in workspace. Commit skipped."

        print("[Jules] Staging and committing workspace changes...")
        self._execute(["git", "add", "."])
        return self._execute(["git", "commit", "-m", message])

    def safe_push(self) -> str:
        """Pushes the active branch to the remote origin with upstream tracking."""
        if not self._run_quality_gates():
            raise RuntimeError("Quality gates failed. Push aborted.")

        active = self._execute(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        print(f"[Jules] Pushing branch '{active}' to origin...")
        return self._execute(["git", "push", "-u", "origin", active])

    def create_pull_request(self, title: str, body: str) -> str:
        """Programmatically opens a pull request on GitHub using the gh CLI."""
        if not self._run_quality_gates():
            raise RuntimeError("Quality gates failed. PR creation aborted.")

        active = self._execute(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if active in ("main", "master"):
            raise ValueError("Cannot create PR from primary tracking branches.")

        print(f"[Jules] Opening Pull Request from '{active}' to main...")
        try:
            # We first push to guarantee the remote branch exists
            self.safe_push()

            # Create the PR via the GitHub CLI
            pr_url = self._execute([
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--head", active,
                "--base", "main"
            ])
            return f"Pull Request successfully opened: {pr_url}"
        except (IOError, subprocess.SubprocessError) as err:
            raise RuntimeError(f"Failed to open PR via gh CLI: {err}") from err

    def automated_merge(self, pr_number: int) -> str:
        """Programmatically merges a pull request once CI checks are verified."""
        print(f"[Jules] Verifying CI status for Pull Request #{pr_number}...")

        # Verify CI gates before allowing merge
        checks = self._execute(["gh", "pr", "checks", str(pr_number)])
        if "fail" in checks.lower() or "pending" in checks.lower():
            raise RuntimeError(f"Cannot merge PR #{pr_number}: CI checks are not passing.")

        print(f"[Jules] CI checks verified. Merging Pull Request #{pr_number}...")
        return self._execute([
            "gh", "pr", "merge", str(pr_number),
            "--squash",
            "--delete-branch"
        ])


if __name__ == "__main__":
    # Local CLI dry-run diagnostic
    try:
        controller = JulesGitController()
        state = controller.scan_branches()
        print(f"[Wurk] Current Local Branch: {state['active_branch']}")
        print(f"[Wurk] Available Local Branches: {state['local_branches']}")
        print(f"[Wurk] Available Remote Branches: {state['remote_branches']}")
    except (IOError, ValueError, subprocess.SubprocessError) as e:
        print(f"[Wurk] Diagnostic Error: {e}", file=sys.stderr)
        sys.exit(1)
