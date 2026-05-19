#!/usr/bin/env python3
import http.server
import os

PORT = 8080
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs"))

handler = http.server.SimpleHTTPRequestHandler
httpd = http.server.HTTPServer(("", PORT), handler)
print(f"Serving at http://localhost:{PORT}")
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down")
    httpd.shutdown()
