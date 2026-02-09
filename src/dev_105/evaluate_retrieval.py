import time
import chromadb
from sentence_transformers import SentenceTransformer
import os
import sys

# Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = "aem_content"
MODEL_NAME = "all-MiniLM-L6-v2"

# Golden Dataset based on output.jsonl content
GOLDEN_DATASET = [
    {
        "query": "What is the WKND copyright year?",
        "expected_source": "/content/wknd/us/en"
    },
    {
        "query": "Where is the WKND office located?",
        "expected_source": "/content/experience-fragments/wknd/us/en/site/footer/master"
    },
    {
         "query": "What does the AEM sample site say?",
         "expected_source": "/content/aemsamplessite/us/en"
    },
    {
        "query": "What is the copyright for the AEM Sample Site?",
        "expected_source": "/content/experience-fragments/aemsamplessite/us/en/site/footer/master"
    },
    {
        "query": "Is there a hello message on WKND?",
        "expected_source": "/content/wknd/us/en"
    }
]

def evaluate():
    print(f"Loading ChromaDB from '{CHROMA_DB_PATH}'...")
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")
        print("Make sure the database path is correct and ingestion has run.")
        sys.exit(1)
    
    print(f"Loading model '{MODEL_NAME}'...")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
    
    total = len(GOLDEN_DATASET)
    hits = 0
    total_latency = 0
    
    print("\n--- Starting Evaluation ---\n")
    
    for i, item in enumerate(GOLDEN_DATASET):
        query = item['query']
        expected = item['expected_source']
        
        try:
            start_time = time.time()
            query_embedding = model.encode([query]).tolist()
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=3,
                include=["metadatas", "distances"]
            )
            latency = (time.time() - start_time) * 1000 # ms
            total_latency += latency
            
            # results['metadatas'][0] is a list of dicts for the first query
            retrieved_sources = [m.get('source') for m in results['metadatas'][0]]
            
            # Soft match: check if expected source is in the retrieved list
            is_hit = expected in retrieved_sources
            
            if is_hit:
                hits += 1
                status = "PASS"
            else:
                status = "FAIL"
                
            print(f"[{i+1}/{total}] Query: '{query}'")
            print(f"  Expected: {expected}")
            print(f"  Retrieved: {retrieved_sources}")
            print(f"  Latency: {latency:.2f}ms | Status: {status}")
            print("-" * 40)
            
        except Exception as e:
            print(f"Error processing query '{query}': {e}")
            print("-" * 40)

    if total > 0:
        avg_latency = total_latency / total
        hit_rate = (hits / total) * 100
        
        print("\n--- Evaluation Summary ---")
        print(f"Total Queries: {total}")
        print(f"Successful Retrievals: {hits}")
        print(f"Hit Rate: {hit_rate:.2f}%")
        print(f"Average Latency: {avg_latency:.2f}ms")
    else:
        print("No queries to evaluate.")

if __name__ == "__main__":
    evaluate()
