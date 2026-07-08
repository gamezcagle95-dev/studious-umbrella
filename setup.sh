#!/bin/bash
# ==============================================================================
# setup.sh - Epiphany Automated Environment Initialization
# Safe, idempotent setup script for isolated containers and CLI environments.
# ==============================================================================

set -eo pipefail

echo "[Wurk] Initializing Decentralized Command Center..."

# 1. Configure Git Identity (Local scope)
echo "[Wurk] Setting local Git commit identity..."
git config --local user.name "wurk-coder"
git config --local user.email "wurk@epiphany.network"

# 2. Establish Dual-Remote Architecture (Overlapping Push)
echo "[Wurk] Configuring overlapping remote targets..."
if git config --get remote.origin.url >/dev/null; then
    CURRENT_ORIGIN=$(git config --get remote.origin.url)

    # Unset all push URLs first to avoid conflicts
    git config --local --unset-all remote.origin.pushurl || true

    # Set standard push to GitHub
    git remote set-url --push origin "$CURRENT_ORIGIN"

    # Opt-in GitLab Mirroring
    if [ "$EPIPHANY_GITLAB_MIRROR" = "true" ]; then
        echo "[Wurk] Opt-in GitLab mirroring detected."
        # Format and append GitLab push target for private CI testing
        GITLAB_MIRROR="${CURRENT_ORIGIN/github.com/gitlab.com}"
        git remote set-url --add --push origin "$GITLAB_MIRROR"
        echo "[Wurk] Overlapping push targets configured successfully."
    else
        echo "[Wurk] GitLab mirroring is disabled (Default)."
    fi
else
    echo "[Wurk] Warning: 'origin' remote not set. Skipping overlapping push wiring."
fi

# 3. Environment Isolation & Python Dependencies
echo "[Wurk] Verifying Python virtual environment..."
if [ -d "venv" ]; then
    echo "[Wurk] Existing venv found. Activating..."
    # shellcheck source=/dev/null
    source venv/bin/activate
else
    echo "[Wurk] Creating a new virtual environment..."
    python3 -m venv venv
    # shellcheck source=/dev/null
    source venv/bin/activate
fi

echo "[Wurk] Upgrading pip and installing dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install web3 eth-account requests pandas python-dotenv pylint
fi

# 4. Install Smart Contract Tooling
echo "[Wurk] Checking for smart contract dependencies..."
if [ -f "package.json" ]; then
    npm install
else
    echo "[Wurk] No package.json detected. Skipping Node dependency resolution."
fi

echo "[Wurk] Setup complete. Environment is secure and isolated."
