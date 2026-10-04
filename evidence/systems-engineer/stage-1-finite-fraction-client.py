"""Own black-box finite-decimal classification probe; no service imports."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.set_int_max_str_digits(0)
base, output = sys.argv[1:3]
literal = str(10 ** 4300 + 1) + ".5"
assert re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", literal)
decimal = Decimal(literal)
assert decimal.is_finite() and decimal.as_tuple().exponent == -1
standard = json.loads(literal)
events = []
started = time.monotonic()


def send(method, path, raw=None, token=None, key=None, expected=200, code=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    request = Request(base + path, data=raw, headers=headers, method=method)
    beginning = time.monotonic()
    try:
        response = urlopen(request, timeout=5)
    except HTTPError as error:
        response = error
    value = json.loads(response.read()) if response.status != 204 else None
    saved = dict(value) if isinstance(value, dict) else value
    if isinstance(saved, dict) and "token" in saved:
        saved["token"] = {"sha256": hashlib.sha256(saved["token"].encode()).hexdigest()}
    passed = response.status == expected and (code is None or value.get("error", {}).get("code") == code)
    events.append({"method": method, "path": path, "request_sha256": hashlib.sha256(raw or b"").hexdigest(),
                   "expected_status": expected, "expected_code": code, "observed_status": response.status,
                   "response": saved, "passed": passed, "wall_seconds": time.monotonic() - beginning})
    return value


fixture = {"users": [{"id": "u", "email": "fraction@example.test", "password": "finite fixture", "display_name": "Finite"}],
           "restaurants": [{"id": "r", "name": "Finite dining", "timezone": "UTC", "slot_minutes": 30,
                            "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                            "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "23:00"}
                                              for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                            "tables": [{"id": "t", "label": "Window", "capacity": 4}]}], "reservations": []}
send("POST", "/_test/reset", json.dumps(fixture).encode(), expected=204)
token = send("POST", "/auth/login", json.dumps({"email": "fraction@example.test", "password": "finite fixture"}).encode())["token"]
normal = json.dumps({"restaurant_id": "r", "table_id": "t", "starts_at_local": "2099-01-01T18:00", "party_size": 2})
send("POST", "/reservations", normal.replace('"party_size": 2', '"party_size": 1.5').encode(), token, "small-fraction", 422, "validation_failed")
send("POST", "/reservations", normal.replace('"party_size": 2', '"party_size": ' + literal).encode(), token, "huge-fraction", 422, "validation_failed")
unknown = (normal[:-1] + ', "ignored_number": ' + literal + '}').encode()
send("POST", "/reservations", unknown, token, "ignored-fraction", 201)
send("POST", "/reservations", normal.encode(), token, "saved-key", 201)
send("POST", "/reservations", unknown, token, "saved-key", 409, "idempotency_key_reuse")
send("POST", "/reservations", normal.replace('"party_size": 2', '"party_size": NaN').encode(), token, "non-json-constant", 400, "malformed_request")
report = {"literal": {"integer_digits": 4301, "fractional_digits": 1, "sha256": hashlib.sha256(literal.encode()).hexdigest(),
                       "valid_json_number_grammar": True, "exact_decimal_finite": decimal.is_finite(),
                       "stdlib_float_result": "infinity" if standard == float("inf") else "finite"},
          "operations": events, "summary": {"operations": len(events), "assertions": len(events),
                                             "failed": sum(not item["passed"] for item in events),
                                             "wall_seconds": time.monotonic() - started}}
Path(output).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report["summary"]))
sys.exit(bool(report["summary"]["failed"]))
