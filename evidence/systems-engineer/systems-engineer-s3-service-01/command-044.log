"""Specification-derived builder diagnostics; independent acceptance is separate.

Run directly against core, or add --url http://127.0.0.1:18100 for HTTP.
No fixture password hashes, session tokens or complete exports are written to disk.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import random
import re
import subprocess
import sys
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

parser = argparse.ArgumentParser()
parser.add_argument("--url")
parser.add_argument("--destination-url")
parser.add_argument("--legacy-url")
parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=1)
args, unittest_args = parser.parse_known_args()
if not args.url or not args.destination_url:
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("tablekeeper_builder_core", root / f"stage-{args.stage}/core.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


class Client:
    def __init__(self, url=None, engine=None):
        self.url = url
        self.engine = (engine if engine is not None else module.Engine()) if url is None else None

    def request(self, method, path, body=None, headers=None):
        headers = headers or {}
        if self.engine:
            return self.engine.request(method, path, headers, body)
        encoded = None if body is None else json.dumps(body).encode()
        request = Request(self.url + path, data=encoded, method=method,
                          headers={"Content-Type": "application/json", **headers})
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None


def fixture(zone="Europe/Berlin", opening="18:00", closing="23:00", duration=90):
    return {"users": [
        {"id": "u_a", "email": "ada@example.test", "password": "fixture password", "display_name": "Ada"},
        {"id": "u_b", "email": "ben@example.test", "password": "fixture password", "display_name": "Ben"}],
        "restaurants": [{"id": "r", "name": "Fixture dining room", "timezone": zone,
            "slot_minutes": 30, "reservation_duration_minutes": duration, "cancellation_cutoff_minutes": 120,
            "opening_hours": [{"weekday": day, "opens": opening, "closes": closing}
                              for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
            "tables": [{"id": "a", "label": "Window", "capacity": 4},
                       {"id": "b", "label": "Garden", "capacity": 4}]}], "reservations": []}



def legacy_projection(value, schema):
    projected=json.loads(json.dumps(value))
    state=projected["state"]
    for field in ("policies","histories","history_origins","series","restaurant_revisions"):state.pop(field,None)
    state["schema"]=schema
    for restaurant in state["restaurants"]:restaurant.pop("manager_user_ids",None)
    for record in state["reservations"]:
        record.pop("revision",None);record.pop("accepted_terms",None)
    if schema==1:
        for receipt in state["receipts"]:receipt.pop("numeric_profile",None)
    return projected

def current_legacy(record, restaurant):
    return {**record,"table_ids":record.get("table_ids",[record.get("table_id")]),"revision":1,
      "accepted_terms":{"policy_version":0,**{k:restaurant[k] for k in ("slot_minutes","reservation_duration_minutes","cancellation_cutoff_minutes","opening_hours")},
        "capacities":{t["id"]:t["capacity"] for t in restaurant["tables"]}}}

class StageOne(unittest.TestCase):
    def setUp(self):
        self.client = Client(args.url)
        self.expect(self.client.request("POST", "/_test/reset", fixture()), 204)
        self.auth = self.login("ada@example.test")
        self.other_auth = self.login("ben@example.test")
        self.counter = 0

    def expect(self, response, status, code=None):
        self.assertEqual(response[0], status, response[1])
        if code:
            self.assertEqual(response[1]["error"]["code"], code)
        return response[1]

    def login(self, email):
        result = self.expect(self.client.request("POST", "/auth/login",
            {"email": email, "password": "fixture password"}), 200)
        return {"Authorization": "Bearer " + result["token"]}

    def body(self, table="a", start="2099-04-16T18:00", party=2):
        return {"restaurant_id": "r", "table_id": table, "starts_at_local": start, "party_size": party}

    def create(self, body=None, key=None, auth=None):
        self.counter += 1
        return self.client.request("POST", "/reservations", self.body() if body is None else body,
            {**(self.auth if auth is None else auth), "Idempotency-Key": key or f"builder-{self.counter}"})

    def exported(self):
        return self.expect(self.client.request("GET", "/_test/export"), 200)

    def test_auth_public_and_private(self):
        self.expect(self.client.request("GET", "/health"), 200)
        self.expect(self.client.request("GET", "/restaurants", headers={"Authorization": "invalid"}), 200)
        self.expect(self.client.request("GET", "/restaurants/r"), 200)
        self.expect(self.client.request("GET", "/reservations"), 401, "unauthenticated")
        self.expect(self.client.request("POST", "/auth/signup", {"email": "new@test", "password": "short",
            "display_name": "New"}), 422, "validation_failed")
        self.expect(self.client.request("POST", "/auth/signup", {"email": False, "password": "long password",
            "display_name": "New"}), 400, "malformed_request")
        self.expect(self.client.request("POST", "/auth/login", {"email": "absent@test", "password": "bad"}),
                    401, "unauthenticated")
        second_session = self.login("ada@example.test")
        record = self.expect(self.create(), 201)
        self.expect(self.client.request("GET", "/reservations/" + record["reference"], headers=second_session), 200)
        self.expect(self.client.request("GET", "/reservations/" + record["reference"], headers=self.other_auth),
                    404, "not_found")
        self.assertNotIn("user_id", record)
        state = self.exported()["state"]
        self.assertTrue(all("password" not in user for user in state["users"]))
        self.assertTrue(all(user["password_hash"]["algorithm"] == "scrypt" for user in state["users"]))

    def test_validation_and_failed_key_reuse(self):
        for party in (True, False, "2", 2.5, 0, -1, None):
            self.expect(self.create(self.body(party=party), key="reusable"), 422, "validation_failed")
        for value in ("2099-04-16T18:00Z", "2099-04-16T18:00:00", "2099-02-30T18:00", "not-time"):
            self.expect(self.create(self.body(start=value), key="reusable"), 422, "validation_failed")
        self.expect(self.create(self.body(table=42), key="reusable"), 400, "malformed_request")
        self.expect(self.create(self.body(start="2099-04-16T18:10"), key="reusable"), 422, "not_on_slot_grid")
        self.expect(self.create(self.body(start="2099-04-16T22:00"), key="reusable"), 422, "outside_opening_hours")
        self.expect(self.create(self.body(party=5), key="reusable"), 422, "party_exceeds_capacity")
        self.expect(self.create(self.body(table="absent"), key="reusable"), 404, "not_found")
        self.expect(self.client.request("POST", "/reservations", self.body(), self.auth), 400,
                    "missing_idempotency_key")
        self.expect(self.create(key="k" * 256), 422, "validation_failed")
        self.expect(self.create(key="reusable"), 201)
        for party in ("1e9", "4.0", "%2B4", "-1", "true", "0"):
            self.expect(self.client.request("GET", "/availability?restaurant_id=r&date=2099-04-16&party_size=" + party),
                        422, "validation_failed")
        self.expect(self.client.request("GET", "/availability?restaurant_id=r&party_size=2"), 422,
                    "validation_failed")

    def test_idempotency_and_snapshot_isolation(self):
        body = {**self.body(), "ignored": {"b": True, "a": [1, None]}}
        original = self.expect(self.create(body, "original"), 201)
        reordered = dict(reversed(list(body.items())))
        self.assertEqual(self.expect(self.create(reordered, "original"), 200), original)
        self.expect(self.create({**body, "party_size": False}, "original"), 409, "idempotency_key_reuse")
        self.expect(self.create({**body, "ignored": {"b": 1, "a": [1, None]}}, "original"), 409,
                    "idempotency_key_reuse")
        amended = self.expect(self.client.request("PATCH", "/reservations/" + original["reference"],
            {"table_id": "b"}, self.auth), 200)
        self.assertEqual(amended["reservation_id"], original["reservation_id"])
        self.expect(self.client.request("POST", "/reservations/" + original["reference"] + "/cancel",
                                       headers=self.auth), 200)
        self.assertEqual(self.expect(self.create(body, "original"), 200), original)
        moves = {"moves": [{"reference": original["reference"]}]}
        self.expect(self.client.request("POST", "/reservation-moves", moves,
            {**self.auth, "Idempotency-Key": "original"}), 409, "reservation_cancelled")
        second = self.expect(self.create(self.body(table="a"), "original", self.other_auth), 201)
        self.assertNotEqual(original["reference"], second["reference"])

    def test_50_identical_and_50_competing_requests(self):
        with ThreadPoolExecutor(max_workers=50) as pool:
            identical = list(pool.map(lambda _: self.create(key="concurrent"), range(50)))
        self.assertEqual([r[0] for r in identical].count(201), 1)
        self.assertEqual([r[0] for r in identical].count(200), 49)
        self.assertTrue(all(r[1] == identical[0][1] for r in identical))
        with ThreadPoolExecutor(max_workers=50) as pool:
            competing = list(pool.map(lambda n: self.create(self.body(table="b"), f"competition-{n}"), range(50)))
        self.assertEqual([r[0] for r in competing].count(201), 1)
        self.assertEqual([r[0] for r in competing].count(409), 49)
        records = self.expect(self.client.request("GET", "/reservations", headers=self.auth), 200)
        self.assertEqual(len(records["reservations"]), 2)

    def test_half_open_empty_and_cancel(self):
        first = self.expect(self.create(), 201)
        self.expect(self.create(self.body(start="2099-04-16T19:30")), 201)
        self.expect(self.create(self.body(start="2099-04-16T19:00")), 409, "table_unavailable")
        query = "/availability?restaurant_id=r&date=2099-04-16&party_size=2&ignored=yes"
        available = self.expect(self.client.request("GET", query), 200)
        self.assertEqual(available["slots"][0]["available_table_ids"], ["b"])
        self.expect(self.create(self.body(table="b")), 201)
        self.assertEqual(self.expect(self.client.request("GET", query), 200)["slots"][0]["available_table_ids"], [])
        cancelled = self.expect(self.client.request("POST", "/reservations/" + first["reference"] + "/cancel",
            headers=self.auth), 200)
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.expect(self.client.request("POST", "/reservations/" + first["reference"] + "/cancel",
            headers=self.auth), 200), cancelled)
        self.assertEqual(self.expect(self.client.request("GET", query), 200)["slots"][0]["available_table_ids"], ["a"])
        closed = fixture()
        closed["restaurants"][0]["opening_hours"] = []
        self.expect(self.client.request("POST", "/_test/reset", closed), 204)
        self.assertEqual(self.expect(self.client.request("GET", query), 200)["slots"], [])

    def test_batch_swaps_rollback_order_and_receipts(self):
        a = self.expect(self.create(), 201)
        b = self.expect(self.create(self.body(table="b")), 201)
        before = self.exported()
        self.expect(self.client.request("PATCH", "/reservations/" + a["reference"], {"table_id": "b"}, self.auth),
                    409, "table_unavailable")
        self.assertEqual(self.exported(), before)
        invalid = {"moves": [{"reference": a["reference"], "table_id": "b"},
                             {"reference": b["reference"], "party_size": 5}]}
        headers = {**self.auth, "Idempotency-Key": "swap"}
        self.expect(self.client.request("POST", "/reservation-moves", invalid, headers), 422,
                    "party_exceeds_capacity")
        self.assertEqual(self.exported(), before)
        swap = {"moves": [{"reference": a["reference"], "table_id": "b"},
                          {"reference": b["reference"], "table_id": "a"}]}
        saved = self.expect(self.client.request("POST", "/reservation-moves", swap, headers), 201)
        self.assertEqual([r["table_id"] for r in saved["reservations"]], ["b", "a"])
        no_op = {"moves": [{"reference": a["reference"]}, {"reference": b["reference"]}]}
        self.assertEqual(self.expect(self.client.request("POST", "/reservation-moves", no_op,
            {**self.auth, "Idempotency-Key": "noop"}), 201), saved)
        self.expect(self.client.request("POST", "/reservations/" + a["reference"] + "/cancel", headers=self.auth), 200)
        self.assertEqual(self.expect(self.client.request("POST", "/reservation-moves", swap, headers), 200), saved)
        self.expect(self.client.request("POST", "/reservation-moves", {"moves": [no_op["moves"][0]] * 2},
            {**self.auth, "Idempotency-Key": "duplicate"}), 422, "validation_failed")

    def test_cutoff_current_start_and_past_creation(self):
        past = self.expect(self.create(self.body(start="2001-01-01T18:00")), 201)
        self.expect(self.client.request("PATCH", "/reservations/" + past["reference"], {"table_id": 0}, self.auth),
                    409, "cutoff_passed")
        self.expect(self.client.request("POST", "/reservations/" + past["reference"] + "/cancel", headers=self.auth),
                    409, "cutoff_passed")
        future = self.expect(self.create(), 201)
        moved = self.expect(self.client.request("PATCH", "/reservations/" + future["reference"],
            {"starts_at_local": "2001-01-02T18:00"}, self.auth), 200)
        self.assertEqual(moved["reference"], future["reference"])
        self.expect(self.client.request("PATCH", "/reservations/" + future["reference"],
            {"starts_at_local": "2099-04-17T18:00"}, self.auth), 409, "cutoff_passed")

    def test_dst_both_zones(self):
        for zone, spring, fall, repeated, end in [
            ("Europe/Berlin", "2026-03-29", "2026-10-25", "02:30", "03:00:00+01:00"),
            ("America/New_York", "2026-03-08", "2026-11-01", "01:30", "02:00:00-05:00")]:
            self.expect(self.client.request("POST", "/_test/reset", fixture(zone, "00:00", "05:00")), 204)
            self.auth = self.login("ada@example.test")
            spring_grid = self.expect(self.client.request("GET",
                f"/availability?restaurant_id=r&date={spring}&party_size=2"), 200)["slots"]
            self.assertFalse(any(s["starts_at_local"][11:13] == "02" for s in spring_grid))
            self.expect(self.create(self.body(start=spring + "T02:30")), 422, "invalid_local_time")
            booked = self.expect(self.create(self.body(start=fall + "T" + repeated)), 201)
            self.assertTrue(booked["ends_at"].endswith(end), booked)
            self.assertEqual((datetime.fromisoformat(booked["ends_at"]).astimezone(timezone.utc) -
                datetime.fromisoformat(booked["starts_at"]).astimezone(timezone.utc)).total_seconds(), 5400)
            grid = self.expect(self.client.request("GET",
                f"/availability?restaurant_id=r&date={fall}&party_size=2"), 200)["slots"]
            self.assertEqual(sum(s["starts_at_local"] == fall + "T" + repeated for s in grid), 1)

    def test_export_import_replacement_invalid_atomicity(self):
        body = self.body()
        saved = self.expect(self.create(body, "receipt"), 201)
        self.expect(self.client.request("PATCH", "/reservations/" + saved["reference"], {"table_id": "b"}, self.auth), 200)
        self.expect(self.client.request("POST", "/reservations/" + saved["reference"] + "/cancel", headers=self.auth), 200)
        export = self.exported()
        destination = Client(args.destination_url)
        self.expect(destination.request("POST", "/_test/reset", fixture()), 204)
        self.expect(destination.request("POST", "/_test/import", export), 204)
        self.assertEqual(self.expect(destination.request("GET", "/_test/export"), 200), export)
        self.assertEqual(self.expect(destination.request("POST", "/reservations", body,
            {**self.auth, "Idempotency-Key": "receipt"}), 200), saved)
        self.expect(destination.request("POST", "/auth/login",
            {"email": "ada@example.test", "password": "fixture password"}), 200)
        stable = self.expect(destination.request("GET", "/_test/export"), 200)
        variants = [{}, {**export, "track": "other"}, {**export, "format_version": True},
                    {**export, "state": {}}]
        broken = deepcopy(export)
        broken["state"]["reservations"][0]["starts_at"] = "2099-04-16T18:00:00+00:00"
        variants.append(broken)
        broken = deepcopy(export)
        broken["state"]["receipts"][0]["response"]["reference"] = "MISSING"
        variants.append(broken)
        for invalid in variants:
            self.expect(destination.request("POST", "/_test/import", invalid), 422, "validation_failed")
            self.assertEqual(self.expect(destination.request("GET", "/_test/export"), 200), stable)
        self.expect(destination.request("POST", "/_test/import", export), 204)
        self.assertEqual(self.expect(destination.request("GET", "/_test/export"), 200), export)
        self.expect(destination.request("POST", "/_test/reset", {}), 204)
        self.expect(destination.request("GET", "/reservations", headers=self.auth), 401, "unauthenticated")
        self.assertEqual(self.expect(destination.request("GET", "/restaurants"), 200), {"restaurants": []})

    def test_required_fixture_arrays_missing_versus_wrong_type(self):
        before = self.exported()
        for field in ("opening_hours", "tables"):
            with self.subTest(field=field, value="missing"):
                missing = fixture()
                del missing["restaurants"][0][field]
                self.expect(self.client.request("POST", "/_test/reset", missing), 422, "validation_failed")
                self.assertEqual(self.exported(), before)
            for wrong_type in (None, {}, False, 1, "array"):
                with self.subTest(field=field, value=wrong_type):
                    invalid = fixture()
                    invalid["restaurants"][0][field] = wrong_type
                    self.expect(self.client.request("POST", "/_test/reset", invalid), 400, "malformed_request")
                    self.assertEqual(self.exported(), before)

    def test_calendar_maximum_and_large_grid_steps(self):
        seeded = fixture("UTC")
        self.expect(self.client.request("POST", "/_test/reset", seeded), 204)
        self.auth = self.login("ada@example.test")
        query = "/availability?restaurant_id=r&date=9999-12-31&party_size=2"
        available = self.expect(self.client.request("GET", query), 200)
        expected = [f"9999-12-31T{hour:02}:{minute:02}"
                    for hour in range(18, 22) for minute in (0, 30)]
        self.assertEqual([slot["starts_at_local"] for slot in available["slots"]], expected)
        self.assertTrue(all(slot["available_table_ids"] == ["a", "b"] for slot in available["slots"]))
        self.expect(self.create(self.body(start="9999-12-31T21:30")), 201)
        self.expect(self.create(self.body(table="b", start="9999-12-31T22:30")), 422, "outside_opening_hours")
        seeded["restaurants"][0]["slot_minutes"] = 5256000
        self.expect(self.client.request("POST", "/_test/reset", seeded), 204)
        huge_grid = self.expect(self.client.request("GET", query), 200)
        self.assertEqual([slot["starts_at_local"] for slot in huge_grid["slots"]], ["9999-12-31T18:00"])

    def test_local_calendar_extremes_outside_utc_range(self):
        for zone, day, opening, closing, booking_time, expected_count in [
            ("America/New_York", "9999-12-31", "18:00", "23:00", "21:30", 8),
            ("Europe/Berlin", "0001-01-01", "00:00", "06:00", "00:00", 10)]:
            with self.subTest(zone=zone, operation="availability"):
                self.expect(self.client.request("POST", "/_test/reset", fixture(zone, opening, closing)), 204)
                self.auth = self.login("ada@example.test")
                grid = self.expect(self.client.request("GET",
                    f"/availability?restaurant_id=r&date={day}&party_size=2"), 200)
                self.assertEqual(len(grid["slots"]), expected_count)
            with self.subTest(zone=zone, operation="create"):
                record = self.expect(self.create(self.body(start=day + "T" + booking_time)), 201)
                self.assertEqual(record["starts_at_local"], day + "T" + booking_time)
                start, end = datetime.fromisoformat(record["starts_at"]), datetime.fromisoformat(record["ends_at"])
                self.assertEqual((end.replace(tzinfo=None) - start.replace(tzinfo=None)) -
                                 (end.utcoffset() - start.utcoffset()), timedelta(minutes=90))
                listed = self.expect(self.client.request("GET", "/reservations", headers=self.auth), 200)
                self.assertEqual(listed["reservations"], [record])
                self.expect(self.create(self.body(start=day + "T" + booking_time)), 409, "table_unavailable")
                destination = Client(args.destination_url)
                export = self.exported()
                self.expect(destination.request("POST", "/_test/import", export), 204)
                self.assertEqual(self.expect(destination.request("GET", "/_test/export"), 200), export)
                response = self.client.request("POST", "/reservations/" + record["reference"] + "/cancel",
                                               headers=self.auth)
                self.expect(response, 200 if day.startswith("9999") else 409,
                            None if day.startswith("9999") else "cutoff_passed")

    def test_exact_rfc3339_historical_representation(self):
        pattern = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?[+-][0-9]{2}:[0-9]{2}\Z")
        epoch = datetime(1, 1, 1)

        def absolute(value):
            delta = value.replace(tzinfo=None) - epoch - value.utcoffset()
            return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds

        def oracle(value):
            # Exhaust all legal minute offsets independently of production's
            # bounded interval/clamped-neighbor selection.
            valid = []
            for minutes in range(-1439, 1440):
                fixed = timedelta(minutes=minutes)
                try:
                    wall = value.replace(tzinfo=None) + (fixed - value.utcoffset())
                except OverflowError:
                    continue
                distance = abs(fixed - value.utcoffset())
                valid.append((distance, minutes, wall))
            _, minutes, wall = min(valid, key=lambda item: (item[0], item[1]))
            return wall.replace(tzinfo=timezone(timedelta(minutes=minutes))).isoformat()

        cases = [
            ("Europe/Berlin", "0001-01-01", "00:00", "06:00", "00:00"),
            ("America/New_York", "0001-01-01", "18:00", "23:00", "18:00"),
            ("Europe/Brussels", "1800-01-01", "18:00", "23:00", "18:00"),
            ("America/New_York", "9999-12-31", "18:00", "23:00", "21:30"),
            ("Europe/Berlin", "2026-10-25", "00:00", "05:00", "02:30")]
        for zone, day, opening, closing, selected in cases:
            with self.subTest(zone=zone, day=day):
                self.expect(self.client.request("POST", "/_test/reset", fixture(zone, opening, closing)), 204)
                self.auth = self.login("ada@example.test")
                grid = self.expect(self.client.request("GET",
                    f"/availability?restaurant_id=r&date={day}&party_size=2"), 200)
                original = datetime.fromisoformat(day + "T" + selected).replace(tzinfo=ZoneInfo(zone), fold=0)
                record = self.expect(self.create(self.body(start=day + "T" + selected), key="wire-receipt"), 201)
                self.assertEqual(record["starts_at_local"], day + "T" + selected)
                self.assertRegex(record["starts_at"], pattern)
                self.assertRegex(record["ends_at"], pattern)
                self.assertEqual(record["starts_at"], oracle(original))
                self.assertEqual(absolute(datetime.fromisoformat(record["starts_at"])), absolute(original))
                self.assertEqual(absolute(datetime.fromisoformat(record["ends_at"])) - absolute(original), 5400000000)
                try:
                    original_end = (original.astimezone(timezone.utc) + timedelta(minutes=90)).astimezone(ZoneInfo(zone))
                except OverflowError:
                    original_end = (original.replace(tzinfo=None) + timedelta(minutes=90)).replace(tzinfo=ZoneInfo(zone))
                    self.assertEqual(original_end.utcoffset(), original.utcoffset())
                self.assertEqual(record["ends_at"], oracle(original_end))
                for available_slot in grid["slots"]:
                    self.assertRegex(available_slot["starts_at"], pattern)
                    actual_local = datetime.fromisoformat(available_slot["starts_at_local"]).replace(tzinfo=ZoneInfo(zone), fold=0)
                    self.assertEqual(absolute(datetime.fromisoformat(available_slot["starts_at"])), absolute(actual_local))
                slot = next(s for s in grid["slots"] if s["starts_at_local"] == day + "T" + selected)
                self.assertEqual(slot["starts_at"], record["starts_at"])
                exported = self.exported()
                self.expect(self.client.request("POST", "/_test/import", exported), 204)
                self.assertEqual(self.exported(), exported)
                self.assertEqual(self.expect(self.create(self.body(start=day + "T" + selected), key="wire-receipt"), 200), record)

    def test_legacy_receipt_strings_survive_new_import_and_replay(self):
        if args.legacy_url:
            legacy = Client(args.legacy_url)
        else:
            # This run's own previously committed Engine is diagnostic input,
            # used only to produce a genuine pre-serializer export in memory.
            code = subprocess.check_output(["git", "show",
                "49287b4a5a1481f995c470ccae31776f03d4b863:stage-1/core.py"], cwd=root)
            namespace = {"__name__": "systems_engineer_legacy_engine"}
            exec(compile(code, "own-committed-legacy-core", "exec"), namespace)
            legacy = Client(engine=namespace["Engine"]())
        self.expect(legacy.request("POST", "/_test/reset", fixture("Europe/Berlin", "00:00", "06:00")), 204)
        session = self.expect(legacy.request("POST", "/auth/login",
            {"email": "ada@example.test", "password": "fixture password"}), 200)
        auth = {"Authorization": "Bearer " + session["token"], "Idempotency-Key": "original-style"}
        body = self.body(start="0001-01-01T00:00")
        original = self.expect(legacy.request("POST", "/reservations", body, auth), 201)
        self.assertTrue(original["starts_at"].endswith("+00:53:28"))
        exported = self.expect(legacy.request("GET", "/_test/export"), 200)
        self.expect(self.client.request("POST", "/_test/import", exported), 204)
        adopted = self.exported()
        # The agreed private schema/profile migration changes metadata only;
        # all original records, bodies, emitted responses and credentials stay.
        self.assertEqual(adopted["state"]["schema"], 3)
        self.assertTrue(all(r["numeric_profile"] == "python-json-v1" for r in adopted["state"]["receipts"]))
        comparable = legacy_projection(adopted, 1)
        comparable["state"]["schema"] = 1
        for receipt in comparable["state"]["receipts"]:
            receipt.pop("numeric_profile")
        self.assertTrue(comparable == exported, "Only adopted private numeric metadata may change")
        self.assertEqual(self.expect(self.client.request("POST", "/reservations", body, auth), 200), original)
        lookup = current_legacy(original, fixture("Europe/Berlin", "00:00", "06:00")["restaurants"][0])
        self.assertEqual(self.expect(self.client.request("GET", "/reservations/" + original["reference"], headers=auth), 200), lookup)
        newer = self.expect(self.client.request("POST", "/reservations", self.body(start="0001-01-01T01:30"),
            {**auth, "Idempotency-Key": "new-style"}), 201)
        self.assertTrue(newer["starts_at"].endswith("+00:53"))
        mixed = self.exported()
        destination = Client(args.destination_url)
        self.expect(destination.request("POST", "/_test/import", mixed), 204)
        self.assertEqual(self.expect(destination.request("GET", "/_test/export"), 200), mixed)
        self.assertEqual(self.expect(destination.request("POST", "/reservations", body, auth), 200), original)

    def test_unbounded_base_fixture_minute_counts(self):
        for field in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes"):
            with self.subTest(field=field):
                huge = fixture("UTC")
                huge["restaurants"][0][field] = 10 ** 18
                self.expect(self.client.request("POST", "/_test/reset", huge), 204)
                self.auth = self.login("ada@example.test")
                detail = self.expect(self.client.request("GET", "/restaurants/r"), 200)
                self.assertEqual(detail[field], 10 ** 18)
                query = "/availability?restaurant_id=r&date=2099-04-16&party_size=2"
                slots = self.expect(self.client.request("GET", query), 200)["slots"]
                if field == "reservation_duration_minutes":
                    self.assertEqual(slots, [])
                    before = self.exported()
                    self.expect(self.create(), 422, "outside_opening_hours")
                    self.assertEqual(self.exported(), before)
                else:
                    if field == "slot_minutes":
                        self.assertEqual([slot["starts_at_local"] for slot in slots], ["2099-04-16T18:00"])
                    record = self.expect(self.create(key="huge-count-receipt"), 201)
                    before = self.exported()
                    if field == "slot_minutes":
                        self.expect(self.create(self.body(table="b", start="2099-04-16T18:30")), 422,
                                    "not_on_slot_grid")
                    else:
                        self.expect(self.client.request("PATCH", "/reservations/" + record["reference"],
                            {"table_id": "b"}, self.auth), 409, "cutoff_passed")
                        self.expect(self.client.request("POST", "/reservations/" + record["reference"] + "/cancel",
                            headers=self.auth), 409, "cutoff_passed")
                    self.assertEqual(self.exported(), before)
                    self.assertEqual(self.expect(self.create(key="huge-count-receipt"), 200), record)
                exported = self.exported()
                destination = Client(args.destination_url)
                self.expect(destination.request("POST", "/_test/import", exported), 204)
                self.assertEqual(self.expect(destination.request("GET", "/_test/export"), 200), exported)


if __name__ == "__main__":
    print("Builder diagnostics; transport=" + ("HTTP" if args.url else "Engine") + "; model/spend unknown")
    unittest.main(argv=[sys.argv[0], *unittest_args], verbosity=2)
