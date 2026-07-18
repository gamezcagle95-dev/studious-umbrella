"""
scripts/fetch_coderabbit_feedback.py - Programmatic CodeRabbit & Review Bot Feedback Fetcher

Fetches, parses, and displays unresolved review-thread feedback from automated review bots
(such as octopus-review[bot] and coderabbitai) for active or all open pull requests.
"""

import os
import sys
import subprocess
import urllib.request
import json
import re
from typing import Dict, Any, List


def run_git_cmd(args: List[str]) -> str:
    """Safely executes a git CLI command and returns clean stdout."""
    try:
        res = subprocess.run(
            ["git"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return "UNKNOWN"


def fetch_json(url: str) -> Any:
    """Fetches JSON data from a public URL with optional authentication."""
    headers = {"User-Agent": "Mozilla/5.0"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as err: # pylint: disable=broad-exception-caught
        print(f"⚠️ API Fetch warning: {err}", file=sys.stderr)
        return None


def get_repo_coordinates() -> tuple[str, str]:
    """Extracts owner and repo names from remote origin URL."""
    remote_url = run_git_cmd(["remote", "get-url", "origin"])
    if not remote_url or remote_url == "UNKNOWN":
        return "", ""

    # Secure regular expression matching both HTTPS and SSH formats of github.com origin URLs
    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", remote_url)
    if match:
        return match.group(1), match.group(2)
    return "", ""


def parse_feedback(comment: Dict[str, Any]) -> Dict[str, str]:
    """Parses automated review bot comment structure into structured issue fields."""
    body = comment.get("body", "")
    lines = [line.strip() for line in body.split("\n") if line.strip()]

    severity = "🟡 MEDIUM"
    title = "Review Needed"
    location = f"{comment.get('path')}:{comment.get('line')}"

    # Extract title and severity from standard review bot headers
    # Example format: **🔴 MINTER_ROLE is never granted — ...**
    for line in lines:
        if line.startswith("**") and ("🔴" in line or "🟠" in line or "🟡" in line or "🟢" in line):
            header = line.strip("*")
            if "🔴" in header:
                severity = "🔴 CRITICAL"
                header = header.replace("🔴", "").strip()
            elif "🟠" in header:
                severity = "🟠 HIGH"
                header = header.replace("🟠", "").strip()
            elif "🟡" in header:
                severity = "🟡 MEDIUM"
                header = header.replace("🟡", "").strip()
            elif "🟢" in header:
                severity = "🟢 LOW"
                header = header.replace("🟢", "").strip()
            title = header.split("—")[0].strip()
            break

    return {
        "severity": severity,
        "title": title,
        "location": location,
        "body_summary": body[:120].replace("\n", " ").strip() + "..."
    }


def analyze_pull_requests(target_prs: List[Dict[str, Any]], owner: str, repo: str) -> List[Dict[str, str]]:
    """Analyzes a list of pull requests and collects all bot feedback comments."""
    all_issues = []
    bot_names = {"octopus-review[bot]", "coderabbitai", "coderabbit[bot]", "coderabbitai[bot]"}

    for pr in target_prs[:3]:  # Limit to first 3 PRs to respect rate limits
        pr_number = pr["number"]
        pr_title = pr["title"]
        comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        comments = fetch_json(comments_url)

        if not comments:
            continue

        print(f"\nAnalyzing PR #{pr_number}: '{pr_title}' ({len(comments)} total review comments)")
        for comment in comments:
            author = comment.get("user", {}).get("login", "")
            if author in bot_names:
                issue = parse_feedback(comment)
                issue["pr"] = str(pr_number)
                all_issues.append(issue)
    return all_issues


def main() -> None:
    """Orchestrates fetching, parsing, and printing unresolved review feedback."""
    print("======================================================================")
    print("      Epiphany Protocol - CodeRabbit & Review Bot Feedback Fetcher")
    print("======================================================================")

    owner, repo = get_repo_coordinates()
    if not owner or not repo:
        print("❌ Could not resolve repository owner or name from git remote origin URL.", file=sys.stderr)
        sys.exit(1)

    active_branch = run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"])
    print(f"Target Repository: {owner}/{repo}")
    print(f"Active Git Branch: {active_branch}")

    # 1. Fetch all open Pull Requests
    pulls_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&per_page=100"
    prs = fetch_json(pulls_url)
    if not prs:
        print("❌ Could not fetch open pull requests or API rate limit exceeded.", file=sys.stderr)
        print("Please check your connection and GitHub API rate limits.")
        sys.exit(0)

    # 2. Find PR for current branch or fallback to all open PRs
    target_prs = [pr for pr in prs if pr["head"]["ref"] == active_branch]
    is_fallback = False
    if not target_prs:
        print(f"\n⚠️ No open pull request found specifically for active branch: {active_branch}")
        print("Falling back to analyzing unresolved feedback across all open pull requests...")
        target_prs = prs
        is_fallback = True

    # 3. Fetch and parse review comments
    all_issues = analyze_pull_requests(target_prs, owner, repo)

    # 4. Display findings in beautiful Markdown table format
    if not all_issues:
        print("\n✨ No unresolved current CodeRabbit review threads found.")
        sys.exit(0)

    print(f"\nCodeRabbit Issues for {owner}/{repo}:")
    print(f"Fallback Active: {is_fallback}")
    print("\n| # | PR | Severity | Issue Title | Location & Details | Type | Action |")
    print("|---|----|----------|-------------|-------------------|------|--------|")
    for idx, issue in enumerate(all_issues, 1):
        print(f"| {idx} | #{issue['pr']} | {issue['severity']} | {issue['title']} | "
              f"{issue['location']}<br>{issue['body_summary']} | 🐛 Bug | Review |")

    print("\n✓ Fetch and parsing completed successfully.\n")


if __name__ == "__main__":
    main()
