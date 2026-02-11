#!/bin/bash

# deploy.sh
# Automates the frontend build and deployment process.

BASE_DIR=$(cd "$(dirname "$0")/../../.."; pwd)
FRONTEND_DIR="$BASE_DIR/ui.frontend"
APPS_DIR="$BASE_DIR/ui.apps"

echo "🚀 Starting Frontend Deployment..."

# 1. Build Frontend
echo "📦 Building React Frontend..."
cd "$FRONTEND_DIR" || exit 1
npm install --legacy-peer-deps
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed."
    exit 1
fi

# 2. Copy Artifacts
echo "📂 Copying Artifacts to ui.apps..."
DEST_CLIENTLIB="$APPS_DIR/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react"

mkdir -p "$DEST_CLIENTLIB/js"
mkdir -p "$DEST_CLIENTLIB/css"

cp dist/assets/*.js "$DEST_CLIENTLIB/js/app.js"
cp dist/assets/*.css "$DEST_CLIENTLIB/css/index.css"

echo "✅ Artifacts copied."

# 3. Deploy to AEM
echo "☁️  Deploying ui.apps to AEM..."
cd "$APPS_DIR" || exit 1
mvn clean install -PautoInstallPackage

if [ $? -eq 0 ]; then
    echo "🎉 Frontend deployed successfully!"
else
    echo "❌ AEM deployment failed."
    exit 1
fi
