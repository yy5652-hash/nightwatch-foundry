"""Specification-derived HTTP decimal-boundary diagnostics; no production imports.

The client alone enables long decimal conversion. The service runs independently,
so client parsing cannot alter the server's conversion configuration. Exports,
passwords and bearer tokens remain in memory; saved traces contain fingerprints.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.set_int_max_str_digits(0)
HUGE = 10 ** 4300 + 1
LOCAL = "2099-01-01T18:10"
events, assertions = [], []
parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--destination-url")
parser.add_argument("--stage", type=int, choices=(1, 2), default=2)
parser.add_argument("--reproduce", action="store_true")
parser.add_argument("--trace", required=True)
args = parser.parse_args()
started = time.monotonic()


def safe(value, key=""):
    if key in ("state", "tokens"):
        return {"private_state_sha256": hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()}
    if key in ("password", "token", "password_hash"):
        return {"fingerprint": hashlib.sha256(str(value).encode()).hexdigest()}
    if type(value) is int and value.bit_length() > 10000:
        literal = str(value)
        return {"integer_digits": len(literal), "sha256": hashlib.sha256(literal.encode()).hexdigest()}
    if isinstance(value, dict):
        return {k: safe(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [safe(v) for v in value]
    return value


def check(condition, label):
    assertions.append({"label": label, "passed": bool(condition)})


def call(method, path, body=None, token=None, key=None, destination=False, raw_body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    raw = raw_body if raw_body is not None else (json.dumps(body, separators=(",", ":")).encode() if body is not None else None)
    request = Request((args.destination_url if destination else args.url) + path,
                      data=raw, headers=headers, method=method)
    beginning = time.monotonic()
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as error:
        response = error
    data = response.read()
    value = json.loads(data) if data else None
    events.append({"method": method, "path": path if len(path) < 1000 else path[:90] + "...[4301-digit query]",
                   "request": safe(body) if raw_body is None else {"raw_sha256": hashlib.sha256(raw_body).hexdigest()},
                   "status": response.status, "response": safe(value),
                   "destination": destination, "wall_seconds": time.monotonic() - beginning})
    return response.status, value


def expect(result, status, label, code=None):
    check(result[0] == status, label + " HTTP " + str(status))
    if code:
        check(isinstance(result[1], dict) and result[1].get("error", {}).get("code") == code,
              label + " error " + code)
    return result[1]


def fixture(field=None, pair=False):
    restaurant = {"id": "r", "name": "Decimal dining", "timezone": "UTC", "slot_minutes": 30,
                  "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                  "opening_hours": [{"weekday": day, "opens": "18:10", "closes": "23:10"}
                                    for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                  "tables": [{"id": "a", "label": "Window", "capacity": 2}]}
    if field == "capacity":
        restaurant["tables"][0][field] = HUGE
    elif field:
        restaurant[field] = HUGE
    if pair:
        restaurant["tables"].append({"id": "b", "label": "Garden", "capacity": HUGE})
        restaurant["combinable"] = [["b", "a"]]
    return {"users": [{"id": "u", "email": "decimal@example.test", "password": "decimal fixture",
                       "display_name": "Decimal diner"}], "restaurants": [restaurant], "reservations": []}


def reset(field=None, pair=False):
    return expect(call("POST", "/_test/reset", fixture(field, pair)), 204, "reset " + str(field))


def login(destination=False):
    value = expect(call("POST", "/auth/login", {"email": "decimal@example.test", "password": "decimal fixture"},
                        destination=destination), 200, "login")
    return value["token"]


def available(party=2, destination=False):
    query = urlencode({"restaurant_id": "r", "date": "2099-01-01", "party_size": str(party)})
    return expect(call("GET", "/availability?" + query, destination=destination), 200, "availability")


def booking(**changes):
    return {"restaurant_id": "r", "table_id": "a", "starts_at_local": LOCAL, "party_size": 2, **changes}


def snapshot():
    return expect(call("GET", "/_test/export"), 200, "snapshot")


try:
    if args.reproduce:
        reset()
        for field in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "capacity"):
            reset(field)
        reset()
        available(HUGE)
    else:
        assert args.destination_url, "independent destination required"
        for field in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "capacity"):
            reset(field)
            detail = expect(call("GET", "/restaurants/r"), 200, "giant configuration")
            value = detail["tables"][0][field] if field == "capacity" else detail[field]
            check(type(value) is int and value == HUGE, field + " exact JSON integer")
            exported = snapshot()
            expect(call("POST", "/_test/import", exported, destination=True), 204, "giant replacement import")
            repeated = expect(call("GET", "/_test/export", destination=True), 200, "destination snapshot")
            check(repeated == exported, field + " unchanged cross-process snapshot")
            login(destination=True)

        reset("slot_minutes")
        slots = available()["slots"]
        check([x["starts_at_local"] for x in slots] == [LOCAL], "huge grid only opening candidate")
        token = login()
        body = booking(starts_at_local="2099-01-01T18:40", ignored_integer=HUGE)
        expect(call("POST", "/reservations", body, token, "grid"), 422, "huge grid off-grid", "not_on_slot_grid")
        body["starts_at_local"] = LOCAL
        original = expect(call("POST", "/reservations", body, token, "grid"), 201, "failed grid key reusable")
        check(expect(call("POST", "/reservations", body, token, "grid"), 200, "giant body replay") == original,
              "original receipt unchanged")
        exported = snapshot()
        expect(call("POST", "/_test/import", exported, destination=True), 204, "successful giant-body import")
        check(expect(call("POST", "/reservations", body, token, "grid", True), 200, "imported original retry") == original,
              "body/key/token/receipt preserved")
        altered = {**body, "ignored_integer": HUGE + 1, "party_size": False}
        expect(call("POST", "/reservations", altered, token, "grid", True), 409,
               "giant body conflict before invalid party", "idempotency_key_reuse")

        reset("reservation_duration_minutes")
        check(available()["slots"] == [], "huge duration no fitting slots")
        token = login()
        before = snapshot()
        expect(call("POST", "/reservations", booking(), token, "duration"), 422,
               "huge duration create refused", "outside_opening_hours")
        check(snapshot() == before, "huge duration failure atomic, no receipt")

        reset("cancellation_cutoff_minutes")
        token = login()
        reservation = expect(call("POST", "/reservations", booking(), token, "cutoff"), 201, "huge cutoff create")
        before = snapshot()
        reference = reservation["reference"]
        expect(call("PATCH", "/reservations/" + reference, {"party_size": 1}, token), 409,
               "huge cutoff edit", "cutoff_passed")
        expect(call("POST", "/reservations/" + reference + "/cancel", token=token), 409,
               "huge cutoff cancel", "cutoff_passed")
        expect(call("POST", "/reservation-moves", {"moves": [{"reference": reference, "party_size": 1}]},
                    token, "cutoff-move"), 409, "huge cutoff move", "cutoff_passed")
        check(snapshot() == before, "cutoff failures preserve records/occupancy/keys")

        reset("capacity", pair=args.stage == 2)
        slots = available(HUGE)["slots"]
        check(len(slots) == 8 and all("a" in x["available_table_ids"] for x in slots),
              "giant capacity serves exact giant query")
        if args.stage == 2:
            expected = [{"table_ids": ["a"], "capacity": HUGE}, {"table_ids": ["b"], "capacity": HUGE},
                        {"table_ids": ["b", "a"], "capacity": HUGE * 2}]
            check(all(x["available_options"] == expected for x in slots), "exact pair capacity and declared order")
        token = login()
        body = booking(party_size=HUGE)
        reservation = expect(call("POST", "/reservations", body, token, "capacity"), 201, "giant party create")
        check(type(reservation["party_size"]) is int and reservation["party_size"] == HUGE, "giant party response exact")
        exported = snapshot()
        expect(call("POST", "/_test/import", exported, destination=True), 204, "giant-party record and receipt import")
        check(expect(call("POST", "/reservations", body, token, "capacity", True), 200, "giant-party imported replay") == reservation,
              "giant-party original receipt exact")
        reference = reservation["reference"]
        changed = expect(call("PATCH", "/reservations/" + reference, {"party_size": 1}, token), 200, "giant-party edit")
        check(changed["party_size"] == 1, "giant-party edit current state")
        check(expect(call("POST", "/reservations", body, token, "capacity"), 200, "giant-party replay after edit") == reservation,
              "giant-party saved receipt remains original")

        moves = {"moves": [{"reference": reference, "party_size": HUGE, "ignored_integer": HUGE}],
                 "ignored_integer": HUGE}
        moved = expect(call("POST", "/reservation-moves", moves, token, "giant-move"), 201, "giant-party batch move")
        check(moved["reservations"][0]["party_size"] == HUGE, "batch exact integer party")
        expect(call("PATCH", "/reservations/" + reference, {"party_size": 1}, token), 200, "edit after giant move")
        check(expect(call("POST", "/reservation-moves", moves, token, "giant-move"), 200, "giant move replay after edit") == moved,
              "batch receipt remains original")
        exported = snapshot()
        expect(call("POST", "/_test/import", exported, destination=True), 204, "giant batch receipt replacement import")
        check(expect(call("POST", "/reservation-moves", moves, token, "giant-move", True), 200, "imported giant move replay") == moved,
              "batch full body/key/token/receipt preserved")
        altered = deepcopy(moves)
        altered["moves"][0]["ignored_integer"] += 1
        altered["moves"][0]["party_size"] = False
        expect(call("POST", "/reservation-moves", altered, token, "giant-move", True), 409,
               "batch changed giant body before invalid party", "idempotency_key_reuse")

        reset()
        slots = available(HUGE)["slots"]
        check(len(slots) == 8 and all(x["available_table_ids"] == [] for x in slots), "giant query small capacity empty singles")
        if args.stage == 2:
            check(all(x["available_options"] == [] for x in slots), "giant query empty options")
        for bad in ("+4", "4.0", "1e9", "-1"):
            expect(call("GET", "/availability?" + urlencode({"restaurant_id": "r", "date": "2099-01-01", "party_size": bad})),
                   422, "invalid query " + bad, "validation_failed")
        token = login()
        before = snapshot()
        for bad, status, code in ((str(HUGE), 400, "malformed_request"), (True, 400, "malformed_request"), (1.5, 400, "malformed_request"),
                                  (-1, 422, "validation_failed")):
            bad_fixture = fixture()
            bad_fixture["restaurants"][0]["slot_minutes"] = bad
            expect(call("POST", "/_test/reset", bad_fixture), status, "invalid base field", code)
            check(snapshot() == before, "invalid reset preserves complete state")
        for raw in (b'{"restaurants":', b'null', b'[]', b'{"slot_minutes":NaN}'):
            expect(call("POST", "/_test/reset", raw_body=raw), 400, "malformed raw reset", "malformed_request")
            check(snapshot() == before, "malformed reset preserves complete state")
        for bad in (str(HUGE), True, 0, 1.5):
            expect(call("POST", "/reservations", booking(party_size=bad), token, "invalid-party"),
                   422, "invalid party", "validation_failed")
finally:
    failures = [x for x in assertions if not x["passed"]]
    report = {"mode": "reproduction" if args.reproduce else "regression", "stage": args.stage,
              "source": "Stage1 sections4/5/7/8/10/11, Stage2 combined capacities and inherited exact receipts",
              "integer_digits": len(str(HUGE)), "operations": events, "assertions": assertions,
              "summary": {"operations": len(events), "assertions": len(assertions), "failed": len(failures),
                          "wall_seconds": time.monotonic() - started}}
    Path(args.trace).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"]))
sys.exit(bool(failures))
