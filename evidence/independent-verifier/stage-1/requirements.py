"""Independent atomic Stage 1 obligations, derived before reading shipped tests.

Line numbers refer to kickoff/tablekeeper/spec/stage-1.md at the kickoff revision.
IDs are stable semantic identifiers. Repeated constraints at different endpoints
are separate rows, so evidence for one path does not silently cover another.
"""
import csv
from pathlib import Path

ROWS = []
INTERFACE_KEYS = {"dockerfile", "run-document", "single-image", "packaged-assets", "listen-all", "port-override", "port-default",
                  "health-status", "health-body", "health-public", "json-content-type", "error-envelope", "invalid-json", "nonobject-json"}


def add(section, line, case, entries, method="black-box HTTP"):
    for key, obligation in entries.items():
        implementation_owner = "interface-engineer" if key in INTERFACE_KEYS else "systems-engineer"
        ROWS.append(dict(requirement_id="TK1-" + key, source_section=section,
                         source_line=line, introduced_stage=1,
                         applicable_stages="1,2,3,4", owner=implementation_owner,
                         implementation_owner=implementation_owner, verification_owner="independent-verifier",
                         requirement_text=obligation, candidate_full_revision="UNASSIGNED",
                         verification_method=method, case=case,
                         executable_command_or_interaction=(f"python3 evidence/independent-verifier/stage-1/runtime.py --repo RESULT_REPOSITORY --workspace WORKSPACE_ROOT --candidate FULL_REVISION --out NEW_DIRECTORY" if case in ["runtime", "provenance"] else f"python3 evidence/independent-verifier/stage-1/probe.py --base http://127.0.0.1:18300 --peer http://127.0.0.1:18301 --candidate FULL_REVISION --out NEW_DIRECTORY --case {case}"),
                         evidence_path="UNVERIFIED", verdict="unverified"))


add("1. Scope", 10, "invariants", {
    "overlap": "Confirmed reservations never overlap on the same table.",
    "half-open": "A reservation beginning exactly at another's end does not overlap.",
    "reject-no-partial": "Rejected writes leave records and occupancy unchanged.",
    "retry-no-duplicate": "Retries do not create duplicate reservations.",
    "restaurant-independent": "Each restaurant uses its own capacities, hours and cutoff.",
})
add("2. Delivery and deployment / Resource limits", 23, "runtime", {
    "dockerfile": "Stage 1 includes a Dockerfile that builds a complete service.",
    "run-document": "RUN.md provides a build/start command without manual setup.",
    "single-image": "No separate runtime service, host dependency or compose startup is needed.",
    "offline": "Service works without outbound runtime network.",
    "cpu": "Service works with 2 vCPU.",
    "memory": "Service works with 2 GiB memory.",
    "startup": "First healthy response occurs within 60 seconds.",
    "max-concurrency": "Service supports 50 in-flight requests.",
    "request-timeout": "Ordinary requests complete within 5 seconds.",
    "reset-timeout": "POST /_test/reset completes within 10 seconds.",
    "import-timeout": "POST /_test/import completes within 10 seconds.",
    "export-timeout": "GET /_test/export completes within 10 seconds.",
    "max-concurrency-timing": "Fifty concurrent ordinary requests each complete within 5 seconds.",
    "packaged-assets": "All runtime initialization, seed data and assets are in the image.",
}, "clean clone, build and constrained offline execution")
add("3.1 Listening", 58, "runtime", {
    "listen-all": "Service listens on 0.0.0.0.",
    "port-override": "Service honors nondefault PORT environment value.",
    "port-default": "Service defaults to port 8080 when PORT is absent.",
}, "container network HTTP and process configuration")
add("3.2 Health", 62, "basics", {
    "health-status": "GET /health returns HTTP 200 when ready.",
    "health-body": "GET /health returns exactly the JSON value {status: ok}.",
    "health-public": "Health does not require authentication.",
})
add("3.3 Reset and seed", 71, "basics", {
    "reset-status": "POST /_test/reset returns 204 with no content.",
    "reset-public": "Reset requires no authentication and is enabled in the delivered image.",
    "reset-replacement": "After reset only the supplied fixture is visible.",
    "reset-repeat": "Repeated resets are supported.",
    "reset-sessions": "Reset clears old bearer tokens.",
    "reset-receipts": "Reset clears successful idempotency receipts.",
})
add("3.4 Conventions / 5. Errors", 86, "conventions", {
    "json-content-type": "JSON responses carry application/json; charset=utf-8.",
    "timestamp-offset": "Every response timestamp uses RFC 3339 with an explicit offset.",
    "unknown-body": "Unknown request body fields are ignored.",
    "unknown-query": "Unknown query parameters are ignored.",
    "generated-id-limit": "Generated IDs are opaque strings of at most 64 characters.",
    "fixture-id-max": "IDs of exactly 64 characters are accepted in reset fixtures.",
    "fixture-id-over": "Fixture IDs longer than 64 characters are rejected with 422 validation_failed.",
    "error-envelope": "Every 4xx and 5xx response has error.code and a human-readable error.message.",
    "no-5xx": "Requests do not produce 5xx, including concurrent load.",
})
add("4. Model / Fixture format", 100, "fixture", {
    "timezone-model": "Restaurant local dates/times follow its IANA timezone.",
    "grid-from-opening": "Start grid is measured from opening rather than midnight.",
    "duration-model": "Every booking occupies the restaurant's configured duration.",
    "cutoff-model": "Each reservation uses its restaurant's cancellation cutoff.",
    "closed-weekday": "A weekday absent from opening_hours is closed.",
    "table-capacity": "Table capacity bounds party size.",
    "weekdays": "All seven weekday values are supported.",
    "same-day-hours": "Legal opening hours are local HH:MM with later same-day closes.",
    "seeded-login": "Seeded users can immediately login with their given password.",
    "seeded-reservation": "Reset accepts confirmed reservations with body fields plus id/reference/user_id.",
    "past-create": "A reservation is not refused solely because its date is in the past.",
    "past-cutoff": "Past reservations remain subject to cancellation/amendment cutoff.",
})
for shape, fields in {
    "fixture-user": ["id", "email", "password", "display_name"],
    "fixture-restaurant": ["id", "name", "timezone", "slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "opening_hours", "tables"],
    "fixture-hours": ["weekday", "opens", "closes"],
    "fixture-table": ["id", "label", "capacity"],
    "fixture-reservation": ["restaurant_id", "table_id", "starts_at_local", "party_size", "id", "reference", "user_id"],
}.items():
    add("4. Fixture format", 109, "fixture", {shape + "-" + field: f"Reset preserves and uses fixture {shape} field {field}." for field in fields})

add("5. Errors", 160, "validation", {
    "invalid-json": "Unparseable JSON body returns 400 malformed_request.",
    "nonobject-json": "Wrong JSON body shape returns 400 malformed_request.",
    "wrong-field-type": "Wrong field types return 400 malformed_request except documented endpoint precedence.",
    "invalid-format": "Correct-type fields with invalid formats return 422 validation_failed.",
    "missing-required": "Missing required fields return 422 validation_failed.",
    "invalid-date": "Invalid calendar dates return 422 validation_failed.",
    "party-string": "String party_size is 422 validation_failed.",
    "party-bool": "Boolean party_size is 422 validation_failed.",
    "party-fraction": "Fractional party_size is 422 validation_failed.",
    "party-zero": "party_size below 1 is 422 validation_failed.",
    "bare-time": "Non-bare starts_at_local strings return 422 validation_failed.",
    "time-wrong-type": "Nonstring starts_at_local returns 400 malformed_request.",
    "decimal-query": "Integer query values must use plain decimal digits.",
    "query-positive": "Availability party_size must be at least 1.",
    "query-date": "Availability date must be a valid local calendar date.",
})

add("6. Authentication", 193, "auth", {
    "signup-status": "Successful signup returns 201.",
    "login-status": "Successful login returns 200.",
    "email-duplicate": "Duplicate signup email returns 409 email_taken.",
    "password-minimum": "Signup passwords below 8 characters return 422 validation_failed.",
    "email-format": "Signup email outside local@domain returns 422 validation_failed.",
    "login-wrong-password": "Wrong password returns 401 unauthenticated.",
    "login-unknown-email": "Unknown login email returns 401 unauthenticated.",
    "tokens-multiple": "Multiple login/signup tokens remain concurrently valid.",
    "tokens-persistent": "Bearer tokens do not expire.",
    "password-hashed": "Stored passwords use a password hash, never plaintext.",
}, "HTTP; hash evidence additionally requires committed storage review and export inspection")
for endpoint, fields in {"signup": ["email", "password", "display_name"], "login": ["email", "password"]}.items():
    add("6. Authentication", 193 if endpoint == "signup" else 200, "auth", {
        f"{endpoint}-{field}-required": f"{endpoint} requires {field}; missing returns 422 validation_failed."
        for field in fields})
    add("6. Authentication", 193 if endpoint == "signup" else 200, "auth", {
        f"{endpoint}-{field}-type": f"{endpoint} {field} must be a string; wrong type returns 400 malformed_request."
        for field in fields})
    add("6. Authentication", 193 if endpoint == "signup" else 200, "auth", {
        f"{endpoint}-response-{field}": f"{endpoint} response includes correct {field}."
        for field in ["user_id", "display_name", "token"]})

for path, public in {"restaurants": True, "restaurant-detail": True, "availability": True,
                     "reservation-list": False, "reservation-lookup": False,
                     "reservation-create": False, "reservation-cancel": False,
                     "reservation-patch": False, "moves": False}.items():
    if public:
        add("6. Authentication / 8. API", 214, "auth", {"auth-" + path: f"{path} is public without token."})
    else:
        for variant, description in {"absent": "absent Authorization header", "unknown": "unknown Bearer token", "basic": "malformed Basic authorization",
                                     "bearer-no-value": "malformed Bearer header without a token", "bearer-empty": "malformed Bearer header with empty value"}.items():
            add("6. Authentication / 8. API", 214, "auth", {f"auth-{path}-{variant}": f"{path}: {description} gives 401 unauthenticated."})

# Field/type/format alternatives are separately observable, rather than one
# representative refusal covering several routes or validation precedence rules.
VALIDATION_VARIANTS = [("party-string", "party_size", "string party size", 422), ("party-bool", "party_size", "boolean party size", 422),
                       ("party-fraction", "party_size", "nonintegral party size", 422), ("party-zero", "party_size", "zero party size", 422),
                       ("party-negative", "party_size", "negative party size", 422), ("time-wrong-type", "starts_at_local", "numeric local timestamp", 400),
                       ("time-z", "starts_at_local", "local timestamp ending in Z", 422), ("time-offset", "starts_at_local", "local timestamp with explicit offset", 422),
                       ("time-seconds", "starts_at_local", "local timestamp including seconds", 422), ("time-space", "starts_at_local", "space instead of T separator", 422),
                       ("time-unpadded", "starts_at_local", "unpadded calendar components", 422), ("date-nonleap", "starts_at_local", "February 29 in a non-leap year", 422),
                       ("date-month", "starts_at_local", "month thirteen", 422), ("date-day", "starts_at_local", "April 31", 422)]
VALIDATION_VARIANTS += [(f"{field}-{kind}", field, f"{kind} {field}", 400) for field in ["restaurant_id", "table_id"] for kind in ["bool", "array", "object", "number", "null"]]
for endpoint in ["create", "patch", "batch"]:
    for variant, field, description, status in VALIDATION_VARIANTS:
        if endpoint != "create" and field == "restaurant_id":
            continue
        add("5. Errors / 8. POST/PATCH /reservations / 11. Atomic reservation moves", 169, "validation",
            {f"validation-{endpoint}-{variant}": f"{endpoint}: {description} returns {status} {'malformed_request' if status == 400 else 'validation_failed'}."})
for variant, description in {"exponent": "1e9", "fraction": "4.0", "plus": "+4", "negative": "-4", "leading-space": "leading whitespace", "trailing-space": "trailing whitespace"}.items():
    add("5. Errors", 175, "validation", {"query-decimal-" + variant: f"party_size query written as {description} returns 422 validation_failed."})
for endpoint, fields in {"signup": ["email", "password", "display_name"], "login": ["email", "password"]}.items():
    for field in fields:
        for variant in ["bool", "number", "array", "object", "null"]:
            add("5. Errors / 6. Authentication", 169, "auth", {f"{endpoint}-{field}-type-{variant}": f"{endpoint}: {variant} {field} returns 400 malformed_request."})
for kind in ["user", "restaurant", "table", "reservation"]:
    for bound in ["max", "over"]:
        add("3.4 Conventions / 4. Fixture format", 89, "conventions", {f"fixture-id-{kind}-{bound}": f"Reset fixture {kind} IDs of {'64 characters are accepted' if bound == 'max' else '65 characters return 422 validation_failed'}."})

for path in ["create", "batch"]:
    add("7. Idempotency", 229, "idempotency", {
        f"{path}-key-missing": f"{path}: absent key returns 400 missing_idempotency_key.",
        f"{path}-key-empty": f"{path}: empty key returns 400 missing_idempotency_key.",
        f"{path}-key-1": f"{path}: a one-character key is valid.",
        f"{path}-key-255": f"{path}: a 255-character key is valid.",
        f"{path}-key-256": f"{path}: a 256-character key returns 422 validation_failed.",
        f"{path}-key-user": f"{path}: identical key strings are independent across users.",
        f"{path}-key-first": f"{path}: first successful keyed request returns 201.",
        f"{path}-key-replay-status": f"{path}: replay returns 200.",
        f"{path}-key-replay-body": f"{path}: replay returns original JSON response exactly.",
        f"{path}-key-json-value": f"{path}: whitespace/key order do not change parsed body identity.",
        f"{path}-key-conflict": f"{path}: same key with different body returns 409 idempotency_key_reuse.",
        f"{path}-key-before-validation": f"{path}: body conflict is resolved before field validation.",
        f"{path}-key-before-resource": f"{path}: receipt replay is resolved before current-resource checks.",
        f"{path}-key-failed-reuse": f"{path}: a key used by a failed 4xx request remains reusable.",
        f"{path}-key-concurrent-first": f"{path}: concurrent identical fresh-key requests have exactly one 201.",
        f"{path}-key-concurrent-replays": f"{path}: all other identical concurrent requests are 200 with the original body.",
        f"{path}-key-once": f"{path}: concurrent identical request changes state exactly once.",
        f"{path}-key-after-amend": f"{path}: replay after amendment returns the original response.",
        f"{path}-key-after-cancel": f"{path}: replay after cancellation returns the original response.",
        f"{path}-key-no-mutation": f"{path}: successful replay has no additional state changes.",
    })
add("7. Idempotency", 237, "idempotency", {"key-path-scope": "Same user/key/JSON body on different paths is independent and succeeds normally."})

add("8. GET /restaurants", 269, "basics", {
    "restaurants-status": "Public list returns 200.",
    "restaurants-envelope": "List returns a restaurants array.",
    "restaurants-id": "List exposes each fixture restaurant id.",
    "restaurants-name": "List exposes each fixture restaurant name.",
    "restaurants-timezone": "List exposes each fixture restaurant timezone.",
})
add("8. GET /restaurants/{id}", 275, "basics", {
    "detail-status": "Restaurant detail returns 200.",
    "detail-unknown": "Unknown restaurant detail returns 404 not_found.",
    **{"detail-" + field: f"Restaurant detail preserves fixture {field}." for field in
       ["id", "name", "timezone", "slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "opening_hours", "tables"]},
})
add("8. GET /availability", 281, "availability", {
    "availability-status": "Public availability returns 200.",
    "availability-required-restaurant": "Missing restaurant_id query returns 422 validation_failed.",
    "availability-required-date": "Missing date query returns 422 validation_failed.",
    "availability-required-party": "Missing party_size query returns 422 validation_failed.",
    "availability-restaurant": "Availability echoes restaurant_id.",
    "availability-date": "Availability echoes local calendar date.",
    "availability-timezone": "Availability echoes restaurant timezone.",
    "availability-slots-array": "Availability includes slots array.",
    "availability-local": "Every slot starts_at_local is full YYYY-MM-DDTHH:MM.",
    "availability-absolute": "Every slot starts_at has the correct explicit offset.",
    "availability-table-ids": "Every slot has available_table_ids array.",
    "availability-grid": "Slots follow every slot step from opening.",
    "availability-final": "Final allowed slot ends at or before closing; later slots are absent.",
    "availability-capacity": "Available tables have capacity at least party size.",
    "availability-occupancy": "Overlapping confirmed reservations remove tables from availability.",
    "availability-order": "Available table IDs retain fixture order.",
    "availability-empty-slot": "An occupied/full slot still appears with empty table list.",
    "availability-closed": "A closed day returns slots: [].",
    "availability-create-roundtrip": "Slot's starts_at_local is accepted unchanged by booking.",
})

RESPONSE_FIELDS = ["reservation_id", "reference", "restaurant_id", "table_id", "party_size", "status", "starts_at_local", "starts_at", "ends_at", "created_at"]
for endpoint, line in [("create", 312), ("list", 356), ("lookup", 362), ("cancel", 367), ("patch", 382), ("batch", 443)]:
    add("8. API / " + endpoint if endpoint != "batch" else "11. Atomic reservation moves", line,
        "booking" if endpoint in ["create", "list", "lookup"] else endpoint,
        {f"{endpoint}-response-{field}": f"{endpoint} response carries the correct reservation {field}." for field in RESPONSE_FIELDS})
add("8. POST /reservations", 312, "booking", {
    "booking-201": "Successful reservation create returns 201.",
    "reference-format": "Reference uses 6..12 uppercase ASCII A-Z0-9 characters.",
    "reference-unique": "References are unique across all reservations, including cancelled ones.",
    "booking-overlap": "Overlapping confirmed occupancy returns 409 table_unavailable.",
    "booking-grid": "Off-grid booking returns 422 not_on_slot_grid.",
    "booking-before-open": "Booking before opening returns 422 outside_opening_hours.",
    "booking-after-close": "Booking ending after closing returns 422 outside_opening_hours.",
    "booking-capacity": "Party above table capacity returns 422 party_exceeds_capacity.",
    "booking-unknown-restaurant": "Unknown restaurant returns 404 not_found.",
    "booking-unknown-table": "Unknown table returns 404 not_found.",
    "booking-other-restaurant-table": "Table belonging to another restaurant returns 404 not_found.",
})
for endpoint in ["create", "patch", "batch"]:
    for field in ["restaurant_id", "table_id", "starts_at_local", "party_size"] if endpoint == "create" else ["table_id", "starts_at_local", "party_size"]:
        add("8. POST/PATCH /reservations / 11. Atomic reservation moves", 312 if endpoint == "create" else 382 if endpoint == "patch" else 443,
            "validation", {f"{endpoint}-input-{field}": f"{endpoint}: {field} enforces its endpoint-specific type and value rules."})
add("8. GET /reservations", 356, "booking", {
    "list-order": "Caller reservations are sorted by starts_at descending.",
    "list-owner": "Caller list includes only that caller's bookings.",
    "list-statuses": "List includes both confirmed and cancelled records.",
    "list-empty": "Empty caller list is {reservations: []}.",
    "lookup-owner": "Another owner's reference returns 404 not_found without revealing its existence.",
    "lookup-unknown": "Unknown reference returns 404 not_found.",
})
add("8. POST /reservations/{reference}/cancel", 367, "cancel", {
    "cancel-200": "Cancellation returns 200 with current cancelled state.",
    "cancel-release": "Cancellation immediately releases occupancy in next availability response.",
    "cancel-twice": "Repeated cancellation returns current state with 200.",
    "cancel-cutoff": "Cancellation within cutoff returns 409 cutoff_passed.",
    "cancel-later": "Cancellation at or after start returns 409 cutoff_passed.",
    "cancel-owner": "Cancellation of another owner's booking returns 404 not_found.",
})
add("8. PATCH /reservations/{reference}", 382, "patch", {
    "patch-subsets": "Any subset of table_id, starts_at_local and party_size may be amended.",
    "patch-no-key": "PATCH needs no idempotency key.",
    "patch-retain-omitted": "Omitted PATCH fields retain their current values.",
    "patch-validation": "PATCH applies the same grid/opening/capacity/time/resource validation as create.",
    "patch-cutoff": "PATCH within cutoff returns 409 cutoff_passed.",
    "patch-current-cutoff": "PATCH cutoff uses current start, not proposed/original start.",
    "patch-cancelled": "PATCH of cancelled booking returns 409 reservation_cancelled.",
    "patch-atomic": "Successful amendment releases old and reserves new occupancy together.",
    "patch-failure-record": "Failed amendment leaves the original record unchanged.",
    "patch-failure-occupancy": "Failed amendment leaves original occupancy unchanged.",
    "patch-identity": "Reservation ID survives amendments.",
    "patch-reference": "Reference survives amendments.",
    "patch-owner": "Another owner's reference returns 404 not_found.",
})
for zone, spring, fall in [("berlin", "2026-03-29", "2026-10-25"), ("new-york", "2026-03-08", "2026-11-01")]:
    add("9. Time and DST", 394, "dst", {
        f"{zone}-spring-absent": f"{zone}: {spring} nonexistent local times do not appear in availability.",
        f"{zone}-spring-error": f"{zone}: booking nonexistent local time gives 422 invalid_local_time.",
        f"{zone}-fall-first": f"{zone}: {fall} repeated-hour booking resolves to the first occurrence.",
        f"{zone}-fall-once": f"{zone}: repeated-hour availability slot appears once.",
        f"{zone}-fall-second": f"{zone}: second occurrence cannot be booked by offset timestamp.",
        f"{zone}-absolute-duration": f"{zone}: duration across DST uses elapsed absolute minutes.",
        f"{zone}-offsets": f"{zone}: timestamps follow date-specific IANA offsets.",
    })
add("10. Export and import", 418, "export", {
    "export-public": "Export requires no authentication.",
    "export-200": "Export returns 200 JSON object.",
    "export-track": "Export track is tablekeeper.",
    "export-version": "Export format_version is 1.",
    "export-state": "Export includes opaque JSON state object.",
    "import-public": "Import requires no authentication.",
    "import-204": "Unchanged export imports with 204 and no body.",
    "import-independent": "Import works in an independent destination process without source volumes or address.",
    "import-replace-data": "Import removes all pre-existing destination reservations/configuration.",
    "import-replace-credentials": "Import removes all pre-existing destination accounts/tokens.",
    "import-repeat": "Repeated import restores exact snapshot without duplicates.",
    "import-invalid-json": "Unparseable import body returns 400 malformed_request.",
    "import-missing": "Missing import wrapper fields return 422 validation_failed.",
    "import-track": "Wrong import track returns 422 validation_failed.",
    "import-version": "Wrong import version returns 422 validation_failed.",
    "import-invalid-state": "Invalid import state returns 422 validation_failed.",
    "import-failure-atomic": "Invalid import leaves all destination state unchanged.",
    "export-readonly": "Export does not mutate source state.",
    "export-snapshot": "Later source writes do not alter an earlier export.",
    "import-accounts": "Import preserves accounts and display identity.",
    "import-passwords": "Imported hashed passwords still allow login.",
    "import-tokens": "Existing source bearer tokens remain valid in destination.",
    "import-fixture": "Import preserves restaurant/table fixture configuration.",
    "import-reservations": "Import preserves every confirmed and cancelled reservation.",
    "import-references": "Import preserves references.",
    "import-identities": "Import preserves reservation IDs.",
    "import-statuses": "Import preserves reservation statuses.",
    "import-timestamps": "Import preserves start/end/creation timestamps exactly.",
    "import-create-receipt": "Import preserves original create response and parsed request identity.",
    "import-batch-receipt": "Import preserves original batch response and parsed request identity.",
    "import-failed-create-key": "Failed reservation-create keys remain reusable after import.",
    "import-failed-batch-key": "Failed batch-move keys remain reusable after import.",
    "reset-imported": "Reset clears imported records, credentials, tokens and retry receipts.",
    "export-atomic": "Concurrent exports represent complete atomic snapshots, not partial transactions.",
})
add("11. Atomic reservation moves", 443, "batch", {
    "batch-min": "Batch accepts 1 move.",
    "batch-max": "Batch accepts 8 distinct moves.",
    "batch-empty": "Empty moves returns 422 validation_failed.",
    "batch-too-many": "9 moves returns 422 validation_failed.",
    "batch-shape": "Invalid moves shape returns 422 validation_failed.",
    "batch-reference-type": "Every move reference must be a string; invalid shape returns 422 validation_failed.",
    "batch-duplicate": "Duplicate move references return 422 validation_failed.",
    "batch-owner": "Another owner's reference returns 404 not_found.",
    "batch-unknown": "Unknown reference returns 404 not_found.",
    "batch-restaurant": "Cross-restaurant moves return 422 validation_failed.",
    "batch-fields": "Batch accepts all ordinary PATCH fields.",
    "batch-omitted": "Omitted move fields retain current values.",
    "batch-unknown-fields": "Unknown move fields are ignored.",
    "batch-identity": "Batch preserves reservation IDs.",
    "batch-owner-preserved": "Batch preserves booking owners.",
    "batch-created": "Batch preserves created_at timestamps.",
    "batch-cancelled": "Cancelled member returns 409 reservation_cancelled.",
    "batch-cutoff": "Existing cutoff applies to every member.",
    "batch-input-order": "First non-occupancy error in input order wins.",
    "batch-cutoff-precedence": "For each member, cutoff errors precede proposed field changes.",
    "batch-validation-before-overlap": "Non-occupancy errors precede all overlap checks.",
    "batch-mutual-overlap": "Resulting members overlapping each other return 409 table_unavailable.",
    "batch-unlisted-overlap": "Result overlapping unlisted booking returns 409 table_unavailable.",
    "batch-unchanged-occupancy": "Unchanged listed members retain occupancy.",
    "batch-swap": "Occupied-table cyclic swaps succeed atomically.",
    "batch-failure-records": "Any failed batch leaves every reservation record unchanged.",
    "batch-failure-occupancy": "Any failed batch leaves all occupancy unchanged.",
    "batch-failure-keys": "Any failed batch leaves its retry key reusable.",
    "batch-response-order": "Successful batch returns every member in input order.",
    "batch-response-unchanged": "Successful batch includes unchanged members.",
    "batch-noop": "No-op moves retain every existing value.",
})
add("Stage 1 preamble / participant guide", 5, "provenance", {
    "source-provenance": "Implementation derives from supplied requirements, not existing domain-product source/API/schema.",
    "complete-clone": "Deliverable contains all required committed files; no nested Git repos, submodules or escaping symlinks.",
    "two-builders": "Both designated builders contribute substantive committed work in the Band room.",
    "history-preserved": "Implementation history and failure/repair evidence remain intact without rewriting.",
    "own-stage": "Stage 1 implements its own stage; official overshoot does not establish Stage 2.",
}, "commit history, room handoff and official isolated harness")

# A second source pass makes inherited generic validation/ignore rules explicit
# on fixture and mutation paths as well as ordinary create requests.
FIXTURE_STRING_FIELDS = {
    "user": ["id", "email", "password", "display_name"],
    "restaurant": ["id", "name", "timezone"],
    "hours": ["weekday", "opens", "closes"],
    "table": ["id", "label"],
    "reservation": ["restaurant_id", "table_id", "starts_at_local", "id", "reference", "user_id"],
}
FIXTURE_NUMBER_FIELDS = {"restaurant": ["slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes"], "table": ["capacity"], "reservation": ["party_size"]}
for shape, fields in {k: v + FIXTURE_NUMBER_FIELDS.get(k, []) for k, v in FIXTURE_STRING_FIELDS.items()}.items():
    for field in fields:
        add("4. Fixture format / 5. Errors", 109, "extra", {f"reset-missing-{shape}-{field}": f"Required fixture {shape}.{field} missing returns 422 validation_failed."})
        for variant in (["string", "bool", "array", "object", "null"] if field in FIXTURE_NUMBER_FIELDS.get(shape, []) else ["number", "bool", "array", "object", "null"]):
            status = 422 if shape == "reservation" and field == "party_size" else 400
            add("4. Fixture format / 5. Errors", 169, "extra", {f"reset-type-{shape}-{field}-{variant}": f"Fixture {shape}.{field} of wrong type {variant} returns {status} {'validation_failed' if status == 422 else 'malformed_request'}."})
for field in ["opening_hours", "tables"]:
    add("4. Fixture format / 5. Errors", 109, "extra", {"reset-missing-restaurant-" + field: f"Required fixture restaurant.{field} missing returns 422 validation_failed."})
for endpoint in ["reset", "signup", "login", "create", "patch", "cancel", "batch", "import"]:
    add("3.4 Conventions", 88, "extra", {"unknown-field-" + endpoint: f"{endpoint} ignores unknown request body fields."})
for endpoint in ["create", "patch", "batch"]:
    for field in ["party_size", "starts_at_local"]:
        for variant in ["array", "object", "null"] + (["bool"] if field == "starts_at_local" else []):
            status = 422 if field == "party_size" else 400
            add("5. Errors / 8. POST/PATCH /reservations / 11. Atomic reservation moves", 172, "extra", {f"extra-type-{endpoint}-{field}-{variant}": f"{endpoint}: {variant} {field} returns {status} {'validation_failed' if status == 422 else 'malformed_request'}."})
    for field in ["restaurant_id", "table_id"] if endpoint == "create" else ["table_id"]:
        add("3.4 Conventions / 5. Errors", 89, "extra", {f"id-over-{endpoint}-{field}": f"{endpoint} {field} longer than 64 characters returns 422 validation_failed."})
for endpoint in ["create", "batch"]:
    add("7. Idempotency", 255, "extra", {f"{endpoint}-failed-occupancy-key": f"{endpoint}: an occupancy-failed key can be reused with its original body after the conflicting occupancy is freed."})
for endpoint in ["patch", "batch"]:
    for label in ["berlin", "new-york"]:
        add("8. PATCH /reservations / 9. Time and DST / 11. Atomic reservation moves", 385, "extra", {f"{endpoint}-{label}-skipped-time": f"{endpoint} rejects a nonexistent local time with 422 invalid_local_time."})
for date_kind, description in [("leap", "2024-02-29"), ("year-one", "0001-01-01"), ("year-max", "9999-12-31")]:
    add("4. Fixture format / 5. Errors", 143, "extra", {"calendar-" + date_kind: f"Legal calendar date {description} is accepted without past-date rejection or year-format truncation."})
add("8. PATCH /reservations / 11. Atomic reservation moves", 385, "extra", {
    "patch-closed-day": "Amendment to a closed day returns 422 outside_opening_hours with no mutation.",
    "batch-closed-day": "Batch amendment to a closed day returns 422 outside_opening_hours with no mutation.",
})


for label, zone in [("utc", "UTC"), ("berlin", "Europe/Berlin"), ("new-york", "America/New_York")]:
    for tag, day in [("min", "0001-01-01"), ("max", "9999-12-31")]:
        prefix = "edge-" + label + "-" + tag
        for suffix, meaning in [("availability", "returns 200 availability"), ("slots", "offers all eight fitting slots"), ("create", "accepts the last fitting slot with 201"), ("start-instant", "preserves the exact IANA start instant"), ("end-instant", "ends after 90 absolute minutes")]:
            add("4. Fixture format / 8. API / 9. Time and DST", 143, "calendar-edges", {prefix+"-"+suffix: f"Calendar boundary {day} in {zone} {meaning}, regardless of UTC representation range."})
        if tag == "min" and label != "utc":
            add("3.4 Conventions / 9. Time and DST", 86, "calendar-edges", {prefix+"-rfc3339": f"Historic {zone} reservation response timestamps are RFC3339 with explicit offsets."})
for operation in ["availability", "create"]:
    add("4. Fixture format / 8. API / 9. Time and DST", 143, "calendar-edges", {"edge-berlin-min-midnight-"+operation: f"A fitting midnight slot at 0001-01-01 Europe/Berlin is accepted by {operation}, even before the UTC calendar minimum."})


def write_matrix(path):
    assert len({r["requirement_id"] for r in ROWS}) == len(ROWS)
    with Path(path).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ROWS[0]))
        w.writeheader()
        w.writerows(ROWS)


if __name__ == "__main__":
    write_matrix(Path(__file__).with_name("coverage-prepared.csv"))
    print(f"Prepared {len(ROWS)} atomic rows; all unverified.")
