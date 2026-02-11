import asyncio
import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
import chromadb
from dotenv import load_dotenv

# Import usage from existing modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.crawler.crawler import process_page
# from src.vector_store.ingest import upsert_batch # Removed to avoid circular import or duplication
from src.utils.embeddings import get_embedding_model, compute_embeddings, compute_query_embedding

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "aem_content")
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
    logger.info("Loading embedding model...")
    state.model = get_embedding_model()
    
    # Initialize HTTP Client for crawler
    import httpx
    state.http_client = httpx.AsyncClient()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Live Sync Service...")
    if state.http_client:
        await state.http_client.aclose()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4502"],  # React app & AEM
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WebhookPayload(BaseModel):
    path: str
    event: Optional[str] = None

class ChatPayload(BaseModel):
    message: str

@app.post("/api/v1/chat")
async def chat_endpoint(payload: ChatPayload):
    try:
        query_text = payload.message
        logger.info(f"Received chat request: {query_text}")
        
        # 1. Generate embedding for the query
        query_embedding = compute_query_embedding(state.model, query_text)
        
        # 2. Query ChromaDB
        results = state.collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        # 3. Format response
        # unique_documents = set()
        formatted_context = []
        
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                source = meta.get("source", "Unknown")
                formatted_context.append(f"Source: {source}\nContent: {doc}")
        
        context_str = "\n\n".join(formatted_context)
        
        # For now, return the retrieved context as the "answer" to prove RAG works
        # Later we will pass this `context_str` + `query_text` to Ollama
        
        # Simple cleanup of AEM noise
        import re
        context_str = re.sub(r'aem-GridColumn--[a-z0-9-]+', '', context_str)
        context_str = re.sub(r'aem-GridColumn', '', context_str)
        
        response_text = f"I found some relevant information in the AEM content:\n\n{context_str}"
        
        if not formatted_context:
            response_text = "I couldn't find any relevant information in the AEM content to answer your question."

        return {
            "role": "assistant",
            "content": response_text
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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
            
            # Use shared compute logic
            embeddings = compute_embeddings(state.model, docs)
            
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
