# Stage 1 TIMESTAMP-3 interface integration check

Tested full candidate: `b4a124e3671ec22a4df0780343f6389ff4b70d05`.
Systems service repair: `f4eeac50227a59ce785768dbb37bb4641d83c88a`.
Extended interface probe: `94c4d59cffb71c2936434d3379673ad4951753e5`.
Stage 1 files were clean; image core.py/server.py hashes match the tested candidate.
No service files or verifier files were changed by Interface for this recheck.

Command: `python3 evidence/interface-engineer/stage-1-container-check.py`.
Evidence directory: `evidence/interface-engineer/interface-engineer-s1-20261004T010412572868Z/`.
Exact Docker commands, source hashes, resource/network settings and output are
retained in run.json, image-source-sha256.json, container-limits.json, build.log,
service.log and probe.json. Only this invocation's own container was removed.

Observed: **577/577 assertions passed, zero failures**, comprising the previous
489 transport/runtime assertions plus 88 timestamp/calendar/recovery assertions.
The count includes repeated media-type/length/timing checks and is not a normative
requirement count or official test count. Probe elapsed: 0.1302 seconds. Cached
build/start/probe/evidence/cleanup elapsed: 1.3416 seconds. Runtime: no networking,
2 vCPU, 2 GiB, nondefault PORT 9090, observed 0.0.0.0 listener.

## Timestamp interpretation checks

New HTTP cases use Berlin `0001-01-01T00:00` and `0001-01-01T18:00`, plus New York
`9999-12-31T21:30`. Their availability and creates are checked against exact IANA
offsets from the packaged zone data, while ordinal arithmetic preserves absolute
instants outside the UTC datetime calendar range. The expected transport offset
is derived by independently enumerating all minute offsets with representable
local clocks, minimizing distance to the IANA seconds offset then choosing the
lower numerical offset on ties. No production serializer or verifier probe code
is read or invoked as the oracle.

Availability/create start and end timestamps pass RFC3339 minute-offset syntax,
exact-instant and nearest-representable-offset checks. Original starts_at_local
values remain unchanged; duration is 90 absolute minutes. Berlin midnight tests
the representable-calendar constraint, and New York covers instants past the UTC
maximum while local timestamp fields remain representable. Reset/import then
lookup and idempotent replay retain these newly issued records and receipts
exactly. Previous modern DST/retry/concurrency and transport checks remain green.

This run tests new receipts across replacement in one process. It does not claim
the genuine prior-version source migration coverage reported by Systems; that
coverage and independent verification remain separate evidence.

## Interpretation and remaining gates

Coordinator decision: evidence/coordinator/timestamp-representation-decision.md.
For subminute historical IANA offsets, the wire offset is minute-aligned and its
clock adjusted to preserve the exact instant. It is not literally the IANA
seconds offset; original wall fields remain truthful. This explicit interpretation
is a final-report risk, not a claim that incompatible offset grammars both hold.
Old successful receipt strings remain immutable under the decision.

The interface integration scope passed; official isolated checks, fresh-clone
review, the complete independent requirement matrix/verdict and promotion remain
independently owned. Stage 2 was not extended. All earlier observations remain
intact; no failed evidence was converted in place.

Harness Codex; operator-configured model gpt-6.1-sol. Actual override, reasoning
effort, token usage, billed spend and catalog-estimated cost are unknown.
