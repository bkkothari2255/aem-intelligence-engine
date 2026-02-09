import requests
import json

URL = "http://localhost:4502/bin/ollama/generate"
AUTH = ("admin", "admin")
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
