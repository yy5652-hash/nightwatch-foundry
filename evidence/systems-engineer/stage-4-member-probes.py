"""Stage 2 integrity diagnostics derived from the complete written specifications.

No transport/UI acceptance claim. Exports/passwords/tokens remain in memory.
The deterministic interval trace contains only synthetic reservation operations.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--url")
parser.add_argument("--destination-url")
parser.add_argument("--source-url")
parser.add_argument("--trace")
args, rest = parser.parse_known_args()
if not args.url or not args.destination_url or not args.source_url:
    root = Path(__file__).resolve().parents[2]
    def engine(stage):
        spec = importlib.util.spec_from_file_location(f"owned_stage_{stage}", root / f"stage-{stage}/core.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.Engine()


class Client:
    def __init__(self, url=None, stage=2):
        self.url = url
        self.engine = None if url else engine(stage)

    def request(self, method, path, body=None, headers=None):
        if self.engine:
            return self.engine.request(method, path, headers or {}, body)
        request = Request(self.url + path, method=method,
                          data=None if body is None else json.dumps(body).encode(),
                          headers={"Content-Type": "application/json", **(headers or {})})
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None


def fixture():
    return {"users": [{"id": "u", "email": "diner@example.test", "password": "fixture password",
                       "display_name": "Diner"},
                      {"id": "v", "email": "other@example.test", "password": "fixture password",
                       "display_name": "Other"}],
            "restaurants": [{"id": "r", "name": "Garden Room", "timezone": "UTC", "slot_minutes": 30,
                "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
                "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "23:00"}
                    for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
                "tables": [{"id": "a", "label": "Window", "capacity": 2},
                           {"id": "b", "label": "Garden", "capacity": 4},
                           {"id": "c", "label": "Courtyard", "capacity": 3},
                           {"id": "d", "label": "Alcove", "capacity": 2}],
                "combinable": [["b", "a"], ["b", "c"], ["c", "d"]]}], "reservations": []}



def legacy_projection(value, schema):
    projected=json.loads(json.dumps(value))
    state=projected["state"]
    for field in ("policies","histories","history_origins","series","restaurant_revisions","plans","closures"):state.pop(field,None)
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

class StageTwo(unittest.TestCase):
    def setUp(self):
        self.client = Client(args.url)
        self.expect(self.client.request("POST", "/_test/reset", fixture()), 204)
        self.auth = self.login(self.client)
        self.key_counter = 0

    def expect(self, response, status, code=None):
        self.assertEqual(response[0], status, response[1])
        if code:
            self.assertEqual(response[1]["error"]["code"], code)
        return response[1]

    def login(self, client, email="diner@example.test"):
        result = self.expect(client.request("POST", "/auth/login",
            {"email": email, "password": "fixture password"}), 200)
        return {"Authorization": "Bearer " + result["token"]}

    def body(self, members=("b", "a"), start="2099-04-16T18:00", party=2):
        return {"restaurant_id": "r", "table_ids": list(members), "party_size": party,
                "starts_at_local": start}

    def create(self, body=None, key=None):
        self.key_counter += 1
        return self.client.request("POST", "/reservations", self.body() if body is None else body,
            {**self.auth, "Idempotency-Key": key or f"s2-{self.key_counter}"})

    def exported(self, client=None):
        return self.expect((client or self.client).request("GET", "/_test/export"), 200)

    def availability(self, party=2):
        return self.expect(self.client.request("GET",
            f"/availability?restaurant_id=r&date=2099-04-16&party_size={party}"), 200)["slots"]

    def patch(self, record, body):
        return self.client.request("PATCH", "/reservations/" + record["reference"], body, self.auth)

    def cancel(self, record):
        return self.client.request("POST", "/reservations/" + record["reference"] + "/cancel", headers=self.auth)

    def moves(self, moves, key="moves"):
        return self.client.request("POST", "/reservation-moves", {"moves": moves},
                                   {**self.auth, "Idempotency-Key": key})

    def test_order_capacity_canonicalization_and_nontransitivity(self):
        expected = [{"table_ids": ["a"], "capacity": 2}, {"table_ids": ["b"], "capacity": 4},
                    {"table_ids": ["c"], "capacity": 3}, {"table_ids": ["d"], "capacity": 2},
                    {"table_ids": ["b", "a"], "capacity": 6},
                    {"table_ids": ["b", "c"], "capacity": 7},
                    {"table_ids": ["c", "d"], "capacity": 5}]
        self.assertEqual(self.availability()[0]["available_options"], expected)
        self.assertEqual(self.availability(6)[0]["available_options"], expected[4:6])
        self.assertEqual(self.availability(6)[0]["available_table_ids"], [])
        self.assertTrue(all(s["available_options"] == [] for s in self.availability(8)))
        self.expect(self.create(self.body(("a", "c"))), 422, "combination_not_allowed")
        made = self.expect(self.create(self.body(("a", "b"), party=6)), 201)
        self.assertEqual(made["table_ids"], ["b", "a"])
        self.assertNotIn("table_id", made)
        self.assertEqual(self.expect(self.client.request("GET", "/reservations/" + made["reference"],
                                        headers=self.auth), 200), made)
        self.expect(self.client.request("GET", "/reservations/" + made["reference"],
            headers=self.login(self.client, "other@example.test")), 404, "not_found")

    def test_member_shape_errors_and_failed_key_reuse(self):
        variants = [(None, 400, "malformed_request"), ("a", 400, "malformed_request"),
                    ([], 422, "validation_failed"), (["a", "a"], 422, "validation_failed"),
                    (["a", "b", "c"], 422, "combination_not_allowed"),
                    (["a", False], 400, "malformed_request"), (["a", ""], 422, "validation_failed"),
                    (["a", "x" * 65], 422, "validation_failed"), (["a", "absent"], 404, "not_found"),
                    (["a", "c"], 422, "combination_not_allowed")]
        before = self.exported()
        for members, status, code in variants:
            body = {**self.body(), "table_ids": members}
            self.expect(self.create(body, "reusable"), status, code)
            self.assertEqual(self.exported(), before)
        self.expect(self.create({**self.body(), "table_id": "a"}, "reusable"), 422, "validation_failed")
        self.expect(self.create(self.body(party=7), "reusable"), 422, "party_exceeds_capacity")
        original = self.expect(self.create(key="reusable"), 201)
        self.assertEqual(self.expect(self.create(key="reusable"), 200), original)
        self.expect(self.create(self.body(("a", "b")), "reusable"), 409, "idempotency_key_reuse")
        self.expect(self.create({"table_ids": []}, "reusable"), 409, "idempotency_key_reuse")

    def test_pair_occupancy_half_open_and_cancellation(self):
        pair = self.expect(self.create(), 201)
        for members in (("a",), ("b",), ("b", "c")):
            self.expect(self.create(self.body(members)), 409, "table_unavailable")
        slot = self.availability()[0]
        self.assertEqual(slot["available_table_ids"], ["c", "d"])
        self.assertEqual(slot["available_options"], [{"table_ids": ["c"], "capacity": 3},
            {"table_ids": ["d"], "capacity": 2}, {"table_ids": ["c", "d"], "capacity": 5}])
        self.expect(self.create(self.body(start="2099-04-16T19:30")), 201)
        self.expect(self.create(self.body(start="2099-04-16T19:00")), 409, "table_unavailable")
        cancelled = self.expect(self.cancel(pair), 200)
        self.assertEqual(self.expect(self.cancel(pair), 200), cancelled)
        self.assertEqual(self.availability()[0]["available_table_ids"], ["a", "b", "c", "d"])
        self.expect(self.create(self.body(("a",))), 201)
        self.expect(self.create(self.body(("b",))), 201)

    def test_amendment_transitions_noops_and_atomic_failures(self):
        single = {**self.body(("a",)), "table_id": "a"}
        del single["table_ids"]
        made = self.expect(self.create(single), 201)
        self.assertEqual(made["table_ids"], ["a"])
        blocked = self.expect(self.create(self.body(("b",))), 201)
        before = self.exported()
        self.expect(self.patch(made, {"table_ids": ["a", "b"]}), 409, "table_unavailable")
        self.assertEqual(self.exported(), before)
        self.expect(self.cancel(blocked), 200)
        paired = self.expect(self.patch(made, {"table_ids": ["a", "b"]}), 200)
        self.assertEqual(paired["table_ids"], ["b", "a"])
        self.assertNotIn("table_id", paired)
        before = self.exported()
        self.assertEqual(self.expect(self.patch(made, {"table_ids": ["b", "a"], "ignored": True}), 200), paired)
        self.assertEqual(self.exported(), before)
        revised = self.expect(self.patch(made, {"table_id": "c", "party_size": 3}), 200)
        self.assertEqual(revised["table_ids"], ["c"])
        self.assertEqual(revised["table_id"], "c")
        for key in ("reference", "reservation_id", "created_at"):
            self.assertEqual(revised[key], made[key])
        before = self.exported()
        self.expect(self.patch(made, {"table_ids": ["b", "a"], "table_id": "a"}), 422, "validation_failed")
        self.assertEqual(self.exported(), before)

    def test_atomic_pair_single_swap_and_receipt_history(self):
        pair = self.expect(self.create(), 201)
        single = self.expect(self.create(self.body(("c",))), 201)
        before = self.exported()
        invalid = [{"reference": pair["reference"], "table_ids": ["b", "c"]},
                   {"reference": single["reference"], "party_size": 4}]
        self.expect(self.moves(invalid), 422, "party_exceeds_capacity")
        self.assertEqual(self.exported(), before)
        overlap = [{"reference": pair["reference"], "table_ids": ["b", "c"]},
                   {"reference": single["reference"]}]
        self.expect(self.moves(overlap), 409, "table_unavailable")
        self.assertEqual(self.exported(), before)
        swap = [{"reference": pair["reference"], "table_ids": ["c", "b"]},
                {"reference": single["reference"], "table_id": "a"}]
        saved = self.expect(self.moves(swap), 201)
        self.assertEqual([r["table_ids"] for r in saved["reservations"]], [["b", "c"], ["a"]])
        self.assertNotIn("table_id", saved["reservations"][0])
        self.assertEqual(saved["reservations"][1]["table_id"], "a")
        before = self.exported()
        self.expect(self.moves([{"reference": pair["reference"], "table_ids": ["c", "b"]},
                                {"reference": single["reference"]}], "noop"), 201)
        after = self.exported()
        self.assertEqual(before["state"]["reservations"], after["state"]["reservations"])
        self.expect(self.cancel(pair), 200)
        self.assertEqual(self.expect(self.moves(swap), 200), saved)
        destination = Client(args.destination_url)
        exported = self.exported()
        self.expect(destination.request("POST", "/_test/import", exported), 204)
        self.assertEqual(self.exported(destination), exported)
        self.assertEqual(self.expect(destination.request("POST", "/reservation-moves", {"moves": swap},
            {**self.auth, "Idempotency-Key": "moves"}), 200), saved)

    def test_seeded_cancelled_pairs_and_fixture_validation(self):
        seeded = fixture()
        seeded["reservations"] = [
            {**self.body(), "id": "s1", "reference": "CANCEL1", "user_id": "u", "status": "cancelled"},
            {**self.body(("a",), start="2099-04-16T19:30"), "id": "s2", "reference": "SINGLE1", "user_id": "u"},
            {**self.body(("b", "c"), start="2099-04-16T19:30"), "id": "s3", "reference": "PAIR001", "user_id": "u"}]
        self.expect(self.client.request("POST", "/_test/reset", seeded), 204)
        self.auth = self.login(self.client)
        self.assertEqual(self.availability()[0]["available_table_ids"], ["a", "b", "c", "d"])
        listing = self.expect(self.client.request("GET", "/reservations", headers=self.auth), 200)["reservations"]
        self.assertEqual({r["reference"]: r["status"] for r in listing},
                         {"CANCEL1": "cancelled", "SINGLE1": "confirmed", "PAIR001": "confirmed"})
        self.expect(self.create(), 201)
        stable = self.exported()
        for pair in (["a"], ["a", "b", "c"], ["a", "a"], ["a", "absent"]):
            invalid = fixture()
            invalid["restaurants"][0]["combinable"] = [pair]
            self.expect(self.client.request("POST", "/_test/reset", invalid), 422, "validation_failed")
            self.assertEqual(self.exported(), stable)

    def test_invalid_pair_import_replacement_is_atomic(self):
        made = self.expect(self.create(self.body(("a", "b")), "original"), 201)
        self.expect(self.patch(made, {"table_ids": ["c", "d"]}), 200)
        self.expect(self.cancel(made), 200)
        exported = self.exported()
        destination = Client(args.destination_url)
        self.expect(destination.request("POST", "/_test/import", exported), 204)
        for field, value in [("table_id", "a"), ("table_ids", ["a", "c"]), ("table_ids", ["c", "c"])]:
            invalid = deepcopy(exported)
            invalid["state"]["reservations"][0][field] = value
            self.expect(destination.request("POST", "/_test/import", invalid), 422, "validation_failed")
            self.assertEqual(self.exported(destination), exported)
        self.assertEqual(self.expect(destination.request("POST", "/reservations", self.body(("a", "b")),
            {**self.auth, "Idempotency-Key": "original"}), 200), made)

    def test_genuine_accepted_stage1_export_tokens_and_original_receipts(self):
        source = Client(args.source_url, stage=1)
        self.expect(source.request("POST", "/_test/reset", fixture()), 204)
        first, second = self.login(source), self.login(source)
        old_body = {"restaurant_id": "r", "table_id": "a", "party_size": 2,
                    "starts_at_local": "2099-04-16T18:00", "table_ids": {"ignored_in_stage_1": True}}
        headers = {**first, "Idempotency-Key": "retained"}
        original = self.expect(source.request("POST", "/reservations", old_body, headers), 201)
        self.assertNotIn("table_ids", original)
        self.expect(source.request("PATCH", "/reservations/" + original["reference"], {"table_id": "b"}, first), 200)
        cancelled = self.expect(source.request("POST", "/reservations/" + original["reference"] + "/cancel",
                                               headers=first), 200)
        members = []
        for table in ("a", "c"):
            body = {**old_body, "table_id": table, "starts_at_local": "2099-04-16T19:30"}
            members.append(self.expect(source.request("POST", "/reservations", body,
                {**first, "Idempotency-Key": "old-" + table}), 201))
        moves = {"moves": [{"reference": members[0]["reference"], "table_id": "c", "table_ids": False},
                           {"reference": members[1]["reference"], "table_id": "a", "table_ids": ["ignored"]}]}
        old_batch = self.expect(source.request("POST", "/reservation-moves", moves, headers), 201)
        self.expect(source.request("POST", "/reservations", {**old_body, "party_size": False},
                                  {**first, "Idempotency-Key": "failed-before-upgrade"}), 422, "validation_failed")
        exported = self.exported(source)
        self.expect(self.client.request("POST", "/_test/import", exported), 204)
        self.assertEqual(legacy_projection(self.exported(), 2), exported)
        self.assertEqual(self.expect(self.client.request("POST", "/reservations", old_body, headers), 200), original)
        self.assertEqual(self.expect(self.client.request("POST", "/reservation-moves", moves, headers), 200), old_batch)
        self.expect(self.client.request("POST", "/reservations", old_body,
            {**first, "Idempotency-Key": "new-key-known-fields"}), 422, "validation_failed")
        current = self.expect(self.client.request("GET", "/reservations/" + original["reference"], headers=second), 200)
        self.assertEqual(current, current_legacy(cancelled, fixture()["restaurants"][0]))
        self.expect(self.client.request("GET", "/reservations", headers=self.auth), 401, "unauthenticated")
        self.assertEqual(self.expect(self.client.request("PATCH", "/reservations/" + members[0]["reference"], {},
            first), 200), current_legacy(old_batch["reservations"][0], fixture()["restaurants"][0]))
        self.assertEqual(legacy_projection(self.exported(), 2), exported)
        fresh_body = {key: value for key, value in old_body.items() if key != "table_ids"}
        fresh_body.update({"table_id": "b", "starts_at_local": "2099-04-16T20:00"})
        self.expect(self.client.request("POST", "/reservations", fresh_body,
                    {**first, "Idempotency-Key": "failed-before-upgrade"}), 201)
        destination = Client(args.destination_url)
        mixed = self.exported()
        self.expect(destination.request("POST", "/_test/import", mixed), 204)
        self.assertEqual(self.exported(destination), mixed)
        self.assertEqual(self.expect(destination.request("POST", "/reservations", old_body, headers), 200), original)
        self.expect(destination.request("POST", "/auth/login",
            {"email": "diner@example.test", "password": "fixture password"}), 200)

    def test_50_identical_pairs_and_50_pair_single_competitors(self):
        with ThreadPoolExecutor(max_workers=50) as pool:
            identical = list(pool.map(lambda _: self.create(key="identical-pair"), range(50)))
        self.assertEqual([r[0] for r in identical].count(201), 1)
        self.assertEqual([r[0] for r in identical].count(200), 49)
        self.assertTrue(all(r[1] == identical[0][1] for r in identical))
        barrier = threading.Barrier(50)
        def attempt(index):
            barrier.wait(timeout=10)
            choice = (("a", "b"), ("a",), ("b",))[index % 3]
            return self.create(self.body(choice, start="2099-04-16T19:30"), f"competitor-{index}")
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(attempt, range(50)))
        winners = [r[1]["table_ids"] for r in results if r[0] == 201]
        if ["b", "a"] in winners:
            self.assertEqual(winners, [["b", "a"]])
        else:
            self.assertEqual(sorted(winners), [["a"], ["b"]])
        self.assertTrue(all(r[0] in (201, 409) for r in results))

    def test_pair_amendment_race_with_new_single_is_serializable(self):
        made = self.expect(self.create(self.body(("a",))), 201)
        barrier = threading.Barrier(2)
        def amend():
            barrier.wait(timeout=10)
            return self.patch(made, {"table_ids": ["a", "b"]})
        def book():
            barrier.wait(timeout=10)
            return self.create(self.body(("b",)))
        with ThreadPoolExecutor(max_workers=2) as pool:
            left, right = pool.submit(amend), pool.submit(book)
            changed, booked = left.result(), right.result()
        self.assertIn((changed[0], booked[0]), ((200, 409), (409, 201)))
        listed = self.expect(self.client.request("GET", "/reservations", headers=self.auth), 200)["reservations"]
        self.assertEqual(len(listed), 1 if changed[0] == 200 else 2)
        current = next(r for r in listed if r["reference"] == made["reference"])
        self.assertEqual(current["table_ids"], ["b", "a"] if changed[0] == 200 else ["a"])

    def test_deterministic_member_interval_reference_oracle(self):
        seed = 20261004
        rng, records, trace = random.Random(seed), {}, []
        restaurant = fixture()["restaurants"][0]
        options = [[t["id"]] for t in restaurant["tables"]] + restaurant["combinable"]
        capacities = {t["id"]: t["capacity"] for t in restaurant["tables"]}
        def overlaps(members, start, exclude=None):
            return any(ref != exclude and row["status"] == "confirmed" and set(members) & set(row["members"])
                and max(start, row["start"]) < min(start + 90, row["start"] + 90)
                for ref, row in records.items())
        def local(start):
            return f"2099-04-16T{start // 60:02d}:{start % 60:02d}"
        try:
            for index in range(160):
                members, start = rng.choice(options), 1080 + rng.randrange(8) * 30
                operation = rng.choice(("create", "create", "patch", "cancel")) if records else "create"
                before = self.exported()
                if operation == "create":
                    body = self.body(members, local(start), 1)
                    expected = 409 if overlaps(members, start) else 201
                    result = self.create(body, f"oracle-{index}")
                    row = self.expect(result, expected, "table_unavailable" if expected == 409 else None)
                    if expected == 201:
                        records[row["reference"]] = {"members": members, "start": start, "status": "confirmed",
                                                     "reservation_id": row["reservation_id"]}
                    reference = None
                else:
                    reference = rng.choice(list(records))
                    old = records[reference]
                    if operation == "cancel":
                        body, expected = None, 200
                        result = self.client.request("POST", "/reservations/" + reference + "/cancel", headers=self.auth)
                        self.expect(result, expected)
                        old["status"] = "cancelled"
                    else:
                        body = {"table_ids": members, "starts_at_local": local(start)}
                        expected = 409 if old["status"] == "cancelled" or overlaps(members, start, reference) else 200
                        result = self.client.request("PATCH", "/reservations/" + reference, body, self.auth)
                        code = "reservation_cancelled" if old["status"] == "cancelled" else "table_unavailable"
                        self.expect(result, expected, code if expected == 409 else None)
                        if expected == 200:
                            old["members"], old["start"] = members, start
                trace.append({"index": index, "operation": operation, "reference": reference,
                              "body": body, "expected_status": expected, "observed_status": result[0]})
                if expected == 409:
                    self.assertEqual(self.exported(), before)
                for slot in self.availability(1):
                    start = int(slot["starts_at_local"][11:13]) * 60 + int(slot["starts_at_local"][14:16])
                    wanted = [{"table_ids": list(selection), "capacity": sum(capacities[m] for m in selection)}
                              for selection in options if not overlaps(selection, start)]
                    self.assertEqual(slot["available_options"], wanted)
                    self.assertEqual(slot["available_table_ids"], [o["table_ids"][0] for o in wanted if len(o["table_ids"]) == 1])
            listing = self.expect(self.client.request("GET", "/reservations", headers=self.auth), 200)["reservations"]
            self.assertEqual({r["reference"] for r in listing}, set(records))
            for row in listing:
                wanted = records[row["reference"]]
                self.assertEqual(row["table_ids"], wanted["members"])
                self.assertEqual(row["status"], wanted["status"])
                self.assertEqual(row["reservation_id"], wanted["reservation_id"])
        finally:
            if args.trace:
                Path(args.trace).write_text(json.dumps({"seed": seed, "operations": trace}, indent=2) + "\n")


if __name__ == "__main__":
    print("Stage 2 builder integrity diagnostics; transport=" + ("HTTP" if args.url else "Engine"))
    unittest.main(argv=[sys.argv[0], *rest], verbosity=2)
