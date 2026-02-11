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

def get_relevant_context(query_text: str, n_results: int = 3, chroma_path: str = CHROMA_DB_PATH, collection_name: str = COLLECTION_NAME) -> str:
    """
    Retrieves relevant context from ChromaDB for a given query.
    Returns a single string tailored for RAG prompts.
    """
    try:
        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        return f"Error accessing vector store: {str(e)}"

    model = get_embedding_model()
    query_embedding = compute_query_embedding(model, query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    if not results['documents'] or not results['documents'][0]:
        return ""

    formatted_context = []
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i]
        source = meta.get('source', 'Unknown')
        formatted_context.append(f"Source: {source}\nContent: {doc}")

    return "\n\n".join(formatted_context)

def main():
    query = "WKND"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print(f"Querying ChromaDB at '{CHROMA_DB_PATH}' for: '{query}'")
    context = get_relevant_context(query)
    
    if context:
        print("\nRetrieved Context:")
        print(context)
    else:
        print("\nNo relevant context found.")

if __name__ == "__main__":
    main()
