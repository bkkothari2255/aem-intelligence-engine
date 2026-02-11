import http.server
import threading
import time
import httpx
import sys
import socket
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
PORT = int(os.getenv("LISTENER_PORT", 8000))
AEM_BASE_URL = os.getenv("AEM_BASE_URL", "http://localhost:4502")
AEM_USER = os.getenv("AEM_USER", "admin")
AEM_PASSWORD = os.getenv("AEM_PASSWORD", "admin")
AEM_UPDATE_URL = f"{AEM_BASE_URL}/content/wknd/us/en/jcr:content"
AUTH = (AEM_USER, AEM_PASSWORD)

received_event = None
server_error = None

class TestHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        global received_event
        try:
            length = int(self.headers.get('content-length', 0))
            if length > 0:
                data = self.rfile.read(length).decode('utf-8')
                print(f"[TestServer] Received POST: {data}")
                received_event = data
            self.send_response(200)
            self.end_headers()
        except Exception as e:
            print(f"[TestServer] Error reading POST: {e}")

    def log_message(self, format, *args):
        # Suppress default logging to keep output clean
        pass

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_server(server_ready_event):
    global server_error
    try:
        server = http.server.HTTPServer(('localhost', PORT), TestHandler)
        server.timeout = 0.5
        server_ready_event.set()
        print(f"[TestServer] Listening on port {PORT}...")
        
        while received_event is None:
            server.handle_request()
            
        server.server_close()
    except OSError as e:
        server_error = e
        server_ready_event.set()

def main():
    if is_port_in_use(PORT):
        print(f"[Error] Port {PORT} is already in use!")
        print("Please stop 'mock_server.py' or any other service running on port 8000.")
        sys.exit(1)

    # 1. Start Verification Server
    print("--- Starting Content Listener Test ---")
    server_ready = threading.Event()
    t = threading.Thread(target=start_server, args=(server_ready,), daemon=True)
    t.start()
    
    server_ready.wait()
    if server_error:
        print(f"[Error] Failed to start server: {server_error}")
        sys.exit(1)

    # 2. Trigger AEM Change
    print(f"[Client] Triggering content update on {AEM_UPDATE_URL}...")
    try:
        # We enforce a change by updating 'jcr:description' with a timestamp
        payload = {"jcr:description": f"Automated Test Update {time.time()}"}
        
        with httpx.Client(auth=AUTH, timeout=10.0) as client:
            # We must use proper form encoding for Sling POST Servlet
            response = client.post(AEM_UPDATE_URL, data=payload)
            
        if response.status_code >= 200 and response.status_code < 300:
            print(f"[Client] Update sent successfully (HTTP {response.status_code}).")
        else:
            print(f"[Client] Failed to update AEM content. HTTP {response.status_code}")
            print(response.text)
            sys.exit(1)
            
    except Exception as e:
        print(f"[Client] Connection error triggering AEM: {e}")
        sys.exit(1)

    # 3. Wait for Callback
    print("[Test] Waiting for listener callback (max 10s)...")
    for i in range(10):
        if received_event:
            break
        time.sleep(1)
        if i % 2 == 0:
            print(".", end="", flush=True)
    print("")

    # 4. Assertions
    if received_event:
        print("\n[SUCCESS] Callback received!")
        print(f"Payload: {received_event}")
        if '"type": "CHANGED"' in received_event or '"type": "MODIFIED"' in received_event: 
             # Note: Sling might send CHANGED or MODIFIED depending on impl details, our code sends event type name
            pass
        sys.exit(0)
    else:
        print("\n[FAILURE] No callback received from AEM.")
        print("Possible causes:")
        print("1. Listener is disabled in OSGi.")
        print("2. Endpoint URL in OSGi config is not 'http://localhost:8000/enrich'.")
        print("3. AEM event queue is delayed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
