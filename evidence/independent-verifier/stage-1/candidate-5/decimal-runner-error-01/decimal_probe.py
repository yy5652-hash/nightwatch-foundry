"""Exact-decimal HTTP evidence. Client conversion is separate from service setup."""
import argparse
import copy
import json
import sys
from probe import Probe, fixture
from decimal_requirements import DECIMAL, FIELDS
from decimal_requirements import ROWS
import probe as probe_module

probe_module.ROWS = ROWS

sys.set_int_max_str_digits(0)  # Only this independent client interpreter.
N_TEXT = "1" + "0" * 4299 + "1"
N = int(N_TEXT)
assert len(N_TEXT) == 4301
p = argparse.ArgumentParser()
for name in ["base", "peer", "candidate", "out"]:
    p.add_argument("--"+name, required=True)
a = p.parse_args()
a.case = "decimal-exact"
q = Probe(a)

def check(key, condition, expected=None, observed=None):
    assert key in DECIMAL
    q.check(key, condition, expected, observed)

def expect(key, method, path, body=None, status=200, code=None, **kwargs):
    assert key in DECIMAL
    return q.expect(key, method, path, body, status=status, code=code, **kwargs)

def config(f, field, value):
    r = f["restaurants"][0]
    if field == "capacity":
        r["tables"][0][field] = value
    else:
        r[field] = value

def value_of(detail, field):
    return detail["tables"][0][field] if field == "capacity" else detail[field]

for field in FIELDS:
    f = fixture()
    config(f, field, N)
    status, _ = q.call("POST", "/_test/reset", f)
    q.check("decimal-limit-"+field, status == 204, 204, status)
    if status != 204:
        continue
    q.setup(f)
    detail = q.call("GET", "/restaurants/r")[1]
    check("decimal-"+field+"-detail", value_of(detail, field) == N, N, detail)
    snapshot = q.state()
    check("decimal-"+field+"-export", q.state() == snapshot and snapshot["track"] == "tablekeeper" and snapshot["format_version"] == 1)
    imported, _ = q.call("POST", "/_test/import", snapshot, base=a.peer)
    observed = q.call("GET", "/restaurants/r", base=a.peer)[1]
    check("decimal-"+field+"-import", imported == 204 and q.state(base=a.peer) == snapshot and value_of(observed, field) == N, N, observed)
    if field == "slot_minutes":
        slots = q.availability()["slots"]
        check("decimal-grid-opening", [x["starts_at_local"] for x in slots] == ["2035-06-04T18:10"], "one opening slot", slots)
        receipt = expect("decimal-grid-create", "POST", "/reservations", q.body(), token=q.a, key="grid-good", status=201)
        expect("decimal-grid-off", "POST", "/reservations", q.body("t0", "2035-06-04T18:40"), token=q.a, key="grid-refused", status=422, code="not_on_slot_grid")
        expect("decimal-grid-failed-key", "POST", "/reservations", q.body("t0"), token=q.a, key="grid-refused", status=201)
    elif field == "reservation_duration_minutes":
        check("decimal-duration-empty", q.availability()["slots"] == [])
        before = q.state()
        expect("decimal-duration-create", "POST", "/reservations", q.body(), token=q.a, key="duration-refused", status=422, code="outside_opening_hours")
        check("decimal-duration-atomic", q.state() == before)
    elif field == "cancellation_cutoff_minutes":
        receipt = expect("decimal-cutoff-create", "POST", "/reservations", q.body(), token=q.a, key="cutoff-create", status=201)
        ref = receipt["reference"]
        before = q.state()
        expect("decimal-cutoff-cancel", "POST", "/reservations/"+ref+"/cancel", {}, token=q.a, status=409, code="cutoff_passed")
        expect("decimal-cutoff-patch", "PATCH", "/reservations/"+ref, {"party_size":False}, token=q.a, status=409, code="cutoff_passed")
        expect("decimal-cutoff-moves", "POST", "/reservation-moves", {"moves":[{"reference":ref,"party_size":False}]}, token=q.a, key="cutoff-failed", status=409, code="cutoff_passed")
        check("decimal-cutoff-atomic", q.state() == before)
        # An ordinary restaurant is in the same replacement state; reuse the
        # failed batch key with that resource, without reset clearing the key.
        ordinary = fixture()["restaurants"][0]
        ordinary["id"] = "ordinary"
        f["restaurants"].append(ordinary)
        q.setup(f)
        protected = q.create(key="protected")
        q.call("POST", "/reservation-moves", {"moves":[{"reference":protected["reference"]}]}, token=q.a, key="cutoff-failed")
        legal = q.create(q.body(restaurant="ordinary"), key="ordinary")
        expect("decimal-cutoff-failed-key", "POST", "/reservation-moves", {"moves":[{"reference":legal["reference"],"party_size":1}]}, token=q.a, key="cutoff-failed", status=201)
    for label, value, status in [("boolean",True,400),("string",N_TEXT,400),("fraction",1.5,422),("negative",-N,422),("zero",0,422)]:
        if field == "cancellation_cutoff_minutes" and label == "zero":
            continue
        bad = copy.deepcopy(f)
        config(bad, field, value)
        before = q.state()
        expect("decimal-"+field+"-"+label, "POST", "/_test/reset", bad, status=status, code="malformed_request" if status == 400 else "validation_failed")
        check("decimal-"+field+"-"+label+"-atomic", q.state() == before)

q.setup()
slots = q.availability(party=N)["slots"]
q.check("decimal-limit-query", len(slots) == 8 and all(x["available_table_ids"] == [] for x in slots), "8 empty fitting starts", slots)
check("decimal-query-empty", len(slots) == 8 and all(x["available_table_ids"] == [] for x in slots))
for label, text in [("exponent","1e4300"),("fraction","4.0"),("plus","%2B4"),("negative","-"+N_TEXT),("zero","0"),("spaces","%204%20")]:
    expect("decimal-query-"+label, "GET", "/availability?restaurant_id=r&date=2035-06-04&party_size="+text, status=422, code="validation_failed")

f = fixture(tables=2)
for table in f["restaurants"][0]["tables"]:
    table["capacity"] = N
q.setup(f)
slots = q.availability(party=N)["slots"]
check("decimal-capacity-query", len(slots) == 8 and slots[0]["available_table_ids"] == ["t0","t1"])
body = dict(q.body("t0",party=N), ignored_decimal=N)
first = expect("decimal-capacity-create", "POST", "/reservations", body, token=q.a, key="giant-create", status=201)
check("decimal-ignored", first["party_size"] == N and "ignored_decimal" not in first)
expect("decimal-ignored-binding", "POST", "/reservations", dict(body, ignored_decimal=N+1, party_size=False), token=q.a, key="giant-create", status=409, code="idempotency_key_reuse")
reordered = json.dumps(dict(reversed(list(body.items()))), indent=2)
check("decimal-reordered-replay", q.call("POST", "/reservations", token=q.a, key="giant-create", raw=reordered) == (200, first))
before = q.state()
expect("decimal-capacity-over", "POST", "/reservations", q.body("t1",party=N+1), token=q.a, key="over", status=422, code="party_exceeds_capacity")
check("decimal-capacity-over-atomic", q.state() == before)
for label, value in [("boolean",True),("string",N_TEXT),("fraction",1.5),("zero",0),("negative",-N)]:
    before = q.state()
    expect("decimal-party-"+label, "POST", "/reservations", q.body("t1",party=value), token=q.a, key="party-"+label, status=422, code="validation_failed")
    check("decimal-party-"+label+"-atomic", q.state() == before)
patched = q.call("PATCH", "/reservations/"+first["reference"], {"party_size":N-1}, token=q.a)[1]
check("decimal-patch-exact", patched["party_size"] == N-1 and patched["reservation_id"] == first["reservation_id"])
second = q.create(q.body("t1",party=N),key="giant-second")
moves = {"moves":[{"reference":first["reference"],"table_id":"t1","party_size":N-2,"ignored_decimal":N},{"reference":second["reference"],"table_id":"t0"}]}
batch = q.call("POST", "/reservation-moves", moves, token=q.a, key="giant-batch")[1]
check("decimal-moves-exact", [x["party_size"] for x in batch["reservations"]] == [N-2,N] and [x["table_id"] for x in batch["reservations"]] == ["t1","t0"])
check("decimal-moves-identity", all(x[k] == original[k] for x,original in zip(batch["reservations"],[first,second]) for k in ["reference","reservation_id","created_at"]))
before = q.state()
bad = {"moves":[{"reference":first["reference"],"party_size":N-3},{"reference":second["reference"],"party_size":N+1}]}
s,v = q.call("POST", "/reservation-moves", bad, token=q.a, key="bad-moves")
check("decimal-moves-rollback", s == 422 and v["error"]["code"] == "party_exceeds_capacity" and q.state() == before)
expect("decimal-moves-failed-key", "POST", "/reservation-moves", {"moves":[{"reference":first["reference"],"party_size":N-3}]}, token=q.a, key="bad-moves", status=201)
for record in [first,second]:
    q.call("POST", "/reservations/"+record["reference"]+"/cancel", {}, token=q.a)
check("decimal-create-original", q.call("POST", "/reservations", body, token=q.a, key="giant-create") == (200,first))
check("decimal-batch-original", q.call("POST", "/reservation-moves", moves, token=q.a, key="giant-batch") == (200,batch))
snapshot = q.state()
source_token = q.a
records = q.call("GET", "/reservations", token=source_token)[1]
q.setup(base=a.peer)
dest_token = q.a
q.call("POST", "/_test/import", snapshot, base=a.peer)
check("decimal-replacement", q.call("GET", "/reservations", token=dest_token, base=a.peer)[0] == 401 and q.state(base=a.peer) == snapshot)
check("decimal-tokens", q.call("GET", "/reservations", token=source_token, base=a.peer)[0] == 200)
check("decimal-password-login", q.call("POST", "/auth/login", {"email":"a@probe.invalid","password":"verifier-pass-A"}, base=a.peer)[0] == 200)
check("decimal-records", q.call("GET", "/reservations", token=source_token, base=a.peer) == (200,records))
check("decimal-import-create-original", q.call("POST", "/reservations", body, token=source_token, key="giant-create", base=a.peer) == (200,first))
check("decimal-import-batch-original", q.call("POST", "/reservation-moves", moves, token=source_token, key="giant-batch", base=a.peer) == (200,batch))
q.call("POST", "/_test/import", snapshot, base=a.peer)
check("decimal-repeat-import", q.state(base=a.peer) == snapshot)
invalid = dict(snapshot,format_version=99)
expect("decimal-invalid-import", "POST", "/_test/import", invalid, base=a.peer, status=422, code="validation_failed")
check("decimal-invalid-import", q.state(base=a.peer) == snapshot)
for label, raw in [("truncated",'{"capacity":'+N_TEXT),("leading-zero",'{"capacity":0'+N_TEXT+'}'),("nan",'{"capacity":NaN}'),("nonobject",N_TEXT)]:
    before = q.state(base=a.peer)
    expect("decimal-json-"+label, "POST", "/_test/reset", raw=raw, base=a.peer, status=400, code="malformed_request")
    check("decimal-json-"+label+"-atomic", q.state(base=a.peer) == before)
q.call("POST", "/_test/reset", fixture(), base=a.peer)
check("decimal-reset-clears", q.call("GET", "/reservations", token=source_token, base=a.peer)[0] == 401 and q.state(base=a.peer) != snapshot)
missing = set(DECIMAL) - {x["requirement_id"][4:] for x in q.results}
assert not missing, missing
raise SystemExit(1 if q.finish() else 0)
