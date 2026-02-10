import asyncio
import httpx
import json
import os
import sys
import aiofiles
from typing import List, Dict, Any
# from langchain_text_splitters import RecursiveCharacterTextSplitter (Removed to avoid zstandard dependency)
from dotenv import load_dotenv

load_dotenv()

# Configuration
AEM_BASE_URL = os.getenv("AEM_BASE_URL", "http://localhost:4502")
AEM_USER = os.getenv("AEM_USER", "admin")
AEM_PASSWORD = os.getenv("AEM_PASSWORD", "admin")
AUTH = (AEM_USER, AEM_PASSWORD)
QUERY_BUILDER_URL = f"{AEM_BASE_URL}/bin/querybuilder.json"
OUTPUT_FILE = "output.jsonl"

# Text Splitter Configuration
class SimpleTextSplitter:
    def __init__(self, chunk_size=650, chunk_overlap=65):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + self.chunk_size
            
            # If we're not at the end, try to find a nice break point
            if end < text_len:
                # Look for paragraph break
                last_break = text.rfind('\n', start, end)
                if last_break == -1 or last_break < start + (self.chunk_size // 2):
                    # Look for sentence break
                    last_break = text.rfind('. ', start, end)
                
                if last_break != -1 and last_break > start:
                    end = last_break + 1  # Include the break character
            
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
            
            # Prevent infinite loops if overlap >= chunk size (shouldn't happen with defaults)
            if start >= end:
                start = end
                
        return [c for c in chunks if c]

CHUNK_SIZE = 650
CHUNK_OVERLAP = 65
splitter = SimpleTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

async def search_pages(client: httpx.AsyncClient, root_path: str = "/content") -> List[str]:
    """
    Finds all cq:Page nodes under the root path using AEM Query Builder.
    """
    params = {
        "path": root_path,
        "type": "cq:Page",
        "p.limit": "-1",  # Fetch all results
        "p.hits": "selective",
        "p.properties": "jcr:path"
    }
    
    try:
        response = await client.get(QUERY_BUILDER_URL, params=params, auth=AUTH)
        response.raise_for_status()
        data = response.json()
        
        hits = data.get("hits", [])
        print(f"Found {len(hits)} pages under {root_path}")
        return [hit["jcr:path"] for hit in hits]
    except Exception as e:
        print(f"Error searching pages: {e}")
        return []

def extract_text_from_component(component: Dict[str, Any]) -> List[str]:
    """
    Recursively extracts text from a Sling Model JSON structure.
    Focuses on common text properties like 'text', 'jcr:title', 'jcr:description'.
    """
    texts = []
    
    # Direct text properties
    for key in ["text", "jcr:title", "jcr:description", "value"]:
        if key in component and isinstance(component[key], str):
            texts.append(component[key])
            
    # Recursive traversal of children
    for key, value in component.items():
        if isinstance(value, dict):
            texts.extend(extract_text_from_component(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    texts.extend(extract_text_from_component(item))
                    
    return texts

async def process_page(client: httpx.AsyncClient, page_path: str) -> List[Dict[str, Any]]:
    """
    Fetches page content via .model.json, extracts text, splits it, and returns chunks.
    """
    model_url = f"{AEM_BASE_URL}{page_path}.model.json"
    
    try:
        response = await client.get(model_url, auth=AUTH)
        if response.status_code == 404:
            # Fallback or just skip
            print(f"Skipping {page_path}: .model.json not found")
            return []
        
        response.raise_for_status()
        data = response.json()
        
        # Extract all text from the page per the "Unified Content Layer" concept
        # We try to get the 'jcr:content' part if available, else root
        content_root = data.get("jcr:content", data)
        raw_texts = extract_text_from_component(content_root)
        # Remove duplicates while preserving order
        seen = set()
        deduped_texts = []
        for t in raw_texts:
            if t not in seen:
                seen.add(t)
                deduped_texts.append(t)
        
        full_text = "\n\n".join(deduped_texts)
        
        if not full_text:
            return []
            
        # Split text
        chunks = splitter.split_text(full_text)
        
        # Format output records
        records = []
        for i, chunk in enumerate(chunks):
            records.append({
                "source": page_path,
                "chunk_id": i,
                "text": chunk,
                "metadata": {
                    "url": f"{AEM_BASE_URL}{page_path}.html",
                    "title": data.get("jcr:content", {}).get("jcr:title", "Unknown")
                }
            })
            
        return records
        
    except Exception as e:
        print(f"Error processing {page_path}: {e}")
        return []

async def main():
    print("Starting AEM Crawler...")
    
    async with httpx.AsyncClient() as client:
        # 1. Discover Pages
        pages = await search_pages(client, "/content")
        
        if not pages:
            print("No pages found. Exiting.")
            return

        # 2. Process Pages (Concurrent with Semaphore)
        sem = asyncio.Semaphore(10) # Limit concurrent requests
        
        async def bounded_process(page):
            async with sem:
                return await process_page(client, page)

        tasks = [bounded_process(page) for page in pages]
        results = await asyncio.gather(*tasks)
        
        # 3. Write Output
        total_chunks = 0
        async with aiofiles.open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for page_results in results:
                for record in page_results:
                    await f.write(json.dumps(record) + "\n")
                    total_chunks += 1
                    
        print(f"Crawling complete. Processed {len(pages)} pages. Generated {total_chunks} chunks.")
        print(f"Output saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
