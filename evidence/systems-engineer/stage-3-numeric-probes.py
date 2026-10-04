"""Own black-box exact-number/state/snapshot diagnostics; no service imports."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
for option in ("base", "peer", "legacy", "old", "out"):
    parser.add_argument("--" + option, required=True)
args = parser.parse_args()
sys.set_int_max_str_digits(0)  # Client only; cannot configure source interpreters.
out = Path(args.out)
out.mkdir(parents=True, exist_ok=False)
events, assertions, scenarios = [], [], []
lock = threading.Lock()
started = time.monotonic()


@dataclass(frozen=True)
class RawNumber:
    token: str


class NumberLexeme(str):
    """Read-only decimal/exponent provenance; never a production codec oracle."""


def encode(value):
    literals = []

    def numeric(item):
        if type(item) is RawNumber:
            marker = "__OWN_RAW_NUMBER_%d__" % len(literals)
            literals.append((json.dumps(marker), item.token))
            return marker
        raise TypeError(type(item).__name__)

    wire = json.dumps(value, default=numeric, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    for marker, token in literals:
        wire = wire.replace(marker, token)
    return wire.encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def same_archived_tree(left, right):
    """Independent tree check: complete mapping, ordered arrays, numeric tokens.

    Opaque export byte order is not specified. Numeric lexemes are required to
    remain identical here, a stronger check than mathematical alias equality.
    This helper never calls or imports the service's codec/equality functions.
    """
    pending = [(left, right)]
    while pending:
        a, b = pending.pop()
        if type(a) is not type(b):
            return False
        if type(a) is dict:
            if a.keys() != b.keys():
                return False
            pending.extend((a[k], b[k]) for k in a)
        elif type(a) is list:
            if len(a) != len(b):
                return False
            pending.extend(zip(a, b))
        elif a != b:
            return False
    return True


def check(label, condition, detail=None):
    with lock:
        assertions.append({"label": label, "passed": bool(condition), "detail": detail})


def http(base, method, path, body=None, *, raw=None, token=None, key=None, expected=None, code=None, label=None):
    wire = raw if raw is not None else (None if body is None else encode(body))
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if key is not None:
        headers["Idempotency-Key"] = key
    begin = time.monotonic()
    try:
        response = urlopen(Request(base + path, data=wire, headers=headers, method=method), timeout=10)
    except HTTPError as error:
        response = error
    with response:
        raw_response = response.read()
        status = response.status
        media, length = response.headers.get("Content-Type", ""), response.headers.get("Content-Length")
    elapsed = time.monotonic() - begin
    parsed = json.loads(raw_response, parse_float=NumberLexeme) if raw_response else None
    name = label or method + " " + path
    observed_code = parsed.get("error", {}).get("code") if type(parsed) is dict else None
    with lock:
        events.append({"label": name, "method": method, "path": path,
                       "request_bytes": 0 if wire is None else len(wire),
                       "request_sha256": None if wire is None else digest(wire),
                       "response_bytes": len(raw_response), "response_sha256": digest(raw_response),
                       "status": status, "code": observed_code, "seconds": elapsed,
                       "credential_fingerprint": None if token is None else digest(token.encode())})
    check(name + " no 5xx", status < 500)
    check(name + " JSON media/framing", "application/json" in media and "charset=utf-8" in media
          and length == str(len(raw_response)))
    check(name + " resource timeout", elapsed <= (10 if path.startswith("/_test/") else 5))
    if status == 204:
        check(name + " empty 204", raw_response == b"")
    if expected is not None:
        check(name + " status", status == expected, {"expected": expected, "observed": status})
    if code is not None:
        check(name + " code", observed_code == code, {"expected": code, "observed": observed_code})
    return status, parsed, raw_response


def fixture(owner="current", capacity=4):
    return {"users": [{"id": owner, "email": owner + "@example.test", "password": "own fixture password",
                       "display_name": owner}], "restaurants": [{"id": "r", "name": "Own numeric dining room",
        "timezone": "UTC", "slot_minutes": 30, "reservation_duration_minutes": 90,
        "cancellation_cutoff_minutes": 0,
        "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "23:00"}
                          for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
        "tables": [{"id": name, "label": name.upper(), "capacity": capacity} for name in ("a", "b", "c")]}],
        "reservations": []}


def reset(base, data=None, owner="current"):
    http(base, "POST", "/_test/reset", data or fixture(owner), expected=204)
    return login(base, owner)


def login(base, owner):
    return http(base, "POST", "/auth/login", {"email": owner + "@example.test", "password": "own fixture password"},
                expected=200)[1]["token"]


def booking(table="a", local="2037-06-01T18:00", party=2, **ignored):
    return {"restaurant_id": "r", "table_id": table, "starts_at_local": local, "party_size": party, **ignored}


def create(base, token, body=None, key="create", expected=201, code=None):
    return http(base, "POST", "/reservations", booking() if body is None else body,
                token=token, key=key, expected=expected, code=code)


def exported(base):
    return http(base, "GET", "/_test/export", expected=200)


def numeric(value, expected):
    return type(value) in (int, NumberLexeme) and Decimal(str(value)) == Decimal(expected)


def scenario(name, operation):
    before = len(assertions)
    begin = time.monotonic()
    try:
        operation()
    except Exception as error:
        check(name + " flow completed", False, {"exception": type(error).__name__, "message": str(error)})
    scenarios.append({"name": name, "assertions": len(assertions) - before,
                      "failed": sum(not row["passed"] for row in assertions[before:]),
                      "seconds": time.monotonic() - begin})


def aliases_and_exact_bodies():
    token = reset(args.base)
    body = booking(party=RawNumber("2.0"), unused=RawNumber("0.100000000000000005"), zero=RawNumber("-0.0"))
    original = create(args.base, token, body, "aliases")
    check("body integral decimal accepted as numeric", numeric(original[1]["party_size"], "2"))
    alias = booking(party=RawNumber("2e0"), unused=RawNumber("0.100000000000000005"), zero=RawNumber("0e4300"))
    replay = create(args.base, token, alias, "aliases", 200)
    check("exact aliases replay original bytes", replay[2] == original[2])
    for changed in (RawNumber("0.1"), "0.100000000000000005", True, None):
        create(args.base, token, {**alias, "unused": changed, "party_size": False}, "aliases", 409, "idempotency_key_reuse")
    ref = original[1]["reference"]
    http(args.base, "PATCH", "/reservations/" + ref, {"party_size": RawNumber("3e0")}, token=token, expected=200)
    http(args.base, "POST", "/reservations/" + ref + "/cancel", token=token, expected=200)
    check("exact original receipt stable after current changes", create(args.base, token, alias, "aliases", 200)[2] == original[2])
    token = reset(args.base)
    arbitrary = booking(unused=RawNumber("1e4300"), fraction=RawNumber("1" + "0" * 4299 + "1.5"))
    saved = create(args.base, token, arbitrary, "finite")
    equal = {**arbitrary, "unused": RawNumber("10e4299")}
    check("finite overflow alias original replay", create(args.base, token, equal, "finite", 200)[2] == saved[2])
    for query in ("1e0", "2.0", "%2B2", "-2", "true"):
        http(args.base, "GET", "/availability?restaurant_id=r&date=2037-06-01&party_size=" + query,
             expected=422, code="validation_failed")
    tiny = booking(table="b", unused=RawNumber("1e-4300"))
    tiny_original = create(args.base, token, tiny, "tiny")
    check("new underflow alias retains exact receipt", create(args.base, token,
          {**tiny, "unused": RawNumber("10e-4301")}, "tiny", 200)[2] == tiny_original[2])
    create(args.base, token, {**tiny, "unused": 0}, "tiny", 409, "idempotency_key_reuse")
    snapshot = exported(args.base)[2]
    http(args.peer, "POST", "/_test/import", raw=snapshot, expected=204)
    check("new underflow identity survives independent import", create(args.peer, token, tiny, "tiny", 200)[2] == tiny_original[2])
    create(args.peer, token, {**tiny, "unused": 0}, "tiny", 409, "idempotency_key_reuse")


def fixture_value_statuses():
    fields = ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "capacity")
    for field in fields:
        for spelling in ("1.0", "1e0"):
            data = fixture()
            target = data["restaurants"][0]["tables"][0] if field == "capacity" else data["restaurants"][0]
            target[field] = RawNumber(spelling)
            http(args.base, "POST", "/_test/reset", data, expected=204)
            detail = http(args.base, "GET", "/restaurants/r", expected=200)[1]
            observed = detail["tables"][0][field] if field == "capacity" else detail[field]
            check(field + " integral value " + spelling, numeric(observed, "1"))
        for wrong in ("1", True, None, {}, []):
            data = fixture()
            target = data["restaurants"][0]["tables"][0] if field == "capacity" else data["restaurants"][0]
            target[field] = wrong
            http(args.base, "POST", "/_test/reset", data, expected=400, code="malformed_request")
        for wrong in (RawNumber("1.5"), RawNumber("1e-4300"), RawNumber("1" + "0" * 4299 + "1.5")):
            before = exported(args.base)[2]
            data = fixture()
            target = data["restaurants"][0]["tables"][0] if field == "capacity" else data["restaurants"][0]
            target[field] = wrong
            http(args.base, "POST", "/_test/reset", data, expected=422, code="validation_failed")
            check(field + " fractional reset atomic", exported(args.base)[2] == before)


def huge_operational_counts():
    exponent = "9" * 80
    huge_token = "1e" + exponent
    for field in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "capacity"):
        data = fixture()
        target = data["restaurants"][0]["tables"][0] if field == "capacity" else data["restaurants"][0]
        target[field] = RawNumber(huge_token)
        token = reset(args.base, data)
        detail = http(args.base, "GET", "/restaurants/r", expected=200)[1]
        observed = detail["tables"][0][field] if field == "capacity" else detail[field]
        check(field + " compact huge metadata numeric wire", type(observed) is NumberLexeme and observed == huge_token)
        slots = http(args.base, "GET", "/availability?restaurant_id=r&date=2037-06-01&party_size=2", expected=200)[1]["slots"]
        if field == "slot_minutes":
            check("huge grid only bounded opening start", len(slots) == 1 and slots[0]["starts_at_local"].endswith("18:00"))
            create(args.base, token, booking(local="2037-06-01T18:30"), "grid", 422, "not_on_slot_grid")
        elif field == "reservation_duration_minutes":
            check("huge duration has no fitting slots", slots == [])
            create(args.base, token, key="duration", expected=422, code="outside_opening_hours")
        else:
            record = create(args.base, token, booking(party=RawNumber(huge_token) if field == "capacity" else 2))[1]
            if field == "cancellation_cutoff_minutes":
                http(args.base, "PATCH", "/reservations/" + record["reference"], {"party_size": 3}, token=token,
                     expected=409, code="cutoff_passed")
                http(args.base, "POST", "/reservations/" + record["reference"] + "/cancel", token=token,
                     expected=409, code="cutoff_passed")
            else:
                check("compact huge party numeric response", type(record["party_size"]) is NumberLexeme and record["party_size"] == huge_token)
                move = {"moves": [{"reference": record["reference"], "party_size": RawNumber("10e" + str(int(exponent) - 1))}]}
                moved = http(args.base, "POST", "/reservation-moves", move, token=token, key="compact-move", expected=201)
                alias = {"moves": [{"reference": record["reference"], "party_size": RawNumber(huge_token)}]}
                check("compact move alias original response", http(args.base, "POST", "/reservation-moves", alias,
                      token=token, key="compact-move", expected=200)[2] == moved[2])
                captured = exported(args.base)[2]
                http(args.peer, "POST", "/_test/import", raw=captured, expected=204)
                check("compact original create retry after replacement", create(args.peer, token,
                      booking(party=RawNumber(huge_token)), expected=200)[1]["reference"] == record["reference"])


def precedence_and_failed_keys():
    token = reset(args.base)
    finite_fraction = RawNumber("1" + "0" * 4299 + "1.5")
    for invalid in (finite_fraction, RawNumber("1e-4300"), RawNumber("1.5"), True, "2", 0, -1):
        create(args.base, token, booking(party=invalid), "reusable", 422, "validation_failed")
    create(args.base, token, booking(party=finite_fraction), None, 400, "missing_idempotency_key")
    create(args.base, None, booking(party=finite_fraction), "no-auth", 401, "unauthenticated")
    first = create(args.base, token, key="reusable")[1]
    create(args.base, token, booking(party=finite_fraction), "reusable", 409, "idempotency_key_reuse")
    moves = {"moves": [{"reference": first["reference"], "party_size": finite_fraction}]}
    http(args.base, "POST", "/reservation-moves", moves, token=token, expected=400, code="missing_idempotency_key")
    http(args.base, "POST", "/reservation-moves", moves, token=token, key="failed-move", expected=422, code="validation_failed")
    good = {"moves": [{"reference": first["reference"], "table_id": "b"}]}
    receipt = http(args.base, "POST", "/reservation-moves", good, token=token, key="failed-move", expected=201)
    http(args.base, "POST", "/reservation-moves", moves, token=token, key="failed-move", expected=409, code="idempotency_key_reuse")
    http(args.base, "POST", "/reservations/" + first["reference"] + "/cancel", token=token, expected=200)
    http(args.base, "POST", "/reservation-moves", moves, token=token, key="cancelled", expected=409, code="reservation_cancelled")
    check("batch original receipt after cancellation", http(args.base, "POST", "/reservation-moves", good,
          token=token, key="failed-move", expected=200)[2] == receipt[2])
    past = create(args.base, token, booking(table="c", local="2000-06-01T18:00"), "past")[1]
    past_move = {"moves": [{"reference": past["reference"], "party_size": finite_fraction}]}
    http(args.base, "POST", "/reservation-moves", past_move, token=token, key="past-move", expected=409, code="cutoff_passed")
    for constant in ("NaN", "Infinity", "-Infinity"):
        http(args.base, "POST", "/reservations", raw=encode(booking(party=RawNumber(constant))),
             token=token, key="literal", expected=400, code="malformed_request")
        http(args.base, "POST", "/reservations", raw=encode(booking(party=RawNumber(constant))),
             key="literal-unauth", expected=400, code="malformed_request")
        http(args.base, "POST", "/reservation-moves", raw=b'{"unused":' + constant.encode() + b'}',
             token=token, key="literal-move", expected=400, code="malformed_request")
    for malformed in (b'{"x":"\xff"}', b'{"x":1,}', b'[]', b'1', b'null'):
        http(args.base, "POST", "/reservations", raw=malformed, token=token, key="malformed",
             expected=400, code="malformed_request")
    create(args.base, token, booking(table="c"), "literal", 201)


def nested_receipts_and_replacement():
    token = reset(args.base)
    retained = []
    for shape in ("object", "array"):
        leaf = b'{"v":0.100000000000000005,"huge":1e4300,"flag":true}'
        opening, closing = (b'{"unused":', b'}') if shape == "object" else (b'[', b']')
        nested = opening * 1100 + leaf + closing * 1100
        base_body = encode(booking(table="a" if shape == "object" else "b"))
        wire = base_body[:-1] + b',"ignored":' + nested + b'}'
        check(shape + " depth1100 valid composition", json.loads(leaf, parse_float=Decimal)["huge"].is_finite(),
              {"wrapping_depth": 1100, "request_bytes": len(wire), "request_sha256": digest(wire)})
        result = http(args.base, "POST", "/reservations", raw=wire, token=token, key="deep-" + shape, expected=201)
        check(shape + " deep original retry", http(args.base, "POST", "/reservations", raw=wire,
              token=token, key="deep-" + shape, expected=200)[2] == result[2])
        changed = wire.replace(b'0.100000000000000005', b'0.1')
        http(args.base, "POST", "/reservations", raw=changed, token=token, key="deep-" + shape,
             expected=409, code="idempotency_key_reuse")
        ref = result[1]["reference"]
        move_wire = b'{"moves":[{"reference":' + json.dumps(ref).encode() + b'}],"ignored":' + nested + b'}'
        moved = http(args.base, "POST", "/reservation-moves", raw=move_wire, token=token, key="deep-move-" + shape, expected=201)
        retained.append((wire, "deep-" + shape, result[2], move_wire, "deep-move-" + shape, moved[2]))
    snapshot_result = exported(args.base)
    snapshot = snapshot_result[2]
    http(args.peer, "POST", "/_test/import", raw=snapshot, expected=204)
    for base in (args.base, args.peer):
        for wire, key, original, move, move_key, moved in retained:
            check("deep original receipt independent destination", http(base, "POST", "/reservations", raw=wire,
                  token=token, key=key, expected=200)[2] == original)
            check("deep original batch independent destination", http(base, "POST", "/reservation-moves", raw=move,
                  token=token, key=move_key, expected=200)[2] == moved)
    adopted = exported(args.peer)
    check("deep state unchanged JSON replacement", same_archived_tree(adopted[1], snapshot_result[1]),
          {"source_sha256": digest(snapshot), "destination_sha256": digest(adopted[2]),
           "byte_order_identical": adopted[2] == snapshot})
    invalid = snapshot.replace(b'"numeric_profile":"exact-v1"', b'"numeric_profile":"invalid"', 1)
    http(args.peer, "POST", "/_test/import", raw=invalid, expected=422, code="validation_failed")
    check("invalid profile atomic with deep bodies", exported(args.peer)[2] == adopted[2])


def genuine_legacy_mixed_profiles():
    for old_base, owner in ((args.legacy, "legacy"), (args.old, "previous")):
        token = reset(old_base, owner=owner)
        second_token = login(old_base, owner)
        precise = {"p": RawNumber("0.100000000000000005"), "round": RawNumber("9007199254740993.0"),
                   "underflow": RawNumber("1e-4300"), "whole": RawNumber("1e0")}
        a_body, b_body = booking(unused=precise), booking(table="b", unused=precise)
        a, b = create(old_base, token, a_body, "old-a"), create(old_base, token, b_body, "old-b")
        move_body = {"moves": [{"reference": a[1]["reference"], "table_id": "b"},
                               {"reference": b[1]["reference"], "table_id": "a"}], "unused": precise}
        moved = http(old_base, "POST", "/reservation-moves", move_body, token=token, key="old-moves", expected=201)
        http(old_base, "POST", "/reservations/" + a[1]["reference"] + "/cancel", token=token, expected=200)
        captured = exported(old_base)[2]
        captured_hash = digest(captured)
        create(old_base, token, booking(table="c"), "after-capture")
        check("captured genuine old export remains immutable", digest(captured) == captured_hash)
        prior = reset(args.peer)
        for base in (args.base, args.peer):
            http(base, "POST", "/_test/import", raw=captured, expected=204)
            check("genuine old create original raw retry", create(base, token, a_body, "old-a", 200)[2] == a[2])
            check("genuine old second create original raw retry", create(base, token, b_body, "old-b", 200)[2] == b[2])
            check("genuine old move original raw retry", http(base, "POST", "/reservation-moves", move_body,
                  token=token, key="old-moves", expected=200)[2] == moved[2])
            http(base, "GET", "/reservations/" + a[1]["reference"], token=second_token, expected=200)
            login(base, owner)
            exact_integer = {**precise, "round": 9007199254740993}
            create(base, token, {**a_body, "unused": exact_integer}, "old-a", 409, "idempotency_key_reuse")
            old_equal = {**precise, "round": 9007199254740992, "p": RawNumber("0.1"), "underflow": 0, "whole": 1}
            check("legacy rounded/underflow/int aliases preserve old meaning", create(base, token,
                  {**a_body, "unused": old_equal}, "old-a", 200)[2] == a[2])
        http(args.peer, "GET", "/reservations", token=prior, expected=401, code="unauthenticated")
        new_body = booking(table="c", unused=RawNumber("0.100000000000000005"))
        current = create(args.base, token, new_body, "new-exact")
        mixed = exported(args.base)
        profiles = [r["numeric_profile"] for r in mixed[1]["state"]["receipts"]]
        check("mixed private state schema3 profiles", mixed[1]["state"]["schema"] == 3
              and "exact-v1" in profiles and "python-json-v1" in profiles)
        http(args.peer, "POST", "/_test/import", raw=mixed[2], expected=204)
        check("mixed original historical replay after second replacement", create(args.peer, token, a_body, "old-a", 200)[2] == a[2])
        check("mixed exact replay after second replacement", create(args.peer, token, new_body, "new-exact", 200)[2] == current[2])
        create(args.peer, token, {**new_body, "unused": RawNumber("0.1")}, "new-exact", 409, "idempotency_key_reuse")
        before = exported(args.peer)[2]
        for invalid in (before.replace(b'"numeric_profile":"exact-v1"', b'"numeric_profile":null', 1),
                        before.replace(b',"numeric_profile":"exact-v1"', b'', 1),
                        before.replace(b'"numeric_profile":"python-json-v1"', b'"numeric_profile":"foreign"', 1)):
            check("profile mutation changes wire", invalid != before)
            http(args.peer, "POST", "/_test/import", raw=invalid, expected=422, code="validation_failed")
            check("invalid profile leaves previous destination unchanged", exported(args.peer)[2] == before)
        http(args.peer, "POST", "/_test/import", raw=before, expected=204)
        check("repeated replacement preserves opaque export", exported(args.peer)[2] == before)
        reset(args.peer)
        http(args.peer, "GET", "/reservations", token=token, expected=401, code="unauthenticated")


def exports_during_writes():
    token = reset(args.base)
    boundary = threading.Barrier(2)

    def writer():
        boundary.wait()
        for index in range(30):
            day = date(2038, 1, 1) + timedelta(days=index)
            create(args.base, token, booking(local=day.isoformat() + "T18:00"), "prefix-%02d" % index)

    snapshots = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(writer)
        boundary.wait()
        for _index in range(20):
            snapshots.append(exported(args.base))
        future.result()
    counts = []
    for _status, parsed, raw in snapshots:
        state = parsed["state"]
        rows, receipts = state["reservations"], state["receipts"]
        n = len(receipts)
        counts.append(n)
        check("concurrent export complete independent prefix", [r["key"] for r in receipts] == ["prefix-%02d" % i for i in range(n)]
              and len(rows) == n and {r["reference"] for r in rows} == {r["response"]["reference"] for r in receipts})
        http(args.peer, "POST", "/_test/import", raw=raw, expected=204)
        check("concurrent snapshot independently importable", len(http(args.peer, "GET", "/reservations", token=token,
              expected=200)[1]["reservations"]) == n)
    check("observed export/write interleaving", any(0 < n < 30 for n in counts), {"prefix_counts": counts})
    captured = snapshots[len(snapshots) // 2][2]
    saved_hash = digest(captured)
    reset(args.base)
    http(args.peer, "POST", "/_test/import", raw=captured, expected=204)
    check("retained export survives source replacement", digest(captured) == saved_hash)


for name, operation in (("exact aliases/full bodies", aliases_and_exact_bodies),
                        ("fixture value/type distinctions", fixture_value_statuses),
                        ("compact operational counts", huge_operational_counts),
                        ("error precedence/failed keys/constants", precedence_and_failed_keys),
                        ("nested receipts/independent replacement", nested_receipts_and_replacement),
                        ("genuine legacy/mixed second replacement", genuine_legacy_mixed_profiles),
                        ("atomic exports during real writes", exports_during_writes)):
    scenario(name, operation)

summary = {"http_requests": len(events), "assertions": len(assertions),
           "passed": sum(row["passed"] for row in assertions), "failed": sum(not row["passed"] for row in assertions),
           "scenarios": len(scenarios), "failed_scenarios": sum(bool(row["failed"]) for row in scenarios),
           "wall_seconds": time.monotonic() - started,
           "maximum_request_seconds": max(row["seconds"] for row in events),
           "maximum_request_bytes": max(row["request_bytes"] for row in events)}
(out / "trace.json").write_text(json.dumps({"summary": summary, "scenarios": scenarios,
                                            "operations": events, "assertions": assertions}, indent=2) + "\n")
print(json.dumps(summary))
sys.exit(bool(summary["failed"]))
