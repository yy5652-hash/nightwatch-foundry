"""Inductive JSON grammar and raw HTTP nesting boundary; no service imports.

The array chain is constructed from one valid finite numeric leaf. Adding one
balanced pair of brackets preserves JSON grammar by the JSON array production.
The client never parses or serializes the deep private state recursively.
"""
import hashlib
import http.client
import json
import sys
import time
from urllib.parse import urlsplit

BASE, PEER, CANDIDATE = sys.argv[1:4]
operations, checks, payloads = [], [], {}
started = time.monotonic()
fixture = {"users": [], "restaurants": [{"id": "r", "name": "Depth Kitchen", "timezone": "UTC", "slot_minutes": 30,
    "reservation_duration_minutes": 60, "cancellation_cutoff_minutes": 0,
    "opening_hours": [{"weekday": "mon", "opens": "18:00", "closes": "23:00"}],
    "tables": [{"id": "t", "label": "Window", "capacity": 4}]}], "reservations": []}
ordinary_fixture = json.dumps(fixture, separators=(",", ":")).encode()
ordinary_create = b'{"restaurant_id":"r","table_id":"t","starts_at_local":"2035-06-04T18:00","party_size":2}'

def digest(raw): return hashlib.sha256(raw).hexdigest()

def chain(depth, leaf="1"):
    assert depth >= 0 and type(depth) is int
    assert json.loads(leaf) in [1, 2]  # shallow independently validated leaves
    raw = "[" * depth + leaf + "]" * depth
    assert raw.count("[") == raw.count("]") == depth
    assert raw[:depth] == "[" * depth and raw[-depth:] == "]" * depth
    return raw.encode()

def with_ignored(raw, value):
    assert raw.startswith(b"{") and raw.endswith(b"}")
    return raw[:-1] + b',"ignored":' + value + b"}"

def call(method, path, raw=None, token=None, key=None, base=BASE):
    url = urlsplit(base)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token is not None: headers["Authorization"] = "Bearer " + token
    if key is not None: headers["Idempotency-Key"] = key
    began = time.monotonic()
    connection = http.client.HTTPConnection(url.hostname, url.port, timeout=10 if path.startswith("/_test/") else 5)
    try:
        connection.request(method, path, body=raw, headers=headers)
        response = connection.getresponse(); status = response.status; response_raw = response.read()
        value = None if not response_raw else json.loads(response_raw) if path != "/_test/export" else None
        content_type = response.getheader("Content-Type")
        error = value.get("error", {}).get("code") if isinstance(value, dict) else None
        if path.startswith("/auth/"): public = {k:v for k,v in value.items() if k != "token"} if isinstance(value,dict) else value
        elif path == "/_test/export": public = {"private_snapshot_sha256": digest(response_raw), "bytes": len(response_raw)}
        else: public = value
        operations.append(dict(method=method, path=path, peer=base, request_sha256=digest(raw) if raw else None,
            request_bytes=len(raw) if raw else 0, status=status, code=error, response=public,
            response_sha256=digest(response_raw), content_type=content_type, duration_seconds=time.monotonic()-began))
        return status, value, response_raw
    finally: connection.close()

def check(rid, expected, observed, code=None):
    status, value, _ = observed
    checks.append(dict(requirement_id="TK1-very-deep-"+rid, passed=status==expected and (code is None or value.get("error",{}).get("code")==code),
        expected={"status":expected,"code":code}, observed={"status":status,"code":value.get("error",{}).get("code") if isinstance(value,dict) else None}, operation=len(operations)))

for depth in [1100, 5000, 10000, 20000]:
    nested = chain(depth)
    payloads[str(depth)] = dict(depth=depth, chain_bytes=len(nested), grammar="inductive balanced arrays around independently parsed finite number",
        chain_sha256=digest(nested), create_body=with_ignored(ordinary_create,nested).decode(), reset_body=with_ignored(ordinary_fixture,nested).decode())
    check(f"{depth}-control-reset",204,call("POST","/_test/reset",ordinary_fixture))
    check(f"{depth}-ignored-reset",204,call("POST","/_test/reset",with_ignored(ordinary_fixture,nested)))
    signup=json.dumps({"email":"depth@probe.invalid","password":"depth-probe-pass","display_name":"Depth Diner"}).encode()
    malformed_signup=call("POST","/auth/signup",with_ignored(signup,nested)[:-1])
    check(f"{depth}-malformed-signup-refusal",400,malformed_signup,"malformed_request")
    deep_signup=call("POST","/auth/signup",with_ignored(signup,nested))
    check(f"{depth}-signup-refusal-rollback",201,deep_signup)
    check(f"{depth}-ignored-signup",201,deep_signup)
    token=deep_signup[1].get("token") if isinstance(deep_signup[1],dict) else None
    if token is None:
        ordinary_signup=call("POST","/auth/signup",signup)
        check(f"{depth}-signup-refusal-rollback",201,ordinary_signup)
        token=ordinary_signup[1]["token"]
    body=with_ignored(ordinary_create,nested); key="depth-create"
    invalid=call("POST","/reservations",with_ignored(ordinary_create.replace(b'"party_size":2',b'"party_size":0'),nested),token,key)
    check(f"{depth}-invalid-party-refusal",422,invalid,"validation_failed")
    created=call("POST","/reservations",body,token,key)
    check(f"{depth}-failed-key-reusable",201,created)
    check(f"{depth}-ignored-create",201,created)
    if created[0]==201:
        alias=call("POST","/reservations",with_ignored(ordinary_create,chain(depth,"1.0")),token,key)
        check(f"{depth}-exact-alias-replay",200,alias)
        if depth in [10000,20000]:
            checks.append(dict(requirement_id=f"TK1-very-deep-{depth}-dependent-accepted-body-alias-replay",passed=alias[0]==200 and alias[1]==created[1],expected="exact same successful deep original receipt",observed="equal" if alias[1]==created[1] else "different",operation=len(operations)))
        original=created[1]
    else:
        recovered=call("POST","/reservations",ordinary_create,token,key)
        check(f"{depth}-failed-key-reusable",201,recovered)
        original=recovered[1]
    check(f"{depth}-used-key-deep-difference",409,call("POST","/reservations",with_ignored(ordinary_create,chain(depth,"2")),token,key),"idempotency_key_reuse")
    move=json.dumps({"moves":[{"reference":original["reference"]}]}).encode()
    moved=call("POST","/reservation-moves",with_ignored(move,nested),token,"depth-move")
    check(f"{depth}-ignored-move",201,moved)
    exported=call("GET","/_test/export")
    check(f"{depth}-export",200,exported)
    captured=exported[2]
    check(f"{depth}-source-cancel",200,call("POST","/reservations/"+original["reference"]+"/cancel",b"{}",token))
    check(f"{depth}-unchanged-peer-import",204,call("POST","/_test/import",captured,base=PEER))
    retry=body if created[0]==201 else ordinary_create
    replay=call("POST","/reservations",retry,token,key,base=PEER)
    check(f"{depth}-import-original-replay",200,replay)
    if depth in [10000,20000]:
        checks.append(dict(requirement_id=f"TK1-very-deep-{depth}-dependent-deep-original-receipt-transfer",passed=created[0]==201 and moved[0]==201 and replay[0]==200 and replay[1]==original,expected="genuine deep create/move receipts in unchanged captured HTTP bytes, original replay",observed="confirmed" if created[0]==moved[0]==201 and replay[0]==200 else "blocked",operation=len(operations)))
    checks.append(dict(requirement_id=f"TK1-very-deep-{depth}-immutable-receipt",passed=replay[1]==original,
        expected="original successful public receipt",observed="equal" if replay[1]==original else "different",operation=len(operations)))

print(json.dumps(dict(candidate=CANDIDATE,requests=len(operations),assertions=len(checks),failed_assertions=sum(not c["passed"] for c in checks),
    duration_seconds=time.monotonic()-started,depths=[1100,5000,10000,20000],max_request_bytes=max(o["request_bytes"] for o in operations),
    max_request_seconds=max(o["duration_seconds"] for o in operations),operations=operations,checks=checks,payloads=payloads),indent=2))
raise SystemExit(1 if any(not c["passed"] for c in checks) else 0)
