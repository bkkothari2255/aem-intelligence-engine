from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"Received update: {post_data.decode('utf-8')}")
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    print("Starting mock enrichment server on port 8000...")
    HTTPServer(('localhost', 8000), SimpleHandler).serve_forever()
