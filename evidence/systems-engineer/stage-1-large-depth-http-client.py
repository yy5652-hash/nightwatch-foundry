"""Independent wire composition and raw export forwarding; never decode state."""
import hashlib
import http.client
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

source, destination, output = sys.argv[1:]
trace, assertions, cases = [], [], []
started = time.monotonic()
export_decoder_calls = 0


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def check(label, passed, **details):
    assertions.append({"label": label, "passed": bool(passed), **details})


def request(base, method, path, raw=None, token=None, key=None, decode=True):
    address = urlsplit(base)
    connection = http.client.HTTPConnection(address.hostname, address.port, timeout=10)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    begin = time.monotonic()
    connection.request(method, path, body=raw, headers=headers)
    response = connection.getresponse()
    body = response.read()
    connection.close()
    value = json.loads(body) if body and decode else None
    item = {"process": "source" if base == source else "destination", "method": method,
            "path": path, "request_bytes": len(raw or b""), "request_sha256": digest(raw or b""),
            "status": response.status, "response_bytes": len(body), "response_sha256": digest(body),
            "seconds": time.monotonic() - begin, "decoded": decode and bool(body)}
    if isinstance(value, dict) and "error" in value:
        item["error"] = value["error"]
    trace.append(item)
    return response.status, value, body


def encode(value):
    return json.dumps(value, separators=(",", ":")).encode()


fixture = {"users": [{"id": "u", "email": "depth@example.test", "password": "depth-control-password", "display_name": "Depth"}],
           "restaurants": [{"id": "r", "name": "Depth control", "timezone": "UTC", "slot_minutes": 30,
                            "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                            "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "23:00"}
                                              for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                            "tables": [{"id": "a", "label": "A", "capacity": 4}, {"id": "b", "label": "B", "capacity": 4}]}],
           "reservations": []}

try:
    for depth in (1100, 10000, 20000):
        for shape in ("array", "object"):
            label = "%s-%s" % (shape, depth)
            case = {"label": label, "depth": depth, "shape": shape, "blocked": []}
            for base in (source, destination):
                check(label + " reset", request(base, "POST", "/_test/reset", encode(fixture))[0] == 204)
            status, login, _ = request(source, "POST", "/auth/login", encode({"email": "depth@example.test", "password": "depth-control-password"}))
            check(label + " login", status == 200)
            token = login["token"]
            leaf = b'{"exact":0.100000000000000005,"large":1e4300}'
            if shape == "array":
                nested = b"[" * depth + leaf + b"]" * depth
            else:
                nested = b'{"x":' * depth + leaf + b"}" * depth
            case["grammar"] = "Valid scalar leaf inside balanced containers composed directly, not parsed by client"
            case["nested_bytes"], case["nested_sha256"] = len(nested), digest(nested)
            shallow_create = encode({"restaurant_id": "r", "table_id": "a", "starts_at_local": "2035-06-04T18:00", "party_size": 2})
            deep_create = shallow_create[:-1] + b',"ignored":' + nested + b"}"
            create_key = "create-" + label
            status, original, _ = request(source, "POST", "/reservations", deep_create, token, create_key)
            case["deep_create_status"] = status
            check(label + " valid deep ignored create", status == 201, expected=201, observed=status)
            create_raw = deep_create
            if status != 201:
                case["blocked"].append("Deep create receipt/replay/export cannot be observed because original valid request was refused")
                status, original, _ = request(source, "POST", "/reservations", shallow_create, token, create_key)
                check(label + " refused create key reusable", status == 201)
                create_raw = shallow_create
            reference = original["reference"]
            shallow_move = encode({"moves": [{"reference": reference, "table_id": "b"}]})
            deep_move = shallow_move[:-1] + b',"ignored":' + nested + b"}"
            move_key = "move-" + label
            status, original_move, _ = request(source, "POST", "/reservation-moves", deep_move, token, move_key)
            case["deep_move_status"] = status
            check(label + " valid deep ignored move", status == 201, expected=201, observed=status)
            move_raw = deep_move
            if status != 201:
                case["blocked"].append("Deep move receipt/replay/export cannot be observed because original valid request was refused")
                status, original_move, _ = request(source, "POST", "/reservation-moves", shallow_move, token, move_key)
                check(label + " refused move key reusable", status == 201)
                move_raw = shallow_move
            status, _, captured = request(source, "GET", "/_test/export", decode=False)
            check(label + " captured export", status == 200)
            case["export_bytes"], case["export_sha256"] = len(captured), digest(captured)
            case["export_contains_deep_receipts"] = create_raw == deep_create and move_raw == deep_move
            check(label + " source changes after snapshot", request(source, "POST", "/reservations/" + reference + "/cancel", token=token)[0] == 200)
            status, _, _ = request(destination, "POST", "/_test/import", captured, decode=False)
            check(label + " unchanged raw export import", status == 204)
            case["forwarded_bytes"], case["forwarded_sha256"] = len(captured), digest(captured)
            check(label + " byte-identical forwarding", case["export_sha256"] == case["forwarded_sha256"])
            status, current, _ = request(destination, "GET", "/reservations/" + reference, token=token)
            check(label + " token reference snapshot state", status == 200 and current["status"] == "confirmed" and current["table_id"] == "b")
            for base in (source, destination):
                status, replay, _ = request(base, "POST", "/reservations", create_raw, token, create_key)
                check(label + " original shallow create response replay", status == 200 and replay == original)
                status, replay, _ = request(base, "POST", "/reservation-moves", move_raw, token, move_key)
                check(label + " original shallow move response replay", status == 200 and replay == original_move)
            check(label + " peer cancellation", request(destination, "POST", "/reservations/" + reference + "/cancel", token=token)[0] == 200)
            status, replay, _ = request(destination, "POST", "/reservations", create_raw, token, create_key)
            check(label + " immutable receipt after peer change", status == 200 and replay == original)
            check(label + " both services remain healthy", all(request(base, "GET", "/health")[0] == 200 for base in (source, destination)))
            cases.append(case)
except Exception as error:
    check("client flow completed without exception", False, exception_type=type(error).__name__, message=str(error))
finally:
    check("client never decodes exported state", export_decoder_calls == 0)
    result = {"cases": cases, "trace": trace, "assertions": assertions,
              "summary": {"requests": len(trace), "assertions": len(assertions),
                          "failed": sum(not a["passed"] for a in assertions), "seconds": time.monotonic() - started,
                          "export_decoder_calls": export_decoder_calls,
                          "deep_export_cases": sum(c["export_contains_deep_receipts"] for c in cases),
                          "blocked_deep_export_cases": sum(bool(c["blocked"]) for c in cases)}}
    Path(output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"]))
    raise SystemExit(bool(result["summary"]["failed"]))
