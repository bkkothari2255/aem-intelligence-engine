# AEM Intelligence Engine

This project bridges **Adobe Experience Manager (AEM)** with modern AI capabilities, enabling RAG (Retrieval-Augmented Generation), real-time content intelligence, and semantic search.

It consists of an **AEM OSGi Bundle** for real-time listeners and AI integration, and a **Python-based Intelligence Layer** for crawling, vector storage, and processing.

## 🚀 Features

*   **Async AEM Crawler**: High-performance asynchronous crawler to scrape and extract text from AEM pages (`cq:Page`) and Experience Fragments.
*   **Vector Database Integration**: Automated ingestion of AEM content into **ChromaDB** using `sentence-transformers` for semantic search.
*   **Real-time Content Listener**: AEM OSGi service that detects content changes (`ADDED`, `MODIFIED`) and pushes updates to the Intelligence Engine immediately.
*   **Ollama Bridge Servlet**: internal AEM Servlet (`/bin/ollama/generate`) to relay prompts to a local LLM (Ollama), enabling AI features directly within AEM components.
*   **Intelligent Chat UI**: A React Spectrum-based chat interface embedded in AEM that streams RAG responses from the Intelligence Engine.
*   **RAG Ready**: Infrastructure to support Retrieval-Augmented Generation by combining AEM content with LLM capabilities.

## 📅 Roadmap

### Sprint 1: Foundation (Completed)
- [x] **Project Structure**: Multi-module Maven project with Python Intelligence Engine.
- [x] **Core Services**: AEM-Python Event listener, Ollama Bridge Servlet.
- [x] **Vector Database**: ChromaDB integration with `sentence-transformers`.
- [x] **Basic UI**: Embedded React Chat Interface.
- [x] **Security**: Author-only access control for AI endpoints.

### Sprint 2: The Enrichment Pipeline (Completed)
- [x] **Recursive Character Splitting**: Implemented chunking with 650/65 overlap.
- [x] **Multi-Model Vectorization**: Support for `all-MiniLM-L12-v2` and `text-embeddings-ada-002`.
- [x] **Dispatcher Log Analysis**: Pandas-based log analysis for high-traffic paths and errors.
- [x] **Embedding Storage**: Automated ChromaDB ingestion.

### Sprint 3: Advanced RAG & UI (Upcoming)
- [ ] **Context-Aware Retrieval**: Chat history support.
- [ ] **Admin Dashboard**: AEM UI for managing vector embeddings and indexing status.
- [ ] **Feedback Loop**: User feedback mechanism for chat responses.

### Future Features
- [ ] **Voice Interface**: Speech-to-Text and Text-to-Speech integration.
- [ ] **Personalization**: User-specific context and recommendations.
- [ ] **Cloud Deployment**: Docker/Kubernetes support for the Python layer.

## 📂 Project Structure

```
.
├── core/                   # AEM OSGi Bundle (Core)
├── ui.frontend/            # React Chat Application (Vite)
├── ui.apps/                # AEM ClientLibs & Components
├── pom.xml                 # Maven Configuration
├── intelligence/           # Python Intelligence Engine
│   ├── src/                # Python Source Code
│   ├── tests/              # Verification Scripts
│   └── requirements.txt    # Python dependencies
├── README.md               # This file
```

## 🛠 Prerequisites

*   **AEM 6.5** or **AEM as a Cloud Service SDK** (running locally on port 4502).
*   **Java 21** (for AEM compilation).
*   **Maven 3.9+**.
*   **Python 3.11+**.
*   **Ollama** (running locally with `llama3.1` model).
*   **Node.js v20+** (for UI Frontend).

## ⚡ Setup & Installation

### 1. Unified Setup (Recommended)

Run the unified setup script to handle Python environment, Frontend build, and AEM deployment automatically.

```bash
./setup.sh
```

### 2. Manual Setup (Alternative)

If you prefer to set up components individually:

**Python Environment:**
```bash
cd intelligence
python3.11 -m venv venv_manual
source venv_manual/bin/activate
pip install fastapi uvicorn chromadb sentence-transformers python-dotenv httpx pydantic aiofiles
```

**AEM Deployment:**
```bash
# Build Frontend & Copy Artifacts
cd ui.frontend
npm install --legacy-peer-deps
npm run build
cp dist/assets/*.js ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/js/app.js
cp dist/assets/*.css ../ui.apps/src/main/content/jcr_root/apps/aem-intelligence/clientlibs/clientlib-react/css/index.css

# Deploy to AEM
cd ../ui.apps
mvn clean install -PautoInstallPackage
```

### 3. Ollama Setup

Ensure Ollama is running and the model is pulled.

```bash
ollama serve
ollama pull llama3.1
```

## 📖 Usage

### Python Backend Service (Chat API)
Start the backend service to handle chat requests:
```bash
cd intelligence
python src/crawler/live_sync_service.py
```
*   API runs on `http://localhost:8000`.

### Data Ingestion (Manual)

1.  **Crawl Content**: Extract content from AEM into `output.jsonl`.
    ```bash
    cd intelligence
    python3 src/crawler/crawler.py
    ```

2.  **Ingest to ChromaDB**: Generate embeddings and store in vector DB.
    ```bash
    python3 src/vector_store/ingest.py
    ```

3.  **Query Content**: Verify retrieval.
    ```bash
    python3 src/vector_store/query.py "What is WKND?"
    ```

### Real-time Event Listener

The `ContentChangeListener` acts as a bridge. To verify it:

1.  Start the verification mock server:
    ```bash
    python3 tests/mock_server.py
    ```
2.  Modify a page in AEM (e.g., `/content/wknd/us/en`).
3.  Watch the `mock_server.py` console for immediate updates.

### Automated Verification

Run the test suite to ensure all components are talking to each other.

```bash
# Verify AEM -> Python Event Flow
cd intelligence
python3 tests/test_content_listener.py

# Verify AEM -> Ollama Bridge
python3 tests/test_ollama_servlet.py

# Verify Retrieval Accuracy
python3 tests/test_retrieval.py
```
