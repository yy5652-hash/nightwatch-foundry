"""Concurrent HTTP/JSON adapter; application decisions belong to core.Engine."""

from __future__ import annotations

import json
import os
import socket
import sys
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core import Engine


class RequestHeaders(Mapping):
    """A case-insensitive view without altering header values."""

    def __init__(self, headers):
        self._values = {key.lower(): value for key, value in headers.items()}

    def __getitem__(self, key):
        return self._values[key.lower()]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


class MalformedRequest(ValueError):
    pass


def reject_constant(value):
    raise MalformedRequest("JSON does not permit non-finite constants")


class Server(ThreadingHTTPServer):
    # A full 50-client burst must not get stuck behind the default small backlog.
    request_queue_size = 128
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, engine):
        self.engine = engine
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "Tablekeeper"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        # Bodies, tokens and private references never enter the access log.
        pass

    def send_error(self, code, message=None, explain=None):
        # BaseHTTPRequestHandler's HTTP framing errors must also be JSON.
        self.close_connection = True
        self.respond(code, {"error": {
            "code": "malformed_request" if code < 500 else "internal_error",
            "message": "Invalid HTTP request" if code < 500 else "Service error",
        }})

    def read_body(self):
        if self.headers.get("Transfer-Encoding") is not None:
            raise MalformedRequest("Use a Content-Length framed JSON request")
        lengths = self.headers.get_all("Content-Length", [])
        if not lengths:
            return None
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            raise MalformedRequest("Invalid Content-Length")
        length = int(lengths[0])
        if length == 0:
            return None
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise MalformedRequest("Incomplete request body")
        try:
            body = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise MalformedRequest("Body must be valid UTF-8 JSON") from exc
        if not isinstance(body, dict):
            raise MalformedRequest("Body must be a JSON object")
        return body

    def respond(self, status, body):
        # Serialize before sending headers so serialization cannot leave a false
        # successful status on an incomplete response. ASCII escapes are UTF-8
        # compatible and also safely preserve JSON-escaped surrogate strings.
        payload = b"" if status == 204 else json.dumps(
            body, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        if self.close_connection:
            self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD" and payload:
            self.wfile.write(payload)

    def dispatch(self):
        try:
            body = self.read_body()
        except (MalformedRequest, socket.timeout, OSError, ValueError) as exc:
            self.close_connection = True
            self.respond(400, {"error": {
                "code": "malformed_request", "message": "Body must be a JSON object",
            }})
            return
        try:
            status, result = self.server.engine.request(
                self.command, self.path, RequestHeaders(self.headers), body
            )
            self.respond(status, result)
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            # The operation may already be committed. Do not try it a second
            # time; the client's original idempotency key recovers its receipt.
            self.close_connection = True
        except Exception as exc:
            # An unexpected backend failure remains a failure, never success.
            print("Engine/response failure: " + type(exc).__name__, file=sys.stderr)
            self.close_connection = True
            self.respond(500, {"error": {
                "code": "internal_error", "message": "Service error",
            }})

    def __getattr__(self, name):
        # Unsupported routes/methods go through Engine's JSON refusal semantics
        # instead of the standard library's HTML 501 response.
        if name.startswith("do_"):
            return self.dispatch
        raise AttributeError(name)


def main():
    port = int(os.environ.get("PORT", "8080"))
    with Server(("0.0.0.0", port), Engine()) as server:
        print(f"Tablekeeper listening on 0.0.0.0:{port}", flush=True)
        server.serve_forever(poll_interval=0.2)


if __name__ == "__main__":
    main()
