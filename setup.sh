#!/usr/bin/env bash
# setup.sh - Epiphany Automated Environment Initialization

# Exit immediately if a command exits with a non-zero status,
# treat unset variables as an error, and fail on pipe errors.
set -euo pipefail

# Get the absolute path of the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_ROOT}"

echo "[Protocol] Initializing Decentralized Command Center in ${REPO_ROOT}..."

# 1. Configure Git Identity
echo "[Protocol] Setting cryptographic commit identity..."
git config --local user.name "epiphany-coder"
git config --local user.email "dev@epiphany.network"

# 2. Establish Dual-Remote Architecture (Overlapping Push)
echo "[Protocol] Wiring overlapping remotes for GitHub and GitLab..."

# Dynamically grab the current GitHub fetch URL
CURRENT_ORIGIN=$(git config --get remote.origin.url)

# Reset push URLs to prevent duplicates on re-run
git config --local --unset-all remote.origin.pushurl || true

# Set the primary push to the existing GitHub origin
git remote set-url --push origin "${CURRENT_ORIGIN}"

# Format and append the secondary push target for GitLab private CI testing
# (Replacing 'github.com' with 'gitlab.com' for the mirror)
GITLAB_MIRROR="${CURRENT_ORIGIN/github.com/gitlab.com}"
git remote set-url --add --push origin "${GITLAB_MIRROR}"

# 3. Environment Isolation & Dependencies
echo "[Protocol] Activating virtual environment for dependency isolation..."
if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
else
    echo "[Protocol] venv not found. Creating a new virtual environment..."
    python3 -m venv venv
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

echo "[Protocol] Installing Python dependencies from requirements.txt..."
python3 -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo "[Protocol] Error: requirements.txt not found."
    exit 1
fi

# 4. Install Smart Contract Tooling
echo "[Protocol] Enforcing supply-chain security for Node.js..."
echo "ignore-scripts=true" > .npmrc

echo "[Protocol] Installing Node dependencies for smart contract compilation..."
if [ -f "package.json" ]; then
    npm install
else
    echo "[Protocol] No package.json detected. Skipping npm install."
fi

echo "[Protocol] Setup complete. Environment is isolated and remotes are synchronized."
