#!/bin/bash
set -e

echo "[Epiphany] Initializing decentralized command center..."

# 1. Python Virtual Environment Setup
if [ ! -d "venv" ]; then
    echo "[Epiphany] Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "[Epiphany] Installing dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
pip install pylint # Ensure pylint is available

# 2. Git Configuration (Idempotent)
echo "[Epiphany] Configuring Git remote mirrors..."
# Add GitLab mirror if configured
if [ "$EPIPHANY_GITLAB_MIRROR" == "true" ]; then
    if ! git remote | grep -q "gitlab"; then
        echo "[Epiphany] Adding GitLab mirror..."
        # Example mirror setup, would normally need a real URL
        # git remote add gitlab https://gitlab.com/epiphany/protocol-mirror.git
    fi
fi

# 3. Pathing
export PYTHONPATH=$PYTHONPATH:.
echo "export PYTHONPATH=\$PYTHONPATH:." >> venv/bin/activate

echo "[Epiphany] Setup complete. System is ready."
