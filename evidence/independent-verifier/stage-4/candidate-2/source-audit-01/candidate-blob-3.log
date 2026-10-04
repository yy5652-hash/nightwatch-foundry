"""Tablekeeper Stage 4 application. HTTP transport is deliberately separate.

The lock is the transaction boundary, including reads and retry resolution. There
is no occupancy cache: confirmed reservation records are the source of truth.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from functools import cmp_to_key
import hashlib
import hmac
import re
import secrets
import sys
import threading
from urllib.parse import parse_qs, unquote, urlsplit
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from json_codec import (EXACT_PROFILE, LEGACY_PROFILE, JsonCodecError, compare_numbers,
                        add_integers, copy_json, is_integral, is_number, multiply_integer, sum_at_least,
                        same_value, to_integer, validate_json)


UTC = timezone.utc
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
LOCAL_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}\Z")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
TIME_PATTERN = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z")
REFERENCE_PATTERN = re.compile(r"[A-Z0-9]{6,12}\Z")
EXPLICIT_PATTERN = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2})[Tt]"
    r"([0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]+))?([Zz]|[+-][0-9]{2}:[0-9]{2})\Z")
SECOND_US = 1_000_000
MINUTE_US = 60 * SECOND_US
DAY_US = 86_400 * SECOND_US


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
    if not is_number(value):
        fail(422 if party else 400, "validation_failed" if party else "malformed_request")
    if not is_integral(value) or compare_numbers(value, minimum) < 0:
        fail(message=f"Invalid {field}")
    return value


def json_value(value):
    """Validate a portable JSON tree, including ignored fields in retry bodies."""
    try:
        validate_json(value)
    except JsonCodecError:
        fail(400, "malformed_request", "Invalid JSON value")


def same_json(left, right, *, profile=EXACT_PROFILE):
    return same_value(left, right, profile=profile)


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
    # ZoneInfo uses the pre-transition offset for fold 0 and post-transition
    # offset for fold 1. A forward jump is a gap; a backward jump is a repeat.
    # This avoids constructing UTC dates outside the local calendar's bounds.
    if local.replace(tzinfo=zone, fold=1).utcoffset() > first.utcoffset():
        fail(422, "invalid_local_time")
    return first


def delta_us(delta):
    return delta.days * DAY_US + delta.seconds * SECOND_US + delta.microseconds


def instant(value):
    """Exact absolute microseconds, with an unrestricted integer day number."""
    return (value.toordinal() * DAY_US + value.hour * 3600 * SECOND_US +
            value.minute * MINUTE_US + value.second * SECOND_US + value.microsecond -
            delta_us(value.utcoffset()))


def naive_at(value):
    ordinal, remainder = divmod(value, DAY_US)
    day = date.fromordinal(ordinal)
    seconds, microsecond = divmod(remainder, SECOND_US)
    hour, seconds = divmod(seconds, 3600)
    minute, second = divmod(seconds, 60)
    return datetime(day.year, day.month, day.day, hour, minute, second, microsecond)


def wire_timestamp(value):
    """RFC3339 numeric-offset representation of the exact resolved instant.

    Historical IANA offsets may contain seconds. Use the nearest representable
    minute offset, adjusting the displayed clock rather than rounding the
    instant. At an equal distance the lower numerical offset wins.
    """
    original_offset = delta_us(value.utcoffset())
    if original_offset % MINUTE_US == 0:
        return value.isoformat()
    absolute = instant(value)
    minimum_clock = DAY_US
    maximum_clock = (date.max.toordinal() + 1) * DAY_US - 1
    # ceil division is exact for both positive and negative integers.
    lower = max(-1439, -((absolute - minimum_clock) // MINUTE_US))
    upper = min(1439, (maximum_clock - absolute) // MINUTE_US)
    if lower > upper:
        fail(message="Instant has no representable RFC3339 timestamp")
    floor = original_offset // MINUTE_US
    candidates = {min(upper, max(lower, floor)), min(upper, max(lower, floor + 1))}
    selected = min(candidates, key=lambda offset: (abs(offset * MINUTE_US - original_offset), offset))
    wall = naive_at(absolute + selected * MINUTE_US)
    return wall.replace(tzinfo=timezone(timedelta(minutes=selected))).isoformat()


def assert_booking_fields(row, expected):
    """Import validates timestamp instants without rewriting original strings."""
    for key, value in expected.items():
        if key in ("starts_at", "ends_at"):
            if instant(timestamp(row.get(key))) != instant(timestamp(value)):
                fail()
        elif key == "table_ids" and key not in row and value == [row.get("table_id")]:
            # Successful Stage 1 originals retain their singleton-only shape.
            continue
        elif key == "accepted_terms" and key not in row:
            # Older successful responses never acquire later-stage fields.
            continue
        elif not same_json(row.get(key), value):
            fail()


def zoned_at(value, zone, hints):
    """Convert an absolute instant without requiring a representable UTC date.

    Ordinary instants use ZoneInfo's UTC conversion. At calendar boundaries,
    invert the local offset relation and verify the exact instant. Both folds
    are considered for an end time, which may be in the second repeated hour.
    """
    try:
        return zone.fromutc(naive_at(value).replace(tzinfo=zone))
    except (ValueError, OverflowError):
        pass
    pending = [delta_us(hint.replace(fold=fold).utcoffset()) for hint in hints for fold in (0, 1)]
    visited = set()
    while pending:
        offset = pending.pop()
        if offset in visited:
            continue
        visited.add(offset)
        try:
            local = naive_at(value + offset)
        except (ValueError, OverflowError):
            continue
        is_gap = local.replace(tzinfo=zone, fold=1).utcoffset() > local.replace(
            tzinfo=zone, fold=0).utcoffset()
        for fold in (0, 1):
            candidate = local.replace(tzinfo=zone, fold=fold)
            actual_offset = delta_us(candidate.utcoffset())
            if not is_gap and actual_offset == offset and instant(candidate) == value:
                return candidate
            if actual_offset not in visited:
                pending.append(actual_offset)
    fail(message="Instant has no representable local calendar time")


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


def explicit_instant(value):
    """Exact closure instant, including decimal digits beyond microseconds."""
    if not isinstance(value, str):
        fail()
    match = EXPLICIT_PATTERN.fullmatch(value)
    if match is None:
        fail()
    day, clock, fraction, offset = match.groups()
    try:
        wall = datetime.fromisoformat(day + "T" + clock)
        if offset.lower() == "z":
            minutes = 0
        else:
            hours, mins = int(offset[1:3]), int(offset[4:6])
            if hours > 23 or mins > 59:
                fail()
            minutes = (hours * 60 + mins) * (-1 if offset[0] == "-" else 1)
        base = instant(wall.replace(tzinfo=timezone(timedelta(minutes=minutes))))
        return Fraction(base) + (Fraction(int(fraction) * SECOND_US, 10 ** len(fraction)) if fraction else 0)
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
        # Base fixture counts, capacities and decimal queries have no published
        # digit maximum. Initialize before transport accepts requests so its
        # JSON decoder/encoder and our query conversion preserve exact integers.
        sys.set_int_max_str_digits(0)
        self._lock = threading.RLock()
        self._state = self._empty_state()

    @staticmethod
    def _empty_state():
        return {"schema": 4, "users": [], "restaurants": [], "tokens": {},
                "reservations": [], "receipts": [], "policies": {},
                "histories": {}, "history_origins": {}, "series": {},
                "restaurant_revisions": {}, "plans": {}, "closures": []}

    def request(self, method: str, target: str, headers: Mapping[str, str],
                body: object | None) -> tuple[int, object | None]:
        with self._lock:
            try:
                result = self._dispatch(method, target, headers, body)
                # Capture detached containers before releasing the state lock;
                # transport encoding may overlap later independent writes.
                return result[0], copy_json(result[1])
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
                        not same_json(envelope.get("format_version"), 1) or "state" not in envelope):
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

        if method == "GET" and len(segments) == 3 and segments[0] == "restaurants" and segments[2] == "policies":
            restaurant = self._restaurant(segments[1])
            return 200, {"policies": self._state["policies"].get(restaurant["id"], [])}
        if method == "GET" and ((len(segments) == 3 and segments[0] == "reservations"
                and segments[2] in ("history", "decision")) or
                (len(segments) == 2 and segments[0] == "series")):
            try:
                user = self._caller(headers)
            except Refusal:
                fail(404, "not_found")
            if segments[0] == "series":
                return 200, self._series_public(self._owned_series(segments[1], user))
            record = self._owned(segments[1], user)
            if segments[2] == "history":
                return 200, {"reference": record["reference"], "entries": self._state["histories"][record["reference"]]}
            return 200, {key: record[key] for key in ("reference", "revision", "accepted_terms")}

        user = self._caller(headers)
        policy_write = len(segments) == 3 and segments[0] == "restaurants" and segments[2] == "policies"
        replan_write = len(segments) == 3 and segments[0] == "restaurants" and segments[2] == "replans"
        apply_write = len(segments) == 5 and segments[0] == "restaurants" and segments[2] == "replans" and segments[4] == "apply"
        series_write = len(segments) == 3 and segments[0] == "series" and segments[2] == "amend"
        if method == "POST" and (path in ("/reservations", "/reservation-moves", "/series") or
                policy_write or replan_write or apply_write or series_write):
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
                    if not same_json(receipt["body"], data, profile=receipt["numeric_profile"]):
                        fail(409, "idempotency_key_reuse")
                    return 200, receipt["response"]
            saved_body = copy_json(data)
            if path == "/reservations":
                record = self._create(user, data)
                response = self._public(record)
                entries = [self._history_entry(record, None, "created", [])]
                def commit():
                    self._state["reservations"].append(record)
                    self._state["histories"][record["reference"]] = entries
                    self._state["history_origins"][record["reference"]] = "stage3"
                    self._bump([record["restaurant_id"]])
            elif path == "/reservation-moves":
                originals, proposed = self._moves(user, data)
                response = {"reservations": [self._public(r) for r in proposed]}
                histories = self._prepared_histories(originals, proposed)
                def commit():
                    self._commit_changes(originals, proposed, histories)
            elif path == "/series":
                agreement, generated, histories = self._series_candidate(user, data)
                response = self._series_public(agreement, generated)
                def commit():
                    self._state["reservations"].extend(generated)
                    self._state["histories"].update(histories)
                    self._state["history_origins"].update({r["reference"]: "stage3" for r in generated})
                    self._state["series"][agreement["series_id"]] = agreement
                    self._bump([generated[0]["restaurant_id"]])
            elif replan_write:
                restaurant = self._manager_restaurant(segments[1], user)
                plan = self._replan_candidate(restaurant, data)
                response = self._plan_public(plan)
                def commit():
                    self._state["plans"][plan["plan_id"]] = plan
            elif apply_write:
                restaurant = self._manager_restaurant(segments[1], user)
                plan, originals, proposed, histories = self._apply_candidate(restaurant, segments[3])
                response = {"plan_id": plan["plan_id"],
                            "restaurant_revision": plan["restaurant_revision"] + 1,
                            "reservations": [self._public(r) for r in proposed]}
                def commit():
                    changed = []
                    for old, new in zip(originals, proposed):
                        if new["revision"] != old["revision"]:
                            old.clear()
                            old.update(new)
                            changed.append(new["reference"])
                    self._state["histories"].update(histories)
                    self._state["closures"].append({"restaurant_id": restaurant["id"],
                        "plan_id": plan["plan_id"], **copy_json(plan["closure"])})
                    plan["applied"] = True
                    self._bump([restaurant["id"]], changed, exception=False)
            elif series_write:
                agreement, originals, proposed = self._series_amend_candidate(segments[1], user, data)
                histories = self._prepared_histories(originals, proposed)
                response = self._series_public(agreement, proposed)
                def commit():
                    self._commit_changes(originals, proposed, histories, exception=False)
            else:
                restaurant = self._restaurant(segments[1])
                if user["id"] not in restaurant.get("manager_user_ids", []):
                    fail(403, "forbidden")
                policies = self._state["policies"].get(restaurant["id"], [])
                response = {**self._policy(data, restaurant), "policy_version": len(policies) + 1}
                saved_policy = copy_json(response)
                def commit():
                    self._state["policies"].setdefault(restaurant["id"], []).append(saved_policy)
                    self._bump([restaurant["id"]])
            receipt = {"user_id": user["id"], "method": method,
                "path": path, "key": key, "body": saved_body, "response": copy_json(response),
                "numeric_profile": EXACT_PROFILE}
            commit()
            self._state["receipts"].append(receipt)
            return 201, response
        if method == "GET" and path == "/reservations":
            records = [r for r in self._state["reservations"] if r["user_id"] == user["id"]]
            records.sort(key=lambda r: instant(timestamp(r["starts_at"])), reverse=True)
            return 200, {"reservations": [self._public(r) for r in records]}
        if len(segments) == 2 and segments[0] == "reservations":
            record = self._owned(segments[1], user)
            if method == "GET":
                return 200, self._public(record)
            if method == "PATCH":
                data = object_body(body)
                proposed = self._amend_candidate(record, data)
                self._check_occupancy([proposed], {record["reference"]})
                histories = self._prepared_histories([record], [proposed])
                response = copy_json(self._public(proposed))
                self._commit_changes([record], [proposed], histories)
                return 200, response
        if (method == "POST" and len(segments) == 3 and segments[0] == "reservations"
                and segments[2] == "cancel"):
            if body is not None:
                object_body(body)
            record = self._owned(segments[1], user)
            if record["status"] != "cancelled":
                self._cutoff(record)
                proposed = {**record, "status": "cancelled", "revision": record["revision"] + 1}
                entries = self._state["histories"][record["reference"]]
                histories = {record["reference"]: [*entries, self._history_entry(proposed, record, "cancelled", entries)]}
                response = copy_json(self._public(proposed))
                self._commit_changes([record], [proposed], histories, exception=False)
                return 200, response
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

    @classmethod
    def _public(cls, record):
        result = {key: value for key, value in record.items() if key != "user_id"}
        result["table_ids"] = list(cls._members(record))
        return result


    def _owned(self, reference, user):
        record = next((r for r in self._state["reservations"]
                       if r["reference"] == reference and r["user_id"] == user["id"]), None)
        if record is None:
            fail(404, "not_found")
        return record

    @staticmethod
    def _base_terms(restaurant):
        return {"policy_version": 0,
                **{key: restaurant[key] for key in ("slot_minutes", "reservation_duration_minutes",
                    "cancellation_cutoff_minutes", "opening_hours")},
                "capacities": {table["id"]: table["capacity"] for table in restaurant["tables"]}}

    def _terms(self, restaurant, local_date, state=None):
        state = self._state if state is None else state
        eligible = [policy for policy in state["policies"].get(restaurant["id"], [])
                    if date.fromisoformat(policy["effective_from"]) <= local_date]
        if not eligible:
            return copy_json(self._base_terms(restaurant))
        policy = max(eligible, key=lambda p: (p["effective_from"], to_integer(p["policy_version"])))
        return copy_json({key: value for key, value in policy.items() if key != "effective_from"})

    @staticmethod
    def _decision_restaurant(restaurant, terms):
        return {**restaurant,
                **{key: terms[key] for key in ("slot_minutes", "reservation_duration_minutes",
                    "cancellation_cutoff_minutes", "opening_hours")},
                "tables": [{**table, "capacity": terms["capacities"][table["id"]]}
                           for table in restaurant["tables"]]}

    @staticmethod
    def _policy(data, restaurant):
        # Every invalid complete policy, including a wrong field type, is 422.
        try:
            effective = data.get("effective_from")
            if not isinstance(effective, str) or not DATE_PATTERN.fullmatch(effective):
                fail()
            date.fromisoformat(effective)
            result = {"effective_from": effective}
            for key, lower, upper in (("slot_minutes", 1, 1440),
                    ("reservation_duration_minutes", 1, 1440),
                    ("cancellation_cutoff_minutes", 0, 10080)):
                value = data.get(key)
                if not is_number(value) or not is_integral(value) or compare_numbers(value, lower) < 0 or compare_numbers(value, upper) > 0:
                    fail()
                result[key] = value
            hours = data.get("opening_hours")
            if not isinstance(hours, list):
                fail()
            result["opening_hours"], days = [], set()
            for entry in hours:
                if not isinstance(entry, dict):
                    fail()
                row = {key: entry.get(key) for key in ("weekday", "opens", "closes")}
                if (any(not isinstance(v, str) for v in row.values()) or
                        row["weekday"] not in WEEKDAYS or row["weekday"] in days or
                        not TIME_PATTERN.fullmatch(row["opens"]) or not TIME_PATTERN.fullmatch(row["closes"]) or
                        row["opens"] >= row["closes"]):
                    fail()
                days.add(row["weekday"])
                result["opening_hours"].append(row)
            capacities = data.get("capacities")
            if not isinstance(capacities, dict) or set(capacities) != {t["id"] for t in restaurant["tables"]}:
                fail()
            for value in capacities.values():
                if not is_number(value) or not is_integral(value) or compare_numbers(value, 1) < 0 or compare_numbers(value, 100) > 0:
                    fail()
            result["capacities"] = copy_json(capacities)
            return result
        except (Refusal, ValueError, TypeError):
            fail(message="Invalid complete policy")

    def _valid_terms(self, value, restaurant, state):
        value = object_body(value)
        version = integer_field(value, "policy_version", minimum=0, party=True)
        if same_json(version, 0):
            expected = self._base_terms(restaurant)
        else:
            policy = next((p for p in state["policies"].get(restaurant["id"], [])
                           if same_json(p["policy_version"], version)), None)
            if policy is None:
                fail()
            expected = {key: val for key, val in policy.items() if key != "effective_from"}
        if not same_json(value, expected):
            fail(message="Invalid accepted terms")
        return copy_json(value)

    @classmethod
    def _changes(cls, record, previous=None):
        members = cls._members(record)
        before = cls._members(previous) if previous else None
        changes = []
        if previous is None or members != before:
            pair = len(members) == 2 or (before is not None and len(before) == 2)
            changes.append({"field": "table_ids" if pair else "table_id",
                            "from": None if before is None else (list(before) if pair else before[0]),
                            "to": list(members) if pair else members[0]})
        for key in ("starts_at_local", "party_size"):
            if previous is None or not same_json(previous[key], record[key]):
                changes.append({"field": key, "from": None if previous is None else previous[key], "to": record[key]})
        return changes

    def _history_entry(self, record, previous, event, entries):
        at = record["created_at"] if event == "created" else wire_timestamp(datetime.now(UTC))
        if entries and instant(timestamp(at)) < instant(timestamp(entries[-1]["at"])):
            at = entries[-1]["at"]
        return {"seq": len(entries) + 1, "at": at, "event": event,
                "changes": [] if event == "cancelled" else copy_json(self._changes(record, previous)),
                "revision": record["revision"], "accepted_terms": copy_json(record["accepted_terms"])}

    def _prepared_histories(self, originals, proposed):
        histories = {}
        for old, new in zip(originals, proposed):
            if new["revision"] != old["revision"]:
                entries = self._state["histories"][old["reference"]]
                histories[old["reference"]] = [*entries, self._history_entry(new, old, "changed", entries)]
        return histories

    def _bump(self, restaurants, references=(), *, exception=True):
        for restaurant_id in set(restaurants):
            counters = self._state["restaurant_revisions"]
            counters[restaurant_id] = counters.get(restaurant_id, 0) + 1
        references = set(references)
        for agreement in self._state["series"].values():
            affected = [o for o in agreement["occurrences"] if o["reference"] in references]
            if affected:
                agreement["revision"] += 1
                if exception:
                    for occurrence in affected:
                        occurrence["exception"] = True

    def _commit_changes(self, originals, proposed, histories, *, exception=True):
        changed = [(old, new) for old, new in zip(originals, proposed) if old["revision"] != new["revision"]]
        for old, new in changed:
            old.clear()
            old.update(new)
        self._state["histories"].update(histories)
        self._bump([new["restaurant_id"] for _, new in changed],
                   [new["reference"] for _, new in changed], exception=exception)

    def _owned_series(self, series_id, user):
        agreement = self._state["series"].get(series_id)
        if agreement is None or agreement["user_id"] != user["id"]:
            fail(404, "not_found")
        return agreement

    def _manager_restaurant(self, restaurant_id, user):
        restaurant = self._restaurant(restaurant_id)
        if user["id"] not in restaurant.get("manager_user_ids", []):
            fail(403, "forbidden")
        return restaurant

    @staticmethod
    def _closure(restaurant, data):
        table_id = text_field(data, "table_id", maximum=64)
        if table_id not in {t["id"] for t in restaurant["tables"]}:
            fail(404, "not_found")
        if explicit_instant(text_field(data, "from")) >= explicit_instant(text_field(data, "to")):
            fail(message="Closure must have a positive interval")
        return {"table_id": table_id, "from": data["from"], "to": data["to"]}

    @staticmethod
    def _interval_overlap(record, closure):
        return (instant(timestamp(record["starts_at"])) < explicit_instant(closure["to"]) and
                explicit_instant(closure["from"]) < instant(timestamp(record["ends_at"])))

    @classmethod
    def _closure_overlap(cls, record, closure):
        return (record["restaurant_id"] == closure["restaurant_id"] and
                closure["table_id"] in cls._members(record) and cls._interval_overlap(record, closure))

    def _blocked(self, record, state=None):
        state = self._state if state is None else state
        return (any(r["status"] == "confirmed" and self._overlap(record, r) for r in state["reservations"])
                or any(self._closure_overlap(record, c) for c in state["closures"]))

    @staticmethod
    def _plan_public(plan):
        return {key: plan[key] for key in ("plan_id", "restaurant_revision", "closure",
                                          "assignments", "moved_count", "unused_seats")}

    @classmethod
    def _reseated(cls, record, members):
        changed = set(cls._members(record)) != set(members)
        if not changed:
            return dict(record)
        result = {key: value for key, value in record.items() if key not in ("table_id", "table_ids")}
        result.update(table_ids=list(members), revision=record["revision"] + 1)
        if len(members) == 1:
            result["table_id"] = members[0]
        return result

    def _replan_candidate(self, restaurant, data):
        closure = self._closure(restaurant, data)
        records = sorted((r for r in self._state["reservations"] if r["status"] == "confirmed"
                          and r["restaurant_id"] == restaurant["id"] and self._interval_overlap(r, closure)),
                         key=lambda r: r["reference"])
        if len(restaurant["tables"]) > 6 or len(restaurant.get("combinable", [])) > 4 or len(records) > 6:
            fail(422, "planning_limit")
        refs = {r["reference"] for r in records}
        fixed = [r for r in self._state["reservations"] if r["status"] == "confirmed" and r["reference"] not in refs]
        closures = [*self._state["closures"], {"restaurant_id": restaurant["id"], **closure}]
        options = [[t["id"]] for t in restaurant["tables"]] + restaurant.get("combinable", [])
        choices = []
        for record in records:
            permitted = []
            for rank, members in enumerate(options):
                counts = [record["accepted_terms"]["capacities"][m] for m in members]
                if not self._capacity_fits(counts, record["party_size"]):
                    continue
                candidate = {**record, "table_ids": list(members)}
                if any(self._overlap(candidate, r) for r in fixed) or any(self._closure_overlap(candidate, c) for c in closures):
                    continue
                capacity = counts[0] if len(counts) == 1 else add_integers(*counts)
                unused = 0 if same_json(capacity, record["party_size"]) else add_integers(capacity, multiply_integer(record["party_size"], -1))
                permitted.append((set(self._members(record)) != set(members), unused, rank, candidate))
            if not permitted:
                fail(409, "no_feasible_plan")
            def order(a, b):
                return ((a[0] > b[0]) - (a[0] < b[0]) or compare_numbers(a[1], b[1])
                        or (a[2] > b[2]) - (a[2] < b[2]))
            choices.append(sorted(permitted, key=cmp_to_key(order)))
        # The bounded search uses lower bounds independent of occupancy; they
        # can only understate an achievable objective and therefore prune safely.
        count = len(records)
        min_moves, min_unused, min_ranks = [0] * (count + 1), [0] * (count + 1), [()] * (count + 1)
        for index in range(count - 1, -1, -1):
            min_moves[index] = min_moves[index + 1] + min(int(o[0]) for o in choices[index])
            surplus = min((o[1] for o in choices[index]), key=cmp_to_key(compare_numbers))
            min_unused[index] = add_integers(surplus, min_unused[index + 1])
            min_ranks[index] = (min(o[2] for o in choices[index]),) + min_ranks[index + 1]
        best, selected = None, None
        def search(index, moved, unused, ranks, assigned):
            nonlocal best, selected
            lower_moved = moved + min_moves[index]
            if best is not None:
                if lower_moved > best[0]:
                    return
                if lower_moved == best[0]:
                    comparison = compare_numbers(add_integers(unused, min_unused[index]), best[1])
                    if comparison > 0 or (comparison == 0 and ranks + min_ranks[index] >= best[2]):
                        return
            if index == count:
                best, selected = (moved, unused, ranks), list(assigned)
                return
            for change, surplus, rank, candidate in choices[index]:
                if any(self._overlap(candidate, old) for old in assigned):
                    continue
                search(index + 1, moved + int(change), add_integers(unused, surplus), ranks + (rank,), [*assigned, candidate])
        search(0, 0, 0, (), [])
        if best is None:
            fail(409, "no_feasible_plan")
        return {"plan_id": self._new_id("plan_", set(self._state["plans"])), "restaurant_id": restaurant["id"],
                "restaurant_revision": self._state["restaurant_revisions"][restaurant["id"]],
                "closure": closure, "assignments": [{"reference": r["reference"], "table_ids": list(self._members(s)),
                    "changed": set(self._members(r)) != set(self._members(s))} for r, s in zip(records, selected)],
                "moved_count": best[0], "unused_seats": best[1], "applied": False,
                "originals": copy_json(records)}

    def _apply_candidate(self, restaurant, plan_id):
        plan = self._state["plans"].get(plan_id)
        if plan is None or plan["restaurant_id"] != restaurant["id"]:
            fail(404, "not_found")
        if plan["applied"]:
            fail(409, "plan_already_applied")
        if plan["restaurant_revision"] != self._state["restaurant_revisions"][restaurant["id"]]:
            fail(409, "stale_plan")
        by_ref = {r["reference"]: r for r in self._state["reservations"]}
        originals = [by_ref[a["reference"]] for a in plan["assignments"]]
        proposed = [self._reseated(r, a["table_ids"]) for r, a in zip(originals, plan["assignments"])]
        histories = {}
        for old, new in zip(originals, proposed):
            if old["revision"] == new["revision"]:
                continue
            entries = self._state["histories"][old["reference"]]
            entry = self._history_entry(new, old, "reassigned", entries)
            entry["changes"] = [{"field": "table_ids", "from": list(self._members(old)), "to": list(self._members(new))}]
            entry["plan_id"] = plan_id
            histories[old["reference"]] = [*entries, entry]
        return plan, originals, proposed, histories

    def _series_amend_candidate(self, series_id, user, data):
        agreement = self._owned_series(series_id, user)
        expected = integer_field(data, "expected_revision", party=True)
        index = integer_field(data, "from_index", minimum=0, party=True)
        clock = data.get("local_time")
        if compare_numbers(index, len(agreement["occurrences"])) >= 0 or not isinstance(clock, str) or not TIME_PATTERN.fullmatch(clock):
            fail()
        if not same_json(expected, agreement["revision"]):
            fail(409, "stale_revision")
        records = {r["reference"]: r for r in self._state["reservations"]}
        originals, proposed = [], []
        for occurrence in agreement["occurrences"][to_integer(index):]:
            record = records[occurrence["reference"]]
            if occurrence["exception"] or record["status"] == "cancelled":
                continue
            local = occurrence["scheduled_starts_at_local"][:10] + "T" + clock
            candidate = dict(record) if local == record["starts_at_local"] else self._amend_candidate(record, {"starts_at_local": local})
            originals.append(record)
            proposed.append(candidate)
        self._check_occupancy(proposed, {r["reference"] for r in originals})
        changed = any(old["revision"] != new["revision"] for old, new in zip(originals, proposed))
        return {**agreement, "revision": agreement["revision"] + int(changed)}, originals, proposed

    def _series_public(self, agreement, generated=()):
        records = {r["reference"]: r for r in [*self._state["reservations"], *generated]}
        return {key: agreement[key] for key in ("series_id", "revision", "interval_weeks")} | {
                "occurrences": [{key: occurrence[key] for key in ("index", "reference", "exception")} |
                    {"reservation": self._public(records[occurrence["reference"]])}
                    for occurrence in agreement["occurrences"]]}

    def _series_candidate(self, user, data):
        anchor = self._owned(text_field(data, "anchor_reference"), user)
        if anchor["status"] == "cancelled":
            fail(409, "reservation_cancelled")
        if any(any(o["reference"] == anchor["reference"] for o in s["occurrences"])
               for s in self._state["series"].values()):
            fail(409, "already_in_series")
        self._cutoff(anchor)
        count = integer_field(data, "count", minimum=2, party=True)
        interval = integer_field(data, "interval_weeks", party=True)
        if compare_numbers(count, 12) > 0 or compare_numbers(interval, 4) > 0:
            fail()
        count, interval = to_integer(count), to_integer(interval)
        original = local_datetime(anchor["starts_at_local"])
        generated, histories = [], {}
        references = {r["reference"] for r in self._state["reservations"]}
        ids = {r["reservation_id"] for r in self._state["reservations"]}
        occurrences = [{"index": 0, "reference": anchor["reference"], "exception": False,
                        "scheduled_starts_at_local": anchor["starts_at_local"]}]
        for index in range(1, count):
            local = original + timedelta(days=index * interval * 7)
            fields = self._booking_fields({"restaurant_id": anchor["restaurant_id"],
                "table_ids": self._members(anchor), "party_size": anchor["party_size"],
                "starts_at_local": local.isoformat(timespec="minutes")})
            self._check_occupancy([*generated, fields])
            record = self._new_record(user, fields, references, ids)
            references.add(record["reference"])
            ids.add(record["reservation_id"])
            generated.append(record)
            histories[record["reference"]] = [self._history_entry(record, None, "created", [])]
            occurrences.append({"index": index, "reference": record["reference"], "exception": False,
                                "scheduled_starts_at_local": record["starts_at_local"]})
        agreement = {"series_id": self._new_id("ser_", set(self._state["series"])),
                     "user_id": user["id"], "revision": 1, "interval_weeks": interval,
                     "occurrences": occurrences}
        return agreement, generated, histories

    @staticmethod
    def _hours(restaurant, local_date):
        return next((h for h in restaurant["opening_hours"]
                     if h["weekday"] == WEEKDAYS[local_date.weekday()]), None)

    @staticmethod
    def _members(record):
        return record["table_ids"] if "table_ids" in record else [record["table_id"]]


    @staticmethod
    def _seating(data, restaurant):
        if "table_ids" in data and "table_id" in data:
            fail(message="Supply table_id or table_ids, not both")
        if "table_ids" in data:
            members = data["table_ids"]
            if not isinstance(members, list):
                fail(400, "malformed_request")
            if not members:
                fail()
            for member in members:
                text_field({"id": member}, "id", maximum=64)
            if len(set(members)) != len(members):
                fail(message="Duplicate table id")
            if len(members) > 2:
                fail(422, "combination_not_allowed")
        else:
            members = [text_field(data, "table_id", maximum=64)]
        tables = {table["id"]: table for table in restaurant["tables"]}
        if any(member not in tables for member in members):
            fail(404, "not_found")
        if len(members) == 2:
            declared = next((pair for pair in restaurant.get("combinable", [])
                             if set(pair) == set(members)), None)
            if declared is None:
                fail(422, "combination_not_allowed")
            members = declared
        return list(members), [tables[member]["capacity"] for member in members]


    @classmethod
    def _amend_fields(cls, record, data):
        fields = {key: record[key] for key in ("restaurant_id", "starts_at_local", "party_size")}
        if "table_ids" in data or "table_id" in data:
            fields.update({key: data[key] for key in ("table_ids", "table_id") if key in data})
        else:
            fields["table_ids"] = cls._members(record)
        fields.update({key: data[key] for key in ("starts_at_local", "party_size") if key in data})
        return fields


    def _record_fields(self, row, state):
        # Response records may carry both singleton representations; request
        # objects may not. Legacy records without table_ids are accepted.
        data = {key: row[key] for key in ("restaurant_id", "starts_at_local", "party_size") if key in row}
        if "table_ids" in row:
            data["table_ids"] = row["table_ids"]
        elif "table_id" in row:
            data["table_id"] = row["table_id"]
        restaurant = self._restaurant(data.get("restaurant_id"), state)
        terms = row.get("accepted_terms", self._base_terms(restaurant))
        version = terms.get("policy_version") if isinstance(terms, dict) else None
        if version is not None and not same_json(version, 0):
            policy = next((p for p in state["policies"].get(restaurant["id"], [])
                           if same_json(p["policy_version"], version)), None)
            if policy is None or policy["effective_from"] > data.get("starts_at_local", "")[:10]:
                fail()
        fields = self._booking_fields(data, state, terms=terms)
        for key in ("table_ids", "table_id"):
            if key in row and row[key] != fields.get(key):
                fail()
        return fields


    @staticmethod
    def _capacity_fits(capacities, party):
        return (compare_numbers(capacities[0], party) >= 0 if len(capacities) == 1
                else sum_at_least(capacities[0], capacities[1], party))

    @staticmethod
    def _original_seating_body(body, snapshot):
        # Public receipt origin is independent of its numeric parser profile.
        # Stage 1 ignored table_ids, even when the new accepted receipt is exact.
        return body if "table_ids" in snapshot else {key: value for key, value in body.items() if key != "table_ids"}

    def _booking_fields(self, data, state=None, *, terms=None):
        restaurant_id = text_field(data, "restaurant_id", maximum=64)
        local = local_datetime(text_field(data, "starts_at_local"))
        party_size = integer_field(data, "party_size", party=True)
        restaurant = self._restaurant(restaurant_id, state)
        terms = self._terms(restaurant, local.date(), state) if terms is None else terms
        restaurant = self._decision_restaurant(restaurant, terms)
        members, capacities = self._seating(data, restaurant)
        zone = ZoneInfo(restaurant["timezone"])
        start = resolve_local(local, zone)
        hours = self._hours(restaurant, local.date())
        if hours is None:
            fail(422, "outside_opening_hours")
        opening = datetime.fromisoformat(f"{local.date().isoformat()}T{hours['opens']}")
        closing = datetime.fromisoformat(f"{local.date().isoformat()}T{hours['closes']}")
        start_value = instant(start)
        duration = multiply_integer(restaurant["reservation_duration_minutes"], MINUTE_US)
        closing_zoned = closing.replace(tzinfo=zone, fold=0)
        closing_value = instant(closing_zoned)
        # Reject an interval that cannot fit before constructing its endpoint.
        # Otherwise a late unbookable slot can overflow the maximum calendar year.
        if (local < opening or local >= closing or
                compare_numbers(duration, closing_value - start_value) > 0):
            fail(422, "outside_opening_hours")
        duration = to_integer(duration)  # Bounded by the actual closing instant.
        end = zoned_at(start_value + duration, zone, (start, closing_zoned))
        minutes = int((local - opening).total_seconds() // 60)
        grid = restaurant["slot_minutes"]
        if minutes and (compare_numbers(grid, minutes) > 0 or minutes % to_integer(grid)):
            fail(422, "not_on_slot_grid")
        if not self._capacity_fits(capacities, party_size):
            fail(422, "party_exceeds_capacity")
        fields = {"restaurant_id": restaurant_id, "table_ids": members, "party_size": party_size,
                  "starts_at_local": data["starts_at_local"], "starts_at": wire_timestamp(start),
                  "ends_at": wire_timestamp(end), "accepted_terms": copy_json(terms)}
        if len(members) == 1:
            fields["table_id"] = members[0]
        return fields

    @classmethod
    def _overlap(cls, left, right):
        if (left["restaurant_id"] != right["restaurant_id"] or
                not set(cls._members(left)).intersection(cls._members(right))):
            return False
        return (instant(timestamp(left["starts_at"])) < instant(timestamp(right["ends_at"])) and
                instant(timestamp(right["starts_at"])) < instant(timestamp(left["ends_at"])))


    def _check_occupancy(self, proposed, excluded=frozenset(), state=None, *, check_closures=True):
        state = self._state if state is None else state
        existing = [r for r in state["reservations"]
                    if r["status"] == "confirmed" and r["reference"] not in excluded]
        for index, candidate in enumerate(proposed):
            if candidate.get("status", "confirmed") != "confirmed":
                continue
            if check_closures and any(self._closure_overlap(candidate, c) for c in state["closures"]):
                fail(409, "table_unavailable")
            if any(self._overlap(candidate, other) for other in existing):
                fail(409, "table_unavailable")
            if any(other.get("status", "confirmed") == "confirmed" and self._overlap(candidate, other)
                   for other in proposed[:index]):
                fail(409, "table_unavailable")

    def _create(self, user, data):
        fields = self._booking_fields(data)
        self._check_occupancy([fields])
        references = {r["reference"] for r in self._state["reservations"]}
        ids = {r["reservation_id"] for r in self._state["reservations"]}
        return self._new_record(user, fields, references, ids)

    def _new_record(self, user, fields, references, ids):
        reference = secrets.token_hex(5).upper()
        while reference in references:
            reference = secrets.token_hex(5).upper()
        record = {"reservation_id": self._new_id("res_", ids),
            "reference": reference, "user_id": user["id"], **fields, "status": "confirmed",
            "created_at": wire_timestamp(datetime.now(UTC)), "revision": 1}
        return record  # Dispatch snapshots the receipt before committing it.

    def _cutoff(self, record):
        remaining = instant(timestamp(record["starts_at"])) - instant(datetime.now(UTC))
        if compare_numbers(remaining, multiply_integer(record["accepted_terms"]["cancellation_cutoff_minutes"], MINUTE_US)) <= 0:
            fail(409, "cutoff_passed")

    def _amend_candidate(self, record, data):
        if "expected_revision" in data:
            expected = integer_field(data, "expected_revision", party=True)
            if not same_json(expected, record["revision"]):
                fail(409, "stale_revision")
        if record["status"] == "cancelled":
            fail(409, "reservation_cancelled")
        self._cutoff(record)
        fields = self._amend_fields(record, data)
        local_datetime(text_field(fields, "starts_at_local"))
        party = integer_field(fields, "party_size", party=True)
        restaurant = self._restaurant(record["restaurant_id"])
        members, _ = self._seating(fields, restaurant)
        if (members == self._members(record) and same_json(party, record["party_size"])
                and fields["starts_at_local"] == record["starts_at_local"]):
            return dict(record)
        revised = self._booking_fields(fields)
        if same_json(revised["party_size"], record["party_size"]):
            revised["party_size"] = record["party_size"]
        for key in ("starts_at", "ends_at"):
            if instant(timestamp(revised[key])) == instant(timestamp(record[key])):
                revised[key] = record[key]
        return {**{key: value for key, value in record.items() if key not in ("table_id", "table_ids")},
                **revised, "revision": record["revision"] + 1}

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
        return originals, proposed  # Dispatch commits all records and receipt together.

    def _availability(self, query):
        explain = "explain" in query
        if explain and (query["explain"] != ["true"]):
            fail()
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
        terms = self._terms(restaurant, local_date)
        restaurant = self._decision_restaurant(restaurant, terms)
        result = {"restaurant_id": restaurant_id, "date": local_date_string,
                  "timezone": restaurant["timezone"], "slots": []}
        hours = self._hours(restaurant, local_date)
        if hours is None:
            return result
        zone = ZoneInfo(restaurant["timezone"])
        opening = datetime.fromisoformat(f"{local_date_string}T{hours['opens']}")
        close = datetime.fromisoformat(f"{local_date_string}T{hours['closes']}")
        closing_zoned = close.replace(tzinfo=zone, fold=0)
        close_value = instant(closing_zoned)
        duration = multiply_integer(restaurant["reservation_duration_minutes"], MINUTE_US)
        # Grid offsets are bounded by this local day's opening window. Stepping
        # past it must not attempt to construct another day (or another year).
        window_minutes = int((close - opening).total_seconds() // 60)
        grid = restaurant["slot_minutes"]
        step = window_minutes if compare_numbers(grid, window_minutes) >= 0 else to_integer(grid)
        for offset in range(0, window_minutes, step):
            local = opening + timedelta(minutes=offset)
            try:
                start = resolve_local(local, zone)
            except Refusal as error:
                if error.code != "invalid_local_time":
                    raise
                continue
            start_value = instant(start)
            if compare_numbers(duration, close_value - start_value) <= 0:
                end_value = start_value + to_integer(duration)
                end = zoned_at(end_value, zone, (start, closing_zoned))
                available, options = [], []
                capacities = {table["id"]: table["capacity"] for table in restaurant["tables"]}
                selections = [[table["id"]] for table in restaurant["tables"]]
                selections.extend(restaurant.get("combinable", []))
                for members in selections:
                    candidate = {"restaurant_id": restaurant_id, "table_ids": members,
                                 "starts_at": wire_timestamp(start), "ends_at": wire_timestamp(end)}
                    counts = [capacities[member] for member in members]
                    if self._capacity_fits(counts, party) and not self._blocked(candidate):
                        capacity = counts[0] if len(counts) == 1 else add_integers(*counts)
                        options.append({"table_ids": list(members), "capacity": capacity})
                        if len(members) == 1:
                            available.append(members[0])
                slot = {"starts_at_local": local.isoformat(timespec="minutes"),
                    "starts_at": wire_timestamp(start), "available_table_ids": available,
                    "available_options": options}
                if explain:
                    slot["explain"] = []
                    for table in restaurant["tables"]:
                        candidate = {"restaurant_id": restaurant_id, "table_id": table["id"],
                                     "starts_at": wire_timestamp(start), "ends_at": wire_timestamp(end)}
                        capacity = compare_numbers(party, table["capacity"]) <= 0
                        clear = not self._blocked(candidate)
                        slot["explain"].append({"table_id": table["id"], "policy_version": terms["policy_version"],
                            "available": capacity and clear,
                            "rules": [{"rule": "capacity", "holds": capacity},
                                      {"rule": "no_overlap", "holds": clear}]})
                result["slots"].append(slot)
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
            if "opening_hours" not in row or "tables" not in row:
                fail(message="Missing opening_hours or tables")
            hours, tables = row["opening_hours"], row["tables"]
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
            if "combinable" in row:
                pairs = row["combinable"]
                if not isinstance(pairs, list):
                    fail(400, "malformed_request")
                restaurant["combinable"] = []
                for pair in pairs:
                    if not isinstance(pair, list):
                        fail(400, "malformed_request")
                    if len(pair) != 2:
                        fail()
                    for member in pair:
                        text_field({"id": member}, "id", maximum=64)
                    if pair[0] == pair[1] or any(member not in table_ids for member in pair):
                        fail()
                    restaurant["combinable"].append(list(pair))
            managers = row.get("manager_user_ids", [])
            if not isinstance(managers, list):
                fail(400, "malformed_request")
            for manager in managers:
                text_field({"id": manager}, "id", maximum=64)
            if len(set(managers)) != len(managers):
                fail()
            restaurant["manager_user_ids"] = list(managers)
            restaurants.append(restaurant)
        return restaurants

    def _fixture(self, fixture):
        state = self._empty_state()
        json_value(fixture)
        state["restaurants"] = self._restaurants(fixture.get("restaurants", []))
        state["policies"] = {r["id"]: [] for r in state["restaurants"]}
        state["restaurant_revisions"] = {r["id"]: 0 for r in state["restaurants"]}
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
            status = text_field(row, "status") if "status" in row else "confirmed"
            if status not in ("confirmed", "cancelled"):
                fail()
            record = {"reservation_id": reservation_id, "reference": reference,
                      "user_id": user_id, **fields, "status": status,
                      "created_at": wire_timestamp(datetime.now(UTC)), "revision": 1}
            reservation_ids.add(reservation_id)
            references.add(reference)
            state["reservations"].append(record)
            entries = [self._history_entry(record, None, "created", [])]
            if status == "cancelled":
                # Reset is the observed creation of an already-cancelled seed;
                # no unobserved historical cancellation event is fabricated.
                entries[0]["event"] = "created"
            state["histories"][reference] = entries
            state["history_origins"][reference] = "stage3"
        self._check_occupancy(state["reservations"], references, state)
        return state

    def _validate_record(self, row, state, *, owner_required=True):
        row = object_body(row)
        fields = self._record_fields(row, state)
        assert_booking_fields(row, fields)
        if "table_ids" not in row:
            fields.pop("table_ids")
        fields.update({key: row[key] for key in ("starts_at", "ends_at")})
        record = {"reservation_id": text_field(row, "reservation_id", maximum=64),
                  "reference": text_field(row, "reference"), **fields,
                  "status": text_field(row, "status"), "created_at": text_field(row, "created_at")}
        if not REFERENCE_PATTERN.fullmatch(record["reference"]) or record["status"] not in ("confirmed", "cancelled"):
            fail()
        timestamp(record["created_at"])
        restaurant = self._restaurant(record["restaurant_id"], state)
        record["accepted_terms"] = self._valid_terms(fields["accepted_terms"], restaurant, state)
        revision = integer_field({"revision": row.get("revision", 1)}, "revision", party=True)
        record["revision"] = to_integer(revision)
        if owner_required:
            record["user_id"] = text_field(row, "user_id", maximum=64)
            if record["user_id"] not in {u["id"] for u in state["users"]}:
                fail()
        return record

    def _import_state(self, source):
        source = object_body(source)
        json_value(source)
        schema = source.get("schema")
        stage4 = same_json(schema, 4)
        modern = same_json(schema, 3) or stage4
        if not (same_json(schema, 1) or same_json(schema, 2) or modern):
            fail()
        state = self._empty_state()
        state["restaurants"] = self._restaurants(source["restaurants"])
        restaurant_ids = {r["id"] for r in state["restaurants"]}
        state["policies"] = {rid: [] for rid in restaurant_ids}
        state["restaurant_revisions"] = {rid: 0 for rid in restaurant_ids}
        if modern:
            policies = object_body(source["policies"])
            if set(policies) != restaurant_ids:
                fail()
            for rid, rows in policies.items():
                if not isinstance(rows, list):
                    fail()
                restaurant = self._restaurant(rid, state)
                for index, row in enumerate(rows, 1):
                    row = object_body(row)
                    policy = self._policy(row, restaurant)
                    if not same_json(row.get("policy_version"), index):
                        fail()
                    state["policies"][rid].append({**policy, "policy_version": index})
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
        state["tokens"] = copy_json(tokens)
        if not isinstance(source["reservations"], list) or not isinstance(source["receipts"], list):
            fail()
        references, reservation_ids = set(), set()
        for row in source["reservations"]:
            if modern and (not isinstance(row, dict) or "revision" not in row or "accepted_terms" not in row):
                fail()
            record = self._validate_record(row, state)
            if record["reference"] in references or record["reservation_id"] in reservation_ids:
                fail()
            references.add(record["reference"])
            reservation_ids.add(record["reservation_id"])
            state["reservations"].append(record)
            state["histories"][record["reference"]] = []
            state["history_origins"][record["reference"]] = "legacy"
        self._check_occupancy(state["reservations"], references, state)
        identities = {r["reference"]: r for r in state["reservations"]}
        receipt_keys = set()
        for row in source["receipts"]:
            row = object_body(row)
            profile = LEGACY_PROFILE if same_json(schema, 1) else row.get("numeric_profile")
            if type(profile) is not str or profile not in (EXACT_PROFILE, LEGACY_PROFILE):
                fail(message="Invalid receipt numeric profile")
            user_id = text_field(row, "user_id", maximum=64)
            method = text_field(row, "method")
            path = text_field(row, "path")
            key = text_field(row, "key", maximum=255)
            parts = [unquote(p) for p in urlsplit(path).path.split("/")[1:]]
            policy_path = len(parts) == 3 and parts[0] == "restaurants" and parts[2] == "policies"
            preview_path = len(parts) == 3 and parts[0] == "restaurants" and parts[2] == "replans"
            apply_path = len(parts) == 5 and parts[0] == "restaurants" and parts[2] == "replans" and parts[4] == "apply"
            amend_path = len(parts) == 3 and parts[0] == "series" and parts[2] == "amend"
            if user_id not in user_ids or method != "POST" or (path not in ("/reservations", "/reservation-moves", "/series") and not (policy_path or preview_path or apply_path or amend_path)):
                fail()
            if (preview_path or apply_path or amend_path) and not stage4:
                fail()
            if not modern and path not in ("/reservations", "/reservation-moves"):
                fail()
            identity = (user_id, method, path, key)
            if identity in receipt_keys:
                fail()
            receipt_keys.add(identity)
            body = object_body(row["body"])
            response = object_body(row["response"])
            if path == "/reservations":
                snapshots = [response]
                original_body = self._original_seating_body(body, response)
                restaurant = self._restaurant(response.get("restaurant_id"), state)
                terms = response.get("accepted_terms", self._base_terms(restaurant))
                original_fields = self._booking_fields(original_body, state, terms=terms)
                assert_booking_fields(response, original_fields)
            elif path == "/reservation-moves":
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
                    original_move = self._original_seating_body(move, snapshot)
                    restaurant = self._restaurant(snapshot.get("restaurant_id"), state)
                    terms = snapshot.get("accepted_terms", self._base_terms(restaurant))
                    amended_fields = self._booking_fields(self._amend_fields(snapshot, original_move), state, terms=terms)
                    assert_booking_fields(snapshot, amended_fields)
            elif policy_path:
                restaurant = self._restaurant(parts[1], state)
                if user_id not in restaurant.get("manager_user_ids", []):
                    fail()
                original = self._policy(body, restaurant)
                version = response.get("policy_version")
                policy = next((p for p in state["policies"][restaurant["id"]]
                               if same_json(p["policy_version"], version)), None)
                if policy is None or not same_json(response, {**original, "policy_version": version}) or not same_json(response, policy):
                    fail()
                snapshots = []
            elif preview_path or apply_path:
                restaurant = self._restaurant(parts[1], state)
                if user_id not in restaurant.get("manager_user_ids", []):
                    fail()
                text_field(response, "plan_id", maximum=64)
                integer_field(response, "restaurant_revision", minimum=0, party=True)
                if preview_path:
                    if not same_json(self._closure(restaurant, body), response.get("closure")):
                        fail()
                    snapshots = []
                else:
                    if response["plan_id"] != parts[3] or not isinstance(response.get("reservations"), list):
                        fail()
                    snapshots = response["reservations"]
            else:
                occurrences = response.get("occurrences")
                if not isinstance(occurrences, list) or not 2 <= len(occurrences) <= 12:
                    fail()
                if not amend_path:
                    if not same_json(body.get("count"), len(occurrences)) or not same_json(body.get("interval_weeks"), response.get("interval_weeks")):
                        fail()
                    if not same_json(response.get("revision"), 1):
                        fail()
                else:
                    expected = integer_field(body, "expected_revision", party=True)
                    from_index = integer_field(body, "from_index", minimum=0, party=True)
                    if (compare_numbers(from_index, len(occurrences)) >= 0 or not isinstance(body.get("local_time"), str)
                            or not TIME_PATTERN.fullmatch(body["local_time"]) or response.get("series_id") != parts[1]
                            or not any(same_json(response.get("revision"), v) for v in (expected, add_integers(expected, 1)))):
                        fail()
                text_field(response, "series_id", maximum=64)
                snapshots = []
                for index, occurrence in enumerate(occurrences):
                    occurrence = object_body(occurrence)
                    if not same_json(occurrence.get("index"), index) or type(occurrence.get("exception")) is not bool or (not amend_path and occurrence["exception"]):
                        fail()
                    snapshot = object_body(occurrence.get("reservation"))
                    if occurrence.get("reference") != snapshot.get("reference"):
                        fail()
                    snapshots.append(snapshot)
                if not amend_path and body.get("anchor_reference") != snapshots[0].get("reference"):
                    fail()
            for snapshot in snapshots:
                saved = self._validate_record(snapshot, state, owner_required=False)
                current = identities.get(saved["reference"])
                if ((saved["status"] != "confirmed" and not amend_path) or current is None or (current["user_id"] != user_id and not apply_path) or
                        any(current[k] != saved[k] for k in ("reservation_id", "restaurant_id", "created_at"))):
                    fail()
            self._check_occupancy(snapshots, references, state, check_closures=False)
            state["receipts"].append({"user_id": user_id, "method": method, "path": path,
                                     "key": key, "body": copy_json(body), "response": copy_json(response),
                                     "numeric_profile": profile})
        if modern:
            self._import_extensions(source, state)
        if stage4:
            self._import_plans(source, state)
        return state

    def _import_extensions(self, source, state):
        records = {r["reference"]: r for r in state["reservations"]}
        histories = object_body(source["histories"])
        origins = object_body(source["history_origins"])
        if set(histories) != set(records) or set(origins) != set(records):
            fail()
        for reference, entries in histories.items():
            record = records[reference]
            origin = origins[reference]
            if origin not in ("legacy", "stage3") or not isinstance(entries, list):
                fail()
            if not entries:
                if origin != "legacy" or record["revision"] != 1:
                    fail()
            previous_time = None
            for index, entry in enumerate(entries, 1):
                entry = object_body(entry)
                expected_revision = index + (1 if origin == "legacy" else 0)
                if not same_json(entry.get("seq"), index) or not same_json(entry.get("revision"), expected_revision):
                    fail()
                at = instant(timestamp(entry.get("at")))
                if previous_time is not None and at < previous_time:
                    fail()
                previous_time = at
                event, changes = entry.get("event"), entry.get("changes")
                if event not in ("created", "changed", "cancelled", "reassigned") or not isinstance(changes, list):
                    fail()
                if event == "reassigned" and (not same_json(source.get("schema"), 4) or
                        len(changes) != 1 or object_body(changes[0]).get("field") != "table_ids" or
                        same_json(changes[0].get("from"), changes[0].get("to"))):
                    fail()
                if event == "reassigned":
                    text_field(entry, "plan_id", maximum=64)
                if event == "created" and (index != 1 or origin != "stage3"):
                    fail()
                if index == 1 and origin == "stage3" and event != "created":
                    fail()
                if event == "cancelled" and (changes or index != len(entries) or record["status"] != "cancelled"):
                    fail()
                names = [object_body(change).get("field") for change in changes]
                if any(name not in ("table_id", "table_ids", "starts_at_local", "party_size") for name in names):
                    fail()
                expected_order = [name for name in ("table_id", "table_ids", "starts_at_local", "party_size") if name in names]
                if names != expected_order or ("table_id" in names and "table_ids" in names):
                    fail()
                if event == "created" and (names not in (["table_id", "starts_at_local", "party_size"], ["table_ids", "starts_at_local", "party_size"]) or any(c.get("from") is not None for c in changes)):
                    fail()
                if event == "changed" and (not changes or any(same_json(c.get("from"), c.get("to")) for c in changes)):
                    fail()
                self._valid_terms(entry.get("accepted_terms"), self._restaurant(record["restaurant_id"], state), state)
            if entries and (not same_json(entries[-1]["revision"], record["revision"]) or
                    not same_json(entries[-1]["accepted_terms"], record["accepted_terms"])):
                fail()
            # Follow actual changed fields backwards from the current view,
            # checking every saved resulting snapshot under its historic terms.
            fields = {"restaurant_id": record["restaurant_id"], "table_ids": self._members(record),
                      "starts_at_local": record["starts_at_local"], "party_size": record["party_size"]}
            for entry in reversed(entries):
                self._booking_fields(fields, state, terms=entry["accepted_terms"])
                for change in entry["changes"]:
                    name = change["field"]
                    current = fields["table_ids"][0] if name == "table_id" else fields.get(name)
                    if not same_json(change.get("to"), current):
                        fail()
                    if entry["event"] != "created":
                        if name == "table_id":
                            fields["table_ids"] = [change["from"]]
                        else:
                            fields[name] = copy_json(change["from"])
            state["histories"][reference] = copy_json(entries)
            state["history_origins"][reference] = origin
        counters = object_body(source["restaurant_revisions"])
        if set(counters) != {r["id"] for r in state["restaurants"]}:
            fail()
        state["restaurant_revisions"] = {rid: to_integer(integer_field({"revision": value}, "revision", minimum=0, party=True)) for rid, value in counters.items()}
        series = object_body(source["series"])
        adopted = set()
        for series_id, agreement in series.items():
            agreement = object_body(agreement)
            if text_field(agreement, "series_id", maximum=64) != series_id:
                fail()
            owner = text_field(agreement, "user_id", maximum=64)
            revision = to_integer(integer_field(agreement, "revision", party=True))
            interval = to_integer(integer_field(agreement, "interval_weeks", party=True))
            occurrences = agreement.get("occurrences")
            if interval > 4 or not isinstance(occurrences, list) or not 2 <= len(occurrences) <= 12:
                fail()
            normalized, scheduled, restaurant_id = [], None, None
            for index, occurrence in enumerate(occurrences):
                occurrence = object_body(occurrence)
                reference = text_field(occurrence, "reference")
                record = records.get(reference)
                if (not same_json(occurrence.get("index"), index) or record is None or record["user_id"] != owner or
                        reference in adopted or type(occurrence.get("exception")) is not bool):
                    fail()
                local = local_datetime(text_field(occurrence, "scheduled_starts_at_local"))
                if index == 0:
                    scheduled, restaurant_id = local, record["restaurant_id"]
                if local != scheduled + timedelta(days=index * interval * 7) or record["restaurant_id"] != restaurant_id:
                    fail()
                if not occurrence["exception"] and (record["starts_at_local"][:10] != local.isoformat()[:10] if same_json(source.get("schema"), 4)
                        else record["starts_at_local"] != local.isoformat(timespec="minutes")):
                    fail()
                adopted.add(reference)
                normalized.append({"index": index, "reference": reference, "exception": occurrence["exception"],
                                   "scheduled_starts_at_local": occurrence["scheduled_starts_at_local"]})
            state["series"][series_id] = {"series_id": series_id, "user_id": owner, "revision": revision,
                                         "interval_weeks": interval, "occurrences": normalized}
        for receipt in state["receipts"]:
            parts = [unquote(p) for p in urlsplit(receipt["path"]).path.split("/")[1:]]
            if receipt["path"] == "/series" or (len(parts) == 3 and parts[0] == "series" and parts[2] == "amend"):
                response = receipt["response"]
                agreement = state["series"].get(response["series_id"])
                if (agreement is None or agreement["user_id"] != receipt["user_id"] or
                        not same_json(agreement["interval_weeks"], response["interval_weeks"]) or
                        [o["reference"] for o in agreement["occurrences"]] != [o["reference"] for o in response["occurrences"]]):
                    fail()

    def _import_plans(self, source, state):
        plans = object_body(source["plans"])
        closures = source["closures"]
        if not isinstance(closures, list):
            fail()
        records = {r["reference"]: r for r in state["reservations"]}
        for plan_id, row in plans.items():
            row = object_body(row)
            if text_field(row, "plan_id", maximum=64) != plan_id or type(row.get("applied")) is not bool:
                fail()
            restaurant = self._restaurant(row.get("restaurant_id"), state)
            revision = to_integer(integer_field(row, "restaurant_revision", minimum=0, party=True))
            if revision > state["restaurant_revisions"][restaurant["id"]]:
                fail()
            closure = self._closure(restaurant, object_body(row.get("closure")))
            originals, assignments = row.get("originals"), row.get("assignments")
            if (len(restaurant["tables"]) > 6 or len(restaurant.get("combinable", [])) > 4 or
                    not isinstance(originals, list) or len(originals) > 6 or not isinstance(assignments, list) or len(assignments) != len(originals)):
                fail()
            normalized, proposed, refs, unused, moved = [], [], [], 0, 0
            for original, assignment in zip(originals, assignments):
                old = self._validate_record(original, state)
                current = records.get(old["reference"])
                if (old["status"] != "confirmed" or old["restaurant_id"] != restaurant["id"] or current is None
                        or any(old[k] != current[k] for k in ("reservation_id", "restaurant_id", "user_id", "created_at"))
                        or not self._interval_overlap(old, closure)):
                    fail()
                assignment = object_body(assignment)
                if assignment.get("reference") != old["reference"] or type(assignment.get("changed")) is not bool:
                    fail()
                members, _ = self._seating({"table_ids": assignment.get("table_ids")}, restaurant)
                if members != assignment["table_ids"]:
                    fail()
                new = self._reseated(old, members)
                change = old["revision"] != new["revision"]
                if assignment["changed"] != change:
                    fail()
                counts = [old["accepted_terms"]["capacities"][m] for m in members]
                if not self._capacity_fits(counts, old["party_size"]) or self._closure_overlap(new, {"restaurant_id": restaurant["id"], **closure}):
                    fail()
                capacity = counts[0] if len(counts) == 1 else add_integers(*counts)
                unused = add_integers(unused, 0 if same_json(capacity, old["party_size"]) else add_integers(capacity, multiply_integer(old["party_size"], -1)))
                moved += int(change)
                refs.append(old["reference"])
                normalized.append(old)
                proposed.append(new)
                if row["applied"] and change:
                    events = [e for e in state["histories"][old["reference"]]
                              if e["event"] == "reassigned" and e.get("plan_id") == plan_id]
                    expected_changes = [{"field": "table_ids", "from": list(self._members(old)), "to": list(members)}]
                    if (len(events) != 1 or events[0]["revision"] != new["revision"] or
                            not same_json(events[0]["changes"], expected_changes) or
                            not same_json(events[0]["accepted_terms"], old["accepted_terms"])):
                        fail()
            if refs != sorted(set(refs)) or not same_json(row.get("moved_count"), moved) or not same_json(row.get("unused_seats"), unused):
                fail()
            self._check_occupancy(proposed, set(records), state, check_closures=False)
            if not row["applied"] and revision == state["restaurant_revisions"][restaurant["id"]]:
                considered = sorted((r for r in state["reservations"] if r["status"] == "confirmed"
                    and r["restaurant_id"] == restaurant["id"] and self._interval_overlap(r, closure)), key=lambda r: r["reference"])
                if not same_json(considered, normalized):
                    fail()
                self._check_occupancy(proposed, set(refs), state, check_closures=False)
            state["plans"][plan_id] = {**copy_json(row), "originals": normalized, "closure": closure,
                                      "restaurant_revision": revision}
        seen = set()
        for row in closures:
            row = object_body(row)
            plan = state["plans"].get(row.get("plan_id"))
            if plan is None or not plan["applied"] or row["plan_id"] in seen or row.get("restaurant_id") != plan["restaurant_id"]:
                fail()
            restaurant = self._restaurant(plan["restaurant_id"], state)
            closure = self._closure(restaurant, row)
            if not same_json(closure, plan["closure"]):
                fail()
            seen.add(row["plan_id"])
            state["closures"].append({"restaurant_id": restaurant["id"], "plan_id": row["plan_id"], **closure})
        if seen != {p["plan_id"] for p in state["plans"].values() if p["applied"]}:
            fail()
        self._check_occupancy(state["reservations"], set(records), state)
        for reference, entries in state["histories"].items():
            for entry in entries:
                if entry["event"] == "reassigned":
                    plan = state["plans"].get(entry["plan_id"])
                    if plan is None or not plan["applied"] or not any(a["reference"] == reference and a["changed"] for a in plan["assignments"]):
                        fail()
        for receipt in state["receipts"]:
            parts = [unquote(p) for p in urlsplit(receipt["path"]).path.split("/")[1:]]
            if len(parts) not in (3, 5) or parts[0] != "restaurants" or parts[2] != "replans":
                continue
            response = receipt["response"]
            plan = state["plans"].get(response["plan_id"])
            if plan is None or plan["restaurant_id"] != parts[1]:
                fail()
            if len(parts) == 3:
                if not same_json(response, self._plan_public(plan)):
                    fail()
            else:
                expected = {"plan_id": plan["plan_id"], "restaurant_revision": plan["restaurant_revision"] + 1,
                    "reservations": [self._public(self._reseated(r, a["table_ids"])) for r, a in zip(plan["originals"], plan["assignments"])]}
                if not plan["applied"] or not same_json(response, expected):
                    fail()
