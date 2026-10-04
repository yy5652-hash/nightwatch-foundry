"""Own spec-derived HTTP decimal and genuine legacy-transfer integration probe.

All credential and exported-state values stay in memory. Durable traces contain
only status, error code, public number fingerprints and request/response hashes.
Client integer configuration affects this separate client interpreter only.
"""

import copy
import hashlib
import http.client
import json
import sys
import time
from urllib.parse import urlsplit

sys.set_int_max_str_digits(0)
URLS = [urlsplit(url) for url in sys.argv[1:4]]
RESULTS, TRACE = [], []
START = time.monotonic()
GIANT = 10 ** 4300 + 1
DIGITS = str(GIANT)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":")).encode()).hexdigest()


def check(name, condition, detail=None):
    RESULTS.append({"name": name, "passed": bool(condition), "detail": detail})


def call(index, method, path, body=None, headers=None, raw=None):
    url = URLS[index]
    timeout = 10 if path.startswith("/_test/") else 5
    conn = http.client.HTTPConnection(url.hostname, url.port, timeout=timeout)
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    start = time.monotonic()
    try:
        conn.request(method, path, data, {"Content-Type": "application/json; charset=utf-8", **(headers or {})})
        response = conn.getresponse()
        wire = response.read()
        value = json.loads(wire) if wire else None
        elapsed = time.monotonic() - start
        check("HTTP JSON media type", response.getheader("Content-Type") == "application/json; charset=utf-8")
        check("HTTP byte framing", response.getheader("Content-Length") == str(len(wire)))
        check("HTTP request budget", elapsed < timeout)
        TRACE.append({"process": index, "method": method,
                      "path": path.replace(DIGITS, "<4301 decimal digits>"),
                      "request_sha256": hashlib.sha256(data or b"").hexdigest(),
                      "response_sha256": hashlib.sha256(wire).hexdigest(),
                      "status": response.status,
                      "code": value.get("error", {}).get("code") if isinstance(value, dict) else None,
                      "seconds": elapsed})
        return response.status, value, wire
    finally:
        conn.close()


def refusal(name, observed, status, code):
    check(name, observed[0] == status and isinstance(observed[1], dict)
          and observed[1].get("error", {}).get("code") == code,
          {"status": observed[0], "expected_status": status})


def fixture(capacity=4, zone="UTC"):
    return {"users": [{"id": "owner", "email": "owner@example.test",
                       "password": "correct horse", "display_name": "Quiet Diner"}],
            "restaurants": [{"id": "r", "name": "Quiet Dining", "timezone": zone,
                             "slot_minutes": 30, "reservation_duration_minutes": 90,
                             "cancellation_cutoff_minutes": 0,
                             "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "23:00"}
                                               for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                             "tables": [{"id": "t1", "label": "Window", "capacity": capacity},
                                        {"id": "t2", "label": "Garden", "capacity": capacity}]}],
            "reservations": []}


def login(index):
    response = call(index, "POST", "/auth/login", {"email": "owner@example.test", "password": "correct horse"})
    check("Password-hashed fixture account remains usable", response[0] == 200)
    return {"Authorization": "Bearer " + response[1]["token"]}


def booking(table="t1", local="2099-06-04T18:00", party=2):
    return {"restaurant_id": "r", "table_id": table, "starts_at_local": local, "party_size": party}


def empty204(name, response):
    check(name, response == (204, None, b""))


def availability(index, party=DIGITS):
    return call(index, "GET", "/availability?restaurant_id=r&date=2099-06-04&party_size=" + party)


def decimal():
    # A raw JSON integer and its encoded public response must stay exact. Each
    # base field is tested in isolation, with ordinary controls between phases.
    for field in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "capacity"):
        state = fixture()
        if field == "capacity":
            state["restaurants"][0]["tables"][0][field] = GIANT
        else:
            state["restaurants"][0][field] = GIANT
        empty204("4301-digit " + field + " reset accepted", call(0, "POST", "/_test/reset", state))
        detail = call(0, "GET", "/restaurants/r")
        observed = detail[1]["tables"][0][field] if field == "capacity" else detail[1][field]
        check("4301-digit " + field + " response is the exact JSON integer",
              type(observed) is int and observed == GIANT and DIGITS.encode() in detail[2])
        auth = login(0)
        offered = availability(0, "2")
        if field == "slot_minutes":
            check("Huge grid has one bounded opening candidate", offered[0] == 200 and
                  [s["starts_at_local"] for s in offered[1]["slots"]] == ["2099-06-04T18:00"])
            check("Opening booking fits huge grid", call(0, "POST", "/reservations", booking(),
                  {**auth, "Idempotency-Key": "huge-grid"})[0] == 201)
            refusal("Later ordinary time is off the huge grid", call(0, "POST", "/reservations",
                    booking("t2", "2099-06-04T18:30"), {**auth, "Idempotency-Key": "grid-failed"}), 422, "not_on_slot_grid")
        elif field == "reservation_duration_minutes":
            check("Huge duration has no fitting slots", offered[:2] == (200, {
                "restaurant_id": "r", "date": "2099-06-04", "timezone": "UTC", "slots": []}))
            refusal("Huge duration create has normal fit refusal", call(0, "POST", "/reservations", booking(),
                    {**auth, "Idempotency-Key": "duration-failed"}), 422, "outside_opening_hours")
        elif field == "cancellation_cutoff_minutes":
            first = call(0, "POST", "/reservations", booking(), {**auth, "Idempotency-Key": "huge-cutoff"})
            check("Huge cutoff permits ordinary create", first[0] == 201)
            before = digest(call(0, "GET", "/_test/export")[1])
            refusal("Huge cutoff cancel is ordinary refusal", call(0, "POST", "/reservations/" + first[1]["reference"] + "/cancel",
                    headers=auth), 409, "cutoff_passed")
            refusal("Huge cutoff amendment is ordinary refusal", call(0, "PATCH", "/reservations/" + first[1]["reference"],
                    {"party_size": 3}, auth), 409, "cutoff_passed")
            check("Huge cutoff failures leave full state unchanged", digest(call(0, "GET", "/_test/export")[1]) == before)
        else:
            fitting = availability(0)
            check("Exact giant query offers fitting singleton", fitting[0] == 200 and len(fitting[1]["slots"]) == 8 and
                  all(s["available_table_ids"] == ["t1"] for s in fitting[1]["slots"]))

    # Successful giant-body identity, original receipt and independent import.
    empty204("Both tables support giant parties", call(0, "POST", "/_test/reset", fixture(GIANT)))
    auth = login(0)
    body = {**booking(party=GIANT), "unknown": {"integer": GIANT + 1, "values": [None, True, 1.5]}}
    key = {**auth, "iDeMpOtEnCy-KeY": "exact-giant-create"}
    original = call(0, "POST", "/reservations", body, key)
    check("Giant party is encoded and stored as exact numeric JSON", original[0] == 201 and
          type(original[1]["party_size"]) is int and original[1]["party_size"] == GIANT and DIGITS.encode() in original[2])
    replay = call(0, "POST", "/reservations", headers=key,
                  raw=json.dumps(body, sort_keys=True, indent=1).encode())
    check("Parsed giant body equality ignores order and whitespace", replay[:2] == (200, original[1]))
    changed = {**body, "unknown": {"integer": GIANT + 2}, "party_size": False, "restaurant_id": "missing"}
    refusal("Changed giant ignored field conflicts before validation", call(0, "POST", "/reservations", changed, key),
            409, "idempotency_key_reuse")
    reference = original[1]["reference"]
    amended = call(0, "PATCH", "/reservations/" + reference, {"party_size": GIANT - 1}, auth)
    check("Giant amendment preserves identity and exact new value", amended[0] == 200 and
          amended[1]["party_size"] == GIANT - 1 and amended[1]["reservation_id"] == original[1]["reservation_id"])
    move_body = {"moves": [{"reference": reference, "table_id": "t2", "party_size": GIANT}], "ignored": GIANT}
    move_key = {**auth, "Idempotency-Key": "giant-move"}
    moved = call(0, "POST", "/reservation-moves", move_body, move_key)
    check("Giant batch produces exact successful receipt", moved[0] == 201 and moved[1]["reservations"][0]["party_size"] == GIANT)
    cancelled = call(0, "POST", "/reservations/" + reference + "/cancel", headers=auth)
    check("Giant reservation cancellation is current state", cancelled[0] == 200 and cancelled[1]["status"] == "cancelled")
    exported = call(0, "GET", "/_test/export")[1]
    check("Export remains exact JSON integers", DIGITS.encode() in json.dumps(exported).encode())
    empty204("Giant state transfers to another process", call(1, "POST", "/_test/import", exported))
    check("Independent giant-state replacement is exact", digest(call(1, "GET", "/_test/export")[1]) == digest(exported))
    for index in (0, 1):
        current = call(index, "GET", "/reservations/" + reference, headers=auth)
        check("Current giant cancelled record retained", current[:2] == (200, cancelled[1]))
        check("Original giant create receipt survives all changes/import",
              call(index, "POST", "/reservations", body, key)[:2] == (200, original[1]))
        check("Original giant move receipt survives cancellation/import",
              call(index, "POST", "/reservation-moves", move_body, move_key)[:2] == (200, moved[1]))

    # Separately distinguish giant valid query from type/value/lexical errors.
    empty204("Normal fixture control", call(0, "POST", "/_test/reset", fixture()))
    too_large = availability(0)
    check("Valid giant plain-digit query succeeds with empty options", too_large[0] == 200 and
          len(too_large[1]["slots"]) == 8 and all(s["available_table_ids"] == [] for s in too_large[1]["slots"]))
    for value in ("1e9", "4.0", "%2B4", "-4", "0", "%EF%BC%94"):
        refusal("Invalid query lexical/value rule " + value, availability(0, value), 422, "validation_failed")
    auth = login(0)
    failed_key = {**auth, "Idempotency-Key": "giant-failure-reuse"}
    refusal("Giant party above ordinary capacity", call(0, "POST", "/reservations", booking(party=GIANT), failed_key),
            422, "party_exceeds_capacity")
    check("Giant rejected key remains reusable", call(0, "POST", "/reservations", booking(), failed_key)[0] == 201)
    for number, value in enumerate((True, False, "2", 1.5, 0, -1)):
        refusal("Party type/value boundary " + str(number), call(0, "POST", "/reservations", booking("t2", party=value),
                {**auth, "Idempotency-Key": "invalid-party-" + str(number)}), 422, "validation_failed")
    refusal("Other wrong body field remains malformed", call(0, "POST", "/reservations", {**booking(), "table_id": 4},
            {**auth, "Idempotency-Key": "wrong-id-type"}), 400, "malformed_request")
    # Syntactically valid fraction is not a JSON parsing error, even when its
    # integer part exceeds binary-float range. It remains an invalid party value.
    fraction = ('{"restaurant_id":"r","table_id":"t2","starts_at_local":"2099-06-04T18:00","party_size":' + DIGITS + '.5}').encode()
    refusal("Giant fraction is endpoint value refusal", call(0, "POST", "/reservations", raw=fraction,
            headers={**auth, "Idempotency-Key": "giant-fraction"}), 422, "validation_failed")
    stable = digest(call(0, "GET", "/_test/export")[1])
    for number, raw in enumerate((b"{", b"null", b"[]", b"true", b"1", b'"x"', b'{"n":NaN}',
                                 b'{"n":Infinity}', b'{"n":-Infinity}', b'{"x":"\xff"}', b'{} trailing')):
        refusal("Strict raw parsing still precedes auth " + str(number), call(0, "POST", "/reservations", raw=raw),
                400, "malformed_request")
    for number, value in enumerate((True, "30", 1.5, -1)):
        bad = fixture()
        bad["restaurants"][0]["slot_minutes"] = value
        refusal("Reset field distinguishes wrong type/value " + str(number), call(0, "POST", "/_test/reset", bad),
                422 if value == -1 else 400, "validation_failed" if value == -1 else "malformed_request")
        check("Refused reset remains all-or-nothing", digest(call(0, "GET", "/_test/export")[1]) == stable)
    refusal("Invalid import remains all-or-nothing", call(0, "POST", "/_test/import",
            {"track": "wrong", "format_version": 1, "state": {}}), 422, "validation_failed")
    check("Invalid import leaves full snapshot unchanged", digest(call(0, "GET", "/_test/export")[1]) == stable)


def legacy():
    # This third process is a genuine pre-serializer service, not mocked state.
    # Bodies use its old supported singleton representation and ignored fields.
    empty204("Genuine older source reset", call(2, "POST", "/_test/reset", fixture()))
    auths = [login(2), login(2)]
    a = {**booking(), "table_ids": ["ignored-in-stage-1"], "legacy_number": 9007199254740993}
    b = booking("t2")
    keys = [{**auths[0], "Idempotency-Key": "legacy-a"}, {**auths[0], "Idempotency-Key": "legacy-b"}]
    originals = [call(2, "POST", "/reservations", body, key) for body, key in zip((a, b), keys)]
    check("Genuine source issued both original references", all(r[0] == 201 for r in originals))
    refs = [r[1]["reference"] for r in originals]
    moves = {"moves": [{"reference": refs[0], "table_id": "t2"}, {"reference": refs[1], "table_id": "t1"}]}
    move_key = {**auths[0], "Idempotency-Key": "legacy-swap"}
    swap = call(2, "POST", "/reservation-moves", moves, move_key)
    check("Genuine source issued atomic batch receipt", swap[0] == 201)
    edited = call(2, "PATCH", "/reservations/" + refs[0], {"starts_at_local": "2099-06-04T19:30"}, auths[0])
    cancelled = call(2, "POST", "/reservations/" + refs[1] + "/cancel", headers=auths[0])
    check("Source mutations differ from its saved receipts", edited[0] == 200 and cancelled[0] == 200 and
          edited[1] != originals[0][1] and cancelled[1] != originals[1][1])
    snapshot = call(2, "GET", "/_test/export")[1]
    fingerprint = digest(snapshot)
    call(2, "POST", "/reservations", booking(local="2099-06-05T18:00"),
         {**auths[0], "Idempotency-Key": "after-export"})
    check("Older source write does not mutate the captured snapshot", digest(snapshot) == fingerprint and
          digest(call(2, "GET", "/_test/export")[1]) != fingerprint)
    for index in (0, 1):
        # Destination-only session must disappear under replacement.
        empty204("Destination baseline reset", call(index, "POST", "/_test/reset", fixture()))
        obsolete = login(index)
        empty204("Original older export replaces independent candidate " + str(index),
                 call(index, "POST", "/_test/import", snapshot))
        check("Complete original state preserved in candidate " + str(index),
              digest(call(index, "GET", "/_test/export")[1]) == fingerprint)
        refusal("Replacement removes previous destination token", call(index, "GET", "/reservations", headers=obsolete),
                401, "unauthenticated")
        for auth in auths:
            listed = call(index, "GET", "/reservations", headers=auth)
            check("Both genuine source sessions survive", listed[0] == 200 and len(listed[1]["reservations"]) == 2)
        for ref, current in zip(refs, (edited, cancelled)):
            check("Original identity/status/timestamps retained",
                  call(index, "GET", "/reservations/" + ref, headers=auths[0])[:2] == (200, current[1]))
        for body, key, original in zip((a, b), keys, originals):
            check("Original create receipt is exact after import/mutation",
                  call(index, "POST", "/reservations", body, key)[:2] == (200, original[1]))
        check("Original atomic swap receipt is exact after import/mutation",
              call(index, "POST", "/reservation-moves", moves, move_key)[:2] == (200, swap[1]))
        before = digest(call(index, "GET", "/_test/export")[1])
        empty204("Repeated import is replacement without duplicates", call(index, "POST", "/_test/import", snapshot))
        check("Repeated import preserves all original state", digest(call(index, "GET", "/_test/export")[1]) == before)
        login(index)
        empty204("Reset clears imported state", call(index, "POST", "/_test/reset",
                 {"users": [], "restaurants": [], "reservations": []}))
        refusal("Reset removes imported session", call(index, "GET", "/reservations", headers=auths[0]), 401, "unauthenticated")
        refusal("Reset removes imported password login", call(index, "POST", "/auth/login",
                {"email": "owner@example.test", "password": "correct horse"}), 401, "unauthenticated")


for title, function in (("Decimal transport and state", decimal), ("Genuine older-state transfer", legacy)):
    try:
        function()
    except Exception as exc:
        check(title + " completed without an infrastructure/flow exception", False, type(exc).__name__)
summary = {"elapsed_seconds": time.monotonic() - START, "operations": len(TRACE), "assertions": len(RESULTS),
           "passed": sum(r["passed"] for r in RESULTS), "failed": sum(not r["passed"] for r in RESULTS),
           "giant_digits": len(DIGITS), "giant_sha256": hashlib.sha256(DIGITS.encode()).hexdigest(),
           "results": RESULTS, "trace": TRACE}
print(json.dumps(summary, indent=2))
sys.exit(1 if summary["failed"] else 0)
