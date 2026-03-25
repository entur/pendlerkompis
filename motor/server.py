"""HTTP-server for Motor — serverer Kontrakt B til frontend.

Stoetar baade enkelt-kall (GET /api/anbefaling) og live-stream
(GET /api/stream) med Server-Sent Events (SSE) som pushar ny
data kvart 3–10 sekund.
"""

import asyncio
import json
import random
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from motor.main import analyser


class MotorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/stream":
            self._handle_stream(parsed)
        elif parsed.path == "/api/anbefaling":
            self._handle_anbefaling(parsed)
        elif parsed.path == "/api/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "Ikkje funne"})

    def _handle_anbefaling(self, parsed):
        params = parse_qs(parsed.query)
        direction = params.get("direction", ["fra_jobb"])[0]
        override_time = params.get("time", [None])[0]
        try:
            result = asyncio.run(analyser(direction=direction, override_time=override_time))
            self._send_json(200, result)
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _handle_stream(self, parsed):
        """SSE-endpoint: pushar ny Kontrakt B kvart 3–10 sekund."""
        params = parse_qs(parsed.query)
        direction = params.get("direction", ["fra_jobb"])[0]
        interval_min = int(params.get("min", ["3"])[0])
        interval_max = int(params.get("max", ["10"])[0])

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        seq = 0
        try:
            while True:
                try:
                    result = asyncio.run(analyser(direction=direction))
                    payload = json.dumps(result, ensure_ascii=False)
                    self.wfile.write(f"id: {seq}\n".encode())
                    self.wfile.write(f"event: anbefaling\n".encode())
                    self.wfile.write(f"data: {payload}\n\n".encode())
                    self.wfile.flush()
                    seq += 1
                    avvik_type = result.get("type", "vaermelding")
                    alvorlighet = result.get("situasjon", {}).get("alvorlighet", "ingen")
                    print(f"[stream] #{seq} {avvik_type} ({alvorlighet})")
                except Exception as e:
                    err = json.dumps({"error": str(e)}, ensure_ascii=False)
                    self.wfile.write(f"event: error\ndata: {err}\n\n".encode())
                    self.wfile.flush()

                delay = random.uniform(interval_min, interval_max)
                time.sleep(delay)
        except (BrokenPipeError, ConnectionResetError):
            print("[stream] Klient kopla fraa.")

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[motor-server] {args[0]}")


def main():
    port = 8000
    server = HTTPServer(("", port), MotorHandler)
    server.daemon_threads = True
    print(f"Motor-server kjoerer paa http://localhost:{port}")
    print(f"  GET /api/anbefaling?direction=fra_jobb       (enkelt-kall)")
    print(f"  GET /api/stream?direction=fra_jobb            (SSE live-stream)")
    print(f"  GET /api/health")
    server.serve_forever()


if __name__ == "__main__":
    main()
