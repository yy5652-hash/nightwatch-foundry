# Stage 1 engine invariants

Scope: package TK-20261004-S1-systems-engineer-A, all four parts and final marker received. Full participant guide and supplementary acceptance brief read. Only `stage-1/core.py` is engine-owned. Interface owns HTTP parsing, listener, image and launch documentation. Independent acceptance remains verifier-owned.

- Every request acquires one engine lock before authentication, state reads, validation, occupancy checks, mutations and receipt recording. Responses are detached JSON snapshots. Concurrent successful identical first requests therefore have exactly one 201 response.
- State has one canonical reservation collection. Occupancy is derived from confirmed records with UTC half-open intervals; there is no separate occupancy cache to partially update.
- Create and batch receipts are separate immutable snapshots keyed by user, method, URL path and key. Parsed JSON equality ignores object key ordering, distinguishes booleans from numbers and retains unknown fields. Failed requests save no receipt. Replay precedes resource validation and returns the original snapshot with 200.
- Single amendments and batch moves construct proposed records without touching originals. All non-occupancy validation is complete before occupancy; batch validation follows input order, with current cutoff before changes for each member. Occupancy is tested against the entire proposed result before one commit.
- Cancel transitions confirmed to cancelled, retaining identity and timestamps. Repeated cancellation returns the current record even after cutoff. Amendments preserve identity, owner, creation time and reference.
- Bare local timestamps are parsed strictly. ZoneInfo fold 0 selects the first repeated-hour occurrence; a UTC round trip rejects skipped-hour times. Duration and overlap use absolute UTC time. Cutoff uses the current stored start and the current clock. Past creation is allowed.
- Reset builds a candidate fixture; import builds and validates a candidate replacement, including hashes, session ownership, record identities, timestamps, occupancy and saved receipts. Only then is state swapped. Export deep-copies the complete state while holding the same lock. No filesystem/process identity is part of the export.
- Passwords use salted scrypt. Tokens are independent cryptographically random bearer credentials and do not expire. Public browsing bypasses authentication; booking lookup filters ownership before exposing records.

Interpretations: email account comparison is case-insensitive; unspecified tie order in reservation listing retains creation/fixture order. Closing-hour comparison uses absolute duration and the first-occurrence IANA closing boundary. No later-stage endpoints or fields are implemented.

Harness: Codex. Operator model: gpt-6.1-sol. Actual runtime model override and effort: unknown (not exposed). Builder probes are diagnostic evidence and do not establish hidden-suite success or stage acceptance.

## Calendar repair update

The initial UTC round-trip implementation above was superseded after independent calendar rejection. Absolute time is an ordinal-based integer microsecond value, so valid local years 1–9999 do not require representable UTC dates. ZoneInfo fold-offset comparisons reject gaps; ordinary endpoint conversion uses ZoneInfo.fromutc and boundary endpoint conversion verifies a local candidate against the exact integer instant. Occupancy, order, cutoff and absolute duration share this representation. The original locking, validation-before-mutation and immutable receipt invariants remain unchanged. Details and the historical IANA offset-seconds/RFC3339 grammar issue are recorded in `stage-1-calendar-repair-02.md`.

## Recorded timestamp interpretation

The complete TIMESTAMP-3 package resolves the earlier pending grammar question. Newly computed subminute-offset timestamps use the nearest representable minute-aligned fixed offset and adjusted clock, with lower-offset ties; exact integer instants and original wall fields remain unchanged. Import and replay retain original timestamp strings and successful receipts rather than canonicalizing history. Ordinary minute-aligned timestamps retain the restaurant offset/clock. This is the coordinator's explicit interpretation exception, detailed and tested in `stage-1-timestamp-repair-03.md`.

## Base-fixture minute-count validation

The base fixture's three minute counts have no Stage 1 stated upper bound. Validation preserves positive integer grid/duration and nonnegative integer cutoff without requiring a timedelta representation. Grid candidates remain bounded by the local opening window; duration fit is checked with exact integer instants before endpoint conversion; cutoff also uses integer arithmetic. A huge duration therefore cannot produce an out-of-hours reservation, while a huge cutoff correctly refuses ordinary future edits/cancellation. Reset/import use the same configuration validation. Details and pre-repair HTTP failures are preserved in `stage-1-minute-boundary-repair-04.md`.
