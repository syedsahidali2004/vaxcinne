"""Tiny web server for the experimental hash. No external dependencies.

Run locally:  python server.py   ->  http://localhost:8000
Hosts like Render/Railway/Fly set the PORT environment variable automatically.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from experimental_hash import hexdigest, generate_initial_state

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES = 1_000_000  # request body limit (1 MB)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(BASE_DIR, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/state":
            state = [f"{v:08X}" for v in generate_initial_state()]
            self._send(200, json.dumps({"initial_state": state}))
        elif path == "/health":
            self._send(200, "ok", "text/plain")
        else:
            self._send(404, json.dumps({"error": "Not found"}))

    def do_POST(self):
        if self.path.split("?")[0] != "/api/hash":
            return self._send(404, json.dumps({"error": "Not found"}))
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BYTES:
                return self._send(413, json.dumps({"error": "Message too large (1 MB max)"}))
            payload = json.loads(self.rfile.read(length) or b"{}")
            message = payload.get("message", "")
            if not isinstance(message, str):
                raise ValueError("message must be a string")
        except (ValueError, json.JSONDecodeError) as exc:
            return self._send(400, json.dumps({"error": str(exc)}))
        self._send(200, json.dumps({"digest": hexdigest(message)}))

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Serving on http://0.0.0.0:{port}")
    server.serve_forever()
