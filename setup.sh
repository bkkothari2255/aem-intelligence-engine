#!/bin/bash

# AEM Intelligence Engine - Unified Setup Script
# Handles Python environment, Frontend build, and AEM deployment.

set -e # Exit on error

echo "🚀 Starting AEM Intelligence Engine Setup..."

# --- 1. Python Environment Setup ---
echo "\n🐍 Setting up Python Environment..."
if [ ! -d "venv_manual" ]; then
    echo "Creating virtual environment (venv_manual)..."
    python3.11 -m venv venv_manual
else
    echo "Virtual environment exists."
fi

source venv_manual/bin/activate
echo "Installing Python dependencies..."
pip install fastapi uvicorn python-multipart chromadb sentence-transformers httpx aiofiles python-dotenv langchain-text-splitters pydantic pandas langchain-openai

# --- 2. Frontend Build (Manual Workaround) ---
echo "\n⚛️  Building Frontend (ui.frontend)..."
cd aem-core/ui.frontend
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
cd ../..

# --- 3. AEM Deployment ---
echo "\n📦 Deploying to AEM (ui.apps)..."
cd aem-core/ui.apps
mvn clean install -PautoInstallPackage

echo "\n✅ Setup Complete!"
echo "------------------------------------------------"
echo "To start the backend service:"
echo "  source venv_manual/bin/activate"
echo "  python src/crawler/live_sync_service.py"
echo "------------------------------------------------"
