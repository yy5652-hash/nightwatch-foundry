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
