"""Supplemental deterministic Engine boundary ownership checks, inside image only.

This imports production in a constrained diagnostic process. It supplements the
separate real HTTP export/write/import checks; it is not HTTP acceptance proof.
"""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, "/app")
from core import Engine
from json_codec import loads

started = time.monotonic()
checks = []


def check(label, value):
    checks.append({"label": label, "passed": bool(value)})


source, peer = Engine(), Engine()
fixture = {"users": [{"id": "u", "email": "u@example.test", "password": "own fixture password",
                      "display_name": "Diner"}],
           "restaurants": [{"id": "r", "name": "Room", "timezone": "UTC", "slot_minutes": 30,
                            "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                            "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "23:00"}
                                              for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                            "tables": [{"id": "a", "label": "A", "capacity": 4},
                                       {"id": "b", "label": "B", "capacity": 4}]}],
           "reservations": []}
check("reset", source.request("POST", "/_test/reset", {}, fixture)[0] == 204)
token = source.request("POST", "/auth/login", {}, {"email": "u@example.test", "password": "own fixture password"})[1]["token"]
headers = {"Authorization": "Bearer " + token, "Idempotency-Key": "original"}
detail = source.request("GET", "/restaurants/r", {}, None)[1]
empty_export = source.request("GET", "/_test/export", {}, None)[1]
detail["tables"][0]["capacity"] = 1
fixture["restaurants"][0]["tables"][0]["capacity"] = 1
check("fixture and detail containers detached from state", source.request("GET", "/restaurants/r", {}, None)[1]["tables"][0]["capacity"] == 4)
nest = b'{"unused":' * 1100 + b'{"n":0.100000000000000005}' + b'}' * 1100
wire = b'{"restaurant_id":"r","table_id":"a","starts_at_local":"2037-06-01T18:00","party_size":2,"ignored":' + nest + b'}'
request_body = loads(wire)
status, result = source.request("POST", "/reservations", headers, request_body)
check("deep create", status == 201)
reference = result["reference"]
request_body["ignored"]["changed"] = True
result["party_size"] = 99
check("saved full request body detached", source.request("POST", "/reservations", headers, loads(wire))[0] == 200)
check("returned create detached from record and receipt", source.request("GET", "/reservations/" + reference, headers, None)[1]["party_size"] == 2
      and source.request("POST", "/reservations", headers, loads(wire))[1]["party_size"] == 2)
current = source.request("GET", "/reservations/" + reference, headers, None)[1]
listing = source.request("GET", "/reservations", headers, None)[1]
export = source.request("GET", "/_test/export", {}, None)[1]
move = {"moves": [{"reference": reference, "table_id": "b"}]}
move_headers = {**headers, "Idempotency-Key": "move"}
moved = source.request("POST", "/reservation-moves", move_headers, move)
check("move", moved[0] == 201)
check("captured current/list/export retain old assignment", current["table_id"] == "a"
      and listing["reservations"][0]["table_id"] == "a" and export["state"]["reservations"][0]["table_id"] == "a")
check("captured pre-create export retains empty reservations and receipts", empty_export["state"]["reservations"] == []
      and empty_export["state"]["receipts"] == [])
check("captured deep snapshot imports independently", peer.request("POST", "/_test/import", {}, export)[0] == 204)
export["state"]["receipts"][0]["body"]["ignored"]["tampered"] = True
export["state"]["reservations"][0]["party_size"] = 99
check("import candidate detached from input", peer.request("POST", "/reservations", headers, loads(wire))[0] == 200
      and peer.request("GET", "/reservations/" + reference, headers, None)[1]["party_size"] == 2)
moved[1]["reservations"][0]["party_size"] = 99
move["moves"][0]["table_id"] = "a"
check("batch request and response detached", source.request("POST", "/reservation-moves", move_headers,
      {"moves": [{"reference": reference, "table_id": "b"}]})[1]["reservations"][0]["party_size"] == 2)
check("cancel", source.request("POST", "/reservations/" + reference + "/cancel", headers, None)[0] == 200)
check("captured old current view survives cancellation", current["status"] == "confirmed")
check("original receipt survives move/cancel", source.request("POST", "/reservations", headers, loads(wire))[1]["table_id"] == "a")
replay = source.request("POST", "/reservations", headers, loads(wire))[1]
replay["reference"] = "CHANGED"
check("returned replay detached from archived receipt", source.request("POST", "/reservations", headers, loads(wire))[1]["reference"] == reference)
summary = {"assertions": len(checks), "passed": sum(c["passed"] for c in checks),
           "failed": sum(not c["passed"] for c in checks), "seconds": time.monotonic() - started,
           "kind": "deterministic Engine ownership diagnostic inside image; not HTTP"}
Path(sys.argv[1]).write_text(json.dumps({"summary": summary, "assertions": checks}, indent=2) + "\n")
print(json.dumps(summary))
sys.exit(bool(summary["failed"]))
