# AEM Intelligence Engine - Setup & Usage Guide

## Overview
This project integrates Adobe Experience Manager (AEM) with a Vector Database (ChromaDB) to provide real-time content enrichment and semantic search capabilities.

## Prerequisites
- **Python 3.11+**
- **Maven 3.8+**
- **Java 11+** (for AEM)
- **AEM instance** running locally on port 4502 (default)

## 1. Installation

### Python Environment
We use a dedicated virtual environment (`venv_chroma`) to manage dependencies.

```bash
# Create and activate virtual environment
python3.11 -m venv venv_chroma
source venv_chroma/bin/activate

# Install dependencies
pip install -r requirements.txt
# Note: real-time service required manually installing:
pip install fastapi uvicorn python-multipart chromadb sentence-transformers httpx aiofiles python-dotenv langchain-text-splitters
```

### AEM Package
Build and deploy the `aem-core` bundle which contains the Content Listener.

```bash
cd aem-core
mvn clean install -PautoInstallBundle
```

## 2. Configuration

### Environment Variables
Create a `.env` file in the root directory:

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

### Starting the Real-Time Sync Service
This service listens for AEM changes and updates the vector store immediately.

```bash
# Terminal 1
source venv_chroma/bin/activate
python src/crawler/live_sync_service.py
```
*Expected output:* `INFO:     Uvicorn running on http://0.0.0.0:8000`

### Full Crawl (Backfill)
To index all existing content:

```bash
# Terminal 2
source venv_chroma/bin/activate
python src/crawler/crawler.py
python src/vector_store/ingest.py
```

## 4. Testing
Run unit tests to verify the service logic without an active AEM instance.

```bash
source venv_chroma/bin/activate
# Install test dependencies if needed
pip install pytest httpx
# Run tests
pytest tests/test_live_sync_service.py
```

## Troubleshooting
- **Permission Errors**: If you encounter `Operation not permitted` on Mac, run:
  ```bash
  chmod -R 755 venv_chroma
  xattr -rc venv_chroma
  ```
- **Port Conflicts**: Ensure port 8000 is free or change `PORT` in `.env` (and update AEM config).
