#!/bin/bash
# setup.sh - Epiphany Automated Environment Initialization

echo "[Wurk] Initializing Decentralized Command Center in /app..."
cd /app || exit

# 1. Configure Git Identity
echo "[Wurk] Setting cryptographic commit identity..."
git config --local user.name "wurk-coder"
git config --local user.email "wurk@epiphany.network"

# 2. Establish Dual-Remote Architecture (Overlapping Push)
echo "[Wurk] Wiring overlapping remotes for GitHub and GitLab..."

# Dynamically grab the current GitHub fetch URL (e.g., https://github.com/gamezcagle95-dev/studious-umbrella.git)
CURRENT_ORIGIN=$(git config --get remote.origin.url)

# Set the primary push to the existing GitHub origin
git remote set-url --push origin "$CURRENT_ORIGIN"

# Format and append the secondary push target for GitLab private CI testing
# (Replacing 'github.com' with 'gitlab.com' for the mirror)
GITLAB_MIRROR="${CURRENT_ORIGIN/github.com/gitlab.com}"
git remote set-url --add --push origin "$GITLAB_MIRROR"

# 3. Environment Isolation & Dependencies
echo "[Wurk] Activating virtual environment for dependency isolation..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[Wurk] venv not found. Creating a new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

echo "[Wurk] Installing Python dependencies into venv..."
pip install --upgrade pip
pip install web3 eth-account requests pandas

# 4. Install Smart Contract Tooling (Hardhat/Foundry/Remix integration)
echo "[Wurk] Installing Node dependencies for smart contract compilation..."
if [ -f "package.json" ]; then
    npm install
else
    echo "[Wurk] No package.json detected. Skipping npm install."
fi

echo "[Wurk] Setup complete. Environment is isolated and remotes are synchronized."
