from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"Received update: {post_data.decode('utf-8')}")
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Mock Enrichment Server is Running. Waiting for POST updates...")

if __name__ == "__main__":
    print("Starting mock enrichment server on port 8000...")
    print("Press Ctrl+C to stop.")
    httpd = HTTPServer(('localhost', 8000), SimpleHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nStopping mock server...")
        httpd.server_close()
        print("Server stopped.")
