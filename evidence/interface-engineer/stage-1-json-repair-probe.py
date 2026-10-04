"""Own black-box JSON repair client; no service/test implementation imports.

URLs: repaired A, repaired B, genuine old49287b4, genuine candidate5.
Actual execution waits for a complete committed service. All exports/credentials
remain in memory; output contains public outcomes and fingerprints only.
The tiny client number reader retains JSON lexical decimals to avoid mistaking
a client float/Decimal limit for an HTTP result. It is not production code.
"""

import copy
import hashlib
import http.client
import json
import re
import sys
import time
from urllib.parse import urlsplit

sys.set_int_max_str_digits(0)
NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")


class NumericLexeme:
    def __init__(self, lexeme):
        if not NUMBER.fullmatch(lexeme):
            raise ValueError("Invalid client numeric construction")
        self.lexeme = lexeme


def reject_constant(value):
    raise ValueError("Invalid JSON constant")


def read(wire):
    return json.loads(wire.decode("utf-8"), parse_float=NumericLexeme,
                      parse_constant=reject_constant)


def write(value):
    if isinstance(value, NumericLexeme):
        return value.lexeme.encode("ascii")
    if value is None or type(value) in (str, bool, int):
        return json.dumps(value, ensure_ascii=True).encode("utf-8")
    if isinstance(value, list):
        return b"[" + b",".join(write(item) for item in value) + b"]"
    if isinstance(value, dict) and all(type(key) is str for key in value):
        return b"{" + b",".join(write(key) + b":" + write(item)
                                for key, item in value.items()) + b"}"
    raise ValueError("Unsupported client value")


def number_tuple(value):
    text = str(value) if type(value) is int else value.lexeme
    sign = -1 if text.startswith("-") else 1
    text = text.lstrip("-")
    pieces = re.split("[eE]", text)
    exponent = int(pieces[1]) if len(pieces) == 2 else 0
    whole, _, fraction = pieces[0].partition(".")
    digits = (whole + fraction).lstrip("0")
    if not digits:
        return [0, "0", 0]
    shortened = digits.rstrip("0")
    return [sign, shortened, exponent - len(fraction) + len(digits) - len(shortened)]


def canonical(value):
    if type(value) is int or isinstance(value, NumericLexeme):
        return ["number", number_tuple(value)]
    if isinstance(value, dict):
        return ["object", [[key, canonical(value[key])] for key in sorted(value)]]
    if isinstance(value, list):
        return ["array", [canonical(item) for item in value]]
    return [type(value).__name__, value]


def same(left, right):
    return canonical(left) == canonical(right)


def fingerprint(value):
    return hashlib.sha256(json.dumps(canonical(value), separators=(",", ":"),
                                     ensure_ascii=True).encode()).hexdigest()


def self_check():
    examples = ["1", "1.0", "1e0", "-0e-999999999999999999999999999999999999",
                "0.100000000000000005", "1e4300", "1e-4300",
                "1e999999999999999999999999999999999999", str(10**4300+1)+".5"]
    checks = [same(read(token.encode()), read(write(read(token.encode())))) for token in examples]
    checks += [same(1, NumericLexeme("1.0")), same(NumericLexeme("1e0"), 1),
               same(NumericLexeme("-0.0"), 0), not same(True, 1), not same("1", 1),
               not same(NumericLexeme("0.100000000000000005"), NumericLexeme("0.1")),
               not same(NumericLexeme("1e-4300"), 0),
               same(NumericLexeme("10e4299"), NumericLexeme("1e4300"))]
    print(json.dumps({"scope": "Own client syntax/exact-value self-check only; no HTTP",
                      "assertions": len(checks), "passed": sum(checks),
                      "failed": len(checks)-sum(checks)}))
    return 0 if all(checks) else 1


GIANT = 10**4300 + 1
DIGITS = str(GIANT)
HUGE_EXP = "999999999999999999999999999999999999"
RESULTS, TRACE = [], []
URLS = []
START = 0


def check(name, condition, detail=None):
    RESULTS.append({"name": name, "passed": bool(condition), "detail": detail})


def call(index, method, path, value=None, headers=None, raw=None):
    wire = raw if raw is not None else (write(value) if value is not None else None)
    timeout = 10 if path.startswith("/_test/") else 5
    url = URLS[index]
    client = http.client.HTTPConnection(url.hostname, url.port, timeout=timeout)
    begin = time.monotonic()
    try:
        client.request(method, path, wire, {"Content-Type": "application/json; charset=utf-8", **(headers or {})})
        response = client.getresponse()
        data = response.read()
        body = read(data) if data else None
        seconds = time.monotonic()-begin
        check("JSON charset", response.getheader("Content-Type") == "application/json; charset=utf-8")
        check("Exact response byte length", response.getheader("Content-Length") == str(len(data)))
        check("Request budget", seconds < timeout)
        TRACE.append({"process": index, "method": method, "path": path.replace(DIGITS, "<4301 digits>"),
                      "status": response.status, "code": body.get("error", {}).get("code") if isinstance(body, dict) else None,
                      "seconds": seconds, "request_sha256": hashlib.sha256(wire or b"").hexdigest(),
                      "response_sha256": hashlib.sha256(data).hexdigest()})
        return response.status, body, data
    finally:
        client.close()


def refusal(name, result, status, code):
    check(name, result[0] == status and isinstance(result[1], dict) and
          result[1].get("error", {}).get("code") == code,
          {"status": result[0], "expected_status": status, "expected_code": code})


def empty(name, result):
    check(name, result == (204, None, b""))


def fixture(capacity=4):
    return {"users": [{"id": "u", "email": "diner@example.test", "password": "correct horse", "display_name": "Quiet Diner"}],
            "restaurants": [{"id": "r", "name": "Quiet Dining", "timezone": "UTC", "slot_minutes": 30,
                             "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                             "opening_hours": [{"weekday": d, "opens": "18:00", "closes": "23:00"}
                                               for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                             "tables": [{"id": t, "label": t, "capacity": capacity} for t in ("t1", "t2")]}],
            "reservations": []}


def login(index):
    result = call(index, "POST", "/auth/login", {"email": "diner@example.test", "password": "correct horse"})
    check("Real password login", result[0] == 200)
    return {"Authorization": "Bearer " + result[1]["token"]}


def booking(table="t1", day="2099-06-04", party=1):
    return {"restaurant_id": "r", "table_id": table, "starts_at_local": day+"T18:00", "party_size": party}


def keyed(auth, key):
    return {**auth, "Idempotency-Key": key}


def snapshot(index):
    return call(index, "GET", "/_test/export")


def bases():
    for field, normal in (("slot_minutes", 30), ("reservation_duration_minutes", 90),
                          ("cancellation_cutoff_minutes", 0), ("capacity", 4)):
        for numeric in (NumericLexeme(str(normal)+".0"), NumericLexeme(str(normal)+"e0"), GIANT,
                        NumericLexeme("1e"+HUGE_EXP)):
            data = fixture()
            target = data["restaurants"][0]["tables"][0] if field == "capacity" else data["restaurants"][0]
            target[field] = numeric
            empty("Exact integral base " + field, call(0, "POST", "/_test/reset", data))
            detail = call(0, "GET", "/restaurants/r")
            actual = detail[1]["tables"][0][field] if field == "capacity" else detail[1][field]
            check("Exact numeric base response " + field, same(actual, numeric) and type(actual) is not str)
            offered = call(0, "GET", "/availability?restaurant_id=r&date=2099-06-04&party_size=1")
            if numeric is GIANT or isinstance(numeric, NumericLexeme) and numeric.lexeme.endswith(HUGE_EXP):
                slots = offered[1]["slots"]
                if field == "slot_minutes":
                    check("Huge grid remains bounded", len(slots) == 1 and slots[0]["starts_at_local"].endswith("18:00"))
                elif field == "reservation_duration_minutes":
                    check("Huge duration has no fitting slots", offered[0] == 200 and slots == [])
                else:
                    check("Huge capacity/cutoff preserves ordinary starts", offered[0] == 200 and len(slots) == 8)
        empty("Ordinary base control", call(0, "POST", "/_test/reset", fixture()))
        stable = fingerprint(snapshot(0)[1])
        for invalid, status in ((NumericLexeme("1.5"), 422), (NumericLexeme(DIGITS+".5"), 422),
                                (True, 400), ("1", 400), (None, 400), ([], 400), ({}, 400), (-1, 422)):
            data = fixture()
            target = data["restaurants"][0]["tables"][0] if field == "capacity" else data["restaurants"][0]
            target[field] = invalid
            refusal("Base type/value " + field, call(0, "POST", "/_test/reset", data), status,
                    "validation_failed" if status == 422 else "malformed_request")
            check("Invalid reset atomic", fingerprint(snapshot(0)[1]) == stable)


def exact_bodies():
    data = fixture(GIANT+1)
    data["unused"] = NumericLexeme("1e"+HUGE_EXP)
    empty("Ignored finite reset number", call(0, "POST", "/_test/reset", data))
    auth = login(0)
    body = booking(party=NumericLexeme("1.0"))
    body["ignored"] = {"overflow": NumericLexeme("1e4300"), "underflow": NumericLexeme("1e-4300"),
                       "precise": NumericLexeme("0.100000000000000005"), "compact": NumericLexeme("1e"+HUGE_EXP),
                       "zero": NumericLexeme("-0e-"+HUGE_EXP), "boolean": True, "list": [1, "1", None]}
    key = keyed(auth, "exact-current")
    original = call(0, "POST", "/reservations", body, key)
    check("Finite ignored numbers accepted with integral party", original[0] == 201 and same(original[1]["party_size"], 1))
    alias = copy.deepcopy(body)
    alias["party_size"] = NumericLexeme("1e0")
    alias["ignored"].update(overflow=NumericLexeme("10e4299"), underflow=NumericLexeme("10e-4301"),
                            precise=NumericLexeme("100000000000000005e-18"),
                            compact=NumericLexeme("10e"+str(int(HUGE_EXP)-1)), zero=0)
    replay = call(0, "POST", "/reservations", alias, key)
    check("Exact numeric aliases replay original", replay[0] == 200 and same(replay[1], original[1]))
    for field, changed in (("underflow", 0), ("precise", NumericLexeme("0.1")), ("boolean", 1),
                           ("list", ["1", 1, None])):
        different = copy.deepcopy(body)
        different["ignored"][field] = changed
        different["party_size"] = False
        refusal("Complete exact ignored identity " + field, call(0, "POST", "/reservations", different, key),
                409, "idempotency_key_reuse")
    exported = snapshot(0)
    receipt = exported[1]["state"]["receipts"][0]
    check("Successful parsed body stored exactly", same(receipt["body"], body))
    check("New receipt profile exact", receipt["numeric_profile"] == "exact-v1")
    empty("Exact body cross-process import", call(1, "POST", "/_test/import", raw=exported[2]))
    check("Exact state replacement unchanged", same(snapshot(1)[1], exported[1]))
    check("Exact aliases replay after import", call(1, "POST", "/reservations", alias, key)[0] == 200)
    giant = booking("t2", party=GIANT)
    giant_key = keyed(auth, "giant-integral")
    created = call(0, "POST", "/reservations", giant, giant_key)
    check("4301-digit party exact current value", created[0] == 201 and same(created[1]["party_size"], GIANT))
    giant["party_size"] = NumericLexeme(DIGITS+"e0")
    check("4301-digit integral exponent alias replays", call(0, "POST", "/reservations", giant, giant_key)[0] == 200)
    refusal("Strict exponent query", call(0, "GET", "/availability?restaurant_id=r&date=2099-06-04&party_size=1e0"),
            422, "validation_failed")
    query = call(0, "GET", "/availability?restaurant_id=r&date=2099-06-05&party_size="+DIGITS)
    check("4301-digit query valid and fitting", query[0] == 200 and all(s["available_table_ids"] == ["t1", "t2"] for s in query[1]["slots"]))


def precedence():
    empty("Precedence fixture", call(0, "POST", "/_test/reset", fixture(GIANT+1)))
    auth = login(0)
    original = call(0, "POST", "/reservations", booking(), keyed(auth, "saved-create"))
    check("Precedence original create", original[0] == 201)
    ref = original[1]["reference"]
    batch = {"moves": [{"reference": ref}]}
    saved_move = call(0, "POST", "/reservation-moves", batch, keyed(auth, "saved-move"))
    check("Precedence original move", saved_move[0] == 201)
    fraction = NumericLexeme(DIGITS+".5")
    for path, body, used in (("/reservations", booking("t2", party=fraction), "saved-create"),
                             ("/reservation-moves", {"moves": [{"reference": ref, "party_size": fraction}]}, "saved-move")):
        stable = fingerprint(snapshot(0)[1])
        refusal("Finite body auth precedence", call(0, "POST", path, body), 401, "unauthenticated")
        refusal("Finite body missing key precedence", call(0, "POST", path, body, auth), 400, "missing_idempotency_key")
        refusal("Finite body used-key precedence", call(0, "POST", path, body, keyed(auth, used)), 409, "idempotency_key_reuse")
        refusal("True large fractional party", call(0, "POST", path, body, keyed(auth, "fraction-"+used)), 422, "validation_failed")
        check("Fraction failures atomic", fingerprint(snapshot(0)[1]) == stable)
        valid = booking("t2") if path == "/reservations" else batch
        check("Fraction failed key reusable", call(0, "POST", path, valid, keyed(auth, "fraction-"+used))[0] == 201)
    past = call(0, "POST", "/reservations", booking(day="2000-06-04"), keyed(auth, "past"))
    check("Past create allowed", past[0] == 201)
    cancelled = call(0, "POST", "/reservations/"+ref+"/cancel", headers=auth)
    check("Future cancellation control", cancelled[0] == 200)
    for item, code in ((past[1]["reference"], "cutoff_passed"), (ref, "reservation_cancelled")):
        stable = fingerprint(snapshot(0)[1])
        refusal("Batch current state precedes fraction", call(0, "POST", "/reservation-moves",
                {"moves": [{"reference": item, "party_size": fraction}]}, keyed(auth, "state-"+code)), 409, code)
        check("Batch current refusal atomic", fingerprint(snapshot(0)[1]) == stable)
    for literal in ("NaN", "Infinity", "-Infinity"):
        for path in ("/reservations", "/reservation-moves", "/_test/reset"):
            refusal("Literal constant remains syntax refusal", call(0, "POST", path, raw=('{"unused":'+literal+'}').encode()),
                    400, "malformed_request")
    for raw in (b"null", b"[]", b"true", b"1", b'"x"', b'{"n":01}', b'{"n":1.}', b'{"n":1e}',
                b'{"n":+1}', b'{"x":"\xff"}', '{"x":1}'.encode("utf-16"), b'{} trailing'):
        refusal("Strict malformed/nonobject UTF8 boundary", call(0, "POST", "/reservations", raw=raw), 400, "malformed_request")


def legacy():
    for source in (2, 3):
        empty("Genuine historical fixture", call(source, "POST", "/_test/reset", fixture()))
        auths = [login(source), login(source)]
        leaves = {"precise": NumericLexeme("0.100000000000000005"), "rounded": NumericLexeme("9007199254740993.0"),
                  "underflow": NumericLexeme("1e-4300"), "integral": NumericLexeme("1e0"),
                  "integer": 9007199254740993, "boolean": True}
        if source == 3:
            leaves["giant_integer"] = GIANT
        bodies = [{**booking(t, "2099-06-10"), "old_ignored": copy.deepcopy(leaves)} for t in ("t1", "t2")]
        keys = [keyed(auths[0], "old-a"), keyed(auths[0], "old-b")]
        originals = [call(source, "POST", "/reservations", b, k) for b, k in zip(bodies, keys)]
        check("Genuine old creates issue references", all(r[0] == 201 for r in originals))
        refs = [r[1]["reference"] for r in originals]
        move = {"moves": [{"reference": refs[0], "table_id": "t2"}, {"reference": refs[1], "table_id": "t1"}],
                "old_ignored": copy.deepcopy(leaves)}
        move_key = keyed(auths[0], "old-swap")
        moved = call(source, "POST", "/reservation-moves", move, move_key)
        check("Genuine old swap receipt", moved[0] == 201)
        call(source, "PATCH", "/reservations/"+refs[0], {"starts_at_local": "2099-06-11T18:00"}, auths[0])
        call(source, "POST", "/reservations/"+refs[1]+"/cancel", headers=auths[0])
        old = snapshot(source)
        check("Genuine unmarked old schema", old[1]["state"]["schema"] == 1 and
              all("numeric_profile" not in r for r in old[1]["state"]["receipts"]))
        for destination in (0, 1):
            empty("Destination baseline", call(destination, "POST", "/_test/reset", fixture()))
            obsolete = login(destination)
            empty("Unmodified genuine snapshot transfer", call(destination, "POST", "/_test/import", raw=old[2]))
            refusal("Replacement removes old destination session", call(destination, "GET", "/reservations", headers=obsolete),
                    401, "unauthenticated")
            archived = snapshot(destination)[1]
            check("New schema and unchanged public envelope", archived["state"]["schema"] == 2 and archived["format_version"] == 1)
            for name, value in old[1]["state"].items():
                if name not in ("schema", "receipts"):
                    check("Genuine account/config/record data unchanged " + name, same(archived["state"][name], value))
            identity = lambda r: (r["user_id"], r["method"], r["path"], r["key"])
            old_receipts = {identity(r): r for r in old[1]["state"]["receipts"]}
            new_receipts = {identity(r): r for r in archived["state"]["receipts"]}
            check("Receipt identities unchanged", old_receipts.keys() == new_receipts.keys())
            for key, a in old_receipts.items():
                b = new_receipts[key]
                check("Legacy archive unchanged plus scoped profile", b["numeric_profile"] == "python-json-v1" and
                      all(same(a[k], b[k]) for k in a))
            for auth in auths:
                check("Real old sessions remain valid", call(destination, "GET", "/reservations", headers=auth)[0] == 200)
            for body, key, original in zip(bodies, keys, originals):
                retry = call(destination, "POST", "/reservations", body, key)
                check("Genuine rounded/underflow original retry", retry[0] == 200 and same(retry[1], original[1]))
            retry = call(destination, "POST", "/reservation-moves", move, move_key)
            check("Genuine legacy original move retry", retry[0] == 200 and same(retry[1], moved[1]))
            different = copy.deepcopy(bodies[0])
            different["old_ignored"]["rounded"] = 9007199254740993
            refusal("Legacy integer must not round", call(destination, "POST", "/reservations", different, keys[0]),
                    409, "idempotency_key_reuse")
            different["old_ignored"]["rounded"] = NumericLexeme("1e4300")
            refusal("Legacy projection overflow remains valid difference", call(destination, "POST", "/reservations", different, keys[0]),
                    409, "idempotency_key_reuse")
        current_body = {**booking(day="2099-06-12", party=NumericLexeme("1.0")),
                        "exact_ignored": copy.deepcopy(leaves), "finite_extra": NumericLexeme("1e4300")}
        current_key = keyed(auths[0], "new-exact")
        current = call(0, "POST", "/reservations", current_body, current_key)
        check("New exact receipt in imported legacy state", current[0] == 201)
        current_move = {"moves": [{"reference": current[1]["reference"], "table_id": "t2"}],
                        "exact_ignored": copy.deepcopy(leaves)}
        current_move_key = keyed(auths[0], "new-exact-move")
        current_moved = call(0, "POST", "/reservation-moves", current_move, current_move_key)
        check("New exact batch in legacy state", current_moved[0] == 201)
        call(0, "POST", "/reservations/"+current[1]["reference"]+"/cancel", headers=auths[0])
        mixed = snapshot(0)
        profiles = [r["numeric_profile"] for r in mixed[1]["state"]["receipts"]]
        check("Mixed profile export", profiles.count("python-json-v1") == 3 and profiles.count("exact-v1") == 2)
        empty("Mixed second independent import", call(1, "POST", "/_test/import", raw=mixed[2]))
        check("Second replacement retains exact full mixed state", same(snapshot(1)[1], mixed[1]))
        for index in (0, 1):
            for body, key, original in zip(bodies, keys, originals):
                retry = call(index, "POST", "/reservations", body, key)
                check("Legacy receipts retain original meaning after second import", retry[0] == 200 and same(retry[1], original[1]))
            check("Legacy swap still original", same(call(index, "POST", "/reservation-moves", move, move_key)[1], moved[1]))
            retry = call(index, "POST", "/reservations", current_body, current_key)
            check("New exact original create after cancellation/second import", retry[0] == 200 and same(retry[1], current[1]))
            retry = call(index, "POST", "/reservation-moves", current_move, current_move_key)
            check("New exact original move after cancellation/second import", retry[0] == 200 and same(retry[1], current_moved[1]))
            changed = copy.deepcopy(current_body)
            changed["exact_ignored"]["precise"] = NumericLexeme("0.1")
            refusal("New receipt never adopts legacy rounding", call(index, "POST", "/reservations", changed, current_key),
                    409, "idempotency_key_reuse")
        stable = fingerprint(snapshot(1)[1])
        for invalid in (None, "unknown-profile"):
            bad = copy.deepcopy(mixed[1])
            if invalid is None:
                del bad["state"]["receipts"][0]["numeric_profile"]
            else:
                bad["state"]["receipts"][0]["numeric_profile"] = invalid
            refusal("Invalid new profile state", call(1, "POST", "/_test/import", bad), 422, "validation_failed")
            check("Invalid profile replacement atomic", fingerprint(snapshot(1)[1]) == stable)
        empty("Repeated mixed replacement", call(1, "POST", "/_test/import", raw=mixed[2]))
        check("Repeated replacement never duplicates", fingerprint(snapshot(1)[1]) == stable)
        login(1)
        empty("Reset clears all imported receipts/credentials", call(1, "POST", "/_test/reset",
              {"users": [], "restaurants": [], "reservations": []}))
        refusal("Reset removes genuine old token", call(1, "GET", "/reservations", headers=auths[0]), 401, "unauthenticated")


def main():
    global URLS, START
    if sys.argv[1:] == ["--self-check"]:
        return self_check()
    if len(sys.argv) != 5:
        raise SystemExit("Requires repairedA repairedB old49287b4 oldCandidate5 URLs")
    URLS = [urlsplit(url) for url in sys.argv[1:]]
    START = time.monotonic()
    for name, function in (("Base numbers", bases), ("Exact bodies", exact_bodies),
                           ("Precedence and malformed", precedence), ("Genuine legacy/mixed", legacy)):
        try:
            function()
        except Exception as exc:
            check(name+" completes without client/flow exception", False, type(exc).__name__)
    summary = {"scope": "Own complete-image HTTP JSON repair diagnostics",
               "seconds": time.monotonic()-START, "operations": len(TRACE), "assertions": len(RESULTS),
               "passed": sum(r["passed"] for r in RESULTS), "failed": sum(not r["passed"] for r in RESULTS),
               "results": RESULTS, "trace": TRACE,
               "max_request_seconds": max((r["seconds"] for r in TRACE), default=0)}
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
