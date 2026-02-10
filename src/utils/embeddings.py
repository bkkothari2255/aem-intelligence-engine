import os
import sys
from sentence_transformers import SentenceTransformer
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local") # local | openai
LOCAL_MODEL_NAME = "all-MiniLM-L12-v2"
OPENAI_MODEL_NAME = "text-embeddings-ada-002"

def get_embedding_model():
    """
    Returns the configured embedding model instance.
    """
    if EMBEDDING_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY not found in environment.")
            sys.exit(1)
        print(f"Using OpenAI Embeddings ({OPENAI_MODEL_NAME})")
        return OpenAIEmbeddings(model=OPENAI_MODEL_NAME, openai_api_key=api_key)
    else:
        print(f"Using Local Embeddings ({LOCAL_MODEL_NAME})")
        return SentenceTransformer(LOCAL_MODEL_NAME)

def compute_embeddings(model, texts):
    """
    Computes embeddings for a list of texts using the provided model.
    Handles differences between SentenceTransformer and LangChain OpenAI.
    """
    if EMBEDDING_PROVIDER == "openai":
        return model.embed_documents(texts)
    else:
        return model.encode(texts).tolist()

def compute_query_embedding(model, text):
    """
    Computes embedding for a single query string.
    """
    if EMBEDDING_PROVIDER == "openai":
        return model.embed_query(text)
    else:
        return model.encode([text]).tolist()[0]
