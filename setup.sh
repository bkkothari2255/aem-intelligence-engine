#!/bin/bash

# AEM Intelligence Engine - Unified Setup Script
# Handles Python environment, Frontend build, and AEM deployment.

set -e # Exit on error

echo "🚀 Starting AEM Intelligence Engine Setup..."

# --- 1. Python Environment Setup ---
# --- 1. Python Environment Setup ---
echo "\n🐍 Setting up Python Environment..."

cd intelligence

if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
    echo "⚠️  Found broken venv (missing activate script). Reinstalling..."
    rm -rf venv
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment (venv)..."
    python3.11 -m venv venv
else
    echo "Virtual environment exists."
fi

source venv/bin/activate
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Return to root
cd ..

# --- 2. Frontend Build (Manual Workaround) ---
echo "\n⚛️  Building Frontend (ui.frontend)..."

# Ensure Node.js 24
NODE_VERSION=$(node -v 2>/dev/null || echo "none")
REQUIRED_VERSION="v24"

if [[ "$NODE_VERSION" != $REQUIRED_VERSION* ]]; then
    echo "⚠️  Node.js 24 is required (found $NODE_VERSION)."
    
    # Check for NVM
    export NVM_DIR="$HOME/.nvm"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        echo "Loading NVM..."
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    elif command -v brew >/dev/null 2>&1 && [ -s "$(brew --prefix nvm)/nvm.sh" ]; then
        echo "Loading NVM from Homebrew..."
        [ -s "$(brew --prefix nvm)/nvm.sh" ] && \. "$(brew --prefix nvm)/nvm.sh"
    else
        echo "❌ NVM not found. Installing NVM..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    fi
    
    # Install/Use Node 24
    echo "Installing/Using Node 24..."
    nvm install 24
    nvm use 24
else
    echo "✅ Node.js 24 detected."
fi

cd ui.frontend
npm install --legacy-peer-deps
npm run build

echo "Copying artifacts to ui.apps..."
# Ensure target directories exist
mkdir -p ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/js
mkdir -p ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/css

# Copy files
cp dist/assets/*.js ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/js/app.js
cp dist/assets/*.css ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/css/index.css

# Return to root
cd ..

# --- 3. AEM Deployment ---
echo "\n📦 Deploying to AEM..."

echo ">> Deploying Core Bundle..."
cd core
mvn clean install -PautoInstallPackage
cd ..

echo ">> Deploying UI Apps..."
cd ui.apps
mvn clean install -PautoInstallPackage

echo "\n✅ Setup Complete!"
echo "------------------------------------------------"
echo "To start the backend service:"
echo "  cd intelligence"
echo "  source venv/bin/activate"
echo "  python src/crawler/live_sync_service.py"
echo "------------------------------------------------"
