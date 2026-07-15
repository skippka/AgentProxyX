from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urljoin

from .cache import optimize_payload
from .cost import estimate_cost
from .firewall import AgentFirewall
from .replay import ReplayStore
from .secrets import redact_text


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


class AgentProxyServer:
    def __init__(
        self,
        config: dict[str, Any],
        store: ReplayStore,
        agent: str,
        target: str | None,
        host: str = "127.0.0.1",
        port: int = 8080,
        dry_run: bool = False,
    ):
        self.config = config
        self.store = store
        self.agent = agent
        self.target = target.rstrip("/") if target else None
        self.host = host
        self.port = port
        self.dry_run = dry_run
        self.firewall = AgentFirewall(config)
        self.httpd: ThreadingHTTPServer | None = None

    def make_handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

            def _send_json(self, code: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                if self.path == "/health":
                    self._send_json(200, {"ok": True, "name": "AgentProxyX", "agent": server.agent})
                    return
                self._handle_proxy()

            def do_POST(self) -> None:
                if self.path == "/v1/agentproxyx/tool-call":
                    self._handle_tool_call()
                    return
                self._handle_proxy()

            def do_PUT(self) -> None:
                self._handle_proxy()

            def do_PATCH(self) -> None:
                self._handle_proxy()

            def do_DELETE(self) -> None:
                self._handle_proxy()

            def _read_body(self) -> bytes:
                length = int(self.headers.get("Content-Length", "0") or "0")
                return self.rfile.read(length) if length else b""

            def _handle_tool_call(self) -> None:
                body = self._read_body()
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception:
                    self._send_json(400, {"allowed": False, "reason": "Invalid JSON"})
                    return
                decision = server.firewall.check_tool_call(payload)
                server.store.add(
                    "tool_allowed" if decision.allowed else "tool_blocked",
                    server.agent,
                    decision.reason,
                    {"payload": payload, "matches": decision.matches},
                )
                self._send_json(200 if decision.allowed else 403, {"allowed": decision.allowed, "reason": decision.reason})

            def _handle_proxy(self) -> None:
                body = self._read_body()
                text = body.decode("utf-8", errors="replace")
                redacted_text, findings = redact_text(text, server.config.get("redaction", {}).get("mask", "[REDACTED]"))
                if findings:
                    server.store.add(
                        "secret_redacted",
                        server.agent,
                        f"Redacted {len(findings)} possible secret(s)",
                        {"findings": [finding.kind for finding in findings]},
                    )
                    body = redacted_text.encode("utf-8")

                cache_result = optimize_payload(body, server.config)
                body = cache_result.body
                if cache_result.changed:
                    server.store.add(
                        "cache_optimized",
                        server.agent,
                        "Added prompt-cache hints",
                        {"cacheable_chars": cache_result.cacheable_chars, "provider": cache_result.provider},
                    )

                if server.dry_run or not server.target:
                    estimate = estimate_cost(body.decode("utf-8", errors="replace"), config=server.config, cacheable_chars=cache_result.cacheable_chars)
                    server.store.add(
                        "request",
                        server.agent,
                        f"Dry-run request: {estimate.input_tokens} input tokens",
                        {"path": self.path, "cost": estimate.__dict__},
                    )
                    self._send_json(
                        200,
                        {
                            "agentproxyx": "dry-run",
                            "path": self.path,
                            "redacted_secrets": len(findings),
                            "cache_optimized": cache_result.changed,
                            "cost": estimate.__dict__,
                        },
                    )
                    return

                target_url = urljoin(server.target + "/", self.path.lstrip("/"))
                headers = {
                    key: value
                    for key, value in self.headers.items()
                    if key.lower() not in HOP_BY_HOP_HEADERS
                }
                headers["Content-Length"] = str(len(body))
                request = urllib.request.Request(target_url, data=body or None, headers=headers, method=self.command)
                try:
                    with urllib.request.urlopen(request, timeout=120) as response:
                        response_body = response.read()
                        estimate = estimate_cost(
                            body.decode("utf-8", errors="replace"),
                            response_body.decode("utf-8", errors="replace"),
                            server.config,
                            cache_result.cacheable_chars,
                        )
                        server.store.add(
                            "request",
                            server.agent,
                            f"{self.command} {self.path} -> {response.status}",
                            {"cost": estimate.__dict__, "target": target_url},
                        )
                        self.send_response(response.status)
                        for key, value in response.headers.items():
                            if key.lower() not in HOP_BY_HOP_HEADERS:
                                self.send_header(key, value)
                        self.send_header("X-AgentProxyX", "active")
                        self.end_headers()
                        self.wfile.write(response_body)
                except urllib.error.HTTPError as exc:
                    error_body = exc.read()
                    server.store.add("provider_error", server.agent, f"Provider returned {exc.code}", {"target": target_url})
                    self.send_response(exc.code)
                    self.send_header("Content-Type", exc.headers.get("Content-Type", "application/json"))
                    self.end_headers()
                    self.wfile.write(error_body)
                except Exception as exc:
                    server.store.add("proxy_error", server.agent, str(exc), {"target": target_url})
                    self._send_json(502, {"error": "AgentProxyX upstream error", "detail": str(exc)})

        return Handler

    def serve_forever(self) -> None:
        self.httpd = ThreadingHTTPServer((self.host, self.port), self.make_handler())
        self.store.add("startup", self.agent, f"Proxy listening on http://{self.host}:{self.port}", {"target": self.target})
        self.httpd.serve_forever()

