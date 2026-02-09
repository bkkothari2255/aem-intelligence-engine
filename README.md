# AEM Intelligence Engine

This project bridges **Adobe Experience Manager (AEM)** with modern AI capabilities, enabling RAG (Retrieval-Augmented Generation), real-time content intelligence, and semantic search.

It consists of an **AEM OSGi Bundle** for real-time listeners and AI integration, and a **Python-based Intelligence Layer** for crawling, vector storage, and processing.

## 🚀 Features

*   **Async AEM Crawler**: High-performance asynchronous crawler to scrape and extract text from AEM pages (`cq:Page`) and Experience Fragments.
*   **Vector Database Integration**: Automated ingestion of AEM content into **ChromaDB** using `sentence-transformers` for semantic search.
*   **Real-time Content Listener**: AEM OSGi service that detects content changes (`ADDED`, `MODIFIED`) and pushes updates to the Intelligence Engine immediately.
*   **Ollama Bridge Servlet**: internal AEM Servlet (`/bin/ollama/generate`) to relay prompts to a local LLM (Ollama), enabling AI features directly within AEM components.
*   **RAG Ready**: Infrastructure to support Retrieval-Augmented Generation by combining AEM content with LLM capabilities.

## 📂 Project Structure

```
.
├── aem-core/               # AEM Maven Project (OSGi Bundle)
│   ├── src/main/java/      # Java Source (ContentChangeListener, OllamaServlet)
│   └── pom.xml             # Maven Configuration
├── src/                    # Python Intelligence Engine
│   ├── crawler/            # AEM Content Crawler
│   └── vector_store/       # ChromaDB Ingestion & Querying
├── tests/                  # Verification Scripts & Mocks
│   ├── mock_server.py      # Python server to mimic Intelligence API
│   └── test_*.py           # Integration tests
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🛠 Prerequisites

*   **AEM 6.5** or **AEM as a Cloud Service SDK** (running locally on port 4502).
*   **Java 21** (for AEM compilation).
*   **Maven 3.9+**.
*   **Python 3.11+**.
*   **Ollama** (running locally with `llama3.1` model).

## ⚡ Setup & Installation

### 1. Python Environment

Initialize the Python environment for the Intelligence Engine.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. AEM Bundle Deployment

Build and deploy the OSGi bundle to your local AEM instance.

```bash
# Ensure AEM is running on localhost:4502
sh .agent/skills/deploy_aem/deploy-aem.sh
```

### 3. Ollama Setup

Ensure Ollama is running and the model is pulled.

```bash
ollama serve
ollama pull llama3.1
```

## 📖 Usage

### Data Ingestion (Manual)

1.  **Crawl Content**: Extract content from AEM into `output.jsonl`.
    ```bash
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
python3 tests/test_content_listener.py

# Verify AEM -> Ollama Bridge
python3 tests/test_ollama_servlet.py

# Verify Retrieval Accuracy
python3 tests/test_retrieval.py
```
