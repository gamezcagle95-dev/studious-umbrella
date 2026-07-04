#!/bin/bash
# setup.sh - Epiphany Automated Environment Initialization

# Exit immediately if a command exits with a non-zero status
set -e

echo "[Wurk] Initializing Decentralized Command Center in /app..."
cd /app || exit 1

# 1. Configure Git Identity
echo "[Wurk] Setting cryptographic commit identity..."
git config --local user.name "wurk-coder"
git config --local user.email "wurk@epiphany.network"

# 2. Establish Dual-Remote Architecture (Overlapping Push)
echo "[Wurk] Wiring overlapping remotes for GitHub and GitLab..."

# Dynamically grab the current GitHub fetch URL
CURRENT_ORIGIN=$(git config --get remote.origin.url)

# Reset push URLs to prevent duplicates on re-run
git config --local --unset-all remote.origin.pushurl || true

# Set the primary push to the existing GitHub origin
git remote set-url --push origin "$CURRENT_ORIGIN"

# Format and append the secondary push target for GitLab private CI testing
# (Replacing 'github.com' with 'gitlab.com' for the mirror)
GITLAB_MIRROR="${CURRENT_ORIGIN/github.com/gitlab.com}"
git remote set-url --add --push origin "$GITLAB_MIRROR"

# 3. Environment Isolation & Dependencies
echo "[Wurk] Activating virtual environment for dependency isolation..."
if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
else
    echo "[Wurk] venv not found. Creating a new virtual environment..."
    python3 -m venv venv
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

echo "[Wurk] Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "[Wurk] Error: requirements.txt not found."
    exit 1
fi

# 4. Install Smart Contract Tooling
echo "[Wurk] Enforcing supply-chain security for Node.js..."
echo "ignore-scripts=true" > .npmrc

echo "[Wurk] Installing Node dependencies for smart contract compilation..."
if [ -f "package.json" ]; then
    npm install
else
    echo "[Wurk] No package.json detected. Skipping npm install."
fi

echo "[Wurk] Setup complete. Environment is isolated and remotes are synchronized."
