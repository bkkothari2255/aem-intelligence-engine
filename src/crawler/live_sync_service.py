import asyncio
import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Import usage from existing modules
# We need to add src to sys.path or use relative imports if running as module
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.crawler.crawler import process_page
from src.vector_store.ingest import upsert_batch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "aem_content")
MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
AEM_BASE_URL = os.getenv("AEM_BASE_URL", "http://localhost:4502")

# Global state
class AppState:
    chroma_client = None
    collection = None
    model = None
    http_client = None

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Live Sync Service...")
    
    # Initialize ChromaDB
    logger.info(f"Connecting to ChromaDB at {CHROMA_DB_PATH}...")
    state.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    state.collection = state.chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    
    # Initialize Model
    logger.info(f"Loading embedding model {MODEL_NAME}...")
    state.model = SentenceTransformer(MODEL_NAME)
    
    # Initialize HTTP Client for crawler
    import httpx
    state.http_client = httpx.AsyncClient()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Live Sync Service...")
    if state.http_client:
        await state.http_client.aclose()

app = FastAPI(lifespan=lifespan)

class WebhookPayload(BaseModel):
    path: str
    event: Optional[str] = None

@app.post("/api/v1/sync")
async def sync_page(payload: WebhookPayload):
    path = payload.path
    logger.info(f"Received sync request for path: {path}")
    
    if not path.startswith("/content"):
        logger.warning(f"Ignored path {path} (not content path)")
        return {"status": "ignored", "reason": "not content path"}
    
    try:
        # 1. Process page to get updated chunks
        # We reuse the process_page function from crawler.py
        # It requires an interactive client, we pass our persistent one
        records = await process_page(state.http_client, path)
        
        if not records:
            logger.info(f"No content found for {path}")
            return {"status": "success", "message": "no content extracted", "chunks_processed": 0}
            
        logger.info(f"Extracted {len(records)} chunks from {path}")
        
        # 2. Prepare data for ChromaDB
        docs = []
        ids = []
        metadatas = []
        
        for record in records:
            text = record.get("text", "")
            if not text:
                continue
                
            source = record.get("source", path)
            chunk_id = record.get("chunk_id", 0)
            
            # Reconstruct metadata as ingest.py does
            meta = record.get("metadata", {}).copy()
            meta["source"] = source
            meta["chunk_id"] = chunk_id
            
            # ID construction: source_chunk_id
            doc_id = f"{source}_{chunk_id}"
            
            docs.append(text)
            ids.append(doc_id)
            metadatas.append(meta)
            
        # 3. Upsert to ChromaDB
        if docs:
            # We reuse the logic from verify/ingest, but we can call upsert directly
            # since we have the objects loaded in memory
            embeddings = state.model.encode(docs).tolist()
            state.collection.upsert(
                ids=ids,
                documents=docs,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Upserted {len(docs)} chunks to ChromaDB")
            
        return {
            "status": "success", 
            "path": path, 
            "chunks_processed": len(records),
            "chunks_upserted": len(docs)
        }

    except Exception as e:
        logger.error(f"Error syncing {path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
