"""Synthetic adapter boundary only; never evidence of Tablekeeper transactions.

Driver injects h from our independently authored exact-number HTTP client.
Imports packaged Server, which calls the packaged codec. Expected values come
from h's lexical reader and exact recursive comparison, not from that codec.
"""
import concurrent.futures
import hashlib
import http.client
import json
import socket
import threading
import time
from server import Server

read, write, same = h["read"], h["write"], h["same"]
checks, trace = [], []
start = time.monotonic()


def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})


class BoundaryFixtureEngine:
    """Echo fixture deliberately bypasses all product field/state semantics."""
    def __init__(self):
        self.calls = 0
        self.lock = threading.Lock()

    def request(self, method, target, headers, body):
        with self.lock:
            self.calls += 1
        if target == "/empty":
            return 204, {"deliberately_unused": object()}
        if target == "/invalid-output":
            return 201, {"unsupported_fixture_leaf": object()}
        return 200, {"method": method, "target": target,
                     "header": headers.get("x-fixture"), "body": body}


engine = BoundaryFixtureEngine()
server = Server(("127.0.0.1", 0), engine)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
port = server.server_port


def call(raw=None, path="/echo?x=%2B4&x=second", method="POST", headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    begin = time.monotonic()
    try:
        c.request(method, path, raw, {"x-FiXtUrE": "preserved", **(headers or {})})
        r = c.getresponse()
        wire = r.read()
        value = read(wire) if wire else None
        check("JSON UTF-8 media type", r.getheader("Content-Type") == "application/json; charset=utf-8")
        check("Exact encoded Content-Length", r.getheader("Content-Length") == str(len(wire)))
        check("Request under five seconds", time.monotonic()-begin < 5)
        trace.append({"method": method, "path": path, "status": r.status,
                      "request_sha256": hashlib.sha256(raw or b"").hexdigest(),
                      "response_sha256": hashlib.sha256(wire).hexdigest()})
        return r.status, value, wire
    finally:
        c.close()


try:
    values = [b'{"n":1.0}', b'{"n":1e0}', b'{"n":-0e-4300}',
              b'{"n":0.100000000000000005}', b'{"n":1e4300}', b'{"n":1e-4300}',
              b'{"n":1e999999999999999999999999999999999999}',
              ('{"n":'+str(10**4300+1)+'}').encode(),
              ('{"n":'+str(10**4300+1)+'.5}').encode(),
              b'{"n":9007199254740993.0,"nested":[true,false,null,"1",1e0]}',
              '{"text":"Zoë 餐桌","escaped":"\\ud800"}'.encode()]
    for raw in values:
        status, value, _ = call(raw)
        check("Exact synthetic numeric/Unicode echo", status == 200 and same(value["body"], read(raw)))
        check("Original target and case-insensitive headers", value["target"] == "/echo?x=%2B4&x=second" and value["header"] == "preserved")
    before = engine.calls
    malformed = [b'{', b'null', b'[]', b'4', b'true', b'"x"', b'{"n":NaN}',
                 b'{"n":Infinity}', b'{"n":-Infinity}', b'{"n":1,}', b'{"n":01}',
                 b'{"n":+1}', b'{"n":1e}', b'{"n":.5}', b'{} trailing', b'{"x":"\xff"}',
                 '{}'.encode('utf-16')]
    for raw in malformed:
        status, value, _ = call(raw)
        check("Syntax/encoding/nonobject HTTP refusal", status == 400 and value["error"]["code"] == "malformed_request")
    check("Malformed bodies never reach fixture Engine", engine.calls == before)
    status, value, wire = call(b'{}', path="/empty")
    check("204 has no body and bypasses unused value encoding", (status, value, wire) == (204, None, b''))
    status, value, _ = call(None)
    check("Absent body remains absent", status == 200 and value["body"] is None)
    status, value, _ = call(b'{}', path="/invalid-output")
    check("Encoding completes before success headers", status == 500 and value["error"]["code"] == "internal_error")
    status, value, _ = call(b'{}', headers={"Transfer-Encoding": "chunked"})
    check("Unsupported transfer encoding remains 400", status == 400 and value["error"]["code"] == "malformed_request")
    before = engine.calls
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.putrequest("POST", "/echo")
    c.putheader("Content-Length", "2")
    c.putheader("Content-Length", "2")
    c.endheaders(b'{}')
    r = c.getresponse()
    value = read(r.read())
    check("Duplicate framing remains 400", r.status == 400 and value["error"]["code"] == "malformed_request" and engine.calls == before)
    c.close()
    barrier = threading.Barrier(50)
    def send_parallel(i):
        raw = ('{"n":'+str(i)+'.000000000000000005}').encode()
        barrier.wait(timeout=5)
        status, value, _ = call(raw)
        return status == 200 and same(value["body"], read(raw))
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
        responses = list(pool.map(send_parallel, range(50)))
    check("50 actual HTTP fixture calls retain independent exact bodies", all(responses))
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)

summary = {"scope": "Synthetic packaged HTTP adapter/codec fixture only; no Tablekeeper state or transaction claim",
           "operations": len(trace)+1, "assertions": len(checks),
           "passed": sum(r["passed"] for r in checks), "failed": sum(not r["passed"] for r in checks),
           "elapsed_seconds": time.monotonic()-start, "checks": checks, "trace": trace,
           "fixture_engine_calls": engine.calls}
print(json.dumps(summary, indent=2))
raise SystemExit(1 if summary["failed"] else 0)
