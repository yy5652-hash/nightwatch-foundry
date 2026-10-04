"""Additional probes from a second complete source pass, outside product folders."""
import copy
import hashlib
import json
from requirements import FIXTURE_STRING_FIELDS, FIXTURE_NUMBER_FIELDS


def run(p):
    from probe import fixture, DAY
    p.setup()
    f = fixture()
    f["reservations"] = [dict(p.body(), id="seed", reference="SEED01", user_id="u_a")]

    def record(fix, shape):
        return {"user": fix["users"][0], "restaurant": fix["restaurants"][0], "hours": fix["restaurants"][0]["opening_hours"][0],
                "table": fix["restaurants"][0]["tables"][0], "reservation": fix["reservations"][0]}[shape]

    for shape, fields in {k: v + FIXTURE_NUMBER_FIELDS.get(k, []) for k, v in FIXTURE_STRING_FIELDS.items()}.items():
        for field in fields:
            invalid = copy.deepcopy(f)
            del record(invalid, shape)[field]
            p.expect(f"reset-missing-{shape}-{field}", "POST", "/_test/reset", invalid, status=422, code="validation_failed")
            variants = [("string", "1"), ("bool", True), ("array", []), ("object", {}), ("null", None)] if field in FIXTURE_NUMBER_FIELDS.get(shape, []) else [("number", 1), ("bool", True), ("array", []), ("object", {}), ("null", None)]
            for variant, value in variants:
                invalid = copy.deepcopy(f)
                record(invalid, shape)[field] = value
                status = 422 if shape == "reservation" and field == "party_size" else 400
                p.expect(f"reset-type-{shape}-{field}-{variant}", "POST", "/_test/reset", invalid, status=status, code="validation_failed" if status == 422 else "malformed_request")
    for field in ["opening_hours", "tables"]:
        invalid = copy.deepcopy(f)
        del invalid["restaurants"][0][field]
        p.expect("reset-missing-restaurant-" + field, "POST", "/_test/reset", invalid, status=422, code="validation_failed")
    # Each field-ignore route is observed independently, not inferred from create.
    unknown = {"ignored": {"deep": [False, None, 7]}}
    p.expect("unknown-field-reset", "POST", "/_test/reset", dict(fixture(), **unknown), status=204)
    p.setup()
    user = dict(email="unknown@probe.invalid", password="correct-password", display_name="Ignored Fields", **unknown)
    p.expect("unknown-field-signup", "POST", "/auth/signup", user, status=201)
    p.expect("unknown-field-login", "POST", "/auth/login", {k: v for k, v in user.items() if k != "display_name"})
    r = p.expect("unknown-field-create", "POST", "/reservations", dict(p.body(), **unknown), token=p.a, key="unknown-create", status=201)
    p.expect("unknown-field-patch", "PATCH", "/reservations/" + r["reference"], unknown, token=p.a)
    p.expect("unknown-field-batch", "POST", "/reservation-moves", dict(moves=[dict(reference=r["reference"], **unknown)], **unknown), token=p.a, key="unknown-batch", status=201)
    p.expect("unknown-field-cancel", "POST", "/reservations/" + r["reference"] + "/cancel", unknown, token=p.a)
    snapshot = p.state()
    p.expect("unknown-field-import", "POST", "/_test/import", dict(snapshot, **unknown), status=204)
    # Observe password hashing through private export and independently recompute
    # scrypt; save only algorithm/length evidence, never salt/key/token material.
    users = snapshot["state"].get("users", [])
    plaintexts = [u["password"] for u in fixture()["users"]] + ["correct-password"]
    passwords_absent = all(password not in json.dumps(snapshot) for password in plaintexts)
    checked = []
    for u in users:
        hashed = u.get("password_hash", {})
        source_password = next((x["password"] for x in fixture()["users"] if x["email"] == u.get("email")), "correct-password")
        try:
            independently_computed = hashlib.scrypt(source_password.encode(), salt=bytes.fromhex(hashed["salt"]), n=16384, r=8, p=1, dklen=32, maxmem=64*1024*1024).hex()
            checked.append(hashed.get("algorithm") == "scrypt" and independently_computed == hashed.get("key"))
        except (ValueError, KeyError):
            checked.append(False)
    p.check("password-hashed", passwords_absent and bool(checked) and all(checked), "password hashes independently verified, no plaintext", {"users_checked": len(checked), "all_digest_matches": all(checked), "plaintext_absent": passwords_absent})
    p.setup()
    r = p.create(p.body(local=DAY + "T21:40"))
    for endpoint in ["create", "patch", "batch"]:
        for field in ["party_size", "starts_at_local"]:
            variants = [("array", []), ("object", {}), ("null", None)] + ([("bool", True)] if field == "starts_at_local" else [])
            for variant, value in variants:
                change = {field: value}
                body = dict(p.body(), **change) if endpoint == "create" else change if endpoint == "patch" else {"moves": [dict(reference=r["reference"], **change)]}
                path = "/reservations" if endpoint == "create" else "/reservations/" + r["reference"] if endpoint == "patch" else "/reservation-moves"
                status = 422 if field == "party_size" else 400
                p.expect(f"extra-type-{endpoint}-{field}-{variant}", "PATCH" if endpoint == "patch" else "POST", path, body, token=p.a, key=f"extra-{p.counter}", status=status, code="validation_failed" if status == 422 else "malformed_request")
        for field in ["restaurant_id", "table_id"] if endpoint == "create" else ["table_id"]:
            change = {field: "x"*65}
            body = dict(p.body(), **change) if endpoint == "create" else change if endpoint == "patch" else {"moves": [dict(reference=r["reference"], **change)]}
            path = "/reservations" if endpoint == "create" else "/reservations/" + r["reference"] if endpoint == "patch" else "/reservation-moves"
            p.expect(f"id-over-{endpoint}-{field}", "PATCH" if endpoint == "patch" else "POST", path, body, token=p.a, key=f"length-{p.counter}", status=422, code="validation_failed")
    for endpoint in ["create", "batch"]:
        p.setup()
        blocker = p.create(p.body("t0"))
        member = p.create(p.body("t1")) if endpoint == "batch" else None
        body = p.body("t0") if endpoint == "create" else {"moves": [{"reference": member["reference"], "table_id": "t0"}]}
        path = "/reservations" if endpoint == "create" else "/reservation-moves"
        p.expect(endpoint + "-failed-occupancy-key", "POST", path, body, token=p.a, key="occupancy-reuse", status=409, code="table_unavailable")
        p.call("POST", "/reservations/" + blocker["reference"] + "/cancel", {}, token=p.a)
        p.expect(endpoint + "-failed-occupancy-key", "POST", path, body, token=p.a, key="occupancy-reuse", status=201)
    for label, zone, local in [("berlin", "Europe/Berlin", "2035-03-25T02:30"), ("new-york", "America/New_York", "2035-03-11T02:30")]:
        # Future transitions allow ordinary PATCH cutoff validation to proceed.
        p.setup(fixture(zone=zone, opens="00:00", closes="06:00", slot=30, duration=90))
        r = p.create(p.body(local="2035-01-01T00:00"))
        p.expect("patch-" + label + "-skipped-time", "PATCH", "/reservations/" + r["reference"], {"starts_at_local": local}, token=p.a, status=422, code="invalid_local_time")
        p.expect("batch-" + label + "-skipped-time", "POST", "/reservation-moves", {"moves": [{"reference": r["reference"], "starts_at_local": local}]}, token=p.a, key="skip-batch", status=422, code="invalid_local_time")
    for tag, day in [("leap", "2024-02-29"), ("year-one", "0001-01-01"), ("year-max", "9999-12-31")]:
        p.setup()
        v = p.expect("calendar-" + tag, "GET", "/availability?restaurant_id=r&party_size=2&date=" + day)
        p.check("calendar-" + tag, isinstance(v, dict) and v.get("date") == day and bool(v.get("slots")) and v["slots"][0]["starts_at_local"] == day+"T18:10")
        p.expect("calendar-" + tag, "POST", "/reservations", p.body(local=day+"T18:10"), token=p.a, key="calendar", status=201)
    f = fixture()
    f["restaurants"][0]["opening_hours"] = [h for h in f["restaurants"][0]["opening_hours"] if h["weekday"] != "tue"]
    p.setup(f)
    r = p.create()
    baseline = p.state()
    for endpoint in ["patch", "batch"]:
        change = {"starts_at_local": "2035-06-05T18:10"}
        body = change if endpoint == "patch" else {"moves": [dict(reference=r["reference"], **change)]}
        p.expect(endpoint + "-closed-day", "PATCH" if endpoint == "patch" else "POST", "/reservations/" + r["reference"] if endpoint == "patch" else "/reservation-moves", body, token=p.a, key="closed", status=422, code="outside_opening_hours")
        p.check(endpoint + "-closed-day", p.state() == baseline)
