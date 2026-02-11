# AEM Intelligence Engine - Setup & Usage Guide

## Overview
This project integrates Adobe Experience Manager (AEM) with a Vector Database (ChromaDB) and local LLMs (Ollama) to provide real-time content enrichment, semantic search, and an Intelligent Chat UI.

## Prerequisites
- **Python 3.11+**
- **Node.js v20+**
- **Maven 3.9+**
- **Java 21** (for AEM)
- **AEM instance** running locally on port 4502 (default)
- **Ollama** running locally

## 1. Installation

### Python Environment
We use a virtual environment to manage dependencies.

**Automated Setup:**
```bash
cd intelligence
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Manual Setup (If EPERM issues occur):**
```bash
cd intelligence
python3.11 -m venv venv_manual
source venv_manual/bin/activate
pip install fastapi uvicorn python-multipart chromadb sentence-transformers httpx aiofiles python-dotenv langchain-text-splitters pydantic
```

### AEM Package Deployment

**Standard Deployment:**
```bash
sh .agent/skills/deploy_aem/deploy-aem.sh
```

**Manual Deployment (If permission errors occur):**
1.  **Build Frontend**:
    ```bash
    cd ui.frontend
    npm install --legacy-peer-deps
    npm run build
    ```
2.  **Copy Artifacts Manually**:
    ```bash
    # Run from ui.frontend
    cp dist/assets/*.js ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/js/app.js
    cp dist/assets/*.css ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/css/index.css
    ```
3.  **Deploy to AEM**:
    ```bash
    cd ../ui.apps
    mvn clean install -PautoInstallPackage
    ```

## 2. Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
AEM_BASE_URL=http://localhost:4502
AEM_USER=admin
AEM_PASSWORD=admin
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=aem_content
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

### AEM Content Listener
Configure AEM to send events to the Python service.

1.  Open **[OSGi Config Manager](http://localhost:4502/system/console/configMgr)**.
2.  Find **"AEM Intelligence - Content Listener"**.
3.  Set **Enrichment Endpoint** to: `http://localhost:8000/api/v1/sync`.
4.  Ensure **Enabled** is checked.
5.  Save.

## 3. Usage

### Starting the Intelligence Service
This service handles Chat API requests and Real-Time sync.

```bash
# Activate your venv first
cd intelligence
source venv_manual/bin/activate  # or venv/bin/activate
python src/crawler/live_sync_service.py
```
*   API runs on: `http://localhost:8000`
*   Chat Endpoint: `POST /api/v1/chat`

### Data Ingestion (Backfill)
To index all existing content:

```bash
python src/crawler/crawler.py
python src/vector_store/ingest.py
```

### Intelligent Chat UI
1.  Navigate to any AEM page where the Chat Component is added.
2.  Or find the component in the AEM Sidekick under "AEM Intelligence" group.
3.  Ask questions like "What is WKND?".

## 4. Troubleshooting
- **Permission Errors**: If you encounter `Operation not permitted` on Mac during build, use the **Manual Deployment** steps above.
- **Port Conflicts**: Ensure port 8000 is free or change `PORT` in `.env` (and update AEM config).
- **Chat Not Responding**: Ensure `live_sync_service.py` is running and `Ollama` is serving content.
