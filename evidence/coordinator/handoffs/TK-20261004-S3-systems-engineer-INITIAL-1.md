COMPLETE STAGE 3 TASK PACKAGE TK-20261004-S3-systems-engineer-INITIAL-1
Shared card #19. Join and keep it current. This is one task, not separate tasks per part. Collect every numbered part and END; confirm completeness before any base copy, implementation, or verification preparation. Earlier parts are not a new task.

Stage 3 Systems ownership and execution scope:
Own stage-3/core.py and stage-3/json_codec.py, plus evidence/systems-engineer/ Stage 3 files. First, copy these two files byte-for-byte, modes preserved, from the newly frozen accepted Stage 2 working folder into stage-3 and commit only those owned paths. Do not extend code until the coordinator records complete predecessor copy proof covering all nine Stage 2 service files and releases the existing implementation phase. Report the exact base-copy revision. Never modify an accepted stage folder.
After release, implement all Stage 3 integrity behavior from the complete cumulative specifications: policy permission/publication/selection and immutable accepted terms, exact explanations, optimistic revisions and ordered immutable owner-only histories/decisions, anchor adoption with per-occurrence policy/DST/atomicity, ordinary series exception/cancellation semantics, canonical pair history, collective-move policies and once-per-operation restaurant/series counters, and atomic export/import compatibility with genuine Stage 1 and Stage 2 services. Preserve exact JSON and per-receipt legacy numeric profiles, original receipt shapes and sessions/references, the detached nonrecursive state/export contract, and all inherited error/ordering/transaction rules.
Retain the existing Engine.request transport boundary and communicate interface contracts directly with the Interface seat already in the room; inspect participants and route literal mentions yourself. No invented manager roles, capability endpoints, bulk series cancellation, or required PATCH expected_revision. Use fixture manager_user_ids only. Where earlier exports lack newly introduced fields, make a source-faithful compatibility decision with independently reviewable evidence; do not fabricate historical events or retroactively enrich original receipts.
Build and probe your complete service image within your own namespace and host port range 18100–18199. Runtime has no outbound network, 2 CPUs and 2 GiB, no host dependencies or separate database. Use deterministic saved traces, atomic rollback/concurrency/retry/upgrade probes and actual old services, preserving every failure/repair. Include no tests/evidence in stage-3 unless genuinely service-required.
Before handing off, commit only owned explicit paths, report the full revision, changed files, actual commands/results and counted scope, assumptions and remaining risks. Commit with Systems Engineer identity, git commit --only with owned paths, no history rewrites. Builder evidence does not establish independent acceptance. Keep your shared card current.

Full factory task:
Scored factory run TK-20261004. Target all four fully specification-complete consecutive Tablekeeper stages, with strong product quality and independent verification, not merely the public minimum. Use the configured seats for substantive implementation and independent review. Report partial completion honestly if genuinely blocked.

Workspace root: /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory
Kickoff repository: /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/kickoff
Result repository: /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-result
Check outputs: /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-checks
Track: tablekeeper

Execution environment: all four seats run on the same macOS host and share the one result working tree above, so only one seat edits or commits a given path at a time and the coordinator sequences overlapping work. The official harness Python is <workspace root>/.venv/bin/python; run it from the kickoff directory, e.g. <workspace root>/.venv/bin/python -m harness run --track tablekeeper --repo <result repository> --stage N --mode isolated --out <check outputs>/<new-unique-name>.
A Docker daemon is running on the host; the first isolated run builds the unchanged official runner image. Use a new --out directory for every run and never delete earlier outputs. Dependencies an implementation needs belong in its own buildable image, not on the host. The official kickoff revision is 803560d2a678ace1414465c098eb0ab5380ffade. Each seat is configured as Codex with model gpt-6.1-sol; record the model and effort your own runtime actually reports.
When a seat runs a service or container directly it uses its own host port range: coordinator 18000-18099, systems 18100-18199, interface 18200-18299, verifier 18300-18399.
Commit with your own seat identity, for example git -c user.name="<Seat Name>" -c user.email="<seat-slug>@nightwatch-foundry.invalid" commit ...
Stay strictly inside the workspace root: do not read, write or execute anything outside it, do not inspect credentials or other projects on this machine, do not change system, Docker or network settings, and do not stop containers or processes you did not start.
Configured seats: coordinator yy5652/foundry-coordinator; systems builder yy5652/systems-engineer; interface builder yy5652/interface-engineer; independent verifier yy5652/independent-verifier. Only these seats may participate.

Authoritative instructions:

1. Read the complete participant guide at kickoff/docs/participant-guide.md under the absolute workspace root before assigning work.
2. Process stages 1 through 4 strictly in order. The complete stage specifications are kickoff/tablekeeper/spec/stage-1.md through stage-4.md. Stage N must extend the accepted Stage N-1 folder while remaining a complete, independent service.
3. For every delegated assignment, include the complete applicable task and full specification text in the direct handoff. A file path or room-message pointer alone is not a complete handoff. The participant guide explicitly allows long handoffs as numbered direct messages. Use a single package identifier and part i/N, at most 12,000 characters per message including routing and context, with a final completion marker. Preserve the full applicable specs across parts. The receiver must confirm all parts arrived before working; an earlier part is not a new task. If transport rejects a part, split and resend that missing part transparently without dropping requirements or asking the human.
4. The result must be created by the seats in this room. Human-authored stage code is forbidden. Preserve all commits and room evidence; never amend, rebase, squash, or rewrite history.
5. Build to the specification, not the visible tests. The verifier must create a requirement coverage matrix and probe untested boundaries, concurrency, idempotency, recovery, upgrade, historical-truth, and deterministic planning behavior using black-box evidence derived from the specification. Number every normative requirement from the full specs. Each ledger row must carry the source section, applicable stage, owner, candidate full revision, verification method, executable command or observed browser interaction, evidence path and verdict. Split bundled obligations so a passing happy path cannot conceal an untested error, ordering, atomicity or recovery rule. Track inherited requirements explicitly; unsupported claims stay unverified. Use deterministic seeds and saved operation traces for randomized invariant checks, and a separately derived small reference oracle where appropriate. Do not copy another entry's implementation, tests or claimed coverage counts.
6. The systems builder owns integrity-critical service behavior. The interface builder owns interface/integration behavior and presentation quality. Both must contribute substantive committed work. The verifier reviews candidates independently and may reject promotion. The coordinator may not silently do all implementation itself.
7. A stage is accepted only after clean startup, applicable official harness checks, earlier-stage regression checks, specification coverage review, and an independent verifier verdict against a named full commit revision.
8. Run final checks in isolated mode. The judged service has no outbound network, 2 vCPU and 2 GiB. Preserve every failure and repair in the room and Git history.
9. Maintain an append-only evidence ledger with wall time, model, usage/cost estimate, commits, checks, rejected candidates, repairs, and remaining risk. Keep ledgers, coverage matrices, probes and other evidence outside the graded stage-N/ folders (for example under evidence/ in the result repository).
10. Prepare measured facts for the operator-authored README.md and FACTORY.md, copy the four generic files in factory/mandates-final/ into mandates/ unchanged, and write one RUN.md per completed stage and all evidence needed for a fresh-clone review. Do not fabricate room.json; it is downloaded from Band after the run.
11. During this run, this dispatch is the only human input. Do not ask the human for clarification, approval, debugging hints, or a go-ahead between stages. Resolve choices from the published requirements and communicate within the band. If truly blocked, report the blocker and evidence as the outcome.
12. Finish with a final report stating the highest consecutive accepted stage, exact revisions, exact observed check counts, clean-clone status, known limitations, elapsed time, and measured or explicitly unknown model spend.
13. Read factory/PRODUCT_ACCEPTANCE.md under the absolute workspace root as a supplementary task-specific acceptance brief, never as a replacement for the complete specs. Do not copy its track-specific content into mandates. Derive independent tests from the specs, including the behaviors absent from shipped checks.
14. Aim for full specification coverage at every stage, not merely the minimum public claim threshold. Freeze each accepted stage before extending its copy. Do not sabotage a correct earlier requirement to fail an overshoot probe.
15. Preserve genuine task ownership: substantial implementation by both builders, independent verifier execution against exact revisions, coordinator integration. Never fabricate disagreements, test counts, model costs, screenshots or handoffs.
16. Keep the room economical: post decisions, handoffs, revisions, verdicts and evidence paths, not long raw logs. Store bulky output in files under the check outputs or evidence/ and cite the path.
17. Time budget: aim to finish all four stages within about 16 hours of this dispatch. At 22 hours stop extending, make sure every accepted stage and the evidence are committed, and post the final report for the highest consecutive accepted stage. An honest partial result is better than an unfinished run.

Begin by confirming all four configured seats already in this room, obtaining reciprocal literal handle messages, publishing the requirements ledger, and assigning Stage 1 work. Work only with these seats in this room. Do not contact other agents, inspect credentials, or access other competitions. Do not reuse toy solution code, the abandoned band-work/result repository, or replay their history into the fresh scored result. Public publishing, final room export and competition submission remain operator-controlled steps.

Additional shared-tree discipline: write room messages, commits and documents in English. Stage/commit only owned explicit paths; no blanket add, stash, hard reset, clean, checkout-all, rebase, amend, force, pull or push. Wait/retry an index lock. Prefix containers, networks, images and temporary directories with your seat name; remove only your own. Every implementation handoff must report full committed revision, changed-file summary, commands run, results, assumptions and remaining risks. During this autonomous run communicate inside the Band room only. All exact local paths in this package are inspectable on this shared host.

Applicable complete Stage 1 specification:
# Tablekeeper — Stage 1: reservations

This stage defines the initial service and its API.

Build from the supplied requirements. Source code, API documentation and schemas from
existing products in this domain must not be used.

## 1. Scope

Diners can search restaurant availability, book a table and receive a confirmation
reference. They can cancel or amend their bookings, including changing several bookings
together. Each restaurant has its own table capacities, opening hours and cancellation policy.
Only the HTTP API is required.

Two `confirmed` reservations must never occupy the same table at overlapping times,
including during concurrent requests. Occupancy is the half-open interval
`[starts_at, starts_at + reservation_duration)`. A 90-minute booking at 19:00 therefore
does not overlap a booking starting at 20:30. Retries and rejected requests must not
create duplicate or partial bookings.

## 2. Delivery and deployment

Deliver an HTTP service, a `Dockerfile` and a `RUN.md` with a command that builds and
starts the service without manual setup. Language, framework and storage are unrestricted.
A `docker-compose.yml` is optional.

The submission is a containerized HTTP service, not a Python package. Python is not
required in the implementation. TypeScript/JavaScript, Go, Rust, Java, Python and any
other language are equally valid. The harness builds the submitted `Dockerfile`, starts
the resulting image and tests only its HTTP behavior; it does not import or execute the
submission's source files on the judge host.

The image must run on its own with `-e PORT=<port>` and a port mapping. Runtime networking
has no outbound access. All runtime dependencies, initialization and seed data must work
within that single container. Compose configuration is not used to start the service.

### Resource limits

The service must operate within these limits:

| Limit | Value |
|---|---|
| CPU | 2 vCPU |
| Memory | 2 GiB |
| Start to first healthy response | 60 s |
| Concurrent requests | up to 50 in flight |
| Per-request timeout | 5 s (10 s for `POST /_test/reset`) |
| Outbound network | available during `docker build`, **none at run time** |
| Disk | ephemeral; state need not survive a container restart |

Runtime assets and dependencies must be included in the image. This includes fonts,
scripts and stylesheets; external services are unavailable at runtime.

## 3. Runtime contract

### 3.1 Listening

Listen on `0.0.0.0` using the `PORT` environment variable, default `8080`.

### 3.2 Health

```http
GET /health  ->  200  {"status": "ok"}
```

Return 200 once the service and its data store can serve requests, within 60 seconds
of container start. Non-200 responses are permitted before the service is ready.

### 3.3 Reset and seed

```http
POST /_test/reset
Content-Type: application/json

{ ...fixture... }

->  204 No Content
```

Replace all service state with the fixture in the request body (§4). When reset returns
204, subsequent requests must see only that fixture. Repeated resets are supported.
This test endpoint must be enabled in the delivered image and requires no authentication.

### 3.4 Conventions

- Requests and responses are `application/json; charset=utf-8`.
- Timestamps in responses are RFC 3339 with an explicit offset, e.g. `2026-09-24T19:00:00+02:00`.
- Unknown fields in a request body are ignored, never an error.
- Unknown query parameters are ignored.
- IDs are opaque strings of at most 64 characters. Their format is yours. This limit
  also applies to IDs supplied in reset fixtures.

## 4. Model

Restaurants and tables are supplied through `POST /_test/reset` only. Restaurant and
table creation endpoints are out of scope.

| Field | On | Meaning |
|---|---|---|
| `timezone` | Restaurant | IANA zone name, e.g. `Europe/Berlin`. All of the restaurant's times are local to this |
| `slot_minutes` | Restaurant | Bookings start on a grid of this many minutes from opening time |
| `reservation_duration_minutes` | Restaurant | How long every reservation occupies its table |
| `cancellation_cutoff_minutes` | Restaurant | A booking cannot be cancelled or changed within this many minutes of its start |
| `opening_hours` | Restaurant | Per weekday. A day with no entry is closed |
| `capacity` | Table | Maximum party size |

### Fixture format

```json
{
  "users": [
    { "id": "u_ada", "email": "ada@example.com",
      "password": "correct horse", "display_name": "Ada" }
  ],
  "restaurants": [
    {
      "id": "r_anker",
      "name": "Zum Anker",
      "timezone": "Europe/Berlin",
      "slot_minutes": 30,
      "reservation_duration_minutes": 90,
      "cancellation_cutoff_minutes": 120,
      "opening_hours": [
        { "weekday": "thu", "opens": "18:00", "closes": "23:00" },
        { "weekday": "fri", "opens": "18:00", "closes": "23:30" }
      ],
      "tables": [
        { "id": "t_1", "label": "1", "capacity": 2 },
        { "id": "t_2", "label": "2", "capacity": 4 }
      ]
    }
  ],
  "reservations": []
}
```

- `weekday` is one of `mon tue wed thu fri sat sun`.
- `opens` and `closes` are local `HH:MM`, 24-hour. `closes` is always later than `opens` on the
  same local day — opening hours never cross midnight.
- Seeded users must be able to log in with the given password immediately.
- `reservations` may seed confirmed bookings, with the same fields as a `POST /reservations`
  body plus `id`, `reference` and `user_id`.

Fixtures may use any calendar date. A booking must not be rejected solely because its
start is in the past; the cancellation and amendment cutoff rules still apply.

## 5. Errors

Every 4xx and 5xx response carries this body:

```json
{ "error": { "code": "table_unavailable", "message": "human readable, any wording" } }
```

Use the specified HTTP status and `code`. The human-readable `message` may use any wording.
Endpoint-specific errors are listed with each endpoint.

| Status | `code` | When |
|---|---|---|
| 400 | `malformed_request` | Unparseable body, or a field of the wrong JSON type |
| 400 | `missing_idempotency_key` | Required `Idempotency-Key` header absent or empty |
| 401 | `unauthenticated` | Missing, malformed or unknown bearer token |
| 403 | `forbidden` | Authenticated, but not permitted to touch this resource |
| 404 | `not_found` | No such resource, or not visible to this caller |
| 409 | `idempotency_key_reuse` | Key already used by this caller with a different request body |
| 422 | `validation_failed` | A required field or query parameter is missing, or a stated rule is violated with no more specific code |

A field of the correct JSON type with an invalid format or out-of-range value gives
422 `validation_failed`, unless an endpoint specifies a different error. This includes
invalid dates, negative counts and values exceeding a stated maximum or length. In addition:

- Endpoint-specific field rules take precedence: invalid `party_size` values (including strings
  and booleans) and `starts_at_local` strings that are not a bare local `YYYY-MM-DDTHH:MM` are
  422 `validation_failed`. Other wrong JSON types follow the rule below.
- An integer-valued **query parameter** is written as plain decimal digits: `1e9`, `4.0` and `+4`
  are 422 `validation_failed` whatever their numeric value.
- Reserve 400 `malformed_request` for a body that does not parse or a field of the wrong type.

Shared ranges, enforced on every endpoint that takes them:

| Field | Valid | Otherwise |
|---|---|---|
| `Idempotency-Key` | 1 to 255 characters | 422 `validation_failed` |

Requests must not produce 5xx responses, including under concurrent load.

## 6. Authentication

Authentication supports signup and login. Email verification, password reset, refresh
tokens and role-management endpoints are out of scope. Permissions specified elsewhere
in these requirements still apply.

```http
POST /auth/signup
{ "email": "a@example.com", "password": "correct horse", "display_name": "Ada" }

->  201  { "user_id": "u_1", "display_name": "Ada", "token": "..." }
```

```http
POST /auth/login
{ "email": "a@example.com", "password": "correct horse" }

->  200  { "user_id": "u_1", "display_name": "Ada", "token": "..." }
```

| Case | Response |
|---|---|
| Email already registered | 409 `email_taken` |
| Password shorter than 8 characters | 422 `validation_failed` |
| `email` not of the form `local@domain` | 422 `validation_failed` |
| Wrong password or unknown email on login | 401 `unauthenticated` |

Every other endpoint requires a bearer token, except `/health`, `/_test/reset`, the two above, and
the three public endpoints named at the top of §8 — `GET /restaurants`, `GET /restaurants/{id}` and
`GET /availability`:

```http
Authorization: Bearer <token>
```

Tokens do not expire. An account may have multiple valid tokens and concurrent sessions.

Passwords must be stored using a password-hashing function such as bcrypt, scrypt or
Argon2, or an equivalent. Plaintext password storage is not permitted.

## 7. Idempotency

Two write paths require an idempotency key: **`POST /reservations`** (§8) and
**`POST /reservation-moves`** (§11).

```http
Idempotency-Key: <client-chosen string, 1..255 characters>
```

The key is scoped to **the authenticated user**. Two different users may use the same key string
with no interaction between them.

A replay means the same user sending the **same method, the same path and the same body**. The
same key with the same body on a different path is a different request, not a replay, and must
succeed normally.

After the body has been parsed as a JSON object and the caller authenticated, idempotency
is resolved before endpoint-specific field validation or current-resource checks. Thus a
used key with a different JSON body returns `409 idempotency_key_reuse` even when that new
body would otherwise be invalid.

| Situation | Response |
|---|---|
| Header absent or empty | 400 `missing_idempotency_key` |
| First use of the key | The normal response, **201** |
| Replay: same key, same body | **200**, body identical to the original response as a JSON value |
| Same key, different body | 409 `idempotency_key_reuse` |
| Key reused after the original request failed with 4xx | Treated as a first use |

"Same body" means the same JSON value after parsing — key order and whitespace do not matter.

For concurrent identical requests with an unused key, exactly one returns 201.
The others return 200 with the same body. The operation takes effect only once.

A successful replay returns the original response, even after the resource changes or
is cancelled. It makes no further state changes.

## 8. API

`GET /restaurants`, `GET /restaurants/{id}` and `GET /availability` are **public** — no bearer
token. Everything else needs one. Diners browse before they sign in.

### `GET /restaurants`

```json
{ "restaurants": [ { "id": "r_anker", "name": "Zum Anker", "timezone": "Europe/Berlin" } ] }
```

### `GET /restaurants/{id}`

The restaurant with its `slot_minutes`, `reservation_duration_minutes`,
`cancellation_cutoff_minutes`, `opening_hours` and `tables`, in the fixture's shape. 404 if
unknown.

### `GET /availability`

```http
GET /availability?restaurant_id=r_anker&date=2026-09-24&party_size=4
```

All three parameters are required; a missing one is 422 `validation_failed`. `date` is a local
calendar date at the restaurant.

```json
{
  "restaurant_id": "r_anker",
  "date": "2026-09-24",
  "timezone": "Europe/Berlin",
  "slots": [
    { "starts_at_local": "2026-09-24T18:00",
      "starts_at": "2026-09-24T18:00:00+02:00",
      "available_table_ids": ["t_2"] }
  ]
}
```

`starts_at_local` is the full `YYYY-MM-DDTHH:MM` and goes into `POST /reservations` unchanged.

A slot appears for every `slot_minutes` step from `opens` such that
`slot + reservation_duration_minutes <= closes`. `available_table_ids` lists the tables of that
restaurant with `capacity >= party_size` and no overlapping confirmed reservation, in fixture
order. A slot with no available table still appears, with an empty list.

A closed day returns `"slots": []`.

### `POST /reservations`

`Idempotency-Key` is required; see §7.

```http
POST /reservations
Authorization: Bearer <token>
Idempotency-Key: 2f9c1a...

{ "restaurant_id": "r_anker", "table_id": "t_2",
  "starts_at_local": "2026-09-24T19:00", "party_size": 4 }
```

`starts_at_local` is wall-clock at the restaurant, with no offset and no `Z`. Resolve it against
the restaurant's `timezone`.

```json
201
{
  "reservation_id": "res_7",
  "reference": "K3P7QW",
  "restaurant_id": "r_anker",
  "table_id": "t_2",
  "party_size": 4,
  "status": "confirmed",
  "starts_at_local": "2026-09-24T19:00",
  "starts_at": "2026-09-24T19:00:00+02:00",
  "ends_at": "2026-09-24T20:30:00+02:00",
  "created_at": "2026-09-21T11:04:03+00:00"
}
```

`reference` is 6 to 12 characters of `A-Z0-9`, unique across all reservations, and never changes.

| Case | Response |
|---|---|
| The table is taken for an overlapping interval | 409 `table_unavailable` |
| `starts_at_local` is not on the slot grid | 422 `not_on_slot_grid` |
| Slot outside opening hours, or the reservation would end after `closes` | 422 `outside_opening_hours` |
| `party_size` exceeds the table's `capacity` | 422 `party_exceeds_capacity` |
| `party_size` below 1, or not an integer | 422 `validation_failed` |
| `starts_at_local` is a local time that does not exist (see §9) | 422 `invalid_local_time` |
| Unknown restaurant, unknown table, or the table belongs to another restaurant | 404 `not_found` |

### `GET /reservations`

The caller's reservations, `starts_at` descending, confirmed and cancelled alike.
Return `200` with `{"reservations": [...]}`; each entry has the same shape as the
create response. An empty list is `{"reservations": []}`.

### `GET /reservations/{reference}`

One reservation. **404 if it is not the caller's** — do not leak the existence of other people's
bookings.

### `POST /reservations/{reference}/cancel`

```json
200
{ "reference": "K3P7QW", "status": "cancelled", ... }
```

Frees the table immediately: the next `GET /availability` must offer that slot again.

| Case | Response |
|---|---|
| Already cancelled | 200 with the current state — cancelling twice is not an error |
| Now is within `cancellation_cutoff_minutes` of `starts_at`, or later | 409 `cutoff_passed` |
| Not the caller's reservation | 404 `not_found` |

### `PATCH /reservations/{reference}`

Change the time, the table or the party size. Any subset of `table_id`, `starts_at_local`,
`party_size`. No idempotency key is required here.

Validation is identical to `POST /reservations`, and the same cutoff rule as cancel applies
(409 `cutoff_passed`), measured against the **current** start time. A cancelled reservation is
409 `reservation_cancelled`. A successful amendment releases the old slot and reserves the
new one together. A failed amendment leaves the original booking and its occupancy unchanged.

`reference` and `reservation_id` survive a change.

## 9. Time and DST

Local dates and times follow the restaurant's `timezone`, including daylight-saving transitions.

**Spring forward.** Local times in the skipped hour do not exist. They never appear in
availability, and booking one is 422 `invalid_local_time`.

**Fall back.** Local times in the repeated hour occur twice. **Always resolve to the first
occurrence — the one before the clocks change.** The slot appears once in availability, and the
second occurrence is not bookable.

`reservation_duration_minutes` is **absolute time**, not wall-clock. A 90-minute reservation
starting at 01:30 on a fall-back night ends 90 real minutes later, and its local `ends_at` will
read 02:00, not 03:00.

The transitions that must be handled:

| Zone | Spring forward | Fall back |
|---|---|---|
| `Europe/Berlin` | 2026-03-29, 02:00 → 03:00 | 2026-10-25, 03:00 → 02:00 |
| `America/New_York` | 2026-03-08, 02:00 → 03:00 | 2026-11-01, 02:00 → 01:00 |

Offsets must follow the IANA rules for the specified zone and date.

## 10. Export and import

The service must support `GET /_test/export` and `POST /_test/import`. Like reset, these
are unauthenticated test endpoints.
Exports may contain credentials and session tokens; handle them as private test artifacts.
Return 200 from export with a JSON object containing `track: "tablekeeper"`,
`format_version: 1` and `state` (an implementation-defined JSON object). The state format
is opaque to the caller and must be accepted unchanged by import.

Import takes that entire object and atomically replaces the service's state, returning
204. It must accept an unchanged export produced by this service. No dependency on the
source process, files, volume, port or network address is allowed. Import is replacement,
not merge; repeating it restores the exported state without duplicating anything. Invalid
JSON follows §5; missing fields, wrong track/version or an invalid state give 422
`validation_failed` without changing the destination. Test control calls have a 10-second
timeout. Export is an atomic, read-only snapshot; subsequent source writes do not change it.

Preserve accounts and hashed-password login, existing bearer tokens, fixture configuration,
reservations, references, all completed idempotent request bodies and original responses.
Identities, statuses and timestamps must not be regenerated. Failed request keys remain
reusable. Existing receipts, references, tokens and retries must remain valid after import;
replacing the state with a fresh fixture does not satisfy this requirement. Import removes
all previous destination data and credentials. Reset continues to clear all state, including
imported state. State need not survive an abrupt container restart.

## 11. Atomic reservation moves

A diner may change several bookings in one request.

`POST /reservation-moves` requires authentication and an idempotency key. Body:

```json
{"moves": [{"reference": "BOOK01", "table_id": "t_2"},
           {"reference": "BOOK02", "table_id": "t_1"}]}
```

`moves` contains 1..8 objects with distinct string references. Invalid shape or duplicate
references gives 422 `validation_failed`. Every booking must belong to the caller and the
same restaurant. Unknown/another owner's reference gives 404 `not_found`; different
restaurants give 422 `validation_failed`. No token gives 401.

Each item accepts the ordinary PATCH fields `table_id`, `starts_at_local`, `party_size`;
omitted fields retain their current values and unknown fields are ignored. The booking's
identity, owner and creation time never change. Cancelled bookings give 409
`reservation_cancelled`. Each booking's existing cutoff applies. Non-occupancy errors use
ordinary amendment codes and take precedence in input order, with cutoff errors preceding
other changes for that booking. An overlap among resulting bookings or with an unlisted
booking gives 409 `table_unavailable`. Unchanged listed bookings retain their occupancy.

Either every move commits or nothing changes: occupancy, reservation records and retry
keys. On success return 201 with `{"reservations": [...]}` in input order, including
unchanged items.
Replays return that original response with 200, even after amendments or cancellations.
No-op moves retain all existing values. Export/import preserves successful batch receipts
as well as the resulting bookings. No batch UI is required.


Applicable complete Stage 2 specification:
# Tablekeeper — Stage 2: online booking and combined tables

The stage-1 requirements continue to apply, with the additions below. Numbered section
references such as §5 and §7 refer to `stage-1.md`.

Diners can search, book and manage reservations in a browser. Restaurants can offer
approved pairs of tables for larger parties.

The following screens must be reachable by URL. Other screens must be reachable through
the UI. Server-side and client-side rendering are both permitted.

| Route | Screen |
|---|---|
| `/` | Search and availability grid |
| `/signup` | Signup |
| `/login` | Login |
| `/lookup` | Look up a reservation by reference |

A screen route returns HTML; §3.4's `application/json` convention is about the API, and does
not govern the routes in the table above.

## Competing clients and uncertain outcomes

The UI must handle responses arriving out of order and connections failing after submission.

- If search A starts before search B but finishes after it, the grid, table labels and
  booking form must describe B. A late response must not restore A's results.
- If another client takes a table after the form opens, a `409 table_unavailable` response
  shows `booking-error` and refreshes availability. Preserve the selected form and its
  inputs so the diner can change their choice. Do not show a confirmation for that attempt.
- If a booking response is lost, including after the booking commits, show nonempty
  `booking-uncertain` text, without `booking-error` or a new confirmation. The unchanged
  form must retry with the same idempotency key and body. A successful retry removes the
  uncertainty/error elements and shows the original reference. A confirmed rejection
  uses `booking-error`.

These rules apply to combination bookings too. No background polling, live updates,
cross-tab storage synchronization, or recovery across a page reload is required. The server
remains authoritative; the browser must not manufacture a successful result from cached data.

The UI must expose the `data-testid` attributes listed below for integration testing.
Additional elements are permitted, and the visual implementation is the team's choice subject
to the product-quality requirements below.

## Product and visual direction

The browser experience must feel like a coherent, presentation-ready restaurant product, not a
test harness with controls attached. Aim for a warm, confident hospitality character. The search,
availability and booking flow should have an obvious visual hierarchy; a diner should be able to
scan dates, times, party size and table choices without having to interpret raw API data. Combined
tables should read as intentional seating options, not as concatenated technical identifiers.

Use a consistent visual system for typography, spacing, colour, controls and feedback. Primary
actions must be easy to identify. Available, unavailable, selected, loading, successful, refused
and uncertain states must be visually distinct as well as satisfying the behavioural requirements
below. Use human-readable restaurant and table labels prominently; expose technical identifiers
only where they help the user.

The required flows must remain clear and usable at a 375 CSS-pixel viewport and at conventional
desktop widths, without horizontal page scrolling. Inputs need visible labels, keyboard focus must
be apparent, and text and controls need sufficient contrast. Provide considered empty, loading and
error states, and keep navigation consistent across the required routes. A custom illustration,
brand asset or exact visual match to a reference is not required.

## Signup and login

| `data-testid` | Element |
|---|---|
| `signup-email`, `signup-password`, `signup-display-name` | Inputs |
| `signup-submit` | Button |
| `login-email`, `login-password`, `login-submit` | Inputs and button |
| `auth-error` | Error message. Present only when there is one |
| `current-user` | Visible on every screen when signed in. Text contains the display name |
| `logout-button` | Button |

## Search and availability grid — `/`

| `data-testid` | Element |
|---|---|
| `restaurant-select` | Selects a restaurant. Option values are restaurant ids |
| `date-input` | Date, value `YYYY-MM-DD` |
| `party-size-input` | Number |
| `search-button` | Runs the search |
| `availability-grid` | Container for the results |
| `slot-{table_id}-{HH:MM}` | One cell per table per slot, e.g. `slot-t_2-19:00` |
| `no-slots` | Shown instead of the grid when the day has no slots |

Each cell carries `data-available="true"` or `data-available="false"`. A cell is `true` exactly
when its `table_id` is in that slot's `available_table_ids` from `GET /availability` for the party
size that was searched, and `false` otherwise. Clicking an available cell
opens the booking form for that table and slot. Clicking an unavailable cell does nothing.
Booking requires a signed-in user: clicking an available cell while signed out shows `auth-error`
or navigates to `/login`, your choice.

## Booking form

| `data-testid` | Element |
|---|---|
| `booking-form` | Container |
| `booking-summary` | Text contains the table label and the local start time |
| `booking-party-size` | Number input, pre-filled from the search |
| `booking-submit` | Button |
| `booking-error` | Error message, when the booking fails |

Keep the booking form on screen after success. Submitting it again without changing a
field must return the same `confirmation-reference`, without `booking-error` or another
booking. Changing a field makes the next submission a new booking request. Retries follow §7.

## Confirmation

Shown after a successful booking.

| `data-testid` | Element |
|---|---|
| `confirmation` | Container |
| `confirmation-reference` | Text is exactly the reference, no surrounding words |
| `confirmation-details` | Text contains the restaurant name, table label and local start time |

## Lookup — `/lookup`

| `data-testid` | Element |
|---|---|
| `lookup-reference-input`, `lookup-submit` | Input and button |
| `reservation-detail` | Container, shown when found |
| `reservation-status` | Text is exactly `confirmed` or `cancelled` |
| `reservation-cancel-button` | Cancels. Absent once cancelled |
| `reservation-error` | Shown when not found, or when a cancel is refused |

## Existing clients after an upgrade

A stage-2 service must accept an export produced by the same team's stage-1 service. A
browser signed in before that export/import upgrade must remain signed in afterwards.
A retained booking reference still works through the lookup screen. A booking whose response
was lost before export remains retryable after import with the same body and key; the UI
must recover the original confirmation. These requirements apply when import completes
between browser requests; migration during an in-flight request is not required. No page
reload or new screen is required. The form and pending retry identity must survive the upgrade.

## Combined tables

A party may book two tables that the restaurant has declared combinable. The booking
occupies both tables for its full duration.
Existing single-table request formats remain supported.

## Model

The restaurant fixture gains one field:

```json
{
  "id": "r_anker",
  "combinable": [ ["t_1", "t_2"], ["t_2", "t_3"] ],
  ...
}
```

Each entry is an unordered pair of table ids in that restaurant. **Pairs only** — never three or
more. A pair not listed cannot be combined, whatever the table sizes are. Combining is not
transitive: `[t_1,t_2]` and `[t_2,t_3]` do not make `{t_1,t_3}` bookable.

A combination's capacity is the sum of its tables' capacities.

Seeded `reservations` are `confirmed` unless they carry a `status` of `cancelled`, and may hold
either `table_id` or `table_ids`.

## API

### `GET /availability`

Slots gain `available_options`. `available_table_ids` stays exactly as it was — single tables
only.

```json
{
  "slots": [
    {
      "starts_at_local": "2026-09-24T19:00",
      "starts_at": "2026-09-24T19:00:00+02:00",
      "available_table_ids": ["t_3"],
      "available_options": [
        { "table_ids": ["t_3"], "capacity": 4 },
        { "table_ids": ["t_1", "t_2"], "capacity": 6 }
      ]
    }
  ]
}
```

`available_options` lists every single table and every declared pair with
`capacity >= party_size` and no overlapping confirmed reservation on any member. Singles first in
fixture order, then pairs in `combinable` order. `table_ids` within a pair is in `combinable`
order.

### `POST /reservations`

The body takes `table_ids` instead of `table_id`:

```json
{ "restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"],
  "starts_at_local": "2026-09-24T19:00", "party_size": 6 }
```

`table_id` is still accepted and means a set of one. Sending both is 422 `validation_failed`.

Responses always carry `table_ids`. They also carry `table_id` **when the set has exactly one
member**, and omit it otherwise.

| Case | Response |
|---|---|
| The pair is not in `combinable` | 422 `combination_not_allowed` |
| More than two tables | 422 `combination_not_allowed` |
| Any table in the set is taken for an overlapping interval | 409 `table_unavailable` |
| `party_size` exceeds the combination's summed capacity | 422 `party_exceeds_capacity` |
| Duplicate table id in the set | 422 `validation_failed` |

`PATCH /reservations/{reference}` accepts `table_ids` under the same rules. Cancelling frees every
table in the set.

## UI

The availability grid gains combination cells, shown when a declared pair is available for the
searched party size:

| `data-testid` | Element |
|---|---|
| `slot-{t_a}+{t_b}-{HH:MM}` | A combination cell, e.g. `slot-t_1+t_2-19:00`. Ids in `combinable` order. Carries `data-available` like a single cell |
| `confirmation-tables` | Text contains every table label in the reservation |
| `reservation-tables` | On the lookup screen. Same |

`booking-summary` must name every table in the selection. A single-table booking's cell testid,
confirmation and lookup are unchanged.

Atomic reservation moves from stage 1 also accept `table_ids` per move. No table may
belong to overlapping resulting bookings. The existing browser recovery and original-receipt
requirements also apply to combined-table bookings.

## Concurrent bookings and amendments

Concurrent requests must produce the same results as executing them one at a time in some
order, and the requirements above hold at every read.


Applicable complete Stage 3 specification:
# Tablekeeper — Stage 3: booking policies, history and recurring reservations

The requirements from stages 1 and 2 continue to apply, with the additions below.
Numbered section references such as §5 and §7 refer to `stage-1.md`.

Restaurants can publish dated booking policies. Diners can see why a table is unavailable,
view their reservation history and arrange recurring bookings.

## Availability explanations

Whether a table is available for a slot is decided by two rules, each independent of the other:

| Rule | Holds when |
|---|---|
| `capacity` | `party_size` is at most the table's `capacity` |
| `no_overlap` | no confirmed reservation on that table overlaps the slot's interval |

A table is available exactly when both hold. `available_table_ids` is unchanged in meaning.

```http
GET /availability?restaurant_id=r_anker&date=2026-09-24&party_size=4&explain=true
```

`explain` is optional. Its only accepted value is `true`; any other value, including `false`,
`1` and the empty string, is 422 `validation_failed`. **Without it the response keeps stage
1's shape** — no explanation fields appear. Published policies can change the slot values.

With it, every slot carries one further field:

```json
{ "starts_at_local": "2026-09-24T18:00",
  "starts_at": "2026-09-24T18:00:00+02:00",
  "available_table_ids": ["t_2"],
  "explain": [
    { "table_id": "t_1", "policy_version": 0, "available": false,
      "rules": [ { "rule": "capacity", "holds": false },
                 { "rule": "no_overlap", "holds": true } ] },
    { "table_id": "t_2", "policy_version": 0, "available": true,
      "rules": [ { "rule": "capacity", "holds": true },
                 { "rule": "no_overlap", "holds": true } ] }
  ] }
```

1. **Every table of the restaurant appears exactly once**, available or not, in fixture order —
   the same order `available_table_ids` uses.
2. **Both rules are reported for every table**, in the order above. A rule that holds is
   reported holding; a table excluded by both reports both false. No rule may be omitted.
3. **`available` is true exactly when both rules hold**, and the `table_id`s whose `available`
   is true are exactly `available_table_ids`, in the same order.
4. A closed day still returns `"slots": []`, and a slot with no available table still appears —
   now with a full `explain` for every table.

## Reservation history

```http
GET /reservations/{reference}/history
```

The reservation's own record, oldest first. Only its owner may read it; anyone else, signed in
or not, gets the same 404 `not_found` that §8 gives for a reservation that is not theirs. A
cancelled reservation still has its history.

The example below shows the event fields; every entry also carries `revision` and
`accepted_terms` as specified under “Policies and accepted terms”.

```json
{ "reference": "ABC12345",
  "entries": [
    { "seq": 1, "at": "2026-09-17T12:00:00+02:00", "event": "created",
      "changes": [ { "field": "table_id", "from": null, "to": "t_2" },
                   { "field": "starts_at_local", "from": null, "to": "2026-09-24T19:00" },
                   { "field": "party_size", "from": null, "to": 4 } ] },
    { "seq": 2, "at": "2026-09-17T12:05:00+02:00", "event": "changed",
      "changes": [ { "field": "table_id", "from": "t_2", "to": "t_3" } ] },
    { "seq": 3, "at": "2026-09-17T12:09:00+02:00", "event": "cancelled", "changes": [] } ]
}
```

1. **`seq` starts at 1 and increases by exactly 1**, so the order is total even when two writes
   land in the same second. Entries are returned in `seq` order, which is also `at` order.
2. **`created` names all three fields**, each with `"from": null`.
3. **`changed` names only the fields that actually changed**, in the order `table_id`,
   `starts_at_local`, `party_size`. A `PATCH` that sets a field to the value it already has
   changed nothing: it still succeeds, and it records **no entry at all**.
4. **`cancelled` carries an empty `changes`**, and nothing follows it.
5. Replaying an idempotent `POST /reservations` records nothing — a replay returns the original
   response and does not re-run the operation (§7).

## Existing screens

No new screens are required for explanations or history. The availability grid continues
to follow the stage-2 rules.

## Policies and accepted terms

Restaurants may now declare `manager_user_ids` in their reset fixture (default `[]`). Only
these users may publish policies. Unknown restaurant is 404;
an authenticated non-manager is 403 `forbidden`; no token is 401. This extends stage 1's
minimal permissions; managers do not gain access to other diners' private lookup/history.

`POST /restaurants/{id}/policies` requires an idempotency key, with stage 1's replay rules.
It accepts a **complete policy**, not a patch:

```json
{
  "effective_from": "2026-09-28",
  "slot_minutes": 30,
  "reservation_duration_minutes": 120,
  "cancellation_cutoff_minutes": 60,
  "opening_hours": [{"weekday": "mon", "opens": "18:00", "closes": "23:00"}],
  "capacities": {"t_1": 2, "t_2": 4, "t_3": 6}
}
```

Returns 201 with the supplied policy plus `policy_version`, an integer starting at 1 and
increasing by one per restaurant. Failed writes and replays allocate no version. Policy 0
is the original fixture's rules and applies before any published policy. Policies are
immutable. Publication order may differ from effective-date order. For a booking's **local
start date**, choose the greatest `effective_from` not later than that date; ties choose
the greatest `policy_version`. A new same-date policy supersedes the old one for future
decisions, without changing any accepted reservation. Effective dates may be in the past;
publication never retroactively edits a booking.

All fields above are required. `effective_from` is an actual `YYYY-MM-DD` date; grid and
duration are integers 1..1440; cutoff is an integer 0..10080; booleans are not integers.
Opening hours follow stage 1 and contain no duplicate weekdays. `capacities` names **exactly**
the restaurant's table ids with integer capacities 1..100. Invalid policy is 422
`validation_failed`, with no version or state change. Table ids, labels, timezone and
declared combinations cannot be changed by a policy. Unknown fields are ignored.

`GET /restaurants/{id}/policies` is public and returns `{"policies": [...]}` in publication
order, omitting policy 0. The ordinary restaurant detail still returns its original fixture
configuration. Availability and booking decisions use the selected policy, not that detail.
With `explain=true`, each table explanation additionally identifies its `policy_version`.

Every reservation response gains `revision` (1 at creation) and `accepted_terms`:

```json
{"policy_version": 0, "slot_minutes": 30,
 "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 120,
 "opening_hours": [{"weekday": "mon", "opens": "18:00", "closes": "23:00"}],
 "capacities": {"t_1": 2, "t_2": 4, "t_3": 6}}
```

These are a snapshot of the entire selected policy, excluding `effective_from`. Seeded
bookings start at revision 1 under policy 0. Responses to old idempotency keys remain the
original response, including the original revision and terms.

- A policy publication does not change existing bookings, their end times, or their history.
- Cancel checks the accepted cutoff, against the current start.
- A real diner amendment (time, tables or party size) checks the old accepted cutoff first,
  then validates **all** resulting fields against the policy applicable to the resulting start
  date. It atomically replaces accepted terms and end time and increments revision once.
- A no-op amendment retains terms, end time and revision and records no history. It still
  requires a confirmed, editable booking.
- Failed amendments change nothing. Cancel increments revision once; repeated cancel does not.
- `PATCH` optionally accepts `expected_revision`. A positive integer differing from the current
  revision gives 409 `stale_revision` before cutoff/validation; invalid type/range gives 422.
  Omission retains stage 1 semantics. Two concurrent amendments using one revision: at most one
  real change succeeds. Unrelated unknown fields remain ignored.

Each history entry additionally carries the reservation's resulting `revision` and complete
`accepted_terms`. Old entries never acquire newer terms. `GET /reservations/{reference}/decision`
returns `{"reference": "...", "revision": 1, "accepted_terms": {...}}` for the current booking,
including after cancellation, with history's owner-only 404 rule. History and decision return
404 even without authentication, resolving the exception to stage 1's general 401 rule.

## Recurring reservations

`POST /series` adopts an existing reservation as occurrence zero of a recurring agreement.
An idempotency key is required. Body:

```json
{"anchor_reference": "ABC12345", "count": 8, "interval_weeks": 1}
```

The anchor must belong to the caller, be confirmed and satisfy its accepted cancellation
cutoff. Unknown or another owner's anchor gives 404 `not_found`; cancelled gives 409
`reservation_cancelled`; already adopted gives 409 `already_in_series`. `count` is an integer
2..12 including the anchor; `interval_weeks` is an integer 1..4. Invalid values, including
booleans, give 422 `validation_failed`. No token gives 401.

Occurrence zero is the anchor itself: its reference, identity, revision, terms, history,
timestamps and original idempotent response remain unchanged. Occurrence i starts on the
anchor's local calendar date plus i × interval_weeks × 7 days, at the same local clock time.
Each generated occurrence independently selects its date's policy, including duration and
capacity, and obeys ordinary opening, DST and occupancy rules. A nonexistent local time
rejects the entire adoption with `invalid_local_time`; repeated times use stage 1's first
occurrence rule. Generated occurrences use the anchor's party size and table selection.
No partial series, reservations, histories, counters or idempotency claim survive failure.
The first failing occurrence in index order determines the ordinary booking error.

Return 201:

```json
{"series_id": "opaque", "revision": 1, "interval_weeks": 1,
 "occurrences": [{"index": 0, "reference": "ABC12345", "exception": false,
                  "reservation": {"...": "ordinary reservation response"}}]}
```

The array includes all count occurrences in index order. Each has a distinct ordinary
reservation reference; references and indices never change when dates or tables change.
Occurrences appear in ordinary reservation lists, occupy tables, and have ordinary histories.
`GET /series/{series_id}` returns this shape with current reservation states. Only the owner
may read it: another user or no token gives 404 `not_found`.

A real individual PATCH permanently marks that occurrence as `exception: true` and increments
the series revision once; a no-op or failure changes neither. Cancellation increments the
series revision once, retaining the cancelled occurrence, but does not mark it as an
exception; repeated cancel does nothing.
Cancelling the anchor does not cancel its siblings. Ordinary cutoff and revision checks still
apply. Adoption increments the restaurant revision once for the whole operation. Replays
return the original series response, even after later changes, and change no counter.
Series creation adds one idempotent write path. Unknown fields are ignored.

A stage-3 service must accept exports produced by the same team's stage-1 or stage-2
service. Adoption must work on reservations imported this way. Existing confirmation links,
sessions and original booking retries remain valid.

## Combined-table history

Stage 3's accepted terms apply to combinations too; capacity is the sum of the **selected
policy's** capacities. In history, retain stage-3 fields for single-to-single operations.
For a creation of a pair, replace the `table_id` change by `table_ids` (from null to the pair).
For a change involving a pair, use `table_ids` (complete before/after lists) instead of
`table_id`. Table-set order is the declared combination order. A reversed input pair names
the same set and is not an amendment on its own. Policy selection, revision and replay rules
are unchanged.

## Collective moves under policies and agreements

Each real change in `POST /reservation-moves` uses individual PATCH semantics: check the
old accepted cutoff, then adopt the resulting date's policy. Per-move `expected_revision`
is optional and follows PATCH validation and stale-revision rules. A no-op retains its
terms and history. All resulting bookings must satisfy amendment and occupancy rules;
failure leaves every booking unchanged. Every changed booking gains one revision and
changed history entry; the restaurant revision increases once for the whole batch.
Each affected series revision increases once,
and each changed series occurrence becomes a permanent diner exception. A
failed batch or replay changes no revisions, histories or exception flags.


Supplementary product acceptance brief (complete specifications prevail):
# Tablekeeper acceptance brief — task-specific, never a seat mandate

Source: official kickoff `803560d2a678ace1414465c098eb0ab5380ffade`,
`docs/participant-guide.md` and all four `tablekeeper/spec/stage-N.md` files.
This is an operator-authored acceptance brief, not implementation or scored evidence.
The complete official specifications prevail over this summary. Seats must derive
their own exhaustive requirement ledger and code in the submitted Band room.

## Target and evidence standard

The target remains four consecutive, fully implemented stages, a polished product,
and a reproducible autonomous factory. The public claim threshold is not our
quality target. Public test percentages or a passing public suite do not establish
hidden-test coverage, a judging score, or a prize.

Every claimed behavior needs a requirement reference, candidate full commit,
independent executable probe or observed UI flow, command, result and artifact path.
Record `unverified` when any link is missing. Never manufacture a rejection.
Tests belong outside graded stage folders unless genuinely needed by the service.
Do not modify the official checker, omit suites, or convert skipped checks to passes.

## Stage 1 — transaction and state foundations

| Requirement family | Independent acceptance evidence beyond a happy path |
|---|---|
| Runtime | Fresh single-image build; nondefault PORT; 0.0.0.0 listener; health within 60 s; 2 CPU/2 GiB; no runtime internet or separate database service. |
| Authentication | Hashed passwords; multiple active tokens; public browsing without token; owner-only reference lookup cannot reveal another account's booking. |
| Validation | Distinguish wrong JSON types from invalid values; reject boolean party sizes; strictly parse decimal query integers and bare local timestamps; ignore unknown fields. |
| Retry semantics | Same user+method+path+parsed JSON replays original response with 200; exactly one concurrent first request returns 201; same key on another path remains independent; different body conflicts before resource validation; failed keys remain reusable. |
| Occupancy | Half-open boundaries; 50 competing requests; no double booking or partial mutation; capacity and grid constraints; closed-day and empty-slot ordering. |
| Time | IANA rules, nonexistent local times, first occurrence in a repeated hour, absolute duration across transitions; do not reject dates merely because they are in the past. |
| Amend/cancel | Cutoff measured against current start; failed amendment leaves old occupancy intact; repeated cancel is stable; reference and identity survive edits. |
| Batch moves | 1..8 distinct references; same owner/restaurant; validate non-occupancy errors in input order before overlap; swap several occupied tables atomically; failed batch leaves receipts and every record unchanged. |
| Export/import | Atomic replacement across independent processes; preserve hashes, tokens, identities, timestamps, successful original receipts and cancelled records; invalid import is all-or-nothing; reset removes all imported state. |

Do not add the later browser or policy/series surfaces to this folder. Copy the
accepted stage forward; never copy a final answer backwards.

## Stage 2 — product experience and uncertain outcomes

Product direction: a warm, calm hospitality product. Use a consistent type scale,
warm neutral surfaces, a restrained accent, clear labels, and human table names.
This is a direction, not a reference design to reproduce. Do not invent reviews,
ratings, restaurant photos, usage counts, or claims about real establishments.
All assets/fonts/scripts must be packaged for offline runtime.

| Required flow | Evidence to capture |
|---|---|
| Browse before login | `/` is useful without authentication; restaurant, date, party size and table choices are legible; booking routes to authentication. |
| Authentication routes | `/signup`, `/login`, `/lookup` load directly; visible labels and focus; signed-in identity visible on all screens; logout state works. |
| Search race | Delay A, complete B, then release A: grid, labels and form remain B, not stale A. |
| Booking conflict | Another client takes the selected option: show refusal, refresh availability, retain form inputs, and never show a false confirmation. |
| Lost response | Commit then drop response: show uncertainty, not refusal/success; retry identical body/key and recover the original reference; another submit after success creates no duplicate. |
| Changed form | A real field change creates a new request identity; an unchanged form retains the same retry identity. |
| Combined seating | Only declared pairs, never transitive combinations; canonical declared order; atomically occupy/release both tables; show both human labels. |
| Upgrade in place | Import a stage-1 export between browser requests: login token, open form, retained reference and uncertain retry still work without a reload. |
| Responsive/accessibility | Real screenshots and keyboard flows at 375 CSS px and desktop; no horizontal page scroll; distinct loading, empty, available, unavailable, selected, success, refusal and uncertainty states. |

Required test IDs are a contract, not a substitute for product-quality review.
Verify text-only constraints (reference and reservation status) precisely.
The Experience Engineer must contribute substantive UI/recovery code and evidence,
not only cosmetic changes after another seat built the entire app.

## Stage 3 — immutable terms, history and recurring agreements

| Risk | Required independent probe |
|---|---|
| Explanation truth | Both capacity and overlap rules reported for each table in fixture order; validate explain=true only; no extra explanation fields when omitted. |
| Policy ordering | Publish effective dates out of order and ties on the same date; select by local booking date then version; preserve existing bookings and immutable historic terms. |
| Manager boundary | Only fixture managers publish; managers do not gain private diner lookup/history access; ordinary restaurant detail remains original fixture configuration. |
| Revision/history | Contiguous seq; exact changed fields/order; no-op/replay/failure creates no event; accepted terms are snapshotted on each historical event; optimistic revision conflicts precede cutoff validation. |
| Receipt longevity | Replay an old create/policy receipt after amendments and cancellation and after import: original body, revision and terms survive. |
| Series adoption | Anchor remains identical; each future occurrence uses its own local date's policy and DST resolution; any failed occurrence rolls back every reservation/history/counter/key. |
| Series exceptions | Real individual change permanently marks exception; cancellation retains occurrence but does not create exception; anchor cancellation does not cancel siblings. |
| Combined history | Pair sets canonicalized; reverse input order alone is a no-op; single/pair transitions use the specified field representation. |
| Batch and series counters | Several changed members in one transaction increment each affected series once and restaurant once; failed batches/replays increment nothing. |
| Cross-version import | Independently export from both earlier stages and adopt imported reservations; preserve sessions and original receipts. |

## Stage 4 — deterministic planning and atomic application

1. Exercise the full supported bound: six tables, four declared pairs, six considered
   bookings, with fixed bookings and existing closures present.
2. Build an independent small exhaustive oracle from the written planning objective:
   minimize changed booking sets, then total unused seats, then the rank vector in
   reference order. Do not use the production solver as its own oracle.
3. Use each booking's accepted capacities, not the latest policy's capacities.
   Preserve its identity, time, party size, owner and accepted terms.
4. Preview must not reserve occupancy, publish closure, increment revision or write
   booking history. Infeasible preview must leave all observable state unchanged.
5. Any intervening revision in that restaurant invalidates a plan; unrelated
   restaurants do not. Replaying a successful apply returns its original receipt;
   a different key for an already applied plan has its specified error.
6. Concurrent applies cannot partially move bookings. Moved records get one revision
   and reassigned event, unmoved records none; restaurant changes once per plan.
7. Bulk series amendments exclude cancelled/exception members and use original
   scheduled dates. Validate the series revision before member cutoff/validation;
   apply occupancy across changed and unchanged members together.
8. Empty eligible/no-op series changes succeed without incrementing revisions.
   A seating repair preserves exception flags and increments each affected series once.
9. Import populated states from every prior stage, including changed/cancelled series
   members, and repeat these operations without losing tokens, receipts or history.

## App-score interaction ownership

The stage-3 and stage-4 specs say no new screens are required. The following are
our product-quality targets, not organizer eligibility requirements. Implement
them only in their applicable stage after core correctness, without changing the
specified API or delaying required regression/upgrade coverage. Experience owns
substantive UI/integration work alongside Systems rather than only a final skin.

- In stage 3, make the existing diner's own confirmation/lookup flow explain
  accepted terms and historical changes clearly. Offer recurring-booking creation
  and a legible occurrence list with cancelled and exception states. Never expose
  another diner's private lookup/history to a manager.
- In stage 4, provide a manager-authorized closure preview/apply workflow showing
  proposed changes separately from committed changes. A stale or infeasible plan
  must remain visibly unapplied; never display optimistic success before evidence.
  Keep diners' lookup/confirmation synchronized with actual applied assignments.
- Make series amendment results distinguish changed, unchanged, cancelled and
  exception occurrences. Preserve original references in the view; show failures
  without implying that a partial operation committed.
- Use actual API responses and declared capabilities only. No mocked manager
  access, fake history, fabricated metrics, or later-stage controls in an earlier
  folder. Capture the real authorized and refused flows in the independent review.

## Promotion and presentation

- Freeze each accepted stage at its full revision before the next copy. Keep every
  applicable public check green as the working target, plus independent spec probes.
- Every stage must claim its own number in isolated mode; the next-suite probe must
  not establish a later stage in an earlier folder. Never intentionally break a
  requirement merely to fail an overshoot probe.
- Use clean clones, no nested Git repositories, submodules, escaping symlinks or
  host-specific runtime dependencies. Preserve failed outputs in unique directories.
- Capture real Band handoffs, a real independent verdict, actual product interactions,
  upgrade/retry recovery and final stage results. Label rehearsal separately.
- Do not publish exported fixture state with tokens/password hashes as a demo asset.
  Inspect the genuine full room export for secrets before public release; follow the
  official rotate-and-redact exception if one is found, never invent room events.
- Include measured elapsed time and catalog-estimated cost only with provenance;
  distinguish estimates from billed spend. Unknown is preferable to an invented value.


Adopted timestamp representation decision:
# Timestamp representation decision — TK-20261004 Stage 1

The published requirements conflict for historical IANA offsets with seconds: Stage1 §3.4 requires RFC3339 numeric offsets (hours/minutes), while §9 requires accurate IANA resolution and offsets. No human steering is permitted. This decision preserves both the original restaurant wall-clock fields and the exact resolved instant; it does not claim that an hours/minutes-only wire offset literally equals a historical seconds offset.

Decision: resolve starts and absolute duration using the exact IANA offset/fold. Keep starts_at_local unchanged. For ordinary minute-aligned IANA offsets, retain the existing restaurant-local RFC3339 timestamp. For a historical subminute offset, serialize the same exact instant using a deterministic nearest minute-aligned fixed offset and an adjusted timestamp clock. Select a representable local calendar result at the supported date boundaries; ties choose the lower numerical offset. Do not round the instant, truncate seconds, restrict the published date range, add zone/date-specific branches, or alter a successful saved receipt on replay. Use the same serialization for availability and new reservation timestamps; verify export/import and original-receipt stability.

The two historical format obligations must be assessed under this recorded interpretation, with independent checks of RFC3339 syntax, exact absolute instant and retained original wall time. Preserve the previous failed observations. A new production revision and independently executed evidence are required; no failed result is converted to a pass in place. All other requirements remain unchanged. The verifier may reject an implementation that violates this interpretation or any remaining requirement.

Known interpretation risk: the literal historic wire offset is minute-aligned rather than the exact IANA subminute offset. The exact IANA resolution is preserved by the represented instant and original local field. Final acceptance must state this exception/interpretation explicitly and must not claim simultaneous literal compliance with incompatible offset grammars. Genuine final room export, operator documents, publication and submission remain operator-controlled.


Adopted original receipt shape decision:
# Original successful receipt shape across upgrades

The explicit original-response rules in Stage1 §7 and §10, and Stage2 existing-client upgrade requirements, govern successful historical replays. A replay returns the exact JSON body issued when the request originally succeeded, with the specified replay HTTP status200. Introducing new response fields in a later stage does not enrich or rewrite that old body. Newly executed writes and current-state lookup/list responses use the current stage's representation. Thus current Stage2 singleton responses carry table_ids and table_id, while a genuine Stage1 original receipt can retain only its original table_id field. The browser must recover the real server-issued original reference and support that legal older shape. The same rule extends to later introduced terms, revisions and histories: successful original receipts retain their original schema and values.

Request identity also remains original. A field ignored by the source stage may become recognized later; import must validate genuine old successful snapshots using their original meaning, preserve the complete original parsed body/key/method/path, and not rerun current endpoint validation as if the old operation were a new write. New requests obey current rules. Failures retain reusable keys.

For independent Stage1-to-Stage2 browser migration, Stage1 has no required HTML application. A valid real-browser probe may serve Stage2's unmodified packaged assets while transparently forwarding its old-compatible API requests to a genuine separately built accepted Stage1 service. That service must actually issue the token and successful booking, including a committed request whose browser response is dropped. Transfer its unchanged in-memory HTTP export to the current Stage2 service between requests, then switch API routing without reloading, authenticating anew, editing the form or regenerating the body/key. The unchanged browser retry must obtain the original real receipt. A retained reference must also work through lookup. The proxy only transports real requests/responses; it does not manufacture state or evidence, and does not claim a Stage1 UI existed. Independent verifier code must implement its own probe protocol rather than copying builder tests.

This records compatibility precedence from the complete supplied specifications. Historical timestamp representation remains governed by the separately recorded decision and its disclosed legacy-string exception. No human approval or new specification field is introduced.


Adopted visible numeric control decision:
# Exact numeric controls interpretation

Recorded by Foundry Coordinator on 2026-10-04 for Stage 2 and inherited stages.

Stage 2’s “Search and availability grid — /” table calls party-size-input a "Number" and its “Booking form” table calls booking-party-size a "Number input, pre-filled from the search". Neither table prescribes an HTML type attribute. Stage 1 section 7.3 accepts integral party_size values at least one, with table capacity as the applicable upper bound; the base fixture specification does not impose a universal numeric maximum.

The coordinator adopts an exact semantic numeric control: the visible editable field retains the complete decimal integer, has a visible label and spinbutton semantics, a numeric input mode, visible increment/decrement controls, and exact keyboard stepping with minimum one. Text storage is an implementation detail used to preserve integers beyond native browser floating-point range. The required test IDs remain on the actual editable field. There is no substitute hidden value or mocked DOM getter. The control must remain usable by keyboard and on a 375px viewport.

Requests still transmit party_size as an integer JSON token and a plain decimal query value, never a JSON string or a rounded/exponent-form substitute. Response integer values and combined capacities must display exactly. Validation remains authoritative on the server. Response syntax validation must reject malformed JSON before any lossless integer representation is applied.

This interpretation is derived from the published functional wording; it does not assert an unstated native HTML input type obligation. Independent verification must assess the real control, exact visible/input/query/body/retry values, labels, keyboard and mobile behavior against the complete specification. This decision is not a verifier acceptance. Preserve candidate-1 and builder failure evidence and report any residual judging ambiguity honestly.


Adopted JSON exact mathematical number decision:
# JSON numeric values and historical receipt compatibility

Adopted by Foundry Coordinator on 2026-10-04 after complete Stage 1 source review and both builders' independent source assessments. This governs Stage 1 and inherited stages; independent implementation acceptance remains pending.

Stage 1 §3.4 defines JSON bodies and says unknown fields are ignored, never an error. Section 5 distinguishes wrong JSON types (400) from correct-type invalid values (422), explicitly prioritizes party-size validation, and imposes plain-digit spelling specifically on integer query parameters. Section 8 requires an integer party size at least one. Section 7 compares the same JSON value after parsing, with object order and whitespace irrelevant. The published text does not prescribe a body integer-token grammar or Python numeric classes.

We adopt value-based body numbers: a finite JSON number whose exact value is integral satisfies a body integer field, subject to its range and endpoint rules. Thus 1, 1.0 and 1e0 have the same numeric meaning. Body field checks must use exact value, without float rounding, truncation or a language-derived upper bound. Query integers still require plain decimal digits; exponent, decimal-point and signed query spellings retain 422. Boolean, string, null, array and object remain distinct JSON types.

Base fixture grid/duration/capacity are interpreted as positive whole counts, and cutoff as a nonnegative whole count. A genuine finite fractional number has the correct numeric JSON type but an invalid whole-count value: 422 validation_failed. Other wrong types retain 400, except the explicit party-size override assigns 422. Zero remains valid only where the field permits it. A missing required field remains 422. This resolves the fourteen candidate-5 source questions prospectively; their original observed reports and provisional expectations remain unchanged. Magnitude does not change type.

A valid finite JSON number in an ignored field must not make a request malformed. Literal NaN/Infinity/-Infinity and malformed JSON/encoding remain 400. Newly executed request-body equality compares exact numeric value recursively, so equal-valued numeric spellings and zero signs are equivalent; booleans never equal numbers, arrays retain order, and objects retain the same complete key/value mapping. Ignored fields still participate in full body identity. Used-key differences must resolve before endpoint/current-resource validation. Numeric wire values stay JSON numbers throughout decode, successful receipts, state serialization and import; no string substitution or precision loss is authorized.

Genuine old services already emitted successful receipts after rounding some decimal/exponent request numbers into finite binary floats. Their exports cannot reconstruct lost original lexemes or precision. Original successful retries must remain valid, and original public response JSON values/strings must remain unchanged. Persist a private receipt-scoped source numeric profile for genuinely imported old receipts. Only that historical comparison projects incoming decimal/exponent-token values through the original decoder's meaning; integer-token values remain exact, booleans remain separate and observed old numeric cross-type equality is retained. Newly executed receipts use exact semantics. Mixed profiles survive export/import to another independent process. Never infer all receipts' semantics from the current stage or silently rewrite a stored original response. A legacy overflow projection cannot equal any legitimately saved infinite receipt; a different valid body receives 409.

This compatibility rule preserves historical parsed meaning; it does not authorize rounding new writes. Both builders supplied genuine-source evidence from revision 49287b4a5a1481f995c470ccae31776f03d4b863, unchanged exports and existing candidate-5 destinations: original 9007199254740993.0 round-tripped as 9007199254740992.0, original retry and equal old aliases replayed, while distinct integer 9007199254740993 conflicted. The new codec must receive independently derived checks for these historical and current semantics, exact fractions/exponents, error precedence, malformed constants, rollback, mixed receipts and resource constraints. Builder design agreement is not a verifier verdict; all current acceptance remains withdrawn.


Source reconciliation reminders (do not replace the full specification):
Use the full actual Stage 3 spec, not earlier hypotheses: permissions come only from each restaurant fixture's manager_user_ids (default []), not signup roles. Manager status never grants another diner's lookup/history/decision. PATCH expected_revision is OPTIONAL; omission retains Stage 1 semantics, invalid present type/range is 422, mismatched positive value is stale_revision before cutoff/validation. /series adopts an existing anchor as occurrence zero; it does not create an independent new anchor. There is no bulk series-cancel endpoint in Stage 3. Real individual PATCH marks a permanent exception and increments series once; cancellation increments series once without exception, repeated cancellation does nothing. Series adoption and collective moves increment restaurant revision once for the whole operation; affected series once per batch. History entries include at/seq/event/changes plus resulting revision and full accepted_terms; snapshot terms on every historical event. Seeded bookings start revision 1 under policy 0. Policy ranges are explicitly bounded (grid/duration 1..1440, cutoff 0..10080, capacities 1..100), unlike unbounded original fixture counts. New policy capacity map names exactly existing table IDs; unknown fields ignored. Explanations absent when explain omitted, explain's only accepted query value is true. No new screens required by organizer; supplementary brief adds real accepted-term/history/series product quality only in Stage 3.

Workspace /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory
Result /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-result
Official harness Python /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/.venv/bin/python; harness cwd /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/kickoff. Final isolated checks always use new output directories under /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-checks. No Stage 3 copy or execution is authorized before renewed Stage 2 acceptance and its frozen manifest.

CURRENT ACCEPTANCE / RELEASE FACTS
Stage 2 accepted full revision 4dba10246b07b2dda19de260d529f9d94ba0a1ed; tree 422380c814043021c2df2daad8edbbb34d5b5887. Stage 1 accepted full revision 75005d57fe0904753eac4eab5bf4e4c9a78b6d1b remains immutable. Coordinator acceptance/freeze/audit commit a7ef75573233fbf4652b56d6609e14d82d21594c. Highest accepted consecutive stage 2. Stage 3 base-copy phase is authorized ONLY after all parts/END acknowledgement; integrity/product extension requires coordinator complete nine-file copy proof and explicit phase release. No Stage 4 assignment or implementation.

Full independent Stage 2 accepted verdict (sealed efd23ed509e039ca285012c0c1b23a952e8d92a0):
# Stage 2 candidate 2: accept

Exact full candidate **`4dba10246b07b2dda19de260d529f9d94ba0a1ed`**, Stage 2 tree **`422380c814043021c2df2daad8edbbb34d5b5887`**: **accept**. Highest consecutive independently accepted stage is **2**. This accepts the complete Stage 2 service and its applicable inherited Stage 1 behavior. Stage 1 remains immutable at `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b`, tree `75f6ece6952c570eedf8a548f4428a5b2c986128`, with independent acceptance `a22de6b769c1454c35650377da1251edc99de744`. No Stage 3 or Stage 4 implementation or acceptance follows from this review.

All thirteen parts and END of `TK-20261004-S2-independent-verifier-CANDIDATE-2` were acknowledged before execution; final inbound part 13 is `06bdfc87-d9d7-42b2-8a2c-dc977bb2fc3e`. [Intake](intake.json) preserves the package and release binding. Systems' substantive implementation is `f783598428a88d53490f68498063ed69e02201b3`; Interface's substantive implementation is `a040054f2a8d00c560bea7f02324d1443c5a3f14`. The Systems seal at the tested candidate and Interface seal `1e3af87d78c2d6c037650a9c134453012d4fb0c6` have the identical Stage 2 tree. The verifier wrote only independent evidence and changed no production file. This document does not embed its own later evidence-commit identifier; the final room report supplies that exact seal.

The final [coverage matrix](coverage.csv) has **6,549 normative rows: 6,549 verified, zero failed, zero unverified**. Twenty-two nonnormative fixture-ID admission diagnostics are separate; all chosen fixtures were admitted, and their 308 conditional usability assertions passed. The 6,571 total records have unique identifiers and all fourteen required metadata fields, including source section, applicable stage, genuine implementation and verification owners, full candidate, actual command or browser interaction, evidence and verdict. [Metadata self-check](metadata-self-check.json) reports no empty required fields, missing owners or missing evidence files. [Bindings](coverage-bindings.json) identify the complete current observations; initial stopped or incorrect verifier attempts are excluded from final binding. This is an independently parameterized specification decomposition, not a hidden-test count or judging score.

## Exact current observations

Thirty-five complete independent protocol runs establish the behavior below. The completed HTTP-only families issue **8,455 requests and 9,398 assertions**, all passed. The eleven completed browser families have **1,134 assertions**, all passed, **294 direct API operations**, **1,603 browser-originated requests** and **156 genuine screenshots**. The four-origin browser upgrade protocol separately records 24 forwarded requests; forwarding transports browser traffic and is not added into a fabricated unique-request total. Health, source inspection, official-checker traffic and the three capture-invalidation checks are outside these protocol totals.

[Completed runs](completed-runs.json) records every exact executable command, observed counts and duration. [Run table](COMPLETED_RUNS.md) provides a compact per-family rendering. Current service requirement failures are zero. [Summary](summary.json), [review records](review-checks.json), [request timing audit](request-timing-audit.json) and [preserved verifier errors](RUNNER_ISSUES.md) keep normative verdicts, raw expectations and runner exceptions distinct.

| Unchanged official isolated scope | Collected | Passed | Failed | Errors / skipped / deselected / xfailed |
| --- | ---: | ---: | ---: | --- |
| Stage 1 regression against the Stage 2 service | 120 | 120 | 0 | 0 / 0 / 0 / 0 |
| Stage 2, comprising 8 API and 17 UI checks | 25 | 25 | 0 | 0 / 0 / 0 / 0 |
| Separate Stage 3 overshoot | 7 | 0 | 1 | 0 / 0 / 0 / 0 |

The overshoot's other six checks were not executed after unchanged `-x` stopped the probe. The harness report correctly claims stage 2 and has null overshoot. No suite, selection, checker, runtime or correct earlier behavior was modified to influence that result. Official green alone was not the acceptance criterion. Measured command time is **34.219868500 seconds**. Kickoff remains clean and unchanged at `803560d2a678ace1414465c098eb0ab5380ffade`.

Executed from the absolute kickoff directory:

```sh
/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/.venv/bin/python -m harness run --track tablekeeper --repo /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/independent-verifier-c2-1004060100-current --stage 2 --mode isolated --out /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-checks/independent-verifier-s2-c2-4dba1024-official-060319
```

The original unique output remains intact. [Official copy](official/report.json), the separate three counts files and [actual command](official-command.json) preserve the observed record.

## Integrity, exact values and concurrency

Fresh inherited runs cover authentication and hashed-password login, multiple tokens, public browsing, owner-only privacy, type/value/error precedence, opaque encoded IDs, calendar endpoints, both required DST zones, current-start cutoff, half-open occupancy, failed-key reuse, immutable original receipts, amendments, cancellation and atomic batches. Current Stage 2 cases exercise declared unordered pairs, canonical declaration order, exact summed capacities, nontransitivity, single/pair transitions, option ordering, cancelled seeds and member-intersection occupancy. Input-ordered non-occupancy errors precede overlap; rejected transactions preserve every booking, occupancy and successful receipt.

The new independent member/interval oracle uses seed **202610052** and saves 160 actual operations with current-state comparisons after each operation. It derives capacities, member sets and half-open intervals from fixture inputs, rather than production helpers. The separately reexecuted earlier independent occupancy/member oracles use seeds `20261004` and `20261005`. Small exhaustive serial-history checks and recorded request intervals validate concurrent pair amendments, singleton creates, cancellation, batch writes and reads. Fifty-client identical requests give exactly one 201 and 49 original 200 receipts; member competitors give exactly one 201 and 49 precise occupancy refusals. Four depth-20,000 single-receipt waves retain the same retry/occupancy guarantees. Deep pair receipts and ordinary pair/member races are separately exercised. Failed competing keys remain reusable.

Snapshot captures use three scheduled modes and four waves: 36 export/list/availability captures overlap atomic eight-member writes. Twelve unchanged actual raw exports each import into two independent destinations. A separately derived generation/prefix oracle checks complete booking and original-receipt relationships and absent future keys. Saved gate events establish client overlap; internal serializer timing is not observed. Source review confirms detached request/response/state snapshots and receipt preparation remain inside the RLock.

Strict UTF-8 grammar, malformed constants and containers, ignored finite overflow/underflow numbers, exact fractions, integral decimal/exponent aliases, boolean/number distinctions and complete parsed-body equality were freshly exercised. Query integers retain plain-digit spelling. Four 4,301-digit base fields and actual query/create/retry/import paths preserve exact numerical values without a language or browser upper bound. No numeric wire value was converted to a JSON string.

The corrected complete inherited decoder run issues **2,041 requests and 1,702 assertions**, all passed; it freshly covers all 1,558 prepared decoder obligations. Real arrays, objects and alternating wrappers at depths 1,100, 5,000, 10,000 and 20,000 succeed in request, receipt and raw state-transfer paths. The separate new combined-table suite performs genuine creates, pair/single swaps, no-op moves, ordered errors, mutation/replay, malformed refusal and successive raw replacements. Deep grammar is constructed from a valid shallow leaf and exact balanced wrappers; the client never decodes deep private exports or raises its recursion limit. The largest observed decoder request is **606,329 bytes**. The timing audit covers 5,931 saved timed operations, with maximum **3.231164002 seconds** and no applicable five-second ordinary or ten-second test-control violations. These are finite measured bounds.

## Genuine migration and browser recovery

Three unmodified historical sources genuinely issue sessions, references and successful create/move receipts: legacy Stage 1 `49287b4a5a1481f995c470ccae31776f03d4b863`, accepted exact Stage 1 `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b`, and legacy Stage 2 `4b92041057beb669d2e6c528e8268f4d0d1e6421`. Actual unchanged HTTP exports replace independent current processes. New exact writes join each genuine source state, followed by another unchanged independent replacement, source/destination mutation, replay, repeated replacement and reset. Password login, existing tokens, references, identities, timestamps, statuses and original public JSON survive; destination credentials are removed rather than merged.

Numeric profile and public-origin shape are independently tested. An accepted exact-profile Stage 1 receipt retains its original singleton response and historically ignored `table_ids` meaning. A genuinely old Stage 2 pair can retain a legacy numeric profile with its original combined response. Full original parsed bodies still govern retry identity. Altered used bodies conflict before current endpoint validation; new writes obey current seating rules. Missing, wrong or unsupported profiles reject atomically. Historical precision and lexemes are not reconstructed from fixtures or guessed from the current stage.

Four real browser upgrade flows cover both Stage 1 origins and old Stage 2 singleton/pair receipts. Unmodified packaged current assets forward compatible API traffic to each genuine old process, which actually logs in, creates a retained booking and move receipt, and commits another booking whose browser response is dropped. Its unchanged raw export imports between browser requests, then routing switches to current Stage 2. The same actual document, user, form, body and key recover the real original reference without reload, authentication or form regeneration. Retained lookup, old create/move receipts and new mixed exact receipts survive a second peer replacement. The proxy only transports real traffic and does not manufacture success or state.

## Product and actual interactions

Fresh browser interactions cover all mandatory routes and test IDs, signed-out browsing/refusal, signup/login/logout, visible signed-in identity, grid truth, human single/pair labels, unavailable-cell behavior, selected forms, exact reference/status text, repeated success and private lookup/cancellation. Search A is held until B and its form finish; releasing A cannot replace B's grid, labels or selection. A rival really commits after form opening; the resulting 409 shows refusal, refreshes availability, preserves form inputs and produces no false confirmation. Precommit loss, committed response loss and a deliberately malformed committed response show uncertainty; unchanged retries retain the original key/body and recover the real receipt. A genuine field edit changes identity.

Actual visible controls retain complete decimal values through 4,301 digits, labels, spinbutton semantics, numeric input mode, visible stepping buttons, exact arrow-key stepping and minimum one. Plain queries, integer JSON body tokens, prefilled values, unchanged retries, exact single/pair capacity labels and stored guest counts are independently observed. Five actual wire spellings of `9007199254740993` include `.0`, `e0`, `30e-1`, `9.007199254740993E+15` and `0.9007199254740993e16`; the service responses themselves establish those spellings. Valid responses are not rewritten to manufacture wire coverage. Quoted URI/Unicode identifiers remain opaque through real selection, path/query/body, confirmation, lookup and cancellation.

Real screenshots and measured widths cover 375 and conventional desktop CSS widths, consistent navigation, labelled controls, keyboard focus and distinct available, unavailable, selected, loading, empty, successful, refused and uncertain states. Warm cream surfaces, green primary actions, clay/amber feedback, human labels and a consistent type/spacing system form a coherent restaurant product. Actual Enter/Tab flows complete mobile booking, lost response and unchanged retry. Transparent ancestor backgrounds are accounted for in contrast calculations: ordinary text at least 4.5:1 and large text at least 3:1, disabled text excluded. This is a scoped product/contrast assessment, not full WCAG certification.

Explicit restaurant-zone end display is freshly checked under browser timezone Pacific/Honolulu, including year 0001 historical Berlin/Brussels/New York strings, both zones' spring/fall transitions and UTC year 9999. The late audit identified fresh browser DST paths that had only API evidence; a new isolated retained-image run executed all five cases, adding thirty verified obligations and five screenshots. No older builder result was substituted for those interactions.

## Clean build, packaged identity and cleanup

The entire nine-file current Docker context builds from a fresh clean detached exact clone at `/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/independent-verifier-c2-1004060100-current`. It and all three genuine-origin clones remain clean at their named revisions. No nested service repository, submodule, escaping symlink, uncommitted runtime dependency, host service interpreter dependency or manual setup is required. Available build cache was reused; no uncached-build claim is made.

Actual current image: **`sha256:051dcc415a2617758d709964473e2a12d4ca6e4653ca6194f648dd194808f2e0`**.

| Actual packaged module | SHA-256 |
| --- | --- |
| core.py | `c5ddc11f9a7c7b80d7d85dd5f9ba93ff4f236a6bf1ee4f4cfc901efae02c957e` |
| json_codec.py | `3bf4c5dd7ccee1c99127d735822331fedb1491af3568d3490a81a092bae49501` |
| server.py | `7ea970fec3b00387de8fb6ff8d448a42019424706407c0a7d41e2168c8376cc9` |

All current context and actual packaged web hashes are saved in [source proof](source-audit/source-proof.json), [preflight](runtime-01/preflight.json) and [summary](summary.json). Three current services and three genuine-source services have inspected **2 CPU, 2 GiB, no mounts**, on an inspected internal offline network. All-interface selected-port listening is established by cross-container health and traffic; host-published reachability is not claimed.

Default 8080 and override 18309 readiness upper bounds are **0.385168417 / 0.477205958 seconds** from separate docker-run calls, before later source inspection. Both satisfy the requested five-second startup check and published sixty-second limit. The additional browser-calendar service uses the already source-bound retained image, with a separately measured 3.248861000-second readiness upper bound and the same constraints; it does not claim another fresh build.

Every inspected service remains healthy and is not OOM-killed before removal. All **nine explicit own service/network cleanup commands exit zero**; separate `--rm` clients also exit successfully where recorded. The final verifier namespace is empty. Images and clean clones remain inspectable. Only own resources were removed. [Final runtime proof](final-runtime-proof.json), [calendar proof](calendar-browser-01/source-runtime-proof.json) and [final seal commands](final-seal-commands.json) preserve the empty production diff and cleanup evidence.

## Reproduction, preserved failures and provenance

Every actual build/Git/Docker/client/health/inspection/cleanup argv is in the per-run `commands.json`, [completed commands](completed-runs.json) and official record. Use the workspace Python, exact named independent protocol blobs, fresh seat-prefixed resources and new unique output folders; never overwrite the preserved outputs. Runtime orchestration is `../candidate2_runtime.py`; complete own invocation is `../candidate2_execute.py`. Runtime preflight and each assembly's `source-proof.json` preserve executed source hashes and sealed revisions. Protocols are independently authored, not copied from builders or official tests. The final [run table](COMPLETED_RUNS.md) links commands for each scope, including supplements after the complete cumulative run.

The review preserves **125 raw failed verifier expectations** in four initial attempts and one separate evidence-writer exception after passing checks. Those observations involved obsolete Stage 1 current-view assumptions or a Stage 1 fixture that had ignored `combinable`; they do not establish service failures. Separate complete corrected runs against unchanged production bind their entire scopes. A partial early stop never establishes downstream coverage. Host evidence-reader errors and the writer TypeError are disclosed in [RUNNER_ISSUES.md](RUNNER_ISSUES.md). Candidate 1 rejection, Stage 1 revoked acceptance and every earlier genuine service defect/repair remain unchanged historical evidence.

The six-file base-copy proof `ab8545fc0f3f9bf1cdf8cd2d3a9e7ed8ad29d3ca` predates extension; all inherited accepted blobs compare byte-for-byte. Both builders have substantive committed production contributions. The genuine shared-index capture at `182582c41d21a23d8ccd95688fa7f1afa0437460` remains disclosed: 32 verifier-authored preparation paths were committed under Interface Git author identity. Git authorship, content authorship and independent execution are not relabelled. Subsequent commits use explicit owned pathspecs and exact resulting-commit inspection; no history is rewritten.

One own test-session token was found in two uncommitted numeric capture artifacts. Before commit, the verifier observed 401 for it in all three current destinations and fingerprinted the private fields. [Correction](PRIVATE_CAPTURE_CORRECTION.json) preserves original and replacement hashes and unchanged source/status/assertion/numeric/timing observations; [invalidation](private-capture-invalidation.json) stores fingerprints and statuses only. No host/account credential or historical committed artifact was changed. The [artifact audit](artifact-audit.json) scans saved owned JSON and valid embedded JSON strings with zero unclassified private payload findings and an explicit byte/hash manifest. Source/log text, peer evidence and genuine full room export are outside this scoped privacy claim. Exports and live credentials otherwise remain in client memory.

## Adopted interpretations and remaining limits

Historical IANA subminute offsets follow the recorded exact-instant/nearest representable minute-offset interpretation, retaining original wall fields and immutable older offset-seconds strings. Literal historical seconds offsets and minute-only RFC3339 grammar cannot be claimed simultaneously. Original successful response shape and values remain immutable across upgrades; current lookup/list and new writes use the current schema. Full old bodies retain their historical ignored-field meaning for receipt validation and still participate in retry identity.

Value-based exact integral body numbers and genuine receipt-scoped legacy comparison follow the adopted decision. Boolean/string/container types remain separate and query spelling remains strict. Numeric profile does not determine public-origin shape. Semantic numeric controls follow the adopted functional interpretation: visible, labelled, exact decimal storage with spinbutton/numeric mode/buttons/keyboard and minimum one. This does not invent a native HTML input-type obligation; residual judging ambiguity remains disclosed.

Finite payload, depth, exponent and concurrency samples do not prove arbitrary-workload performance. Very large exact output coefficients for widely separated exponents remain constrained by finite resources. Exact instantaneous cutoff equality uses a labelled source supplement, not a fictional clock-controlled HTTP endpoint. Serializer timing is unobserved; visual/contrast evidence is scoped. No hidden judging result, genuine room export, public release or final submission is claimed; these remain operator-controlled.

Measured current-review activation to aggregation is **1,807.946213 seconds**, `2026-10-04T05:59:20.202000+00:00` to `2026-10-04T06:29:28.148213+00:00`. Verdict writing and sealing timing are separate; whole-factory elapsed belongs to the coordinator. Harness **Codex**, configured model **gpt-6.1-sol**. Actual runtime model override, effort, tokens, catalog-estimated cost and billed spend are **unknown**.


Full concrete-file addendum (sealed 9b0c7db9450a7a3b74a789dbe24e3bcfbaff1244); original artifacts preserved:
# Stage 2 candidate 2 — concrete visual evidence links

Independent verdict **accept** remains against exact full candidate `4dba10246b07b2dda19de260d529f9d94ba0a1ed`, Stage 2 tree `422380c814043021c2df2daad8edbbb34d5b5887`. This prospective addendum completes five file-link metadata findings in the existing review. Coordinator promotion/freeze and Stage 3 copy remain separate gates pending the concrete file-link audit; this document does not authorize later-stage work.

The [updated complete matrix](coverage.csv) replaces only `evidence_path` in `TK2-visual-coherent`, `TK2-visual-human-labels`, `TK2-visual-actions`, `TK2-visual-navigation` and `TK2-visual-no-invented-facts`. All 6,571 records and every other field are unchanged: **6,549 normative rows verified**, zero failed/unverified, and 22 separate diagnostics. The original [matrix](../coverage.csv), [verdict](../VERDICT.md), [summary](../summary.json), original binding/review/metadata/audit files and coordinator rejection audit remain byte-identical to their seals. [Preservation and metadata proof](metadata-self-check.json) supplies hashes and the exact five field differences.

The coordinator's preserved `evidence/coordinator/stage-2-candidate-2-metadata-audit.json` correctly records `fail` for five directory-only links. My previous exact-tree check accepted the directory prefix, which did not satisfy the required concrete file-link standard. Its original failure and the original sealed matrices remain inspectable; neither is rewritten into a pass. The new complete matrix checks every current evidence path with `is_file()` and has zero missing or directory-only paths.

| Observation | Concrete current screenshot evidence |
| --- | --- |
| Coherent warm presentation and hierarchy | [Selected desktop flow](../browser-01/visual/states-1280-selected.png), [successful desktop flow](../browser-01/visual/states-1280-successful.png), [mobile search](../browser-01/visual/visual-375-search.png) |
| Human labels and intentional combined seating | [Selected Garden Bench + Window Alcove](../browser-01/visual/states-1280-selected.png), [both labels in confirmation](../browser-01/visual/states-1280-successful.png), [mobile Together options](../browser-01/visual/visual-375-search.png) |
| Clear primary actions | [Find/Confirm booking](../browser-01/visual/states-1280-selected.png), [Create account](../browser-01/visual/visual-1280-signup.png), [Sign in](../browser-01/visual/visual-1280-login.png), [Find reservation](../browser-01/visual/visual-1280-lookup.png) |
| Consistent navigation across all four routes | [Search](../browser-01/visual/states-1280-selected.png), [signup](../browser-01/visual/visual-1280-signup.png), [login](../browser-01/visual/visual-1280-login.png), [lookup](../browser-01/visual/visual-1280-lookup.png) |
| No invented establishment facts in the reviewed product | [Mobile search](../browser-01/visual/visual-375-search.png), [signup](../browser-01/visual/visual-1280-signup.png), [login](../browser-01/visual/visual-1280-login.png), [lookup](../browser-01/visual/visual-1280-lookup.png), [actual successful booking](../browser-01/visual/states-1280-successful.png) |

Every repaired row additionally names the concrete [original review records](../review-checks.json), [actual visual-run report](../browser-01/visual/summary.json) and [row-specific observations](visual-observations.json). The screenshots were reinspected during this correction. Cream/green/clay styling, labelled Together seating, prominent green actions and consistent route navigation match the original observations. The reviewed pages contain fixture and reservation information rather than fabricated reviews, ratings, restaurant photos, usage metrics or real-establishment claims. This remains a scoped product observation, not an arbitrary-content or full accessibility certification.

No uncovered behavior was found. **Service/browser reruns: zero. Production edits: zero.** Existing current HTTP/browser/official counts, timing, genuine upgrades, screenshots, all four adopted interpretations and limitations remain unchanged. [File proof](file-proof.json) binds concrete existing evidence bytes; no screenshot was reconstructed or replaced. The new metadata run reports five repaired rows, no other field changes, complete required metadata, all current links resolving to files and zero errors.

Executed from the result repository with the workspace Python:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-2/candidate2_file_links.py
```

[Command proof](command-proof.json) records the actual invocation and successful output. The original verifier verdict commit is `efd23ed509e039ca285012c0c1b23a952e8d92a0`; its inspection seal is `cc271a32cfadec85a8deb578041c87ef099c9cfa`. The new evidence revision is supplied after exact owned-commit inspection in the room report, avoiding a circular self-commit identifier here. Configured harness/model remain Codex/gpt-6.1-sol; actual model override, effort, usage and cost remain unknown.


Full accepted Stage 2 Systems handoff (4dba10246b07b2dda19de260d529f9d94ba0a1ed):
# Stage 2 reconstructed integrity — Systems handoff

**Own constrained checks pass. Stage 2 remains unaccepted; highest independently accepted consecutive stage is 1.** Complete independent startup, unchanged official/inherited checks, specification coverage and a named verifier verdict remain coordinator-controlled gates. No Stage 3 work occurred.

## Exact source and responsibility

| Identity | Full revision |
| --- | --- |
| Immutable accepted Stage 1 | `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b` |
| Stage 1 independent acceptance | `a22de6b769c1454c35650377da1251edc99de744` |
| Systems two-file base copy | `c2b4c4be92ce6add82af62e11b8d71e1916bfe0e` |
| Append-only acknowledgement metadata correction | `41498b7ee24e8a50b48b6c14a60bccdadf39c076` |
| Coordinator six-file inheritance proof | `ab8545fc0f3f9bf1cdf8cd2d3a9e7ed8ad29d3ca` |
| Systems substantive reconstructed source | `f783598428a88d53490f68498063ed69e02201b3` |
| Interface runtime/browser integration | `a040054f2a8d00c560bea7f02324d1443c5a3f14` |
| First full probe/source binding | `d03e0448d924799d09d585b35d2b49558a079d4a` |
| Final corrected complete tested candidate/protocol | `a67e48030cbacc3ea3305c115aa25bf19f303734` |
| Tested Stage 2 tree | `422380c814043021c2df2daad8edbbb34d5b5887` |

The final evidence successor is reported in the room after commit. It adds evidence only and must have the identical tested Stage 2 tree. Systems authored/changed only `stage-2/core.py`, `stage-2/json_codec.py` and explicit owned paths under `evidence/systems-engineer/`. Interface owns transport, Docker/RUN and browser assets. No frozen Stage 1 production file was edited. Every commit used `--only` explicit paths, followed by exact own changed-path inspection.

All sixteen numbered parts and END of `TK-20261004-S2-systems-engineer-RECONSTRUCT-2` were received and acknowledged before base work. Phase B release is inbound `c1a8f4d4-2555-40d4-997f-775bdfd33d4e`, after the committed all-six-file proof. The initial report's part-16 receipt ID was incorrectly labelled a reciprocal acknowledgement ID; the original report remains unchanged and the append-only correction explicitly records the actual reciprocal ID as unknown. No room event is invented.

## Restored invariants

Member sets support singles and explicit unordered pairs, canonicalize to declaration order, preserve fixture option order, sum capacities exactly and reject undeclared/transitive/three-member seating. Occupancy intersects members over half-open absolute intervals. Create, amendment, cancellation, batch moves, fixtures and import use the same occupancy rules. Real single/pair changes remove obsolete seating fields; no-op and reverse-order amendments retain stored values. Batch candidates validate in input order before occupancy, and records plus successful receipt commit under the inherited RLock.

Accepted exact numeric values, strict nonrecursive JSON decoding, immutable numeric leaves, iterative copies, receipt preparation and detached response snapshots remain the foundation. Booking capacity comparison avoids expanding exponent metadata. Actual eligible pair sum outputs use exact aligned coefficients; ordinary integer sums remain integer JSON tokens. Number values never become wire strings. Unknown body values remain part of complete retry identity.

Original public receipt shape and numeric comparison profile are independent. A newly accepted exact-profile Stage 1 receipt still has original singleton shape and may include formerly ignored `table_ids` in its full body. Genuine old Stage 2 receipts may have combined shape and a legacy numeric profile. Import validates those successful originals by their saved public shape, retains complete bodies/profiles and never enriches original responses. Current views use Stage 2 representations. Mixed receipts survive another independent replacement with existing hashes, sessions, identities, references, statuses and timestamps intact.

Authoring inputs: the complete cumulative assignment/specifications/brief and four adopted decisions, coordinator release/proof, own committed Stage 1/Stage 2 implementation and diagnostics, and Interface's separately committed integration consumed solely as a complete image context. No verifier probe/oracle or shipped test implementation was read, copied or executed. No external domain code/schema, memory, toy/abandoned result, outside-workspace source or host dependency installation was used.

## Final observed checks

| Own executable scope | Actual result | Seconds |
| --- | --- | ---: |
| Combined exact capacities, three genuine origins, deep pair receipts/raw migration/races | 410 HTTP requests, 1,774 assertions, zero failed; 3/3 scenarios | 12.972681923 |
| Complete exact values/types/precedence/deep/snapshot/legacy suite | 373 HTTP requests, 1,773 assertions, zero failed; 7/7 scenarios | 1.186101126 |
| 4,301-digit integer configuration/query/pair/export suite | 92 HTTP operations, 148 assertions, zero failed | 0.497090709 |
| Stage 2 member/interval, atomicity and ordinary concurrency | 11/11 HTTP scenarios, no skips; seed 20261004, 160 saved oracle operations | 1.340 |
| Inherited API/authentication/calendar/occupancy/receipt scenarios | 15/15 HTTP scenarios, no skips | 2.458 |
| Packaged helper arithmetic, explicitly not HTTP | 6,030/6,030 assertions; seed 2026100403 | 0.030291375 |
| Full clean clone/build/start/six-client/cleanup driver | All six clients exit 0, no driver exception | 112.270812167 |

The three counted wire clients total 875 requests/operations and 3,695 assertions. This excludes uncounted unittest-scenario traffic, health/inspection and helper diagnostics; no normative row count or total factory coverage is inferred. No official harness or hidden judging result is claimed by this handoff.

The additional wire client genuinely builds/runs accepted Stage 1 `75005d57`, old Stage 1 `49287b4a5a1481f995c470ccae31776f03d4b863` and old Stage 2 `16aee9f0ea10de5b8fa81a84429cc337c3c4490f`. Those sources really issue multiple sessions, references and create/move receipts, then changes/cancellation. Their unchanged exports replace independent current processes. Stage 1 ignored `table_ids`, old rounded numeric aliases, precise exact current values, old singleton and combined shapes, original responses, password login and tokens remain valid. Different complete bodies conflict before resource validation; fresh writes obey current rules. Mixed second imports, replacement instead of merge, repeated replacement, profile refusal and reset/session clearing pass. No legacy state or receipt was manufactured from a fixture or lost lexeme.

Actual combined receipts use arrays/objects at depths 10,000 and 20,000 and alternating wrappers at depth 20,000. Balanced wrappers surround independently valid finite leaves. The client never decodes private exports or changes its recursion limit. Numeric aliases replay originals; boolean/number differences conflict. Deep swaps, no-ops, ordered non-occupancy errors, overlap rollback and failed-key reuse pass. The final additional client captures 60 raw exports and forwards 25 unchanged successful snapshots, with matching request/response hashes and byte counts. After amendments, cancellation and a second raw replacement, original create/move responses remain unchanged.

Fifty identical depth-20,000 pair creates give exactly one 201 and 49 identical original 200 responses. Fifty pair/member competitors give one 201 and 49 precise 409 refusals; a failed key remains reusable. The successful deep race receipt survives raw transfer/cancellation/replay. The separate member/interval oracle and ordinary races are derived from fixture sets and interval arithmetic, not production helpers. The exact-number suite also captures twenty real snapshots overlapping thirty writes and independently checks complete prefix relationships before peer import.

Largest request in the additional client: 484,856 bytes. Maximum request time: 3.230782501 seconds, below the ordinary five-second limit. These are finite samples, not arbitrary-size/depth/exponent workload guarantees.

## Runtime identity and reproduction

Actual current image: `sha256:1df6918c6feef58bb0b414ab9cdcbb01c1e161550f92c0d80ef59efb0481c8c4`.

| Packaged production module | Actual SHA-256 |
| --- | --- |
| core.py | `c5ddc11f9a7c7b80d7d85dd5f9ba93ff4f236a6bf1ee4f4cfc901efae02c957e` |
| json_codec.py | `3bf4c5dd7ccee1c99127d735822331fedb1491af3568d3490a81a092bae49501` |
| server.py | `7ea970fec3b00387de8fb6ff8d448a42019424706407c0a7d41e2168c8376cc9` |

The entire nine-file committed Stage 2 Docker context was built from a clean detached clone. Every context/probe file is hashed; all three actual packaged module hashes match the named candidate in both current instances. Accepted/old source contexts and actual module identities are separately checked. Available build cache was reused; no uncached-build claim is made. Default 8080 and override 18171 health-command return measured 3.274851500/3.272882417 seconds after launch, before source inspection. These are readiness upper bounds, not the first possible healthy instant. Cross-container requests reach the selected ports. Host-published reachability is not claimed.

Five services and six separate diagnostic clients each run at inspected 2 CPU/2 GiB, no mounts, on an inspected internal offline network. Own mappings are 18170–18174. All twelve final run container/network cleanup commands return zero; first-run twelve do too. Temporary contexts are removed. Images and clean clones remain; no peer process was stopped. Final clone remains clean at the exact tested revision:

`/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/systems-engineer-s2-reconstruct-20261004t054759469645`.

Commands from the absolute result repository (reproductions require new unique output names):

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-2-reconstruct-container-check.py --revision d03e0448d924799d09d585b35d2b49558a079d4a --probe-revision d03e0448d924799d09d585b35d2b49558a079d4a --out evidence/systems-engineer/systems-engineer-s2-reconstruct-service-01
../../.venv/bin/python -B evidence/systems-engineer/stage-2-reconstruct-container-check.py --revision a67e48030cbacc3ea3305c115aa25bf19f303734 --probe-revision a67e48030cbacc3ea3305c115aa25bf19f303734 --out evidence/systems-engineer/systems-engineer-s2-reconstruct-service-02
../../.venv/bin/python -B evidence/systems-engineer/stage-2-reconstruct-evidence-audit.py --candidate a67e48030cbacc3ea3305c115aa25bf19f303734 --runs evidence/systems-engineer/systems-engineer-s2-reconstruct-direct-01 evidence/systems-engineer/systems-engineer-s2-reconstruct-direct-02 evidence/systems-engineer/systems-engineer-s2-reconstruct-service-01 evidence/systems-engineer/systems-engineer-s2-reconstruct-service-02
```

Every executed Git/build/Docker/health/probe/inspection/cleanup argv, return code, log and timing is in each `runtime.json`. The optional missing `json_codec.py` Git lookup on genuinely old five/eight-file sources returns 128 as a recorded source-absence diagnostic; it is not a service/test failure. Actual probes come from named committed blobs and their hashes are recorded. Direct Engine/helper commands and timings are separately saved in direct run `commands.json`.

## Preserved failures, audit and remaining gates

Direct-01 retains 11/11 current and 14/15 inherited scenarios: the old Stage 2 branch incorrectly expected private schema 1 unchanged instead of adopted schema 2/profile metadata. Direct-02 separately passes 11/11, 15/15 and 6,030 helper controls after an evidence-only correction. Service-01 remains failed with two obsolete 400/malformed_request expectations for numeric slot_minutes=1.5; actual adopted response was 422/validation_failed. Service-02 separately passes all six clients with identical production bytes. Neither original output is changed into a pass. Prior independent rejections, real decoder/digit/UI failures, repairs and the shared-index authorship incident remain immutable history.

`stage-2-reconstruct-evidence-audit.json` binds 320 files and inspects 12,612 saved JSON object records: 124 private/credential fingerprints, zero raw private JSON payload findings. Live exports/tokens/password hashes stay in memory. The scoped scan excludes source/log strings, peer evidence and the genuine room export. It checks raw forwardings, source/resources, clean clones, twelve cleanup exits per run and all six frozen Stage 1 files. Browser/product evidence is independently Interface-owned and is not an interaction claim by Systems.

All four adopted decisions remain explicit: value-based exact numeric semantics and genuine legacy profiles; immutable original response shape; semantic exact numeric controls (Interface-owned); exact IANA instant with nearest representable minute-offset historical serialization and unchanged original wall fields. Genuine old offset-seconds strings remain immutable. Literal historical subminute offsets and minute-only RFC3339 grammar are not claimed simultaneously. Extremely large output coefficients for widely separated capacity exponents are not claimed to fit finite resources.

Final driver UTC window: 2026-10-04T05:47:59.469767+00:00 to 2026-10-04T05:49:51.741051+00:00; measured 112.270812167 seconds. This is a scoped execution interval; whole factory elapsed is coordinator-owned. Harness Codex/configured gpt-6.1-sol; actual model override, effort, tokens, catalog-estimated and billed spend are unknown. Independent named acceptance, public release, genuine room export and submission remain separate gates. No later stage is extended.


Full accepted Stage 2 Interface handoff (1e3af87d78c2d6c037650a9c134453012d4fb0c6):
# Stage 2 reconstruction — complete Interface handoff

**Own complete-service integration passes; independent Stage 2 acceptance remains pending.**
Highest consecutive independently accepted stage is **1**. Tested full candidate
`f783598428a88d53490f68498063ed69e02201b3`, Stage 2 tree
`422380c814043021c2df2daad8edbbb34d5b5887`. Frozen Stage 1 remains
`75005d57fe0904753eac4eab5bf4e4c9a78b6d1b`, tree
`75f6ece6952c570eedf8a548f4428a5b2c986128`. The own evidence successor is reported
in the room after its exact --only commit inspection, avoiding a circular identifier.

## Implementation and source ownership

Complete sixteen-part `TK-20261004-S2-interface-engineer-RECONSTRUCT-2` and END
preceded all work. Base copy is `a594b7c81bf28b15406dfc4c8de5a873c7a81c45`.
Coordinator proof `ab8545fc0f3f9bf1cdf8cd2d3a9e7ed8ad29d3ca` and release
`d698ee6c-caf1-41cd-8feb-f9e78a6f4582` preceded extension. Interface implementation
and original complete protocol are `a040054f2a8d00c560bea7f02324d1443c5a3f14`.
Its exact twelve-path --only commit contains five owned production paths and
seven own evidence paths. Systems owns core.py/json_codec.py. No Stage 1,
Systems, verifier, or later-stage production file was edited by Interface.

The accepted raw-byte codec adapter now serves the original offline browser
routes/assets, preserving serialize-before-headers, real byte lengths, empty
204 and disconnect recovery. Dockerfile/ignore package the codec and web assets;
RUN.md describes the single image, semantic numeric controls and real upgrades.
The browser resolves integral decimal/exponent values exactly for unsafe numeric
display and capacity sums after strict response syntax validation. Existing
status/local-end/search-generation/conflict/uncertain-retry repairs and substantive
product assets remain. All test source is outside graded folders. No peer test,
oracle, external domain source or host dependency was read/installed/executed.

## Exact own observations

| Executed scope | Result | Browser seconds | Whole driver seconds |
| --- | --- | ---: | ---: |
| Complete browser/API/runtime and all original 34 plus new 9 scenarios | 43/43 scenarios, 793 assertions, zero failed; 89 real screenshots | 34.370 | 117.110912042 |
| Labelled numeric wire capture supplement, identical production | 5/5 scenarios, 90 assertions, zero failed; 10 real screenshots | 3.853 | 86.596982334 |

These are owning-builder assertions/scenarios, not normative coverage rows,
official counts, hidden results or independent acceptance. No scenario is skipped.
Full run records 288 direct API client operations, 460 browser-originated requests
and 27 real route-forwarding operations. Forwarding transports those browser
requests; these counters are separate and are not added into a fabricated unique
HTTP-request total. Supplement counters are recorded in its browser-report.json.
Maximum full-run measured direct/forward request time is 0.071973458 seconds;
this excludes browser-only timing and does not establish arbitrary workloads.

The complete run exercises actual direct routes/auth/logout/public browse,
keyboard/mobile inputs, exact reference/status text, singleton/pair occupancy,
50 identical and 50 competing pair requests, stale search A after B, rival 409
refresh with preserved form, committed-drop uncertainty/retry and changed field
identity. Exact integer controls/query/body/display/retry pass through 4,301 digits.
Real malformed committed responses remain uncertain and recover the original
reference. Both specified DST zones and historical/calendar local ends remain
truthful, including immutable old offset-seconds strings.

Four real browser upgrade flows use unchanged packaged Stage 2 assets against
actual independent sources: accepted Stage 1 `75005d57...`, historic Stage 1
`49287b4a5a1481f995c470ccae31776f03d4b863`, and old Stage 2
`16aee9f0ea10de5b8fa81a84429cc337c3c4490f` for singles and pairs. Each source
actually issues the token, retained create/move receipts and committed booking
whose browser response is dropped. Unmodified export bytes stay in memory and
replace current state between requests. The same document, user, form, body and
key recover the real original reference; retained lookup works. Genuine Stage 1
receipts with formerly ignored table_ids retain their original meaning and
original table_id-only response. Old Stage 2 combined receipts retain their
shape independently of numeric profile. Source mutation after capture does not
alter the replacement. Original create/move receipts and new exact receipts
survive raw mixed replacement through another independent peer and back.
Four migration traces match export/import lengths/digests; four additional mixed
roundtrip traces retain fingerprints and decoded=false. No export is reconstructed
from a fixture or published as demo state.

Actual capacity responses preserve `9007199254740993.0`, `9007199254740993e0`,
`90071992547409930e-1`, `9.007199254740993E+15` and
`0.9007199254740993e16`; exact single and pair counts, input/retry and labels pass.
Opaque quoted URI/Unicode IDs survive real query/path/body/selection/lookup/cancel;
canonical declared pairs show human labels. No mocked DOM value or string-valued
JSON party size is used. Numeric controls retain the adopted semantic interpretation.

## Runtime, reproducibility and product review

Full run directory: `interface-engineer-s2-reconstructed-20261004t054351394649z/`.
Supplement: `interface-engineer-s2-reconstructed-20261004t054725205604z/`.
Both are under this evidence directory; runtime-report.json saves all actual
Git/Docker/client argv, source/image/probe hashes, statuses, resource inspections,
startup/cleanup/timing and clean clone paths. Full driver source is sealed at
`b50f54c2d5525c6f0dc454fef42f5d382580649c`; original full protocol at a040054f.
Supplement driver/protocol are `bc36441e726766055d1739f00da246666a4dd44f`.

From the result root with the assigned workspace Python:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-2-reconstruction-container-check.py --revision f783598428a88d53490f68498063ed69e02201b3 --probe-revision a040054f2a8d00c560bea7f02324d1443c5a3f14
../../.venv/bin/python -B evidence/interface-engineer/stage-2-reconstruction-container-check.py --revision f783598428a88d53490f68498063ed69e02201b3 --probe-revision bc36441e726766055d1739f00da246666a4dd44f --scenario-prefix integral-wire-
../../.venv/bin/python -B evidence/interface-engineer/stage-2-reconstruction-evidence-audit.py --out <new-proof-file>
```

Use the exact named driver blob for historical reproduction; current source adds
labelled supplement support and seals its own executed bytes. Every runner creates
a new unique output. The prefix is an additional owning-builder supplement after
the complete run, never an official-suite filter. The dependency-runner image is
unchanged and used for Playwright/packaged Node, not official or peer test source.
No official harness was run by this Interface handoff.

Fresh clean detached complete clones at f7835984 remain unchanged. Actual current
image is `sha256:b1849d76040e3d4773c6cabe898c74b5b86f49ae5ce1014c3040bf80d570db81`.
Full default8080 / override9090 health upper bounds are 3.271699333 / 3.237950875
seconds from each docker-run invocation to health-command return, before later
source inspection. Five independent service processes and the separate browser
client each have inspected 2 CPU/2 GiB, no mounts and an internal offline network.
All-interface access is observed through real cross-container browser/API flows;
host-published reachability is not claimed. Build cache was available; no
uncached-build claim. Own full host mappings use 18250–18254. All seven cleanup
commands in each full/supplement run return zero; the preserved failed run also
has seven successful cleanups, 21 total recorded removals. Only own resources
were removed. Images and exact clean clones remain; temporary old contexts are removed.

Visual inspection of the actual full-run desktop confirmation, opaque-ID mobile
lookup, integral-exponent mobile lookup and old Stage 2 pair uncertainty confirms
warm cream/green/clay hierarchy, human labels, exact counts, clear navigation,
labelled controls and distinct success/uncertainty. Actual 375px/desktop width and
keyboard flows pass; this is a scoped Interface product assessment, not complete
accessibility certification or independent product acceptance.

The scoped evidence proof hashes 330 files across four own output folders and
inspects 914 saved JSON object records plus 35 embedded JSON strings in seven
JSON files, finding zero raw password/password_hash/token/tokens/state/authorization
fields. Live exports/tokens/hashes remain in memory. Source/log strings, peer
artifacts and genuine final room export are outside this privacy claim. Synthetic
test passwords appear in authored probe code. The operator still owns final room
export secret review, publication and submission.

## Preserved errors and remaining gates

The original run has 43 DNS runner errors before any HTTP response and zero
assertions; its FAIL output, executed protocol and 43 blank diagnostic captures
remain immutable. The shorter-name driver fixes that runner defect, not service
code. The full passing run's signed-exponent trace extractor clipped a minus sign;
actual independent Decimal and browser checks passed. A trace-only repair and new
five-case run verify complete tokens without replacing the original observations.
The initial artifact audit used host python3 lacking sys.set_int_max_str_digits,
stopping before evidence reads/writes; its observed error is separately preserved.
The workspace-Python reproducible audit passes. No error is relabelled as a service
pass and no source change followed any of these evidence issues.

Independent named startup, cumulative specification/official/inherited checks,
complete coverage and acceptance remain coordinator/verifier gates. Highest
accepted stage remains 1. No Stage 3/4 work occurred. Historical nearest-minute
wire offset/exact instant/original wall time and immutable legacy-string exception,
original receipt shape, exact numeric/legacy comparison and semantic numeric-control
interpretations remain explicit. Finite sizes/number spellings/scenarios do not
prove arbitrary input performance. Measured durations above are scoped runs;
whole-factory elapsed is coordinator-owned. Harness Codex/configured gpt-6.1-sol;
actual model override, effort, tokens, catalog estimates and billed spend unknown.

The earlier sections below preserve the preparation/copy/error chronology.

---

# Stage 2 reconstruction — Interface base copy

**Phase A is complete locally; Stage 2 is unpromoted.** Highest independently accepted consecutive stage is 1. Stage 1 is immutable at `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b`, tree `75f6ece6952c570eedf8a548f4428a5b2c986128`, independently accepted at `a22de6b769c1454c35650377da1251edc99de744`.

All sixteen parts and END of `TK-20261004-S2-interface-engineer-RECONSTRUCT-2` arrived before work. Shared card 17 authorizes this exact base copy only. Interface copied the four owned runtime files from immutable Git blobs, with no byte normalization. Existing Stage 2 web assets, frozen Stage 1 and all prior source/history remain unchanged. Systems owns its separate core/module copy.

| File | Source and target SHA-256 |
| --- | --- |
| server.py | `fb8d9e41eb13c3a736d49573903253a6cb98284790cf5edc9caeb352f0e0946c` |
| Dockerfile | `ee2fbc4476fdac158e83f18ffb254ff14c2643017092c9baf186c03d06bdb528` |
| .dockerignore | `393ca989893a3ceee4e6fe5366f6b7ac019a51900b9dadc08a56787688c1da1c` |
| RUN.md | `ac938287c37b9da1a76e230466362dd1cdf928fadf8676399c7b495aecb7530f` |

Reproduction: for each listed file, read `git show 75005d57fe0904753eac4eab5bf4e4c9a78b6d1b:stage-1/<file>` as bytes and write those identical bytes to `stage-2/<file>`. Exact executed argv, pre-copy hashes, source blob identities, retained web asset hashes and observed comparisons are in `stage-2-reconstruction-base-copy.json`. Four of four copied files compare byte-for-byte equal. Frozen Stage 1 and web assets compare unchanged before/after. The full resulting own commit is reported in the room after `--only` commit and exact changed-path inspection; embedding its own identifier here would be circular.

No application, Docker build, browser or official check was executed for this intermediate step. The copied RUN.md and Dockerfile are intentionally the original Stage 1 bytes; they will be restored for Stage 2 only after the coordinator commits its six-file proof and releases Phase B. Other target files may temporarily be incompatible. No Stage 2 acceptance or runtime behavior is inferred from a copy check.

The next authorized phase restores Interface static routes/image/RUN integration on this stable bytes adapter and extends its exact numeric presentation probes. All prior semantic controls, exact status, restaurant-local end, search-race and uncertain-response repairs must remain. Full genuine old/new Stage 1 and old Stage 2 upgrade flows and complete independent review remain required. Historical timestamp, immutable receipt and semantic numeric-control interpretations remain disclosed.

Authoring inputs: complete current direct package, authoritative room plan, full participant guide, accepted source and own existing source/history. No peer probe/oracle or external domain source was read, copied or executed. Model: configured Codex/gpt-6.1-sol; actual override, effort, usage and spend unknown. Copy/check elapsed is scoped and measured in the manifest, not whole-factory time.

## Released Phase B implementation preparation

Coordinator release d698ee6c-caf1-41cd-8feb-f9e78a6f4582 follows committed six-file
proof ab8545fc0f3f9bf1cdf8cd2d3a9e7ed8ad29d3ca and base
41498b7ee24e8a50b48b6c14a60bccdadf39c076. Static route/asset serving and security
headers were restored over the accepted bytes adapter; loads/dumps still bind
the shared codec and response bytes are serialized before status/headers.
The image and ignore file package web assets plus json_codec.py. RUN.md retains
all prior product/retry/upgrade instructions and records exact numeric semantics.
The browser now resolves whole decimal/exponent response tokens exactly before
selecting an unsafe-integer display string; strict JSON syntax validation precedes
that conversion. Existing semantic numeric fields, exact status, restaurant-local
end-time, search-generation, conflict and uncertain-retry code remain intact.

Own prepared browser scopes add five actual integral-wire fixture/presentation
flows, opaque quoted URI/Unicode IDs, genuine historic Stage 1 and old Stage 2
single/pair browser upgrade bridges, raw unchanged export transfer, old create/move
receipt replay and mixed-origin replacement through an independent peer. The
existing 34 scenarios remain in the complete run. Tests are prepared, not passing
execution claims. The new source-bound driver builds a clean detached clone and
genuine historical contexts, hashes actual packaged source, runs default/override
PORT at 2 CPU/2 GiB on an internal network without mounts, and sends sealed own
probe bytes on stdin to the dependency-runner image. Each run has a new directory.

Three Python AST checks pass. Packaged Node JavaScript syntax check exits zero
in 1.365196916 seconds under network-none/2 CPU/2 GiB; this is syntax evidence
only. Artifact interface-engineer-s2-reconstructed-preflight-20261004t053951158486z.
Actual complete service execution waits for the Systems named committed core/module
handoff. No peer probe/oracle implementation was read or executed; only own code,
the complete assignment, accepted copy proof and own historical source were used.
The four adopted timestamp, original receipt, semantic numeric-control and exact
numeric/legacy-profile decisions remain applicable. Stage 2 remains unaccepted.

## Preserved first runner failure and correction

The first complete-image run at f783598428a88d53490f68498063ed69e02201b3
with own protocol a040054f2a8d00c560bea7f02324d1443c5a3f14 returned raw
FAIL: 0/43 scenarios, 0 assertions, 43 ENOTFOUND errors before any initial
HTTP response. All five services had passed health, constrained resource and
packaged-source checks. Driver container names exceeded the 63-byte DNS-label
limit; this is an owning-runner defect, not an observed service failure. The
original result/logs/executed source and blank failure captures remain unchanged
in interface-engineer-s2-reconstructed-20261004t054140435353z. Total driver
time 85.839779500 seconds; seven own cleanup commands all exit zero.
The only correction shortens seat-prefixed driver resource names, adds explicit
DNS-label assertions and inspects actual client constraints. Production and
protocol sources stay unchanged. A new unique execution is required; this
failed run establishes no browser behavior or acceptance.

## Full browser pass and narrow trace correction

The corrected full run at unchanged f783598428a88d53490f68498063ed69e02201b3
passes 43/43 scenarios, 793 assertions in 34.370 seconds; total driver
117.110912042 seconds. Artifact interface-engineer-s2-reconstructed-20261004t054351394649z,
89 genuine screenshots, seven cleanup commands all zero. Sources and resource
identities match; clean clone remains retained. Five actual API responses retain
integral decimal/exponent capacities, and their exact single/pair display succeeds.
The third case trace extractor omitted the minus sign and stored a partial
capacity token, while the independent Decimal value assertion and real browser
flow passed. This is a trace-only regex defect; the original result/source stays
unchanged. The recorder now recognizes the complete JSON number grammar. A
labelled five-scenario integral-wire supplement will independently execute
corrected capture against identical production; it is not a replacement or
shortened version of the complete 43-scenario run. No official suite is selected
or modified. The driver also seals its executed source in future run artifacts.


END OF COMPLETE CONTENT TK-20261004-S3-systems-engineer-INITIAL-1
