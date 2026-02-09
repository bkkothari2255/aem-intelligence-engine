import chromadb
from sentence_transformers import SentenceTransformer
import json
import os
import sys

# Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = "aem_content"
INPUT_FILE = os.getenv("INPUT_FILE", "output.jsonl")
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 50

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        sys.exit(1)

    print(f"Initializing ChromaDB at '{CHROMA_DB_PATH}'...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    print(f"Loading embedding model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Reading '{INPUT_FILE}' and ingesting...")
    
    batch_docs = []
    batch_ids = []
    batch_metadatas = []
    count = 0

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                item = json.loads(line)
                text = item.get('text', '')
                source = item.get('source', 'unknown')
                chunk_id = item.get('chunk_id', 0)
                metadata = item.get('metadata', {}).copy()
                
                # Enhance metadata with source/chunk info
                metadata['source'] = source
                metadata['chunk_id'] = chunk_id
                
                # ID construction
                doc_id = f"{source}_{chunk_id}"

                if text:
                    batch_docs.append(text)
                    batch_ids.append(doc_id)
                    batch_metadatas.append(metadata)
            
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line[:50]}...")
                continue

            if len(batch_docs) >= BATCH_SIZE:
                upsert_batch(collection, model, batch_docs, batch_ids, batch_metadatas)
                count += len(batch_docs)
                print(f"Ingested {count} chunks...")
                batch_docs = []
                batch_ids = []
                batch_metadatas = []

        # Process remaining
        if batch_docs:
            upsert_batch(collection, model, batch_docs, batch_ids, batch_metadatas)
            count += len(batch_docs)
            print(f"Ingested {count} chunks...")

    print(f"Ingestion complete. Total chunks: {count}")

def upsert_batch(collection, model, docs, ids, metadatas):
    embeddings = model.encode(docs).tolist()
    collection.upsert(
        ids=ids,
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas
    )

if __name__ == "__main__":
    main()
