# Stage 1 candidate 6: reject

Exact full candidate `ab0cf79767b6768153a73894bf5768bf3328491a`, complete production
`debff0bbf2625936d30e1e11066b966a46320137`, Stage 1 tree
`d2905df39546a619afbad3547b10205bb6c01610`: **reject**. Highest consecutive
independently accepted stage remains **0**. Stage 2 promotion and later-stage
extension do not follow this review.

The repaired service preserves exact finite JSON numbers and genuine historical
receipt profiles in the tested cases. It still refuses valid ignored nested
JSON at modest payload sizes. The smallest failing sampled reset uses an ordinary
fixture plus an unknown `ignored` field containing 10,000 balanced array wrappers
around numeric `1`: **20,314 bytes**, expected204, observed400 `malformed_request`,
message `Body must be a JSON object`. The top-level body is an object. The same
create is20,100bytes. Depth20,000 fails too; depth1100 and5000 controls pass.
These are sampled bounds, not a discovered exact admission threshold.

Stage1 §3.4 says unknown request fields are ignored, never an error; no JSON
nesting ceiling is stated. Section5 reserves malformed_request for unparseable
bodies or wrong types. Balanced arrays around an independently validated finite
numeric leaf are valid by the JSON array production. The client constructs
these raw bytes and never uses the production decoder or its own recursive
parser to decide deep grammar. Sections7/10 require complete successful body
semantics and preserved receipts. The same valid boundary returns400 on signup,
create and moves (expected201), and on a changed complete body for an already
successful key (expected409 idempotency_key_reuse). Ten failed HTTP assertions
represent one decoder admission defect across the tested routes/orderings.

The separately committed client is [very_deep_probe.py](../very_deep_probe.py),
protocol source revision `c771649942f92685d03b90e5caa79f5125f85866`. Actual source SHA and Docker
argv are in `very-deep-01/command.json`; the full commit is resolved below rather
than inferred from a short revision. The executed host command was:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-1/very_deep_run.py --runtime evidence/independent-verifier/stage-1/candidate-6/baseline-01 --out evidence/independent-verifier/stage-1/candidate-6/very-deep-01
```

The driver uses an already running own clean exact-candidate source and independent
peer plus a separate constrained stdlib client. Run the named baseline driver
with a new unique output, `--execute --keep-running --run-probes`, before the
raw boundary driver; the own extra driver records subsequent cleanup. The raw
nonsecret create/reset bodies, request digests, byte sizes, statuses, error bodies,
timings and controls are in `very-deep-01/probes.json`. Synthetic credentials,
authorization values and full captured exports remain in memory. The failed
runtime image is `sha256:fe6eb3f8a4679a7d6078947df9a8208caad9fc1e04386e1781845731a4ee94bf`;
`failure-image-proof.json` confirms actual packaged core/server/codec hashes
match the named candidate. Source review identifies the shared json.loads
boundary and its RecursionError-to400 mapping; no production code was changed.

The final coverage matrix has **2657 normative rows:2638 verified,15 failed,
4 unverified**, plus22 non-normative fixture-ID admission diagnostics. The15
failed rows are ten sampled boundary cases and five affected general/endpoint
unknown-field obligations. The four unverified dependent deep alias/transfer
paths require a successful depth10000/20000 receipt that this candidate never
issued. Ordinary fallback receipts and their import/replay are not presented as
successful deep receipts. All2603 previously prepared normative rows were
freshly executed or audited for this full candidate. No historical passing row
or builder assertion total is reused as current proof. All22 ID fixtures were
admitted; the308 conditional usability obligations passed with reserved and
Unicode IDs through encoded routes, exact query/body identity and replacement.

Current independent HTTP probe totals are **4284 requests,3644 assertions,
11 raw failed expectations**. Ten are established service failures. One is a
preserved obsolete private-envelope equality expectation: original schema1
versus adopted schema2 with receipt profiles. It is excluded from normative
failure assessment with source rationale, and the fresh corrected genuine-source
run passes25/25. Original bytes/results remain unchanged. Startup health calls,
source/image diagnostic execution and official-check requests are outside these
HTTP client totals.

| Independent run | HTTP requests | Assertions | Raw failures | Seconds |
|---|---:|---:|---:|---:|
| baseline-probes | 1485 | 1497 | 0 | 7.652050 |
| baseline-original-minimal | 4 | 9 | 0 | 0.015889 |
| baseline-calendar-minimal | 8 | 12 | 0 | 0.102045 |
| baseline-race50 | 55 | 11 | 0 | 0.118162 |
| baseline-legacy | 26 | 24 | 1 | 0.238512 |
| baseline-decimal | 196 | 124 | 0 | 1.194089 |
| large-minutes | 39 | 26 | 0 | 0.170066 |
| semantic | 631 | 481 | 0 | 4.206167 |
| opaque-ids | 374 | 308 | 0 | 1.061642 |
| nesting | 516 | 484 | 0 | 2.454829 |
| snapshot | 810 | 531 | 0 | 4.773692 |
| numeric | 30 | 27 | 0 | 0.128278 |
| fractional | 38 | 35 | 0 | 0.073987 |
| legacy-current | 26 | 25 | 0 | 0.195540 |
| very-deep | 46 | 50 | 10 | 0.176682 |

Fresh official isolated Stage1: **120 collected,120 passed,0 failed/errors/skipped/
deselected/xfailed**. Stage2 overshoot is separate: **25 collected,0 passed,
1 failed,24 not executed**,0 errors/skips/deselections/xfailed. Official wall
interval is 30.633702seconds. The clean Stage1 folder claims1 on shipped checks;
that directional public result does not override this independent rejection.
Earlier-stage regression: none applies. Kickoff is unchanged and clean at
`803560d2a678ace1414465c098eb0ab5380ffade`; no suite selection/modification occurred.
The original unique official output remains in final-checks and is copied under
`official/` for fresh-clone review.

Fresh constrained single-image builds ran from clean detached clones. Default8080
and override18309 cross-container health took 0.394412seconds and 0.372427seconds
from docker-run start. Own service processes had inspected2CPU/2GiB, no mounts
and internal offline networks or network-none. Current and genuine old source
core/server identities matched, and actual current packaged codec identities
were checked. Available build cache was reused; no uncached-build claim is made.
All 29 recorded own service/client/network cleanup commands exited0, and a
final verifier-namespace container inventory is empty. Images and clean clones
remain. No other seat's resource was stopped or changed.

Fresh evidence includes50-client identical/competing races, seeded160-operation
occupancy trace, half-open boundaries, owner privacy, cutoff/no-op/move ordering,
atomic rollback, both required DST zones, calendar endpoints, and exact giant
numeric/query values. The semantic suite issues genuine sessions, references,
create/move receipts from an unmodified separately running old source, imports
unchanged HTTP exports, adds exact current receipts and transfers mixed origins
through two more independent destinations. Historical offset-seconds strings and
original public receipts remain unchanged. Missing/wrong/null/unknown receipt
profiles reject atomically. No historical state or receipt is fabricated.

The nesting suite freshly verifies objects/arrays/alternating wrappers through
1101. Snapshot tests use three independently scheduled capture modes and four
waves each:36 export/list/availability captures overlap atomic8-member writes,
with each of12 raw export captures forwarded unchanged into two independent
replacement destinations. An independently derived generation/prefix oracle
checks public records, original create/move receipts and absent future keys.
Read-side and client gate events are recorded; internal serializer timing is
unobserved and not claimed. Source confirms copies remain inside the RLock.

The complete source, packaging, initial handoffs, declarations, empty intake,
authored path history and adopted decisions were freshly reviewed in
`source-audit.json`/`source-inputs/`. Both builders have substantive committed
production work. No builder test/oracle implementation or external domain code
was read. The genuine shared-index attribution deviation182582c, verifier seals
and Interface correction remain explicit; content authorship is not relabelled
as Git author or another seat's execution.

`REVIEW_CORRECTIONS.md` preserves the own unsupported END-in-file assertion,
initial source-snapshot naming collision, evidence-reader digit-limit error,
obsolete private-envelope expectation and current failed-key control reassessment.
None is relabelled as a service pass. All actual high-depth refusals stay failed.

Historical timestamps follow the recorded exact-instant/nearest representable
minute-offset interpretation, with original wall fields and immutable old
strings retained. Literal historic IANA subminute wire offsets and minute-only
RFC3339 grammar are not claimed simultaneously. Finite numeric/depth examples
do not prove arbitrary-payload performance. Exact instantaneous clock boundaries
use labelled source supplements; no unpublished clock API or clock-controlled
HTTP observation is invented. Hidden judging results, full genuine room export,
publication and submission remain operator-controlled.

Measured check-execution window: 535.998743seconds from 2026-10-04T04:23:17.580657+00:00 to 2026-10-04T04:32:13.579400+00:00.
The earlier intake/acknowledgement marker is approximate; the recorded whole
review interval is about 774.7seconds, explicitly not an exact measurement.
Whole factory elapsed is coordinator-owned. HarnessCodex/configured gpt-6.1-sol;
actual model override, effort, token usage, catalog-estimated and billed spend
are **unknown**. A new complete named repair handoff and independent rerun are
required before acceptance.
