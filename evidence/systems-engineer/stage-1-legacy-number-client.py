"""Genuine old parser receipts and counterfactual exact comparison evidence."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

old_url, current_url, output = sys.argv[1:4]
events, checks = [], []
started = time.monotonic()


def check(value, label):
    checks.append({"label": label, "passed": bool(value)})


def call(url, method, path, raw=None, token=None, key=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    request = Request(url + path, data=raw, headers=headers, method=method)
    beginning = time.monotonic()
    try:
        response = urlopen(request, timeout=5)
    except HTTPError as error:
        response = error
    wire = response.read()
    value = json.loads(wire) if wire else None
    events.append({"source": "genuine old" if url == old_url else "candidate5",
                   "method": method, "path": path, "request_sha256": hashlib.sha256(raw or b"").hexdigest(),
                   "response_sha256": hashlib.sha256(wire).hexdigest(), "expected_status": expected,
                   "observed_status": response.status, "wall_seconds": time.monotonic() - beginning})
    check(response.status == expected, method + " " + path + " HTTP " + str(expected))
    return value, wire


fixture = {"users": [{"id": "u", "email": "numeric-legacy@example.test", "password": "legacy fixture", "display_name": "Legacy"}],
           "restaurants": [{"id": "r", "name": "Legacy dining", "timezone": "UTC", "slot_minutes": 30,
                            "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                            "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "23:00"}
                                              for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                            "tables": [{"id": "t", "label": "Window", "capacity": 4}]}], "reservations": []}
call(old_url, "POST", "/_test/reset", json.dumps(fixture).encode(), expected=204)
auth, _ = call(old_url, "POST", "/auth/login", json.dumps({"email": "numeric-legacy@example.test", "password": "legacy fixture"}).encode())
token = auth["token"]


def body(literal, local):
    base = json.dumps({"restaurant_id": "r", "table_id": "t", "starts_at_local": local, "party_size": 2})
    return (base[:-1] + ', "ignored_number": ' + literal + '}').encode()


cases = [("point", "0.100000000000000005", "0.1", "0.10000000000000002", "2099-01-01T18:00"),
         ("large", "9007199254740993.0", "9007199254740992", "9007199254740993", "2099-01-01T19:30")]
originals = {}
for key, literal, alias, different, local in cases:
    original, _ = call(old_url, "POST", "/reservations", body(literal, local), token, key, 201)
    originals[key] = original
    replay, _ = call(old_url, "POST", "/reservations", body(literal, local), token, key)
    check(replay == original, key + " genuine original retry")
    replay, _ = call(old_url, "POST", "/reservations", body(alias, local), token, key)
    check(replay == original, key + " genuine source parser alias")
    call(old_url, "POST", "/reservations", body(different, local), token, key, 409)

exported, wire_export = call(old_url, "GET", "/_test/export")
exact_export = json.loads(wire_export, parse_float=Decimal)
receipt_fields = sorted(exported["state"]["receipts"][0])
observations = []
for key, literal, alias, different, local in cases:
    receipt = next(row for row in exported["state"]["receipts"] if row["key"] == key)
    exact_receipt = next(row for row in exact_export["state"]["receipts"] if row["key"] == key)
    stored = receipt["body"]["ignored_number"]
    exact_stored = exact_receipt["body"]["ignored_number"]
    observations.append({"key": key, "original_literal": literal, "old_stored_type": type(stored).__name__,
                         "old_export_literal": json.dumps(stored), "exact_imported_value": str(exact_stored),
                         "counterfactual_exact_original_matches": Decimal(literal) == exact_stored,
                         "legacy_original_matches": json.loads(literal) == stored,
                         "legacy_integer_alias_matches": json.loads(alias) == stored,
                         "legacy_distinct_integer_or_fraction_matches": json.loads(different) == stored})
    check(Decimal(literal) != exact_stored, key + " raw precision lost in genuine export")
call(current_url, "POST", "/_test/import", wire_export, expected=204)
for key, literal, alias, different, local in cases:
    replay, _ = call(current_url, "POST", "/reservations", body(literal, local), token, key)
    check(replay == originals[key], key + " unchanged original receipt after actual import")
    call(current_url, "POST", "/reservations", body(different, local), token, key, 409)

report = {"receipt_fields": receipt_fields, "state_schema": exported["state"]["schema"],
          "export_has_numeric_profile": any("numeric" in key or "parser" in key for key in exported["state"]),
          "observations": observations, "operations": events, "assertions": checks,
          "summary": {"operations": len(events), "assertions": len(checks),
                      "failed": sum(not value["passed"] for value in checks), "wall_seconds": time.monotonic() - started}}
Path(output).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report["summary"]))
sys.exit(bool(report["summary"]["failed"]))
