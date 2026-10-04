# Bounded nested JSON preparation

Source suggestion `1f3176df-4062-4575-b9e6-59f502357d31` is incorporated under the
complete candidate-6 preparation assignment and shared card 12. The supplement
adds **412 normative sample obligations**. The cumulative prospective view now
has **2,072 normative rows and 22 separate ID-admission diagnostics: 2,094 records**.
All remain unverified for the pending final candidate. Previous preparation
snapshots, candidate rejections and actual service observations remain unchanged.

No service or official check was executed. No image, container or network was
created. Five Python files parse with AST. **60 local input checks pass: 48 valid
generated values and 12 expected truncated-JSON refusals.** The pending handoff
guard still refuses before Docker or output creation. These are preparation and
client grammar checks, not service or resource-performance evidence.

## Source applicability

Stage 1 §3.4 says unknown request fields are ignored, never an error. Section 5
distinguishes unparseable JSON/wrong types from valid field values and prohibits
5xx responses. Section 7 uses the complete parsed JSON value for retry identity,
including otherwise ignored fields, before endpoint/current-resource checks.
Successful receipt replays stay original after later changes. Section 10 requires
an unchanged opaque export and successful parsed request bodies/original responses
to survive atomic independent-process replacement. Section 11 applies the same
receipt and ignored-field rules to reservation moves.

No nesting ceiling is published in those requirements. The source-derived tests
therefore submit independently validated finite nested JSON of modest byte size
in ignored fields and check the existing behavior. An implementation or language
recursion limit is not itself a new source rule. At the same time the service has
explicit CPU, memory and request-duration limits: actual candidate observations
must be measured and classified before a verdict. This preparation establishes
no failure, performance guarantee or ability to process arbitrary depth.

## Inputs and independent client

Wrapper depths are **32, 999, 1,100 and 1,101**, each with object, array and
alternating-object/array chains. The small leaf contains a precise finite decimal,
signed zero, ordered number/bool/string elements and text containing escaped
quotes, slashes, brackets and Unicode. Its containers add two levels, so the
largest generated value has container depth **1,103** and **10,028 bytes**.
These are ignored-value sizes; the future actual complete request and opaque
export byte counts remain unobserved. A moves body uses copies in both the outer
ignored field and a move item's ignored field.

The generator constructs the in-memory chain iteratively. A separate raw-string
builder creates opening wrappers, the small encoded leaf and closing wrappers
without using the deep tree encoder. The independent client parser validates
each complete literal. An iterative chain inspection checks every expected
container/key/list shape and exact leaf; an iterative depth walk measures nesting.
Exact numeric and object-order aliases must compare equal, while changed precise
numbers and number-to-boolean changes must remain distinct. Truncation removes a
required closing delimiter and must be refused as malformed JSON. Raw original
ignored literals are preserved under raw-ignored-values/ with no credentials or
exported fixture state.

Only the **separate evidence interpreter** uses recursion limit 20,000 so its
existing own JSON oracle/trace serialization can inspect these bounded samples.
The source service has a different process/interpreter, receives only HTTP and
is never configured by this client. No host/system/Docker/network setting is
changed. The generator, grammar check and value oracle are independent verifier
code; no product, builder test, builder oracle or shipped checker is imported.

## Prepared real-service protocol

Each scenario performs reset, signup and seeded login with ignored deep values.
Real create and move requests then test first201, exact alias200/original response,
changed-number and changed-type409, missing auth/key precedence, fractional party
422, failed-key reuse, full-state immutability around refusals and original
responses after successful correction/cancellation. An ignored deep PATCH is
checked as an unchanged-state operation. A malformed truncated body must still
give400 and leave state unchanged.

The real service must produce its own export after those successful writes; the
client forwards its **unchanged raw HTTP bytes** to an independently running
destination. It checks the entire parsed snapshot, the real source token/current
private records, original deep create and move replays, and changed deep leaf
conflicts after import. Nothing is reconstructed from fixture data or simulated
responses. Export bytes and observed export depth are recorded as metrics while
the credential-bearing export stays in memory. Export depth is not a normative
predicate: private state is opaque, and receipt preservation is assessed through
actual imported original/changed retries. HTTP trace metadata records
actual request bytes/hashes, status, response framing and each request duration.

The guarded runtime adds --probe-family nesting. That family starts two current
processes from a fresh detached complete named candidate clone, default8080 and
override18335 with own host ports18336/18335. Each has 2 CPU, 2 GiB, internal
offline networking and no service mounts. Cross-container health, complete source
and image hashes, every command, timing and cleanup are recorded. The client has
its own constrained image. No resource result is claimed until that driver is
actually executed against the complete named candidate.

## Commands and evidence

Actual preparation command from the result repository:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-1/nesting_prepare.py
```

Only after the explicit complete final candidate and both complete builder
handoffs, use the same required repo/workspace/candidate/handoff/new-output
arguments to semantic_runtime.py as the preceding preparation, adding:

```sh
--probe-family nesting
```

nesting_input.py, nesting_requirements.py, nesting_probe.py, nesting_prepare.py
and Nesting.Probe.Dockerfile are new own evidence files. semantic_runtime.py adds
the guarded family without altering graded service files. Source-proof.json
binds current source hashes; earlier hashes remain historical snapshots at their
named commits. input-grammar-validation.json and preparation-summary.json contain
the actual local checks. coverage-prepared.csv has the 412 new rows;
coverage-cumulative-prepared.csv retains the 22 ID-admission diagnostics as
explicitly nonnormative. Diagnostics are not added to a normative failure/pass
count. Preparation-seal.json records measured supplement wall time and the
scoped private-artifact inspection.

Highest accepted consecutive stage remains **0**. Stage 2 remains frozen. Full
source/coverage/startup/official/regression execution still awaits the complete
named final handoff. Historical timestamp/original-response/exact-new-and-legacy
numeric interpretations remain disclosed. Neither this finite sample plan nor a
future bounded pass can establish arbitrary-depth or arbitrary-payload performance.

Harness Codex; configured model gpt-6.1-sol. Actual model override, effort, usage,
catalog estimate and billed spend are unknown. Whole factory elapsed remains
coordinator-owned. This preparation is not a repaired-candidate verdict.
