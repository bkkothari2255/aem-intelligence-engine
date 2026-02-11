import chromadb
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.embeddings import get_embedding_model, compute_query_embedding

load_dotenv()

# Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "aem_content")

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

    model = get_embedding_model()
    # Compute query embedding (handles OpenAI/Local switch)
    query_embedding = compute_query_embedding(model, query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    print("\nResults:")
    if not results['documents']:
        print("No results found.")
        return

    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        print(f"[{i+1}] Distance: {dist:.4f}")
        print(f"    Source: {meta.get('source')}")
        print(f"    Text: {doc[:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    main()
