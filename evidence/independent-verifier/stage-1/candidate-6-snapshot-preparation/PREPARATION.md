# Export/read snapshot concurrency preparation

The source note `22b8029c-5250-46dc-8b1f-1e5c74f4d46d` is incorporated into
the existing complete candidate-6 preparation/card 12. This supplement adds
**531 normative bounded-schedule obligations**. The cumulative prospective
matrix has **2,603 normative rows plus 22 separate nonnormative ID-admission
diagnostics: 2,625 records**. Every candidate row remains unverified.

Local validation passes **59 independent observable-state oracle and schedule
checks**, and five Python files parse with AST. The full-candidate handoff guard
refuses before Docker or output creation. **Zero HTTP requests, official checks,
image builds, service containers or networks were executed or created.** No
service defect, race reproduction or acceptance follows this preparation.

## Source and state oracle

Stage 1 §10 requires an atomic read-only export and unchanged independent-process
replacement, preserving tokens, identities, timestamps and completed request
bodies/original receipts. Subsequent source writes cannot change the snapshot.
Sections 1/8/11 require coherent half-open occupancy and all-or-nothing moves;
§7 requires original receipt replay without mutation. These are observable
requirements, not a requirement to use a particular lock or serializer.

The independent oracle uses eight real bookings on eight tables. Each successful
atomic move cycles all table assignments and sets every party size to generation
number plus two. The resulting public record set has one unique legal generation.
Every imported identity, creation/start/end timestamp and status must retain its
actual original value. A mixed generation, duplicate/missing reference, changed
identity or occupancy mismatch is rejected by the local oracle. List order is not
invented for equal start instants. An independent minutes/half-open oracle derives
the expected availability and fixture table order.

Synthetic public records exist only in local oracle self-checks. They are never
submitted as exported state or used to manufacture service observations. Actual
future probes obtain every token/reference/create/move receipt from real HTTP.
The private state stays opaque: coherence is checked by unchanged raw import,
public authenticated records and real receipt behavior, not assumed private keys.

## Deterministic schedule and response lifetime

Seed **20261004** fixes route launch orders. Each of three modes runs four waves
with three sequential successful eight-record moves per wave. Export, private
reservation list and public availability reads are captured on separate sockets:

- `send-barrier`: all GET requests are sent before writer and receive gates open.
- `first-byte-held`: each response's headers and first body byte arrive before
  writers start; body reception resumes after the first completed move response.
- `send-held`: GET requests are sent, writes run, then response reception resumes.

The plan has **36 read captures, including 12 exports**, each export replaced
unchanged into **two independent destinations**. Successful receipt bodies carry
16,384 bytes of valid ignored padding to exercise nontrivial response encoding
and transmission. Actual whole request/export size, timing and achieved overlap
remain unobserved until execution. The client sets only its own socket receive
buffer, not host/system/Docker/network settings.

The future event trace records request send, first byte, receive release, each
completed write response and capture completion using a monotonic clock. It also
records the saved seed/release policy, exact actual operation body/hash and every
status/response hash. Release policy and operation identities are deterministic;
OS scheduling and timings are observations, not promised repeatable values.

Client gates keep requests alive across writes and assess the **complete emitted
HTTP response**, beyond dispatch/lock acquisition. They do not expose when
Engine.request returns or exactly when the server encodes a value. No internal
serializer overlap is inferred from an in-flight socket alone. A bounded pass is
evidence for the observed schedules, never proof of all possible interleavings.

Deliberately held receive times are separately recorded and excluded from a
server latency claim. Unheld ordinary/control requests retain 5/10-second checks.
Capture framing, status, complete JSON syntax and actual full durations are
recorded. Schedule/runner exceptions stay distinct from actual HTTP failures.

## Capture replacement and receipt coherence

For each export the destination first issues its own session and booking. The
unchanged raw source bytes then replace that destination. Source tokens and all
eight records must survive; the old destination session and record must disappear.
The observed generation must lie inside that wave's permissible linearization
interval and agree across all records.

Every original create receipt and every move receipt through the captured
generation must replay200 with its actual archived response. Later moves already
completed on the source must be absent from the captured retry history: their
used keys with changed invalid bodies give422 on the destination, rather than
409 for an already saved receipt. A never-written key provides a fresh control
even when the capture lands on the wave's last generation. Thus both lagging and
premature receipt snapshots can be detected without editing the opaque export.

Replays/refusals must leave the entire imported snapshot unchanged. Repeating
the same raw import restores it without duplicates. The destination's parsed
export must equal the actual captured source snapshot after later source writes.
Exports stay only in client memory; evidence saves fingerprints/byte counts,
captured generation and the number of checked original/prefix/future keys.

## Runtime and commands

Actual local preparation command from the result repository:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-1/snapshot_prepare.py
```

Only after the explicit complete final named candidate and both complete builder
handoffs, use semantic_runtime.py's required repo/workspace/full-candidate/handoff
and new unique output arguments, adding `--probe-family snapshot`. This family
builds the complete named Stage 1 tree from a clean detached clone, starts three
matching current processes and checks source/image hashes. Default8080 and
override ports18335/18337 use own host mappings18336/18335/18337. Each service
has 2CPU/2GiB, an internal offline network and no mounts. Both destinations are
independent processes. Every command/startup/resource observation and own-only
cleanup is retained. These are planned conditions, not executed runtime claims.

The initial unsealed local draft had507 rows;24 prospective checks for absent
later move keys were added before candidate execution. No failed observation or
previous sealed matrix was rewritten. Old numeric, opaque-ID and nesting
preparation directories and all prior verdicts remain unchanged. The source-proof
records current own code hashes; no product, builder probe/oracle or official test
source was imported, copied or read for this supplement. The scope is owned
evidence only.

Highest consecutive accepted stage remains **0**. Card12 stays in progress for
the full named review; Stage2 remains frozen. Historical timestamp, immutable
original response and exact-new/receipt-scoped legacy numeric interpretations
remain applicable. No arbitrary payload, concurrency or interleaving performance
claim is made. HarnessCodex; configuredgpt-6.1-sol; actual override/effort/usage,
catalog-estimated cost and billed spend unknown. Whole factory elapsed is
coordinator-owned; preparation-seal.json records only this supplement's time.
