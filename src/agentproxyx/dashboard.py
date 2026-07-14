from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from .replay import ReplayStore


WEB_DIR = Path(__file__).with_name("web")


class DashboardServer:
    def __init__(self, store: ReplayStore, host: str = "127.0.0.1", port: int = 7778):
        self.store = store
        self.host = host
        self.port = port
        self.httpd: ThreadingHTTPServer | None = None

    def make_handler(self) -> type[BaseHTTPRequestHandler]:
        store = self.store

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

            def do_GET(self) -> None:
                if self.path.startswith("/events"):
                    payload = json.dumps({"events": store.recent()}, ensure_ascii=False).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return

                file_path = WEB_DIR / ("index.html" if self.path in {"/", "/index.html"} else self.path.lstrip("/"))
                if not file_path.exists() or not file_path.is_file():
                    self.send_error(404)
                    return
                content = file_path.read_bytes()
                content_type = "text/html; charset=utf-8"
                if file_path.suffix == ".css":
                    content_type = "text/css; charset=utf-8"
                if file_path.suffix == ".js":
                    content_type = "application/javascript; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

        return Handler

    def start_background(self) -> Thread:
        self.httpd = ThreadingHTTPServer((self.host, self.port), self.make_handler())
        thread = Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()
        return thread

