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
import sys
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--url")
parser.add_argument("--destination-url")
args, unittest_args = parser.parse_known_args()
if not args.url or not args.destination_url:
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("tablekeeper_builder_core", root / "stage-1/core.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


class Client:
    def __init__(self, url=None):
        self.url = url
        self.engine = module.Engine() if url is None else None

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


if __name__ == "__main__":
    print("Builder diagnostics; transport=" + ("HTTP" if args.url else "Engine") + "; model/spend unknown")
    unittest.main(argv=[sys.argv[0], *unittest_args], verbosity=2)
