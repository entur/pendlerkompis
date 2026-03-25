"""HTTP-server for Motor — serverer Kontrakt B til frontend."""

import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from motor.main import analyser


class MotorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/anbefaling":
            params = parse_qs(parsed.query)
            direction = params.get("direction", ["fra_jobb"])[0]
            override_time = params.get("time", [None])[0]

            try:
                result = asyncio.run(analyser(direction=direction, override_time=override_time))
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif parsed.path == "/api/health":
            self._send_json(200, {"status": "ok"})

        else:
            self._send_json(404, {"error": "Ikkje funne"})

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
    print(f"Motor-server kjoerer paa http://localhost:{port}")
    print(f"  GET /api/anbefaling?direction=fra_jobb")
    print(f"  GET /api/anbefaling?direction=fra_hjem")
    print(f"  GET /api/health")
    server.serve_forever()


if __name__ == "__main__":
    main()
