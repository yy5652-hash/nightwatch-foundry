"""Specification-derived black-box integration checks, using only stdlib.

Execute inside a container with the service URL as argv[1]. No snapshot, token,
password hash or response body is emitted to the durable output.
"""

import concurrent.futures
from datetime import date, datetime
import hashlib
import http.client
import json
import re
import socket
import sys
import threading
import time
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


URL = urlsplit(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9090")
RESULTS = []
START = time.monotonic()


def check(name, condition, detail=None):
    RESULTS.append({"name": name, "passed": bool(condition), "detail": detail})


def call(method, path, body=None, headers=None, raw=None):
    connection = http.client.HTTPConnection(URL.hostname, URL.port, timeout=5)
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    request_headers = {"Content-Type": "application/json; charset=utf-8", **(headers or {})}
    begin = time.monotonic()
    try:
        connection.request(method, path, data, request_headers)
        response = connection.getresponse()
        wire = response.read()
        response_headers = dict((key.lower(), value) for key, value in response.getheaders())
        check("JSON response media type: " + method + " " + path.split("?")[0],
              response_headers.get("content-type") == "application/json; charset=utf-8")
        check("Response length matches bytes", response_headers.get("content-length") == str(len(wire)))
        check("Request completed within 5 seconds", time.monotonic() - begin < 5)
        value = json.loads(wire) if wire else None
        return response.status, value, wire
    finally:
        connection.close()


def error(name, response, status, code):
    check(name, response[0] == status and response[1].get("error", {}).get("code") == code,
          {"observed_status": response[0], "expected_status": status})


def absolute_seconds(local, offset_seconds):
    # Ordinal arithmetic deliberately avoids conversion to a UTC datetime, which
    # cannot represent an instant just beyond the supported local calendar range.
    return local.date().toordinal() * 86400 + local.hour * 3600 + local.minute * 60 + local.second - offset_seconds


def interpreted_timestamp(name, wire, instant, iana_offset_seconds):
    match = re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}", wire)
    check(name + ": RFC3339 minute-offset syntax", match is not None)
    if match is None:
        return
    parsed = datetime.fromisoformat(wire)
    offset = int(parsed.utcoffset().total_seconds())
    check(name + ": exact represented instant", absolute_seconds(parsed, offset) == instant and parsed.microsecond == 0)
    # Independently enumerate every RFC3339 minute offset whose adjusted clock is
    # representable, then apply the coordinator's nearest/lower-tie rule.
    minimum = date.min.toordinal() * 86400
    maximum_exclusive = (date.max.toordinal() + 1) * 86400
    options = [minute for minute in range(-1439, 1440)
               if minimum <= instant + minute * 60 < maximum_exclusive]
    expected = min(options, key=lambda minute: (abs(minute * 60 - iana_offset_seconds), minute))
    check(name + ": nearest representable offset with lower tie", offset == expected * 60)


def run():
    deadline = time.monotonic() + 55
    while True:
        try:
            health = call("GET", "/health")
            if health[:2] == (200, {"status": "ok"}):
                break
        except (OSError, http.client.HTTPException):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("No healthy response within 55 seconds")
        time.sleep(0.05)
    check("Healthy response within runtime budget", time.monotonic() - START < 60)
    listener = f"00000000:{URL.port:04X}"
    with open("/proc/net/tcp") as proc:
        check("Nondefault PORT bound on 0.0.0.0", listener in proc.read())

    hours = [{"weekday": day, "opens": "00:00", "closes": "23:59"}
             for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]]
    fixture = {
        "users": [{"id": "diner", "email": "diner@example.test", "password": "correct horse", "display_name": "Ada"}],
        "restaurants": [
            {"id": "berlin", "name": "Quiet Table", "timezone": "Europe/Berlin",
             "slot_minutes": 30, "reservation_duration_minutes": 90,
             "cancellation_cutoff_minutes": 0, "opening_hours": hours,
             "tables": [{"id": f"t{i}", "label": str(i), "capacity": 4} for i in range(1, 5)]},
            {"id": "new-york", "name": "Morning Table", "timezone": "America/New_York",
             "slot_minutes": 30, "reservation_duration_minutes": 90,
             "cancellation_cutoff_minutes": 0, "opening_hours": hours,
             "tables": [{"id": "n1", "label": "Window", "capacity": 4}]},
        ], "reservations": [],
    }
    reset = call("POST", "/_test/reset", fixture)
    check("Reset returns truly empty 204", reset == (204, None, b""))
    for wire in [b"{", b"null", b"[]", b'"text"', b"4", b"true", b'{"x":NaN}',
                 b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1,}', b'{"x":"\xff"}', b'{} trailing']:
        error("Raw JSON rejected before auth/idempotency: " + wire.hex(),
              call("POST", "/reservations", raw=wire), 400, "malformed_request")
    error("Malformed JSON rejected on import", call("POST", "/_test/import", raw=b"{"), 400, "malformed_request")
    error("Object without token reaches authentication", call("POST", "/reservations", {}), 401, "unauthenticated")
    restaurants = call("GET", "/restaurants?unused=anything")
    check("Public browsing and ignored query fields", restaurants[0] == 200 and len(restaurants[1]["restaurants"]) == 2)
    signup = call("POST", "/auth/signup", {"email": "unicode@example.test", "password": "correct horse",
                                           "display_name": "Zoë 餐桌", "unknown": {"x": [True, None, 1.5]}})
    check("Unicode JSON and unknown nested fields", signup[0] == 201 and signup[1]["display_name"] == "Zoë 餐桌")
    login = call("POST", "/auth/login", {"email": "diner@example.test", "password": "correct horse"})
    check("Fixture account can log in", login[0] == 200)
    token = login[1]["token"]
    auth = {"aUtHoRiZaTiOn": "Bearer " + token}
    body = {"restaurant_id": "berlin", "table_id": "t1", "starts_at_local": "2099-01-01T19:00",
            "party_size": 2, "ignored": {"a": 1, "b": [None, False]}}
    create_headers = {**auth, "iDeMpOtEnCy-KeY": "mixed-case"}
    first = call("POST", "/reservations", body, create_headers)
    check("Case-insensitive headers create successfully", first[0] == 201)
    replay = call("POST", "/reservations", headers=create_headers, raw=json.dumps(body, sort_keys=True, indent=2).encode())
    check("Key order/whitespace replay preserves original JSON", replay[:2] == (200, first[1]))
    error("Different JSON conflicts before field validation",
          call("POST", "/reservations", {"party_size": False}, create_headers), 409, "idempotency_key_reuse")
    error("Valid JSON boolean party is endpoint validation", call("POST", "/reservations", {**body, "party_size": True},
                                                                {**auth, "Idempotency-Key": "boolean-party"}), 422, "validation_failed")
    error("Missing key after valid parsing/auth", call("POST", "/reservations", body, auth), 400, "missing_idempotency_key")
    error("Empty key", call("POST", "/reservations", body, {**auth, "Idempotency-Key": ""}), 400, "missing_idempotency_key")
    error("Overlength key", call("POST", "/reservations", body, {**auth, "Idempotency-Key": "x" * 256}), 422, "validation_failed")
    for party in ["1e9", "4.0", "%2B4"]:
        error("Query integer grammar " + party,
              call("GET", "/availability?restaurant_id=berlin&date=2099-01-01&party_size=" + party), 422, "validation_failed")
    failed_headers = {**auth, "Idempotency-Key": "failed-then-recovered"}
    error("Failed key does not become receipt", call("POST", "/reservations", {}, failed_headers), 422, "validation_failed")
    recovery = call("POST", "/reservations", {**body, "table_id": "t2"}, failed_headers)
    check("Failed key reusable with corrected JSON", recovery[0] == 201)

    # A start barrier makes all 50 clients compete on the same unused request.
    concurrent_body = {**body, "table_id": "t3"}
    concurrent_headers = {**auth, "Idempotency-Key": "fifty-identical"}
    barrier = threading.Barrier(50)

    def same_request(_):
        barrier.wait(timeout=5)
        return call("POST", "/reservations", concurrent_body, concurrent_headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
        responses = list(pool.map(same_request, range(50)))
    check("50 identical concurrent writes: exactly one first use", sum(r[0] == 201 for r in responses) == 1)
    check("49 replay responses and no 5xx", sum(r[0] == 200 for r in responses) == 49)
    check("50 concurrent receipts agree", all(r[1] == responses[0][1] for r in responses))
    barrier = threading.Barrier(50)

    def competing_request(index):
        barrier.wait(timeout=5)
        return call("POST", "/reservations", {**body, "table_id": "t4"},
                    {**auth, "Idempotency-Key": "competing-" + str(index)})

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
        competition = list(pool.map(competing_request, range(50)))
    check("50 competing writes: exactly one booking", sum(r[0] == 201 for r in competition) == 1)
    check("Other 49 competitors refuse occupancy", sum(r[0] == 409 and r[1]["error"]["code"] == "table_unavailable" for r in competition) == 49)

    # Observe only one response byte then drop the connection after commit.
    lost_body = {**body, "starts_at_local": "2099-01-01T21:00"}
    wire = json.dumps(lost_body).encode()
    raw_request = ("POST /reservations HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
                   "Authorization: Bearer " + token + "\r\nIdempotency-Key: commit-then-drop\r\n"
                   "Content-Length: " + str(len(wire)) + "\r\nConnection: close\r\n\r\n").encode() + wire
    with socket.create_connection((URL.hostname, URL.port), timeout=5) as connection:
        connection.sendall(raw_request)
        check("Lost-response probe sees only a partial response", connection.recv(1) == b"H")
    lost_retry = call("POST", "/reservations", lost_body, {**auth, "Idempotency-Key": "commit-then-drop"})
    check("Commit-then-drop retry recovers original receipt", lost_retry[0] == 200)
    listed = call("GET", "/reservations", headers=auth)
    check("No duplicates after bursts and lost response", len(listed[1]["reservations"]) == 5)

    reference = first[1]["reference"]
    cancel = call("POST", "/reservations/" + reference + "/cancel", headers=auth)
    check("Bodyless cancel reaches Engine", cancel[0] == 200 and cancel[1]["status"] == "cancelled")
    old_replay = call("POST", "/reservations", body, create_headers)
    check("Replay after cancellation returns original confirmed receipt", old_replay[:2] == (200, first[1]))

    export = call("GET", "/_test/export")
    digest = hashlib.sha256(json.dumps(export[1], sort_keys=True).encode()).hexdigest()
    error("Invalid import refused", call("POST", "/_test/import", {"track": "wrong", "format_version": 1, "state": {}}), 422, "validation_failed")
    after = call("GET", "/_test/export")
    check("Rejected import leaves snapshot unchanged", hashlib.sha256(json.dumps(after[1], sort_keys=True).encode()).hexdigest() == digest)
    call("POST", "/_test/reset", {"users": [], "restaurants": [], "reservations": []})
    error("Reset clears old token", call("GET", "/reservations", headers=auth), 401, "unauthenticated")
    imported = call("POST", "/_test/import", export[1])
    check("Import returns truly empty 204", imported == (204, None, b""))
    restored = call("GET", "/reservations/" + reference, headers=auth)
    check("Imported bearer token and cancelled record retained", restored[:2] == (200, cancel[1]))
    restored_replay = call("POST", "/reservations", body, create_headers)
    check("Imported original idempotent response retained", restored_replay[:2] == (200, first[1]))

    for restaurant, local, expected_start, expected_end in [
        ("new-york", "2026-11-01T01:30", "2026-11-01T01:30:00-04:00", "2026-11-01T02:00:00-05:00"),
        ("berlin", "2026-10-25T02:30", "2026-10-25T02:30:00+02:00", "2026-10-25T03:00:00+01:00"),
    ]:
        response = call("POST", "/reservations", {"restaurant_id": restaurant, "table_id": "n1" if restaurant == "new-york" else "t1",
                                                   "starts_at_local": local, "party_size": 2},
                        {**auth, "Idempotency-Key": "dst-" + restaurant})
        check("IANA repeated hour and absolute duration: " + restaurant,
              response[0] == 201 and response[1]["starts_at"] == expected_start and response[1]["ends_at"] == expected_end)
    error("IANA skipped hour rejected", call("POST", "/reservations", {**body, "starts_at_local": "2026-03-29T02:30"},
                                             {**auth, "Idempotency-Key": "dst-skipped"}), 422, "invalid_local_time")

    historic_receipts = []
    for index, (restaurant, local_text) in enumerate([
        ("berlin", "0001-01-01T00:00"),
        ("berlin", "0001-01-01T18:00"),
        ("new-york", "9999-12-31T21:30"),
    ]):
        local = datetime.fromisoformat(local_text)
        zone = ZoneInfo("Europe/Berlin" if restaurant == "berlin" else "America/New_York")
        offset = int(local.replace(tzinfo=zone, fold=0).utcoffset().total_seconds())
        instant = absolute_seconds(local, offset)
        available = call("GET", "/availability?restaurant_id=" + restaurant + "&date=" + local_text[:10] + "&party_size=2")
        slot = next((s for s in available[1].get("slots", []) if s["starts_at_local"] == local_text), None)
        check("Calendar/historical slot remains available: " + local_text, available[0] == 200 and slot is not None)
        if slot is not None:
            interpreted_timestamp("Availability " + local_text, slot["starts_at"], instant, offset)
        calendar_body = {"restaurant_id": restaurant, "table_id": "t1" if restaurant == "berlin" else "n1",
                         "starts_at_local": local_text, "party_size": 2}
        calendar_headers = {**auth, "Idempotency-Key": "calendar-interpretation-" + str(index)}
        reservation = call("POST", "/reservations", calendar_body, calendar_headers)
        check("Calendar/historical create succeeds: " + local_text, reservation[0] == 201)
        if reservation[0] == 201:
            check("Original wall-clock field retained: " + local_text, reservation[1]["starts_at_local"] == local_text)
            interpreted_timestamp("Create start " + local_text, reservation[1]["starts_at"], instant, offset)
            interpreted_timestamp("Create end " + local_text, reservation[1]["ends_at"], instant + 90 * 60, offset)
            historic_receipts.append((calendar_body, calendar_headers, reservation[1]))
    historic_export = call("GET", "/_test/export")
    call("POST", "/_test/reset", {"users": [], "restaurants": [], "reservations": []})
    historic_import = call("POST", "/_test/import", historic_export[1])
    check("Historical/calendar snapshot import remains empty 204", historic_import == (204, None, b""))
    for calendar_body, calendar_headers, original in historic_receipts:
        restored = call("GET", "/reservations/" + original["reference"], headers=auth)
        check("Historical/calendar reservation unchanged after import", restored[:2] == (200, original))
        replay = call("POST", "/reservations", calendar_body, calendar_headers)
        check("Historical/calendar original receipt replay unchanged", replay[:2] == (200, original))


try:
    run()
except Exception as exc:
    check("Probe completed without an infrastructure/flow exception", False, type(exc).__name__)
summary = {"elapsed_seconds": round(time.monotonic() - START, 4), "checks": len(RESULTS),
           "passed": sum(r["passed"] for r in RESULTS), "failed": sum(not r["passed"] for r in RESULTS),
           "results": RESULTS}
print(json.dumps(summary, indent=2))
sys.exit(1 if summary["failed"] else 0)
