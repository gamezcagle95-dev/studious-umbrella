#!/bin/bash
# ==============================================================================
# EPIPHANY PROTOCOL SETUP - CORE WORKSPACE INITIALIZATION
# System Profile: Epiphany Protocol
# ==============================================================================
set -e

echo "🚀 Initializing Epiphany Protocol Workspace..."

# 1. Local Environment Setup
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "🆙 Upgrading pip and installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 2. Node Dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node dependencies..."
    npm install @openzeppelin/contracts@5.0.2 --quiet
fi

# 3. Git Remote Configuration (Dual-Remote Strategy)
echo "🔧 Configuring dual-remote push targets..."
# Get current origin URL
ORIGIN_URL=$(git remote get-url origin 2>/dev/null || echo "git@github.com:wurk-coder/epiphany-protocol.git")

# Clear existing push URLs to start fresh and avoid duplicates
git config --unset-all remote.origin.pushurl || true

# Add primary and mirror URLs
git remote set-url --add --push origin "$ORIGIN_URL"
GITLAB_URL=$(echo "$ORIGIN_URL" | sed 's/github.com/gitlab.com/')
git remote set-url --add --push origin "$GITLAB_URL"

echo "✓ Remotes configured:"
git remote -v

# 4. Workspace Preparation
mkdir -p artifacts/contracts
mkdir -p artifacts/proofs
mkdir -p public
mkdir -p pipelines/src
mkdir -p scripts

echo "======================================================================"
echo "✅ SETUP COMPLETE: Workspace initialized for Epiphany Protocol MVP"
echo "======================================================================"
