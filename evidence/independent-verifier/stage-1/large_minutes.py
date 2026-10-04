"""HTTP-only audit of positive fixture minute counts without a published maximum.

Executed inside the constrained service container as a separate HTTP client.
Credentials and exported state remain in memory; output uses fingerprints.
"""
import copy
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1]
CANDIDATE = sys.argv[2]
HUGE = 10**18
trace, assertions = [], []
started = time.monotonic()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def safe(value):
    if isinstance(value, dict):
        return {key: ({"private_value_sha256": digest(item)} if key in {"token", "password", "state"} else safe(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [safe(item) for item in value]
    return value


def call(method, path, body=None, token=None, key=None):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    request = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
    began = time.monotonic()
    try:
        try:
            response = urllib.request.urlopen(request, timeout=10 if path.startswith("/_test/") else 5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            status, raw = response.status, response.read()
        value = json.loads(raw) if raw else None
    except Exception as error:
        status, value = 0, {"transport_error": str(error)}
    trace.append(dict(operation=len(trace)+1, method=method, path=path, body=safe(body), has_token=bool(token), key=key,
                      status=status, response=safe(value), duration_seconds=time.monotonic()-began))
    return status, value


def check(key, passed, expected, observed):
    assertions.append(dict(requirement_id="TK1-"+key, passed=bool(passed), expected=safe(expected), observed=safe(observed)))


def expect(key, method, path, body=None, status=200, code=None, **kwargs):
    observed_status, value = call(method, path, body, **kwargs)
    check(key, observed_status == status and (code is None or isinstance(value, dict) and value.get("error", {}).get("code") == code),
          dict(status=status, code=code), dict(status=observed_status, body=value))
    return observed_status, value


fixture = {"users": [{"id": "u", "email": "large@probe.invalid", "password": "large-minutes-pass", "display_name": "Boundary Diner"}],
           "restaurants": [{"id": "r", "name": "Boundary Kitchen", "timezone": "UTC", "slot_minutes": 30,
                            "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                            "opening_hours": [{"weekday": "tue", "opens": "18:10", "closes": "23:10"}],
                            "tables": [{"id": "t", "label": "Window", "capacity": 2}]}], "reservations": []}
booking = dict(restaurant_id="r", table_id="t", starts_at_local="2035-06-05T18:10", party_size=2)
expect("probe-large-minutes-control", "POST", "/_test/reset", fixture, status=204)
for field in ["slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes"]:
    current = copy.deepcopy(fixture)
    current["restaurants"][0][field] = HUGE
    prefix = "large-"+field
    reset_status, _ = expect(prefix+"-reset", "POST", "/_test/reset", current, status=204)
    if reset_status != 204:
        continue
    detail_status, detail = call("GET", "/restaurants/r")
    check(prefix+"-detail", detail_status == 200 and detail.get(field) == HUGE, HUGE, detail)
    export_status, exported = call("GET", "/_test/export")
    import_status, _ = call("POST", "/_test/import", exported)
    detail_status, imported_detail = call("GET", "/restaurants/r")
    check(prefix+"-import", export_status == 200 and import_status == 204 and detail_status == 200 and imported_detail.get(field) == HUGE,
          "export/import preserves the positive count exactly", dict(export=export_status, import_status=import_status, detail=imported_detail))
    login_status, login = call("POST", "/auth/login", dict(email=current["users"][0]["email"], password=current["users"][0]["password"]))
    if login_status != 200:
        continue
    token = login["token"]
    if field == "slot_minutes":
        status, available = expect("large-grid-availability", "GET", "/availability?restaurant_id=r&date=2035-06-05&party_size=2")
        check("large-grid-one-opening-slot", status == 200 and [slot["starts_at_local"] for slot in available.get("slots", [])] == ["2035-06-05T18:10"],
              ["2035-06-05T18:10"], available)
        expect("large-grid-create", "POST", "/reservations", booking, token=token, key="large-grid", status=201)
        late = dict(booking, starts_at_local="2035-06-05T18:40")
        expect("large-grid-late", "POST", "/reservations", late, token=token, key="large-grid-late", status=422, code="not_on_slot_grid")
    elif field == "reservation_duration_minutes":
        status, available = expect("large-duration-availability", "GET", "/availability?restaurant_id=r&date=2035-06-05&party_size=2")
        check("large-duration-no-fitting-slot", status == 200 and available.get("slots") == [], [], available)
        expect("large-duration-create", "POST", "/reservations", booking, token=token, key="large-duration", status=422, code="outside_opening_hours")
    else:
        status, receipt = expect("large-cutoff-create", "POST", "/reservations", booking, token=token, key="large-cutoff", status=201)
        if status != 201:
            continue
        reference = receipt["reference"]
        _, before = call("GET", "/_test/export")
        expect("large-cutoff-cancel", "POST", "/reservations/"+reference+"/cancel", {}, token=token, status=409, code="cutoff_passed")
        expect("large-cutoff-patch", "PATCH", "/reservations/"+reference, {"party_size": 1}, token=token, status=409, code="cutoff_passed")
        expect("large-cutoff-moves", "POST", "/reservation-moves", {"moves": [{"reference": reference, "party_size": 1}]}, token=token, key="large-cutoff-moves", status=409, code="cutoff_passed")
        _, after = call("GET", "/_test/export")
        check("large-cutoff-rollback", before == after, "records, occupancy and retry keys unchanged", dict(before_sha256=digest(before), after_sha256=digest(after)))

result = dict(candidate_full_revision=CANDIDATE, value=HUGE, http_operations=len(trace), assertions=len(assertions),
              failed_assertions=sum(not item["passed"] for item in assertions), duration_seconds=time.monotonic()-started,
              operations=trace, results=assertions)
print(json.dumps(result, indent=2))
raise SystemExit(bool(result["failed_assertions"]))
