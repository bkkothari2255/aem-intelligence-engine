import chromadb
from sentence_transformers import SentenceTransformer
import sys

import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "aem_content")
MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

def main():
    query = "WKND"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print(f"Querying ChromaDB at '{CHROMA_DB_PATH}' for: '{query}'")
    
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error accessing collection: {e}")
        return

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3
    )

    print("\nResults:")
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        print(f"[{i+1}] Distance: {dist:.4f}")
        print(f"    Source: {meta.get('source')}")
        print(f"    Text: {doc[:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    main()
