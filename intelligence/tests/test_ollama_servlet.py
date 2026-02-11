import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

AEM_BASE_URL = os.getenv("AEM_BASE_URL", "http://localhost:4502")
URL = f"{AEM_BASE_URL}/bin/ollama/generate"
AEM_USER = os.getenv("AEM_USER", "admin")
AEM_PASSWORD = os.getenv("AEM_PASSWORD", "admin")
AUTH = (AEM_USER, AEM_PASSWORD)

PAYLOAD = {"prompt": "What is the capital of France?"}

print(f"Testing Ollama Servlet at {URL}...")
try:
    response = requests.post(URL, data=PAYLOAD, auth=AUTH)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response from Ollama:")
        res_json = response.json()
        print(json.dumps(res_json, indent=2))
        
        # Check if actual response text is present
        if "response" in res_json:
            print(f"\nExtracted Answer: {res_json['response']}")
        else:
            print("\nWarning: 'response' field not found in JSON.")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Request failed: {e}")
