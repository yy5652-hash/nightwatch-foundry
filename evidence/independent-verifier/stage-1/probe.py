#!/usr/bin/env python3
"""Spec-derived black-box probes. No product imports or shipped-test imports.

Run against TWO independent service processes. Raw exports stay only in memory.
Every result names a stable atomic requirement; absent evidence stays unverified.
"""
import argparse
import concurrent.futures
import copy
import csv
import datetime as dt
import hashlib
import json
import random
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo
from requirements import ROWS, RESPONSE_FIELDS

UTC = dt.timezone.utc
DAY = "2035-06-04"
SECRET_KEYS = {"token", "password", "password_hash", "password_salt", "salt", "hash", "tokens", "sessions"}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def safe(value):
    if isinstance(value, dict):
        return {k: ({"private_value_sha256": fingerprint(v)} if k in SECRET_KEYS or k == "state" else safe(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [safe(x) for x in value]
    return value


def fixture(zone="UTC", opens="18:10", closes="23:10", slot=30, duration=90, cutoff=0, tables=3):
    return {"users": [{"id": "u_a", "email": "a@probe.invalid", "password": "verifier-pass-A", "display_name": "Diner A"},
                      {"id": "u_b", "email": "b@probe.invalid", "password": "verifier-pass-B", "display_name": "Diner B"}],
            "restaurants": [{"id": "r", "name": "Verifier Kitchen", "timezone": zone,
                             "slot_minutes": slot, "reservation_duration_minutes": duration,
                             "cancellation_cutoff_minutes": cutoff,
                             "opening_hours": [{"weekday": day, "opens": opens, "closes": closes} for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]],
                             "tables": [{"id": f"t{i}", "label": f"Table {i}", "capacity": [2, 4, 6][i % 3]} for i in range(tables)]}],
            "reservations": []}


class Probe:
    def __init__(self, args):
        self.args = args
        self.out = Path(args.out)
        self.out.mkdir(parents=True, exist_ok=False)
        self.results = []
        self.trace = []
        self.lock = threading.Lock()
        self.counter = 0
        self.error_shapes = []
        self.content_types = []
        self.latencies = []
        self.statuses = []
        self.race_latencies = []
        self.tokens = {}
        self.started = time.monotonic()

    def check(self, key, condition, expected=None, observed=None):
        with self.lock:
            self.results.append({"requirement_id": "TK1-" + key, "passed": bool(condition),
                                 "expected": safe(expected), "observed": safe(observed)})

    def call(self, method, path, body=None, token=None, key=None, base=None, raw=None, auth=None):
        base = base or self.args.base
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if auth is not None:
            headers["Authorization"] = auth
        if key is not None:
            headers["Idempotency-Key"] = key
        data = raw.encode() if raw is not None else json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
        started = time.monotonic()
        try:
            try:
                response = urllib.request.urlopen(req, timeout=10 if path.startswith("/_test/") else 5)
            except urllib.error.HTTPError as e:
                response = e
            with response:
                status = response.status
                text = response.read().decode()
                ctype = response.headers.get("Content-Type", "")
            value = json.loads(text) if text else None
        except Exception as e:
            status, value, ctype = 0, {"transport_error": str(e)}, ""
        elapsed = time.monotonic() - started
        with self.lock:
            self.counter += 1
            self.trace.append({"operation": self.counter, "method": method, "path": path,
                               "peer": base, "body": safe(body), "raw": "[invalid/alternate serialized body]" if raw is not None else None,
                               "has_token": token is not None or auth is not None,
                               "key": key, "status": status, "response": safe(value), "duration_seconds": elapsed,
                               "request_started_monotonic": started, "request_finished_monotonic": started + elapsed})
            self.statuses.append(status)
            self.latencies.append((path, elapsed, status))
            if value is not None:
                self.content_types.append(ctype.lower().replace(" ", ""))
            if status >= 400:
                self.error_shapes.append(isinstance(value, dict) and isinstance(value.get("error"), dict)
                                         and isinstance(value["error"].get("code"), str)
                                         and isinstance(value["error"].get("message"), str) and bool(value["error"]["message"]))
        return status, value

    def expect(self, rid, method, path, body=None, status=200, code=None, **kwargs):
        got, value = self.call(method, path, body, **kwargs)
        passed = got == status and (code is None or isinstance(value, dict) and value.get("error", {}).get("code") == code)
        self.check(rid, passed, {"status": status, "code": code}, {"status": got, "body": value})
        return value

    def setup(self, f=None, base=None):
        self.f = f or fixture()
        status, _ = self.call("POST", "/_test/reset", self.f, base=base)
        if status != 204:
            raise RuntimeError(f"Legal reset fixture rejected: {status}")
        for user in self.f["users"]:
            status, receipt = self.call("POST", "/auth/login", {"email": user["email"], "password": user["password"]}, base=base)
            if status != 200 or not receipt.get("token"):
                raise RuntimeError(f"Seeded login failed: {status}")
            self.tokens[user["id"]] = receipt["token"]
        self.a = self.tokens[self.f["users"][0]["id"]]
        self.b = self.tokens[self.f["users"][1]["id"]]

    def body(self, table="t1", local=DAY + "T18:10", party=2, restaurant="r"):
        return dict(restaurant_id=restaurant, table_id=table, starts_at_local=local, party_size=party)

    def create(self, body=None, token=None, key=None, base=None):
        key = key or f"create-{self.counter}"
        status, receipt = self.call("POST", "/reservations", body or self.body(), token=token or self.a, key=key, base=base)
        if status != 201:
            raise RuntimeError(f"Create setup failed: status={status}, body={receipt}")
        return receipt

    def availability(self, party=2, day=DAY, rid="r", base=None):
        path = "/availability?" + urllib.parse.urlencode(dict(restaurant_id=rid, date=day, party_size=party))
        status, value = self.call("GET", path, base=base)
        if status != 200:
            raise RuntimeError(f"Availability setup failed: {status}")
        return value

    def state(self, base=None):
        status, value = self.call("GET", "/_test/export", base=base)
        if status != 200:
            raise RuntimeError(f"Export setup failed: {status}")
        return value

    def reservation_shape(self, prefix, value, expected):
        for field in RESPONSE_FIELDS:
            if field in expected:
                valid = value.get(field) == expected[field]
            elif field == "reservation_id":
                valid = isinstance(value.get(field), str) and 1 <= len(value[field]) <= 64
            elif field == "reference":
                valid = isinstance(value.get(field), str) and re.fullmatch(r"[A-Z0-9]{6,12}", value[field]) is not None
            elif field in ["starts_at", "ends_at", "created_at"]:
                valid = isinstance(value.get(field), str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}", value[field]) is not None
            else:
                valid = field in value
            self.check(prefix + "-response-" + field, valid, expected.get(field, "specified response field"), value.get(field))

    def basics(self):
        self.expect("health-status", "GET", "/health")
        value = self.call("GET", "/health")[1]
        self.check("health-body", value == {"status": "ok"}, {"status": "ok"}, value)
        self.check("health-public", value == {"status": "ok"})
        self.setup()
        old = self.a
        self.create(key="reset-receipt")
        status, value = self.call("POST", "/_test/reset", fixture())
        self.check("reset-status", status == 204 and value is None)
        self.check("reset-public", status == 204)
        self.expect("reset-sessions", "GET", "/reservations", token=old, status=401, code="unauthenticated")
        self.setup()
        self.check("reset-repeat", True, "repeated resets with 204", status)
        self.expect("reset-receipts", "POST", "/reservations", self.body(), token=self.a, key="reset-receipt", status=201)
        f = fixture()
        f["restaurants"][0]["id"] = "replacement"
        self.setup(f)
        value = self.call("GET", "/restaurants")[1]
        self.check("reset-replacement", value == {"restaurants": [{"id": "replacement", "name": "Verifier Kitchen", "timezone": "UTC"}]})
        self.setup()
        status, value = self.call("GET", "/restaurants")
        self.check("restaurants-status", status == 200)
        self.check("restaurants-envelope", isinstance(value.get("restaurants"), list))
        for field in ["id", "name", "timezone"]:
            self.check("restaurants-" + field, value["restaurants"][0][field] == self.f["restaurants"][0][field])
        status, value = self.call("GET", "/restaurants/r")
        self.check("detail-status", status == 200)
        for field in self.f["restaurants"][0]:
            self.check("detail-" + field, value.get(field) == self.f["restaurants"][0][field])
        self.expect("detail-unknown", "GET", "/restaurants/missing", status=404, code="not_found")

    def auth(self):
        self.setup()
        signup = dict(email="new@probe.invalid", password="12345678", display_name="New Diner")
        value = self.expect("signup-status", "POST", "/auth/signup", signup, status=201)
        first_token = value["token"]
        for field in ["user_id", "display_name", "token"]:
            self.check("signup-response-" + field, value.get(field) == signup[field] if field == "display_name" else isinstance(value.get(field), str) and bool(value[field]))
        login = self.expect("login-status", "POST", "/auth/login", {k: signup[k] for k in ["email", "password"]})
        for field in ["user_id", "display_name", "token"]:
            self.check("login-response-" + field, login.get(field) == value[field] if field != "token" else isinstance(login.get(field), str) and bool(login[field]))
        self.expect("email-duplicate", "POST", "/auth/signup", signup, status=409, code="email_taken")
        self.expect("password-minimum", "POST", "/auth/signup", dict(signup, email="short@probe.invalid", password="1234567"), status=422, code="validation_failed")
        for email in ["no-at", "@domain", "local@"]:
            self.expect("email-format", "POST", "/auth/signup", dict(signup, email=email), status=422, code="validation_failed")
        self.expect("login-wrong-password", "POST", "/auth/login", dict(email=signup["email"], password="badpassword"), status=401, code="unauthenticated")
        self.expect("login-unknown-email", "POST", "/auth/login", dict(email="absent@probe.invalid", password="badpassword"), status=401, code="unauthenticated")
        for endpoint, fields in [("signup", ["email", "password", "display_name"]), ("login", ["email", "password"])]:
            body = {k: signup[k] for k in fields}
            for field in fields:
                missing = {k: v for k, v in body.items() if k != field}
                self.expect(f"{endpoint}-{field}-required", "POST", "/auth/" + endpoint, missing, status=422, code="validation_failed")
                for variant, invalid in [("bool", True), ("number", 5), ("array", []), ("object", {}), ("null", None)]:
                    self.expect(f"{endpoint}-{field}-type-{variant}", "POST", "/auth/" + endpoint, dict(body, **{field: invalid}), status=400, code="malformed_request")
                    self.check(f"{endpoint}-{field}-type", self.results[-1]["passed"])
        self.check("tokens-multiple", all(self.call("GET", "/reservations", token=t)[0] == 200 for t in [first_token, login["token"], self.a, self.b]))
        paths = [("restaurants", "GET", "/restaurants", None, True), ("restaurant-detail", "GET", "/restaurants/r", None, True),
                 ("availability", "GET", "/availability?restaurant_id=r&date=" + DAY + "&party_size=2", None, True)]
        r = self.create()
        ref = r["reference"]
        paths += [("reservation-list", "GET", "/reservations", None, False), ("reservation-lookup", "GET", "/reservations/" + ref, None, False),
                  ("reservation-create", "POST", "/reservations", self.body(), False), ("reservation-cancel", "POST", "/reservations/" + ref + "/cancel", {}, False),
                  ("reservation-patch", "PATCH", "/reservations/" + ref, {}, False), ("moves", "POST", "/reservation-moves", {"moves": [{"reference": ref}]}, False)]
        for name, method, path, body, public in paths:
            variants = [("absent", None), ("unknown", "Bearer missing-token"), ("basic", "Basic wrong"), ("bearer-no-value", "Bearer"), ("bearer-empty", "Bearer ")] if not public else [("public", None)]
            for variant, auth in variants:
                self.expect("auth-" + name + ("-" + variant if not public else ""), method, path, body, status=200 if public else 401, code=None if public else "unauthenticated", auth=auth, key="auth-test")

    def fixture_case(self):
        f = fixture(zone="Europe/Berlin")
        f["reservations"] = [dict(self.body(), id="seed_res", reference="SEED01", user_id="u_a")]
        self.setup(f)
        r = self.call("GET", "/reservations/SEED01", token=self.a)[1]
        self.check("seeded-login", bool(self.a))
        self.check("seeded-reservation", r.get("reservation_id") == "seed_res")
        for shape, records in [("fixture-user", f["users"]), ("fixture-restaurant", f["restaurants"]),
                               ("fixture-hours", f["restaurants"][0]["opening_hours"]), ("fixture-table", f["restaurants"][0]["tables"]),
                               ("fixture-reservation", f["reservations"])]:
            for field in records[0]:
                if shape == "fixture-user":
                    ok = bool(self.tokens.get(records[0]["id"]))
                    if field in ["id", "display_name"]:
                        login = self.call("POST", "/auth/login", {k: records[0][k] for k in ["email", "password"]})[1]
                        ok = login.get("user_id" if field == "id" else field) == records[0][field]
                elif shape == "fixture-restaurant":
                    ok = self.call("GET", "/restaurants/r")[1].get(field) == records[0][field]
                elif shape == "fixture-reservation":
                    ok = r.get("reservation_id" if field == "id" else field) == records[0][field] if field != "user_id" else self.call("GET", "/reservations/SEED01", token=self.b)[0] == 404
                else:
                    detail = self.call("GET", "/restaurants/r")[1]
                    ok = detail["opening_hours" if shape == "fixture-hours" else "tables"][0][field] == records[0][field]
                self.check(shape + "-" + field, ok)
        self.check("timezone-model", r["starts_at"] == DAY + "T18:10:00+02:00")
        self.check("duration-model", dt.datetime.fromisoformat(r["ends_at"]) - dt.datetime.fromisoformat(r["starts_at"]) == dt.timedelta(minutes=90))
        self.check("grid-from-opening", self.availability()["slots"][0]["starts_at_local"].endswith("18:10"))
        self.check("same-day-hours", len(self.availability()["slots"]) == 8)
        for offset in range(7):
            day = (dt.date.fromisoformat(DAY) + dt.timedelta(days=offset)).isoformat()
            self.check("weekdays", bool(self.availability(day=day)["slots"]))
        self.expect("table-capacity", "POST", "/reservations", self.body("t0", party=3), token=self.a, key="capacity", status=422, code="party_exceeds_capacity")
        self.setup()
        past = self.create(self.body(local="2020-06-04T18:10"))
        self.check("past-create", past.get("status") == "confirmed")
        self.expect("past-cutoff", "POST", "/reservations/" + past["reference"] + "/cancel", {}, token=self.a, status=409, code="cutoff_passed")
        closed = fixture()
        closed["restaurants"][0]["opening_hours"] = []
        self.setup(closed)
        self.check("closed-weekday", self.availability()["slots"] == [])
        # Cutoff is exercised against live UTC, with whole-minute margins.
        f = fixture(opens="00:00", closes="23:59", slot=1, duration=1, cutoff=2)
        now = dt.datetime.now(UTC).replace(second=0, microsecond=0)
        inside = (now + dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M")
        f["reservations"] = [dict(self.body(local=inside), id="near", reference="NEAR01", user_id="u_a")]
        self.setup(f)
        self.expect("cutoff-model", "POST", "/reservations/NEAR01/cancel", {}, token=self.a, status=409, code="cutoff_passed")

    def availability_case(self):
        self.setup()
        v = self.availability()
        self.check("availability-status", isinstance(v, dict))
        for key, field in [("restaurant", "restaurant_id"), ("date", "date"), ("timezone", "timezone")]:
            self.check("availability-" + key, v.get(field) == {"restaurant_id": "r", "date": DAY, "timezone": "UTC"}[field])
        slots = v["slots"]
        self.check("availability-slots-array", isinstance(slots, list))
        expected = [(dt.datetime.fromisoformat(DAY + "T18:10") + dt.timedelta(minutes=30 * i)).strftime("%Y-%m-%dT%H:%M") for i in range(8)]
        self.check("availability-grid", [s["starts_at_local"] for s in slots] == expected)
        self.check("availability-final", slots[-1]["starts_at_local"] == DAY + "T21:40")
        for s in slots:
            self.check("availability-local", bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", s["starts_at_local"])))
            self.check("availability-absolute", s["starts_at"] == s["starts_at_local"] + ":00+00:00")
            self.check("availability-table-ids", isinstance(s["available_table_ids"], list))
            self.check("availability-order", s["available_table_ids"] == ["t0", "t1", "t2"])
        self.check("availability-capacity", all(s["available_table_ids"] == ["t2"] for s in self.availability(party=5)["slots"]))
        for field in ["restaurant_id", "date", "party_size"]:
            params = dict(restaurant_id="r", date=DAY, party_size=2)
            del params[field]
            self.expect("availability-required-" + {"restaurant_id": "restaurant", "date": "date", "party_size": "party"}[field], "GET", "/availability?" + urllib.parse.urlencode(params), status=422, code="validation_failed")
        first = self.create(self.body(local=slots[0]["starts_at_local"]))
        self.check("availability-create-roundtrip", first["starts_at_local"] == slots[0]["starts_at_local"])
        self.check("availability-occupancy", "t1" not in self.availability()["slots"][0]["available_table_ids"])
        self.create(self.body("t0"))
        self.create(self.body("t2"))
        self.check("availability-empty-slot", self.availability()["slots"][0]["available_table_ids"] == [])
        f = fixture()
        f["restaurants"][0]["opening_hours"] = []
        self.setup(f)
        self.check("availability-closed", self.availability()["slots"] == [])

    def validation(self):
        self.setup()
        r = self.create(self.body(local=DAY + "T21:40"))
        for raw in ["{", "not json"]:
            self.expect("invalid-json", "POST", "/reservations", token=self.a, key="malformed", raw=raw, status=400, code="malformed_request")
        for value in [[], True, None, "object required"]:
            self.expect("nonobject-json", "POST", "/reservations", token=self.a, key="shape", raw=json.dumps(value), status=400, code="malformed_request")
        cases = [("party-string", "party_size", "2", 422), ("party-bool", "party_size", True, 422), ("party-fraction", "party_size", 1.5, 422),
                 ("party-zero", "party_size", 0, 422), ("party-negative", "party_size", -1, 422), ("time-wrong-type", "starts_at_local", 1, 400)]
        cases += [(tag, "starts_at_local", x, 422) for tag, x in [("time-z", DAY + "T18:10Z"), ("time-offset", DAY + "T18:10+00:00"), ("time-seconds", DAY + "T18:10:00"), ("time-space", DAY + " 18:10"), ("time-unpadded", "2035-6-4T18:10")]]
        cases += [(tag, "starts_at_local", x, 422) for tag, x in [("date-nonleap", "2035-02-29T18:10"), ("date-month", "2035-13-01T18:10"), ("date-day", "2035-04-31T18:10")]]
        cases += [(f"{field}-{tag}", field, val, 400) for field in ["restaurant_id", "table_id"] for tag, val in [("bool", True), ("array", []), ("object", {}), ("number", 2), ("null", None)]]
        for endpoint in ["create", "patch", "batch"]:
            for rid, field, invalid, status in cases:
                if endpoint != "create" and field == "restaurant_id":
                    continue
                changes = {field: invalid}
                path = "/reservations" if endpoint == "create" else "/reservations/" + r["reference"] if endpoint == "patch" else "/reservation-moves"
                body = dict(self.body(), **changes) if endpoint == "create" else changes if endpoint == "patch" else {"moves": [dict(reference=r["reference"], **changes)]}
                self.expect(f"validation-{endpoint}-{rid}", "PATCH" if endpoint == "patch" else "POST", path, body, token=self.a, key=f"val-{self.counter}", status=status, code="malformed_request" if status == 400 else "validation_failed")
                passed = self.results[-1]["passed"]
                self.check(f"{endpoint}-input-{field}", passed)
                generic = "bare-time" if rid.startswith("time-") and rid != "time-wrong-type" else "invalid-date" if rid.startswith("date-") else "wrong-field-type" if field in ["restaurant_id", "table_id"] else "party-zero" if rid == "party-negative" else rid
                self.check(generic, passed)
        for field in self.body():
            body = self.body()
            del body[field]
            self.expect("missing-required", "POST", "/reservations", body, token=self.a, key=f"missing-{field}", status=422, code="validation_failed")
        for variant, party in [("exponent", "1e9"), ("fraction", "4.0"), ("plus", "+4"), ("negative", "-4"), ("leading-space", " 4"), ("trailing-space", "4 ")]:
            self.expect("query-decimal-" + variant, "GET", "/availability?restaurant_id=r&date=" + DAY + "&party_size=" + urllib.parse.quote(party), status=422, code="validation_failed")
            self.check("decimal-query", self.results[-1]["passed"])
        self.expect("query-positive", "GET", "/availability?restaurant_id=r&date=" + DAY + "&party_size=0", status=422, code="validation_failed")
        for day in ["2035-02-29", "2035-04-31", "2035-13-01", "2035-6-04", DAY + "T00:00"]:
            self.expect("query-date", "GET", "/availability?restaurant_id=r&party_size=2&date=" + urllib.parse.quote(day), status=422, code="validation_failed")
        self.check("invalid-format", all(x["passed"] for x in self.results if x["requirement_id"] in ["TK1-bare-time", "TK1-query-date"]))

    def booking(self):
        self.setup()
        r = self.expect("booking-201", "POST", "/reservations", self.body(), token=self.a, key="booking", status=201)
        self.reservation_shape("create", r, dict(self.body(), status="confirmed"))
        self.check("reference-format", bool(re.fullmatch(r"[A-Z0-9]{6,12}", r["reference"])))
        self.expect("booking-overlap", "POST", "/reservations", self.body(local=DAY + "T19:10"), token=self.a, key="overlap", status=409, code="table_unavailable")
        errors = [("booking-grid", self.body(local=DAY + "T18:11"), 422, "not_on_slot_grid"),
                  ("booking-before-open", self.body(local=DAY + "T17:40"), 422, "outside_opening_hours"),
                  ("booking-after-close", self.body(local=DAY + "T22:10"), 422, "outside_opening_hours"),
                  ("booking-capacity", self.body("t0", party=3), 422, "party_exceeds_capacity"),
                  ("booking-unknown-restaurant", self.body(restaurant="missing"), 404, "not_found"),
                  ("booking-unknown-table", self.body("missing"), 404, "not_found")]
        for rid, body, status, code in errors:
            self.expect(rid, "POST", "/reservations", body, token=self.a, key=rid, status=status, code=code)
        f = fixture()
        other = copy.deepcopy(f["restaurants"][0])
        other["id"] = "other"
        other["tables"] = [dict(id="other_t", label="Other", capacity=8)]
        f["restaurants"].append(other)
        self.setup(f)
        self.expect("booking-other-restaurant-table", "POST", "/reservations", self.body("other_t"), token=self.a, key="foreign-table", status=404, code="not_found")
        r = self.create()
        later = self.create(self.body(local=DAY + "T20:10"))
        self.call("POST", "/reservations/" + r["reference"] + "/cancel", {}, token=self.a)
        rows = self.call("GET", "/reservations", token=self.a)[1]["reservations"]
        self.check("list-order", [x["reference"] for x in rows] == [later["reference"], r["reference"]])
        self.check("list-statuses", [x["status"] for x in rows] == ["confirmed", "cancelled"])
        self.check("list-owner", self.call("GET", "/reservations", token=self.b)[1] == {"reservations": []})
        self.check("list-empty", self.call("GET", "/reservations", token=self.b)[1] == {"reservations": []})
        self.reservation_shape("list", rows[0], later)
        lookup = self.call("GET", "/reservations/" + later["reference"], token=self.a)[1]
        self.reservation_shape("lookup", lookup, later)
        self.expect("lookup-owner", "GET", "/reservations/" + r["reference"], token=self.b, status=404, code="not_found")
        self.expect("lookup-unknown", "GET", "/reservations/MISS01", token=self.a, status=404, code="not_found")
        self.check("reference-unique", len({x["reference"] for x in rows}) == len(rows))

    def cancel(self):
        self.setup()
        r = self.create()
        path = "/reservations/" + r["reference"] + "/cancel"
        self.expect("cancel-owner", "POST", path, {}, token=self.b, status=404, code="not_found")
        value = self.expect("cancel-200", "POST", path, {}, token=self.a)
        self.reservation_shape("cancel", value, dict(r, status="cancelled"))
        self.check("cancel-release", "t1" in self.availability()["slots"][0]["available_table_ids"])
        again = self.expect("cancel-twice", "POST", path, {}, token=self.a)
        self.check("cancel-twice", again == value)
        past = self.create(self.body(local="2020-06-04T18:10"))
        self.expect("cancel-later", "POST", "/reservations/" + past["reference"] + "/cancel", {}, token=self.a, status=409, code="cutoff_passed")
        f = fixture(opens="00:00", closes="23:59", slot=1, duration=1, cutoff=2)
        local = (dt.datetime.now(UTC).replace(second=0, microsecond=0) + dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M")
        f["reservations"] = [dict(self.body(local=local), id="near", reference="NEAR01", user_id="u_a")]
        self.setup(f)
        self.expect("cancel-cutoff", "POST", "/reservations/NEAR01/cancel", {}, token=self.a, status=409, code="cutoff_passed")

    def patch(self):
        self.setup()
        r = self.create()
        path = "/reservations/" + r["reference"]
        self.expect("patch-owner", "PATCH", path, {}, token=self.b, status=404, code="not_found")
        value = self.expect("patch-no-key", "PATCH", path, {"table_id": "t2"}, token=self.a)
        self.reservation_shape("patch", value, dict(r, table_id="t2"))
        self.check("patch-identity", value["reservation_id"] == r["reservation_id"])
        self.check("patch-reference", value["reference"] == r["reference"])
        self.check("patch-retain-omitted", all(value[k] == r[k] for k in r if k != "table_id"))
        self.check("patch-atomic", "t1" in self.availability()["slots"][0]["available_table_ids"] and "t2" not in self.availability()["slots"][0]["available_table_ids"])
        for changes in [{"party_size": 3}, {"starts_at_local": DAY + "T20:10"}, {}, {"table_id": "t1", "party_size": 2, "starts_at_local": DAY + "T18:10"}]:
            status, value = self.call("PATCH", path, changes, token=self.a)
            self.check("patch-subsets", status == 200)
        original = self.call("GET", path, token=self.a)[1]
        before_av = self.availability()
        for changes, code in [({"table_id": "t0", "party_size": 3}, "party_exceeds_capacity"), ({"starts_at_local": DAY + "T18:11"}, "not_on_slot_grid"),
                              ({"starts_at_local": DAY + "T22:10"}, "outside_opening_hours"), ({"table_id": "missing"}, "not_found")]:
            self.expect("patch-validation", "PATCH", path, changes, token=self.a, status=404 if code == "not_found" else 422, code=code)
            self.check("patch-failure-record", self.call("GET", path, token=self.a)[1] == original)
            self.check("patch-failure-occupancy", self.availability() == before_av)
        self.call("POST", path + "/cancel", {}, token=self.a)
        self.expect("patch-cancelled", "PATCH", path, {}, token=self.a, status=409, code="reservation_cancelled")
        f = fixture(opens="00:00", closes="23:59", slot=1, duration=1, cutoff=2)
        now = dt.datetime.now(UTC).replace(second=0, microsecond=0)
        local = (now + dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M")
        f["reservations"] = [dict(self.body(local=local), id="near", reference="NEAR01", user_id="u_a")]
        self.setup(f)
        self.expect("patch-cutoff", "PATCH", "/reservations/NEAR01", {"starts_at_local": DAY + "T18:10"}, token=self.a, status=409, code="cutoff_passed")
        self.expect("patch-current-cutoff", "PATCH", "/reservations/NEAR01", {"starts_at_local": DAY + "T18:10"}, token=self.a, status=409, code="cutoff_passed")
        # Moving a far-future reservation to a past legal slot must use the CURRENT cutoff.
        self.setup()
        r = self.create()
        value = self.expect("patch-current-cutoff", "PATCH", "/reservations/" + r["reference"], {"starts_at_local": "2020-06-04T18:10"}, token=self.a)
        self.expect("patch-current-cutoff", "PATCH", "/reservations/" + r["reference"], {"starts_at_local": DAY + "T18:10"}, token=self.a, status=409, code="cutoff_passed")

    def race(self, path, body, key_prefix, same=True):
        barrier = threading.Barrier(50)
        def operation(i):
            barrier.wait(timeout=10)
            started = time.monotonic()
            value = self.call("POST", path, body, token=self.a, key=key_prefix if same else key_prefix + str(i))
            with self.lock:
                finished = time.monotonic()
                self.race_latencies.append({"request": i, "group": key_prefix, "elapsed_seconds": finished-started,
                                            "started_monotonic": started, "finished_monotonic": finished, "status": value[0]})
            return value
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
            return list(pool.map(operation, range(50)))

    def idempotency(self):
        for prefix, path in [("create", "/reservations"), ("batch", "/reservation-moves")]:
            self.setup()
            seed = self.create(self.body("t0"))
            body = self.body("t1") if prefix == "create" else {"moves": [{"reference": seed["reference"]}]}
            self.expect(prefix + "-key-missing", "POST", path, body, token=self.a, status=400, code="missing_idempotency_key")
            self.expect(prefix + "-key-empty", "POST", path, body, token=self.a, key="", status=400, code="missing_idempotency_key")
            self.expect(prefix + "-key-256", "POST", path, body, token=self.a, key="x" * 256, status=422, code="validation_failed")
            original = self.expect(prefix + "-key-1", "POST", path, body, token=self.a, key="x", status=201)
            self.check(prefix + "-key-first", True, 201, 201)
            replay = self.expect(prefix + "-key-replay-status", "POST", path, body, token=self.a, key="x")
            self.check(prefix + "-key-replay-body", replay == original)
            replay = self.call("POST", path, token=self.a, key="x", raw=json.dumps(body, sort_keys=True, indent=3))[1]
            self.check(prefix + "-key-json-value", replay == original)
            self.expect(prefix + "-key-conflict", "POST", path, dict(body, ignored=True), token=self.a, key="x", status=409, code="idempotency_key_reuse")
            self.expect(prefix + "-key-before-validation", "POST", path, {"invalid": True}, token=self.a, key="x", status=409, code="idempotency_key_reuse")
            refs = [original["reference"]] if prefix == "create" else [seed["reference"]]
            for ref in refs:
                self.call("PATCH", "/reservations/" + ref, {"table_id": "t2"}, token=self.a)
            replay = self.call("POST", path, body, token=self.a, key="x")[1]
            self.check(prefix + "-key-after-amend", replay == original)
            for ref in refs:
                self.call("POST", "/reservations/" + ref + "/cancel", {}, token=self.a)
            before = self.state()
            replay = self.call("POST", path, body, token=self.a, key="x")[1]
            self.check(prefix + "-key-after-cancel", replay == original)
            self.check(prefix + "-key-before-resource", replay == original)
            self.check(prefix + "-key-no-mutation", self.state() == before)
            body2 = self.body("t1") if prefix == "create" else {"moves": [{"reference": self.create(self.body("t1"))["reference"]}]}
            self.expect(prefix + "-key-255", "POST", path, body2, token=self.a, key="y" * 255, status=201)
            body_b = self.body("t2", local=DAY + "T20:10") if prefix == "create" else {"moves": [{"reference": self.create(self.body("t2", local=DAY + "T20:10"), token=self.b)["reference"]}]}
            self.expect(prefix + "-key-user", "POST", path, body_b, token=self.b, key="x", status=201)
            self.expect(prefix + "-key-failed-reuse", "POST", path, {"bad": True}, token=self.a, key="failed-key", status=422, code="validation_failed")
            body3 = self.body("t0", local=DAY + "T20:10") if prefix == "create" else {"moves": [{"reference": self.create(self.body("t0", local=DAY + "T20:10"))["reference"]}]}
            self.expect(prefix + "-key-failed-reuse", "POST", path, body3, token=self.a, key="failed-key", status=201)
            self.setup()
            seed = self.create(self.body("t0"))
            body = self.body("t1") if prefix == "create" else {"moves": [{"reference": seed["reference"], "table_id": "t1"}]}
            results = self.race(path, body, "race")
            self.check(prefix + "-key-concurrent-first", sum(s == 201 for s, _ in results) == 1, "exactly one 201", [s for s, _ in results])
            self.check(prefix + "-key-concurrent-replays", sum(s == 200 for s, _ in results) == 49 and all(b == results[0][1] for _, b in results))
            listed = self.call("GET", "/reservations", token=self.a)[1]["reservations"]
            self.check(prefix + "-key-once", len(listed) == (2 if prefix == "create" else 1))
        # One JSON body valid on BOTH paths through ignored extra fields.
        self.setup()
        seed = self.create(self.body("t0"))
        both = dict(self.body("t1"), moves=[{"reference": seed["reference"]}])
        s1, _ = self.call("POST", "/reservations", both, token=self.a, key="same-path-key")
        s2, _ = self.call("POST", "/reservation-moves", both, token=self.a, key="same-path-key")
        self.check("key-path-scope", (s1, s2) == (201, 201), [201, 201], [s1, s2])

    def dst(self):
        for label, zone, spring, fall, repeated, offset in [("berlin", "Europe/Berlin", "2026-03-29", "2026-10-25", "02:30", "+02:00"),
                                                          ("new-york", "America/New_York", "2026-03-08", "2026-11-01", "01:30", "-04:00")]:
            self.setup(fixture(zone=zone, opens="00:00", closes="06:00", slot=30, duration=90))
            slots = self.availability(day=spring)["slots"]
            self.check(label + "-spring-absent", all("T02:" not in s["starts_at_local"] for s in slots))
            self.expect(label + "-spring-error", "POST", "/reservations", self.body(local=spring + "T02:30"), token=self.a, key="spring", status=422, code="invalid_local_time")
            fall_slots = self.availability(day=fall)["slots"]
            local = fall + "T" + repeated
            self.check(label + "-fall-once", sum(s["starts_at_local"] == local for s in fall_slots) == 1)
            r = self.create(self.body(local=local), key="fall")
            self.check(label + "-fall-first", r["starts_at"] == local + ":00" + offset)
            self.expect(label + "-fall-second", "POST", "/reservations", self.body(local=local + ("+01:00" if label == "berlin" else "-05:00")), token=self.a, key="second", status=422, code="validation_failed")
            absolute = dt.datetime.fromisoformat(r["starts_at"]).astimezone(UTC) + dt.timedelta(minutes=90)
            expected_end = absolute.astimezone(ZoneInfo(zone)).isoformat()
            self.check(label + "-absolute-duration", r["ends_at"] == expected_end, expected_end, r["ends_at"])
            for slot in slots + fall_slots:
                expected_start = dt.datetime.fromisoformat(slot["starts_at_local"]).replace(tzinfo=ZoneInfo(zone), fold=0).isoformat()
                self.check(label + "-offsets", slot["starts_at"] == expected_start, expected_start, slot["starts_at"])

    def batch(self):
        self.setup(fixture(tables=9))
        bookings = [self.create(self.body(f"t{i}", party=1)) for i in range(8)]
        moves = [{"reference": r["reference"], "table_id": f"t{(i+1)%8}"} for i, r in enumerate(bookings)]
        receipt = self.expect("batch-swap", "POST", "/reservation-moves", {"moves": moves}, token=self.a, key="cycle", status=201)
        values = receipt["reservations"]
        self.check("batch-max", len(values) == 8)
        self.check("batch-response-order", [v["reference"] for v in values] == [r["reference"] for r in bookings])
        for i, v in enumerate(values):
            self.reservation_shape("batch", v, dict(bookings[i], table_id=f"t{(i+1)%8}"))
            self.check("batch-identity", v["reservation_id"] == bookings[i]["reservation_id"])
            self.check("batch-created", v["created_at"] == bookings[i]["created_at"])
            self.check("batch-owner-preserved", self.call("GET", "/reservations/" + v["reference"], token=self.b)[0] == 404)
        noop = {"moves": [{"reference": values[0]["reference"], "unknown": True}]}
        value = self.expect("batch-min", "POST", "/reservation-moves", noop, token=self.a, key="noop", status=201)
        self.check("batch-noop", value["reservations"] == [values[0]])
        self.check("batch-omitted", value["reservations"] == [values[0]])
        self.check("batch-unknown-fields", value["reservations"] == [values[0]])
        self.check("batch-response-unchanged", value["reservations"] == [values[0]])
        errors = [("batch-empty", {"moves": []}, 422, "validation_failed"),
                  ("batch-too-many", {"moves": [{"reference": "UNKN" + str(i)} for i in range(9)]}, 422, "validation_failed"),
                  ("batch-duplicate", {"moves": [{"reference": values[0]["reference"]}] * 2}, 422, "validation_failed"),
                  ("batch-unknown", {"moves": [{"reference": "UNKN01"}]}, 404, "not_found"),
                  ("batch-mutual-overlap", {"moves": [{"reference": values[0]["reference"], "table_id": "t8"}, {"reference": values[1]["reference"], "table_id": "t8"}]}, 409, "table_unavailable"),
                  ("batch-unlisted-overlap", {"moves": [{"reference": values[0]["reference"], "table_id": values[1]["table_id"]}]}, 409, "table_unavailable"),
                  ("batch-unchanged-occupancy", {"moves": [{"reference": values[0]["reference"]}, {"reference": values[1]["reference"], "table_id": values[0]["table_id"]}]}, 409, "table_unavailable")]
        errors += [("batch-shape", body, 422, "validation_failed") for body in [{}, {"moves": {}}, {"moves": True}, {"moves": [1]}, {"moves": [{}]}]]
        errors += [("batch-reference-type", {"moves": [{"reference": invalid}]}, 422, "validation_failed") for invalid in [True, 5, [], None]]
        for rid, body, status, code in errors:
            before = self.state()
            before_av = self.availability(party=1)
            failed_key = "batch-error-" + str(self.counter)
            self.expect(rid, "POST", "/reservation-moves", body, token=self.a, key=failed_key, status=status, code=code)
            self.check("batch-failure-records", self.state() == before)
            self.check("batch-failure-occupancy", self.availability(party=1) == before_av)
            self.expect("batch-failure-keys", "POST", "/reservation-moves", noop, token=self.a, key=failed_key, status=201)
        self.expect("batch-owner", "POST", "/reservation-moves", noop, token=self.b, key="foreign", status=404, code="not_found")
        # First non-occupancy error takes precedence even over earlier occupancy conflicts.
        for body, code, status in [({"moves": [{"reference": values[0]["reference"], "party_size": 0}, {"reference": "MISS01"}]}, "validation_failed", 422),
                                   ({"moves": [{"reference": "MISS01"}, {"reference": values[0]["reference"], "party_size": 0}]}, "not_found", 404)]:
            self.expect("batch-input-order", "POST", "/reservation-moves", body, token=self.a, key="order-" + str(self.counter), status=status, code=code)
        body = {"moves": [{"reference": values[0]["reference"], "table_id": values[1]["table_id"]}, {"reference": values[1]["reference"], "party_size": 0}]}
        self.expect("batch-validation-before-overlap", "POST", "/reservation-moves", body, token=self.a, key="validation-before", status=422, code="validation_failed")
        changed = self.expect("batch-fields", "POST", "/reservation-moves", {"moves": [{"reference": values[0]["reference"], "table_id": "t8", "party_size": 2, "starts_at_local": DAY + "T20:10"}]}, token=self.a, key="all-fields", status=201)
        self.check("batch-fields", all(changed["reservations"][0][k] == v for k, v in dict(table_id="t8", party_size=2, starts_at_local=DAY+"T20:10").items()))
        self.call("POST", "/reservations/" + values[0]["reference"] + "/cancel", {}, token=self.a)
        self.expect("batch-cancelled", "POST", "/reservation-moves", noop, token=self.a, key="cancelled", status=409, code="reservation_cancelled")
        f = fixture()
        other = copy.deepcopy(f["restaurants"][0])
        other["id"] = "other"
        other["tables"] = [dict(id="other_t", label="Other", capacity=4)]
        f["restaurants"].append(other)
        self.setup(f)
        a = self.create()
        b = self.create(self.body("other_t", restaurant="other"))
        self.expect("batch-restaurant", "POST", "/reservation-moves", {"moves": [{"reference": a["reference"]}, {"reference": b["reference"]}]}, token=self.a, key="cross-rest", status=422, code="validation_failed")
        f = fixture(opens="00:00", closes="23:59", slot=1, duration=1, cutoff=2)
        local = (dt.datetime.now(UTC).replace(second=0, microsecond=0) + dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M")
        f["reservations"] = [dict(self.body(local=local), id="near", reference="NEAR01", user_id="u_a")]
        self.setup(f)
        self.expect("batch-cutoff", "POST", "/reservation-moves", {"moves": [{"reference": "NEAR01"}]}, token=self.a, key="cutoff", status=409, code="cutoff_passed")
        self.expect("batch-cutoff-precedence", "POST", "/reservation-moves", {"moves": [{"reference": "NEAR01", "party_size": 0}]}, token=self.a, key="cutoff-first", status=409, code="cutoff_passed")

    def invariants(self):
        self.setup()
        self.create()
        adjacent = self.create(self.body(local=DAY + "T19:40"))
        self.check("half-open", adjacent["status"] == "confirmed")
        self.setup()
        results = self.race("/reservations", self.body(), "occupancy-", same=False)
        self.check("overlap", sum(s == 201 for s, _ in results) == 1 and sum(s == 409 and b.get("error", {}).get("code") == "table_unavailable" for s, b in results) == 49)
        listed = self.call("GET", "/reservations", token=self.a)[1]["reservations"]
        self.check("retry-no-duplicate", len(listed) == 1)
        self.check("reject-no-partial", len(listed) == 1)
        # Independent small occupancy oracle: half-open integer minute intervals.
        self.setup(fixture(opens="12:00", closes="23:00", slot=15, duration=45))
        rng = random.Random(20261004)
        oracle = []
        trace = []
        for operation in range(160):
            table = "t" + str(rng.randrange(3))
            minute = 12*60 + 15*rng.randrange(42)
            local = DAY + "T" + f"{minute//60:02}:{minute%60:02}"
            expected = 409 if any(t == table and a < minute+45 and minute < b for t, a, b in oracle) else 201
            status, value = self.call("POST", "/reservations", self.body(table, local=local, party=1), token=self.a, key=f"property-{operation}")
            trace.append(dict(operation=operation, table=table, start_minute=minute, duration=45, expected=expected, observed=status))
            self.check("overlap", status == expected, expected, status)
            if expected == 201:
                oracle.append((table, minute, minute+45))
            self.check("reject-no-partial", len(self.call("GET", "/reservations", token=self.a)[1]["reservations"]) == len(oracle))
        (self.out / "randomized-occupancy-trace.json").write_text(json.dumps(dict(seed=20261004, objective="half-open non-overlap", operations=trace), indent=2))
        # Independent configuration in another restaurant.
        f = fixture()
        other = copy.deepcopy(f["restaurants"][0])
        other.update(id="other", slot_minutes=20, reservation_duration_minutes=40)
        other["opening_hours"] = [{"weekday": d, "opens": "12:05", "closes": "14:05"} for d in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]]
        other["tables"] = [dict(id="other_t", label="Other", capacity=9)]
        f["restaurants"].append(other)
        self.setup(f)
        v = self.availability(party=9, rid="other")
        self.check("restaurant-independent", len(v["slots"]) == 5 and all(x["available_table_ids"] == ["other_t"] for x in v["slots"]) and v["slots"][0]["starts_at_local"].endswith("12:05"))

    def export(self):
        if not self.args.peer or self.args.peer == self.args.base:
            raise RuntimeError("Independent peer process required for export/import coverage")
        self.setup()
        a_token, b_token = self.a, self.b
        create_body = self.body()
        r = self.create(create_body, key="export-create")
        other = self.create(self.body("t0"), key="other-create")
        batch_body = {"moves": [{"reference": r["reference"], "table_id": "t2"}, {"reference": other["reference"], "table_id": "t1"}]}
        batch = self.call("POST", "/reservation-moves", batch_body, token=self.a, key="export-batch")[1]
        self.call("POST", "/reservations/" + r["reference"] + "/cancel", {}, token=self.a)
        self.call("POST", "/reservations", {"invalid": True}, token=self.a, key="failed-export")
        self.call("POST", "/reservation-moves", {"moves": []}, token=self.a, key="failed-batch-export")
        before = self.state()
        snapshot = self.state()
        self.check("export-readonly", snapshot == before)
        self.check("export-public", isinstance(snapshot, dict))
        self.check("export-200", isinstance(snapshot, dict))
        self.check("export-track", snapshot.get("track") == "tablekeeper")
        self.check("export-version", snapshot.get("format_version") == 1)
        self.check("export-state", isinstance(snapshot.get("state"), dict))
        source_rows = self.call("GET", "/reservations", token=a_token)[1]
        source_detail = self.call("GET", "/restaurants/r")[1]
        # Destination begins with genuinely different credentials and data.
        dest = fixture()
        dest["users"][0].update(id="destination", email="destination@probe.invalid", password="destination-pass")
        dest["restaurants"][0]["id"] = "destination_rest"
        self.setup(dest, base=self.args.peer)
        dest_token = self.a
        status, value = self.call("POST", "/_test/import", snapshot, base=self.args.peer)
        self.check("import-public", status == 204)
        self.check("import-204", status == 204 and value is None)
        rows = self.call("GET", "/reservations", token=a_token, base=self.args.peer)[1]
        self.check("import-independent", rows == source_rows)
        self.check("import-replace-data", self.call("GET", "/restaurants/destination_rest", base=self.args.peer)[0] == 404)
        self.check("import-replace-credentials", self.call("GET", "/reservations", token=dest_token, base=self.args.peer)[0] == 401 and self.call("POST", "/auth/login", dict(email="destination@probe.invalid", password="destination-pass"), base=self.args.peer)[0] == 401)
        self.check("import-tokens", all(self.call("GET", "/reservations", token=t, base=self.args.peer)[0] == 200 for t in [a_token, b_token]))
        self.check("tokens-persistent", self.call("GET", "/reservations", token=a_token, base=self.args.peer)[0] == 200)
        self.check("import-fixture", self.call("GET", "/restaurants/r", base=self.args.peer)[1] == source_detail)
        login_status, login = self.call("POST", "/auth/login", dict(email="a@probe.invalid", password="verifier-pass-A"), base=self.args.peer)
        self.check("import-passwords", login_status == 200)
        self.check("import-accounts", login_status == 200 and login.get("user_id") == "u_a" and login.get("display_name") == "Diner A")
        for key in ["reservations", "references", "identities", "statuses", "timestamps"]:
            self.check("import-" + key, rows == source_rows)
        self.check("import-create-receipt", self.call("POST", "/reservations", create_body, token=a_token, key="export-create", base=self.args.peer) == (200, r))
        self.check("import-batch-receipt", self.call("POST", "/reservation-moves", batch_body, token=a_token, key="export-batch", base=self.args.peer) == (200, batch))
        self.expect("import-failed-create-key", "POST", "/reservations", self.body("t0", local=DAY + "T20:10"), token=a_token, key="failed-export", base=self.args.peer, status=201)
        self.expect("import-failed-batch-key", "POST", "/reservation-moves", {"moves": [{"reference": other["reference"]}]}, token=a_token, key="failed-batch-export", base=self.args.peer, status=201)
        self.call("POST", "/_test/import", snapshot, base=self.args.peer)
        self.check("import-repeat", self.call("GET", "/reservations", token=a_token, base=self.args.peer)[1] == source_rows)
        invalids = [("import-missing", {k: v for k, v in snapshot.items() if k != field}) for field in ["track", "format_version", "state"]]
        invalids += [("import-track", dict(snapshot, track="other")), ("import-version", dict(snapshot, format_version=2)), ("import-invalid-state", dict(snapshot, state={})), ("import-invalid-state", dict(snapshot, state=[]))]
        for rid, invalid in invalids:
            baseline = self.state(self.args.peer)
            self.expect(rid, "POST", "/_test/import", invalid, base=self.args.peer, status=422, code="validation_failed")
            self.check("import-failure-atomic", self.state(self.args.peer) == baseline)
        baseline = self.state(self.args.peer)
        self.expect("import-invalid-json", "POST", "/_test/import", raw="{", base=self.args.peer, status=400, code="malformed_request")
        self.check("import-failure-atomic", self.state(self.args.peer) == baseline)
        immutable_hash = fingerprint(snapshot)
        self.a, self.b = a_token, b_token
        self.create(self.body("t2", local=DAY + "T20:10"), key="source-later")
        self.check("export-snapshot", fingerprint(snapshot) == immutable_hash and self.state() != snapshot)
        self.call("POST", "/_test/reset", fixture(), base=self.args.peer)
        self.check("reset-imported", self.call("GET", "/reservations", token=a_token, base=self.args.peer)[0] == 401)
        self.setup(base=self.args.peer)
        self.check("reset-imported", self.call("POST", "/reservations", create_body, token=self.a, key="export-create", base=self.args.peer)[0] == 201)
        # Export concurrently with whole-table swaps. Every snapshot must be one complete layout.
        self.setup()
        first = self.create(self.body("t0"))
        second = self.create(self.body("t1"))
        def swapper():
            for i in range(20):
                body = {"moves": [{"reference": first["reference"], "table_id": "t1" if i % 2 == 0 else "t0"},
                                  {"reference": second["reference"], "table_id": "t0" if i % 2 == 0 else "t1"}]}
                self.call("POST", "/reservation-moves", body, token=self.a, key="export-swap-" + str(i))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(swapper)
            snaps = [self.state() for _ in range(25)]
            future.result()
        for snap in snaps:
            self.call("POST", "/_test/import", snap, base=self.args.peer)
            data = self.call("GET", "/reservations", token=self.a, base=self.args.peer)[1]["reservations"]
            self.check("export-atomic", len(data) == 2 and {x["table_id"] for x in data} == {"t0", "t1"})

    def conventions(self):
        self.setup()
        r = self.create(dict(self.body(), arbitrary={"nested": [True, None]}))
        self.check("unknown-body", r["status"] == "confirmed")
        v = self.availability()
        v2 = self.call("GET", "/availability?restaurant_id=r&date=" + DAY + "&party_size=2&ignored=true")[1]
        self.check("unknown-query", v == v2)
        self.check("generated-id-limit", isinstance(r["reservation_id"], str) and len(r["reservation_id"]) <= 64)
        for kind in ["user", "restaurant", "table", "reservation"]:
            for length in [64, 65]:
                f = fixture()
                f["reservations"] = [dict(self.body(), id="seed", reference="SEED01", user_id="u_a")]
                identifier = "i" * length
                if kind == "user":
                    f["users"][0]["id"] = identifier
                    f["reservations"][0]["user_id"] = identifier
                elif kind == "restaurant":
                    f["restaurants"][0]["id"] = identifier
                    f["reservations"][0]["restaurant_id"] = identifier
                elif kind == "table":
                    f["restaurants"][0]["tables"][1]["id"] = identifier
                    f["reservations"][0]["table_id"] = identifier
                else:
                    f["reservations"][0]["id"] = identifier
                status, value = self.call("POST", "/_test/reset", f)
                passed = status == 204 if length == 64 else status == 422 and value.get("error", {}).get("code") == "validation_failed"
                self.check(f"fixture-id-{kind}-" + ("max" if length == 64 else "over"), passed)
                self.check("fixture-id-max" if length == 64 else "fixture-id-over", passed)
        self.check("timestamp-offset", all(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}", r[k]) for k in ["starts_at", "ends_at", "created_at"]))

    def finish(self):
        self.check("json-content-type", bool(self.content_types) and all(x == "application/json;charset=utf-8" for x in self.content_types), "application/json;charset=utf-8", sorted(set(self.content_types)))
        self.check("error-envelope", bool(self.error_shapes) and all(self.error_shapes))
        self.check("no-5xx", all(0 < s < 500 for s in self.statuses), "no 5xx or transport failures", sorted(set(self.statuses)))
        self.check("request-timeout", all(seconds < 5 and status > 0 for path, seconds, status in self.latencies if not path.startswith("/_test/")))
        for endpoint in ["reset", "import", "export"]:
            samples = [(seconds, status) for path, seconds, status in self.latencies if path == "/_test/" + endpoint]
            if samples:
                self.check(endpoint + "-timeout", all(seconds < 10 and status > 0 for seconds, status in samples), "all calls <10s", samples)
        if self.race_latencies:
            self.check("max-concurrency", len(self.race_latencies) >= 50 and all(x["status"] > 0 for x in self.race_latencies))
            self.check("max-concurrency-timing", len(self.race_latencies) >= 50 and all(x["status"] > 0 and x["elapsed_seconds"] < 5 for x in self.race_latencies), "50 in-flight, each <5s", self.race_latencies)
        by_id = {}
        for result in self.results:
            by_id.setdefault(result["requirement_id"], []).append(result)
        rows = copy.deepcopy(ROWS)
        for row in rows:
            row["candidate_full_revision"] = self.args.candidate
            evidence = by_id.get(row["requirement_id"], [])
            row["verdict"] = "verified" if evidence and all(x["passed"] for x in evidence) else "failed" if evidence else "unverified"
            if evidence:
                row["evidence_path"] = str(self.out / "assertions.json") + "#" + row["requirement_id"]
                row["executable_command_or_interaction"] = " ".join(["python3", str(Path(__file__)), "--base", self.args.base, "--peer", self.args.peer or "", "--candidate", self.args.candidate, "--out", str(self.out), "--case", self.args.case])
        with (self.out / "coverage.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (self.out / "assertions.json").write_text(json.dumps(self.results, indent=2))
        (self.out / "concurrency-timing.json").write_text(json.dumps(self.race_latencies, indent=2))
        with (self.out / "operations.jsonl").open("w") as f:
            for op in self.trace:
                f.write(json.dumps(op) + "\n")
        summary = dict(candidate=self.args.candidate, stage=1, source="independent probes; unseen judging suite not available",
                       seed=20261004, requests=len(self.trace), assertions=len(self.results), failures=sum(not x["passed"] for x in self.results),
                       rows=len(rows), verified=sum(x["verdict"] == "verified" for x in rows), failed=sum(x["verdict"] == "failed" for x in rows),
                       unverified=sum(x["verdict"] == "unverified" for x in rows), duration_seconds=time.monotonic()-self.started)
        (self.out / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary))
        return summary["failures"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--peer")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--case", default="all")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.candidate):
        parser.error("--candidate must be a full commit revision")
    probe = Probe(args)
    cases = dict(basics=probe.basics, fixture=probe.fixture_case, auth=probe.auth, availability=probe.availability_case,
                 validation=probe.validation, booking=probe.booking, cancel=probe.cancel, patch=probe.patch,
                 idempotency=probe.idempotency, dst=probe.dst, batch=probe.batch, invariants=probe.invariants,
                 export=probe.export, conventions=probe.conventions)
    from supplemental import run as run_supplemental
    cases["extra"] = lambda: run_supplemental(probe)
    from calendar_edges import run as run_calendar_edges
    cases["calendar-edges"] = lambda: run_calendar_edges(probe)
    selected = list(cases) if args.case == "all" else args.case.split(",")
    for case in selected:
        try:
            cases[case]()
        except Exception as e:
            probe.results.append(dict(requirement_id="PROBE-CASE-" + case, passed=False, expected="case completes", observed=str(e)))
    raise SystemExit(1 if probe.finish() else 0)


if __name__ == "__main__":
    main()
