"""Tablekeeper Stage 1 application. HTTP transport is deliberately separate.

The lock is the transaction boundary, including reads and retry resolution. There
is no occupancy cache: confirmed reservation records are the source of truth.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import hashlib
import hmac
import math
import re
import secrets
import threading
from urllib.parse import parse_qs, unquote, urlsplit
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


UTC = timezone.utc
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
LOCAL_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}\Z")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
TIME_PATTERN = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z")
REFERENCE_PATTERN = re.compile(r"[A-Z0-9]{6,12}\Z")


class Refusal(Exception):
    def __init__(self, status: int, code: str, message: str | None = None):
        super().__init__(message or code.replace("_", " "))
        self.status = status
        self.code = code


def fail(status: int = 422, code: str = "validation_failed", message: str | None = None):
    raise Refusal(status, code, message)


def object_body(value):
    if not isinstance(value, dict):
        fail(400, "malformed_request", "Expected a JSON object")
    return value


def text_field(body, field, *, maximum=None):
    if field not in body:
        fail(message=f"Missing {field}")
    value = body[field]
    if not isinstance(value, str):
        fail(400, "malformed_request", f"{field} must be a string")
    if maximum is not None and (not value or len(value) > maximum):
        fail(message=f"Invalid {field} length")
    return value


def integer_field(body, field, *, minimum=1, party=False):
    if field not in body:
        fail(message=f"Missing {field}")
    value = body[field]
    if type(value) is not int:
        fail(422 if party else 400, "validation_failed" if party else "malformed_request")
    if value < minimum:
        fail(message=f"Invalid {field}")
    return value


def json_value(value):
    """Validate a portable JSON tree, including ignored fields in retry bodies."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, list):
        for item in value:
            json_value(item)
        return
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        for item in value.values():
            json_value(item)
        return
    fail(400, "malformed_request", "Invalid JSON value")


def same_json(left, right):
    # JSON booleans are not numbers, despite Python's True == 1.
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    return type(left) is type(right) and left == right


def local_datetime(value):
    if not isinstance(value, str):
        fail(400, "malformed_request", "starts_at_local must be a string")
    if not LOCAL_PATTERN.fullmatch(value):
        fail(message="Use a bare local YYYY-MM-DDTHH:MM")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        fail(message="Invalid local timestamp")


def resolve_local(local, zone):
    first = local.replace(tzinfo=zone, fold=0)
    if first.astimezone(UTC).astimezone(zone).replace(tzinfo=None) != local:
        fail(422, "invalid_local_time")
    return first


def timestamp(value):
    if not isinstance(value, str):
        fail()
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None or "T" not in value:
            fail()
        return parsed
    except (ValueError, OverflowError):
        fail()


def password_hash(password):
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1,
                         dklen=32, maxmem=64 * 1024 * 1024)
    return {"algorithm": "scrypt", "salt": salt.hex(), "key": key.hex()}


def password_matches(password, stored):
    key = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(stored["salt"]),
                         n=16384, r=8, p=1, dklen=32, maxmem=64 * 1024 * 1024)
    return hmac.compare_digest(key, bytes.fromhex(stored["key"]))


class Engine:
    def __init__(self):
        self._lock = threading.RLock()
        self._state = self._empty_state()

    @staticmethod
    def _empty_state():
        return {"schema": 1, "users": [], "restaurants": [], "tokens": {},
                "reservations": [], "receipts": []}

    def request(self, method: str, target: str, headers: Mapping[str, str],
                body: object | None) -> tuple[int, object | None]:
        with self._lock:
            try:
                result = self._dispatch(method, target, headers, body)
                return result[0], deepcopy(result[1])
            except Refusal as error:
                return error.status, {"error": {"code": error.code, "message": str(error)}}
            except (ValueError, OverflowError, UnicodeError, RecursionError):
                # Invalid numeric/date ranges or JSON trees must never become 5xx.
                return 422, {"error": {"code": "validation_failed", "message": "Invalid value"}}

    def _dispatch(self, method, target, headers, body):
        parts = urlsplit(target)
        path = parts.path
        segments = [unquote(p) for p in path.split("/")[1:]]
        query = parse_qs(parts.query, keep_blank_values=True)
        headers = {key.lower(): value for key, value in headers.items()}

        if method == "GET" and path == "/health":
            return 200, {"status": "ok"}
        if method == "POST" and path == "/_test/reset":
            self._state = self._fixture(object_body(body))
            return 204, None
        if method == "GET" and path == "/_test/export":
            return 200, {"track": "tablekeeper", "format_version": 1, "state": self._state}
        if method == "POST" and path == "/_test/import":
            envelope = object_body(body)
            try:
                if (envelope.get("track") != "tablekeeper" or
                        type(envelope.get("format_version")) is not int or
                        envelope["format_version"] != 1 or "state" not in envelope):
                    fail()
                candidate = self._import_state(envelope["state"])
            except (Refusal, ValueError, TypeError, KeyError, OverflowError, RecursionError):
                fail(message="Invalid export envelope or state")
            self._state = candidate
            return 204, None
        if method == "POST" and path in ("/auth/signup", "/auth/login"):
            return self._authenticate(path, object_body(body))
        if method == "GET" and path == "/restaurants":
            return 200, {"restaurants": [
                {key: r[key] for key in ("id", "name", "timezone")}
                for r in self._state["restaurants"]]}
        if method == "GET" and len(segments) == 2 and segments[0] == "restaurants":
            return 200, self._restaurant(segments[1])
        if method == "GET" and path == "/availability":
            return 200, self._availability(query)

        user = self._caller(headers)
        if method == "POST" and path in ("/reservations", "/reservation-moves"):
            data = object_body(body)
            json_value(data)
            key = headers.get("idempotency-key")
            if key is None or key == "":
                fail(400, "missing_idempotency_key")
            if not isinstance(key, str) or len(key) > 255:
                fail()
            for receipt in self._state["receipts"]:
                if (receipt["user_id"], receipt["method"], receipt["path"], receipt["key"]) == (
                        user["id"], method, path, key):
                    if not same_json(receipt["body"], data):
                        fail(409, "idempotency_key_reuse")
                    return 200, receipt["response"]
            if path == "/reservations":
                response = self._create(user, data)
            else:
                response = self._moves(user, data)
            self._state["receipts"].append({"user_id": user["id"], "method": method,
                "path": path, "key": key, "body": deepcopy(data), "response": deepcopy(response)})
            return 201, response
        if method == "GET" and path == "/reservations":
            records = [r for r in self._state["reservations"] if r["user_id"] == user["id"]]
            records.sort(key=lambda r: timestamp(r["starts_at"]).astimezone(UTC), reverse=True)
            return 200, {"reservations": [self._public(r) for r in records]}
        if len(segments) == 2 and segments[0] == "reservations":
            record = self._owned(segments[1], user)
            if method == "GET":
                return 200, self._public(record)
            if method == "PATCH":
                data = object_body(body)
                proposed = self._amend_candidate(record, data)
                self._check_occupancy([proposed], {record["reference"]})
                record.update(proposed)
                return 200, self._public(record)
        if (method == "POST" and len(segments) == 3 and segments[0] == "reservations"
                and segments[2] == "cancel"):
            if body is not None:
                object_body(body)
            record = self._owned(segments[1], user)
            if record["status"] != "cancelled":
                self._cutoff(record)
                record["status"] = "cancelled"
            return 200, self._public(record)
        fail(404, "not_found")

    @staticmethod
    def _email(data):
        email = text_field(data, "email")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+", email):
            fail(message="Invalid email")
        return email

    @staticmethod
    def _new_id(prefix, existing):
        while True:
            value = prefix + uuid.uuid4().hex
            if value not in existing:
                return value

    def _authenticate(self, path, data):
        email = self._email(data)
        password = text_field(data, "password")
        if path == "/auth/signup":
            if len(password) < 8:
                fail(message="Password must have at least eight characters")
            name = text_field(data, "display_name")
            if any(u["email"].casefold() == email.casefold() for u in self._state["users"]):
                fail(409, "email_taken")
            user = {"id": self._new_id("u_", {u["id"] for u in self._state["users"]}),
                    "email": email, "display_name": name, "password_hash": password_hash(password)}
            self._state["users"].append(user)
            status = 201
        else:
            user = next((u for u in self._state["users"]
                         if u["email"].casefold() == email.casefold()), None)
            if user is None or not password_matches(password, user["password_hash"]):
                fail(401, "unauthenticated")
            status = 200
        token = secrets.token_urlsafe(32)
        while token in self._state["tokens"]:
            token = secrets.token_urlsafe(32)
        self._state["tokens"][token] = user["id"]
        return status, {"user_id": user["id"], "display_name": user["display_name"], "token": token}

    def _caller(self, headers):
        auth = headers.get("authorization", "")
        if not isinstance(auth, str) or not re.fullmatch(r"(?i:Bearer) [^\s]+", auth):
            fail(401, "unauthenticated")
        user_id = self._state["tokens"].get(auth.split(" ", 1)[1])
        user = next((u for u in self._state["users"] if u["id"] == user_id), None)
        if user is None:
            fail(401, "unauthenticated")
        return user

    def _restaurant(self, restaurant_id, state=None):
        if not isinstance(restaurant_id, str) or not restaurant_id or len(restaurant_id) > 64:
            fail()
        state = self._state if state is None else state
        restaurant = next((r for r in state["restaurants"] if r["id"] == restaurant_id), None)
        if restaurant is None:
            fail(404, "not_found")
        return restaurant

    @staticmethod
    def _public(record):
        return {key: value for key, value in record.items() if key != "user_id"}

    def _owned(self, reference, user):
        record = next((r for r in self._state["reservations"]
                       if r["reference"] == reference and r["user_id"] == user["id"]), None)
        if record is None:
            fail(404, "not_found")
        return record

    @staticmethod
    def _hours(restaurant, local_date):
        return next((h for h in restaurant["opening_hours"]
                     if h["weekday"] == WEEKDAYS[local_date.weekday()]), None)

    def _booking_fields(self, data, state=None):
        restaurant_id = text_field(data, "restaurant_id", maximum=64)
        table_id = text_field(data, "table_id", maximum=64)
        local = local_datetime(text_field(data, "starts_at_local"))
        party_size = integer_field(data, "party_size", party=True)
        restaurant = self._restaurant(restaurant_id, state)
        table = next((t for t in restaurant["tables"] if t["id"] == table_id), None)
        if table is None:
            fail(404, "not_found")
        zone = ZoneInfo(restaurant["timezone"])
        start = resolve_local(local, zone)
        end = (start.astimezone(UTC) + timedelta(
            minutes=restaurant["reservation_duration_minutes"])).astimezone(zone)
        hours = self._hours(restaurant, local.date())
        if hours is None:
            fail(422, "outside_opening_hours")
        opening = datetime.fromisoformat(f"{local.date().isoformat()}T{hours['opens']}")
        closing = datetime.fromisoformat(f"{local.date().isoformat()}T{hours['closes']}")
        if local < opening or local >= closing or end.astimezone(UTC) > closing.replace(
                tzinfo=zone, fold=0).astimezone(UTC):
            fail(422, "outside_opening_hours")
        minutes = int((local - opening).total_seconds() // 60)
        if minutes % restaurant["slot_minutes"]:
            fail(422, "not_on_slot_grid")
        if party_size > table["capacity"]:
            fail(422, "party_exceeds_capacity")
        return {"restaurant_id": restaurant_id, "table_id": table_id, "party_size": party_size,
                "starts_at_local": data["starts_at_local"], "starts_at": start.isoformat(),
                "ends_at": end.isoformat()}

    @staticmethod
    def _overlap(left, right):
        if (left["restaurant_id"] != right["restaurant_id"] or
                left["table_id"] != right["table_id"]):
            return False
        return (timestamp(left["starts_at"]).astimezone(UTC) <
                timestamp(right["ends_at"]).astimezone(UTC) and
                timestamp(right["starts_at"]).astimezone(UTC) <
                timestamp(left["ends_at"]).astimezone(UTC))

    def _check_occupancy(self, proposed, excluded=frozenset(), state=None):
        state = self._state if state is None else state
        existing = [r for r in state["reservations"]
                    if r["status"] == "confirmed" and r["reference"] not in excluded]
        for index, candidate in enumerate(proposed):
            if candidate.get("status", "confirmed") != "confirmed":
                continue
            if any(self._overlap(candidate, other) for other in existing):
                fail(409, "table_unavailable")
            if any(other.get("status", "confirmed") == "confirmed" and self._overlap(candidate, other)
                   for other in proposed[:index]):
                fail(409, "table_unavailable")

    def _create(self, user, data):
        fields = self._booking_fields(data)
        self._check_occupancy([fields])
        references = {r["reference"] for r in self._state["reservations"]}
        reference = secrets.token_hex(5).upper()
        while reference in references:
            reference = secrets.token_hex(5).upper()
        record = {"reservation_id": self._new_id("res_", {
            r["reservation_id"] for r in self._state["reservations"]}),
            "reference": reference, "user_id": user["id"], **fields, "status": "confirmed",
            "created_at": datetime.now(UTC).isoformat()}
        self._state["reservations"].append(record)
        return self._public(record)

    def _cutoff(self, record):
        restaurant = self._restaurant(record["restaurant_id"])
        remaining = timestamp(record["starts_at"]).astimezone(UTC) - datetime.now(UTC)
        if remaining <= timedelta(minutes=restaurant["cancellation_cutoff_minutes"]):
            fail(409, "cutoff_passed")

    def _amend_candidate(self, record, data):
        if record["status"] == "cancelled":
            fail(409, "reservation_cancelled")
        self._cutoff(record)
        fields = {key: record[key] for key in (
            "restaurant_id", "table_id", "starts_at_local", "party_size")}
        fields.update({key: data[key] for key in ("table_id", "starts_at_local", "party_size") if key in data})
        return {**record, **self._booking_fields(fields)}

    def _moves(self, user, data):
        moves = data.get("moves")
        if not isinstance(moves, list) or not 1 <= len(moves) <= 8:
            fail()
        if any(not isinstance(m, dict) or not isinstance(m.get("reference"), str) for m in moves):
            fail()
        references = [m["reference"] for m in moves]
        if len(set(references)) != len(references):
            fail()
        originals, proposed = [], []
        restaurant_id = None
        for move in moves:
            record = self._owned(move["reference"], user)
            if restaurant_id is not None and record["restaurant_id"] != restaurant_id:
                fail()
            restaurant_id = record["restaurant_id"]
            candidate = self._amend_candidate(record, move)
            originals.append(record)
            proposed.append(candidate)
        self._check_occupancy(proposed, set(references))
        for original, candidate in zip(originals, proposed):
            original.update(candidate)
        return {"reservations": [self._public(r) for r in proposed]}

    def _availability(self, query):
        def parameter(name):
            if name not in query or not query[name][0]:
                fail(message=f"Missing {name}")
            return query[name][0]
        restaurant_id = parameter("restaurant_id")
        local_date_string = parameter("date")
        party_string = parameter("party_size")
        if not DATE_PATTERN.fullmatch(local_date_string) or not re.fullmatch(r"[0-9]+", party_string):
            fail()
        try:
            local_date = date.fromisoformat(local_date_string)
            party = int(party_string)
        except ValueError:
            fail()
        if party < 1:
            fail()
        restaurant = self._restaurant(restaurant_id)
        result = {"restaurant_id": restaurant_id, "date": local_date_string,
                  "timezone": restaurant["timezone"], "slots": []}
        hours = self._hours(restaurant, local_date)
        if hours is None:
            return result
        zone = ZoneInfo(restaurant["timezone"])
        local = datetime.fromisoformat(f"{local_date_string}T{hours['opens']}")
        close = datetime.fromisoformat(f"{local_date_string}T{hours['closes']}")
        close_utc = close.replace(tzinfo=zone, fold=0).astimezone(UTC)
        while local < close:
            try:
                start = resolve_local(local, zone)
            except Refusal as error:
                if error.code != "invalid_local_time":
                    raise
                local += timedelta(minutes=restaurant["slot_minutes"])
                continue
            end_utc = start.astimezone(UTC) + timedelta(minutes=restaurant["reservation_duration_minutes"])
            if end_utc <= close_utc:
                available = []
                for table in restaurant["tables"]:
                    candidate = {"restaurant_id": restaurant_id, "table_id": table["id"],
                                 "starts_at": start.isoformat(), "ends_at": end_utc.isoformat()}
                    if table["capacity"] >= party and not any(
                            r["status"] == "confirmed" and self._overlap(candidate, r)
                            for r in self._state["reservations"]):
                        available.append(table["id"])
                result["slots"].append({"starts_at_local": local.isoformat(timespec="minutes"),
                    "starts_at": start.isoformat(), "available_table_ids": available})
            local += timedelta(minutes=restaurant["slot_minutes"])
        return result

    @staticmethod
    def _restaurants(rows):
        if not isinstance(rows, list):
            fail(400, "malformed_request")
        restaurants, ids = [], set()
        for row in rows:
            row = object_body(row)
            restaurant = {key: text_field(row, key, maximum=64 if key == "id" else None)
                          for key in ("id", "name", "timezone")}
            if restaurant["id"] in ids:
                fail()
            ids.add(restaurant["id"])
            try:
                ZoneInfo(restaurant["timezone"])
            except (ZoneInfoNotFoundError, ValueError):
                fail()
            for key in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes"):
                restaurant[key] = integer_field(row, key, minimum=0 if key == "cancellation_cutoff_minutes" else 1)
                # All minute counts must be representable by datetime arithmetic.
                try:
                    timedelta(minutes=restaurant[key])
                except OverflowError:
                    fail()
            hours, tables = row.get("opening_hours"), row.get("tables")
            if not isinstance(hours, list) or not isinstance(tables, list):
                fail(400, "malformed_request")
            restaurant["opening_hours"], restaurant["tables"] = [], []
            days, table_ids = set(), set()
            for entry in hours:
                entry = object_body(entry)
                opening = {key: text_field(entry, key) for key in ("weekday", "opens", "closes")}
                if (opening["weekday"] not in WEEKDAYS or opening["weekday"] in days or
                        not TIME_PATTERN.fullmatch(opening["opens"]) or
                        not TIME_PATTERN.fullmatch(opening["closes"]) or opening["opens"] >= opening["closes"]):
                    fail()
                days.add(opening["weekday"])
                restaurant["opening_hours"].append(opening)
            for entry in tables:
                entry = object_body(entry)
                table = {"id": text_field(entry, "id", maximum=64), "label": text_field(entry, "label"),
                         "capacity": integer_field(entry, "capacity")}
                if table["id"] in table_ids:
                    fail()
                table_ids.add(table["id"])
                restaurant["tables"].append(table)
            restaurants.append(restaurant)
        return restaurants

    def _fixture(self, fixture):
        state = self._empty_state()
        json_value(fixture)
        state["restaurants"] = self._restaurants(fixture.get("restaurants", []))
        users = fixture.get("users", [])
        reservations = fixture.get("reservations", [])
        if not isinstance(users, list) or not isinstance(reservations, list):
            fail(400, "malformed_request")
        ids, emails = set(), set()
        for row in users:
            row = object_body(row)
            user_id = text_field(row, "id", maximum=64)
            email = self._email(row)
            password = text_field(row, "password")
            if user_id in ids or email.casefold() in emails:
                fail()
            ids.add(user_id)
            emails.add(email.casefold())
            state["users"].append({"id": user_id, "email": email,
                "display_name": text_field(row, "display_name"), "password_hash": password_hash(password)})
        reservation_ids, references = set(), set()
        for row in reservations:
            row = object_body(row)
            user_id = text_field(row, "user_id", maximum=64)
            reservation_id = text_field(row, "id", maximum=64)
            reference = text_field(row, "reference")
            if (user_id not in ids or reservation_id in reservation_ids or reference in references
                    or not REFERENCE_PATTERN.fullmatch(reference)):
                fail()
            fields = self._booking_fields(row, state)
            record = {"reservation_id": reservation_id, "reference": reference,
                      "user_id": user_id, **fields, "status": "confirmed",
                      "created_at": datetime.now(UTC).isoformat()}
            reservation_ids.add(reservation_id)
            references.add(reference)
            state["reservations"].append(record)
        self._check_occupancy(state["reservations"], references, state)
        return state

    def _validate_record(self, row, state, *, owner_required=True):
        row = object_body(row)
        fields = self._booking_fields(row, state)
        if any(row.get(key) != value for key, value in fields.items()):
            fail()
        record = {"reservation_id": text_field(row, "reservation_id", maximum=64),
                  "reference": text_field(row, "reference"), **fields,
                  "status": text_field(row, "status"), "created_at": text_field(row, "created_at")}
        if not REFERENCE_PATTERN.fullmatch(record["reference"]) or record["status"] not in ("confirmed", "cancelled"):
            fail()
        timestamp(record["created_at"])
        if owner_required:
            record["user_id"] = text_field(row, "user_id", maximum=64)
            if record["user_id"] not in {u["id"] for u in state["users"]}:
                fail()
        return record

    def _import_state(self, source):
        source = object_body(source)
        json_value(source)
        if type(source.get("schema")) is not int or source["schema"] != 1:
            fail()
        state = self._empty_state()
        state["restaurants"] = self._restaurants(source["restaurants"])
        if not isinstance(source["users"], list):
            fail()
        user_ids, emails = set(), set()
        for row in source["users"]:
            row = object_body(row)
            user = {"id": text_field(row, "id", maximum=64), "email": self._email(row),
                    "display_name": text_field(row, "display_name")}
            hashed = row.get("password_hash")
            if (not isinstance(hashed, dict) or hashed.get("algorithm") != "scrypt"
                    or not isinstance(hashed.get("salt"), str) or
                    not re.fullmatch(r"[0-9a-f]{32}", hashed["salt"]) or
                    not isinstance(hashed.get("key"), str) or
                    not re.fullmatch(r"[0-9a-f]{64}", hashed["key"])):
                fail()
            if user["id"] in user_ids or user["email"].casefold() in emails:
                fail()
            user_ids.add(user["id"])
            emails.add(user["email"].casefold())
            user["password_hash"] = {key: hashed[key] for key in ("algorithm", "salt", "key")}
            state["users"].append(user)
        tokens = source["tokens"]
        if not isinstance(tokens, dict) or any(
                not isinstance(token, str) or not token or not isinstance(owner, str) or owner not in user_ids
                for token, owner in tokens.items()):
            fail()
        state["tokens"] = deepcopy(tokens)
        if not isinstance(source["reservations"], list) or not isinstance(source["receipts"], list):
            fail()
        references, reservation_ids = set(), set()
        for row in source["reservations"]:
            record = self._validate_record(row, state)
            if record["reference"] in references or record["reservation_id"] in reservation_ids:
                fail()
            references.add(record["reference"])
            reservation_ids.add(record["reservation_id"])
            state["reservations"].append(record)
        self._check_occupancy(state["reservations"], references, state)
        identities = {r["reference"]: r for r in state["reservations"]}
        receipt_keys = set()
        for row in source["receipts"]:
            row = object_body(row)
            user_id = text_field(row, "user_id", maximum=64)
            method = text_field(row, "method")
            path = text_field(row, "path")
            key = text_field(row, "key", maximum=255)
            if user_id not in user_ids or method != "POST" or path not in ("/reservations", "/reservation-moves"):
                fail()
            identity = (user_id, method, path, key)
            if identity in receipt_keys:
                fail()
            receipt_keys.add(identity)
            body = object_body(row["body"])
            response = object_body(row["response"])
            if path == "/reservations":
                snapshots = [response]
                original_fields = self._booking_fields(body, state)
                if any(response.get(k) != v for k, v in original_fields.items()):
                    fail()
            else:
                moves = body.get("moves")
                snapshots = response.get("reservations")
                if (not isinstance(moves, list) or not 1 <= len(moves) <= 8 or
                        not isinstance(snapshots, list) or len(snapshots) != len(moves)):
                    fail()
                move_refs = [object_body(m).get("reference") for m in moves]
                if any(not isinstance(ref, str) for ref in move_refs) or len(set(move_refs)) != len(move_refs):
                    fail()
                if move_refs != [object_body(s).get("reference") for s in snapshots]:
                    fail()
                if len({object_body(s).get("restaurant_id") for s in snapshots}) != 1:
                    fail()
                for move, snapshot in zip(moves, snapshots):
                    amended_fields = {k: snapshot[k] for k in (
                        "restaurant_id", "table_id", "party_size", "starts_at_local")}
                    amended_fields.update({k: move[k] for k in (
                        "table_id", "party_size", "starts_at_local") if k in move})
                    self._booking_fields(amended_fields, state)
                    if any(move[k] != snapshot.get(k) for k in ("table_id", "party_size", "starts_at_local") if k in move):
                        fail()
            for snapshot in snapshots:
                saved = self._validate_record(snapshot, state, owner_required=False)
                current = identities.get(saved["reference"])
                if (saved["status"] != "confirmed" or current is None or current["user_id"] != user_id or
                        any(current[k] != saved[k] for k in ("reservation_id", "restaurant_id", "created_at"))):
                    fail()
            self._check_occupancy(snapshots, references, state)
            state["receipts"].append({"user_id": user_id, "method": method, "path": path,
                                     "key": key, "body": deepcopy(body), "response": deepcopy(response)})
        return state
