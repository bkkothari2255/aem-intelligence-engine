import chromadb
import os
import sys

# Configuration
CHROMA_DB_DIR = "./chroma_db"
COLLECTION_NAME = "aem-knowledge-base"

def setup_chroma():
    """
    Initializes a local ChromaDB persistent client and ensures the collection exists.
    """
    print(f"Initializing ChromaDB in {CHROMA_DB_DIR}...")
    
    try:
        # Create a persistent client that saves to disk
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        
        # Get or create the collection
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        print("Successfully connected to ChromaDB.")
        print(f"Collection '{COLLECTION_NAME}' is ready.")
        print(f"Current collection count: {collection.count()}")
        
        return client, collection
        
    except Exception as e:
        print(f"Error setting up ChromaDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_chroma()
