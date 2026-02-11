#!/bin/bash

# rebuild_venv.sh
# Cleans and recreates the Python virtual environment for the Intelligence Engine.

BASE_DIR=$(cd "$(dirname "$0")"; pwd)
VENV_DIR="$BASE_DIR/venv"
REQ_FILE="$BASE_DIR/requirements.txt"

echo "🧹 Cleaning up existing virtual environment..."
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "✅ Removed $VENV_DIR"
else
    echo "ℹ️  No existing venv found."
fi

echo "📦 Creating new virtual environment..."
python3 -m venv "$VENV_DIR"
echo "✅ Created venv at $VENV_DIR"

echo "🔄 Activating and installing dependencies..."
source "$VENV_DIR/bin/activate"

# Upgrade pip to avoid issues with older versions
pip install --upgrade pip

if [ -f "$REQ_FILE" ]; then
    pip install -r "$REQ_FILE"
    echo "✅ Dependencies installed successfully!"
else
    echo "⚠️  requirements.txt not found at $REQ_FILE"
fi

echo "🎉 Environment rebuild complete."
echo "👉 To activate: source intelligence/venv/bin/activate"
