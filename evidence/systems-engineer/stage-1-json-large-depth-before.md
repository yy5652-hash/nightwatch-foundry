# Frozen Stage 1 candidate 6: observed decoder boundary

The bounded continuation in message `cf8d9d1e-0a8a-4430-a5b8-4716177f8174` found an actual decoder refusal beyond the previously measured depths. This is an owning-builder finding, not an independent verdict. Highest consecutive accepted stage remains **0**. All six Stage 1 production files and all Stage 2 source remain unchanged under coordinator freeze message `e441e637-b5c9-43da-bad2-500897f4dd4a`.

Frozen full candidate: `ab0cf79767b6768153a73894bf5768bf3328491a`. Stage 1 tree: `d2905df39546a619afbad3547b10205bb6c01610`. Its production source is identical to the previously built/tested full revision `4a92f3e7fcf009edc34f7c410a44ae405909e080`, with Systems implementation `debff0bbf2625936d30e1e11066b966a46320137`. The retained exact complete-service image is `sha256:e84435e7048666224b36d3d8784d0e5c8545cbe9168def24876caa18a0646ae3`. This continuation reuses that image and verifies its actual source hashes; it does not claim a new build or independent acceptance.

## Distinguishing the observed boundaries

The isolated probe composes a valid finite-number/boolean object leaf inside exactly balanced arrays or objects. It constructs the corresponding in-memory tree iteratively for direct-operation controls. It never needs a deep reference decoder to establish the wrapper grammar. Per-process input bytes, exact hashes, source hash, exit state, timings, maximum RSS and assertion results are saved.

At 10,000 and 20,000 wrappers in both shapes, **all eight decoder and serialization-round-trip processes fail** with `JsonCodecError`. All **16 direct validation, exact equality, encoding and copying processes pass**. Totals: 24 isolated processes, 16 passing processes, eight failed processes; 36 assertions, 28 passed, eight failed. Full driver time is 7.266341208 s. Inputs are 20,056 / 40,056 bytes for arrays and 110,056 / 220,056 bytes for objects. Maximum measured operation time is 0.047545833 s; maximum RSS is 31,968 Linux KiB. Every process has 2 CPU, 2 GiB, network none and no mounts. All 24 cleanup commands return zero. No process is OOM-killed or crashes without a diagnostic result.

A separate 10,000-array decoder process captures the exception cause: `RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string`. Its one assertion fails, process exit is 1, maximum RSS is 23,804 KiB and cleanup returns zero. Driver time is 0.326791583 s; operation time is 0.000498000 s. The unchanged interpreter recursion limit is 1,000, and the packaged interpreter reports Python 3.12.15. No interpreter configuration was changed by these diagnostics.

These new observations do not alter the earlier report `c061c7a9f1cc4fde6ffdd34b2e75bab1fb02a633`: its isolated decoder controls passed at their measured depths, and its failures were recursive traversal/equality/encoding. The later host decoder checks through 5,000 wrappers also retain their original scope. A successful smaller-depth check does not prove this larger boundary.

Current `copy_json` is already an explicit-stack mutable-container copy, **not a serialization round trip**. At both larger depths, the copy probe checks that every wrapper and leaf is detached, emitted bytes match independently composed valid input, and mutating the copy does not change the original numeric leaf. Those four copy processes and their 12 assertions pass. The decoder refusal must not be attributed to copying, direct encoding, equality, resource exhaustion or a client runner.

## Real HTTP and unchanged raw export transfer

Two independent matching-image service processes and a separate standard-library wire client run with 2 CPU / 2 GiB each, no mounts, on an inspected internal offline network. Ports are 18161 and 18162. The client imports no service implementation and composes requests directly from valid shallow objects plus balanced wrapper bytes. It parses only shallow authentication, booking, move, lookup, error and health responses. It retains export bytes in memory and passes those bytes directly to the other service's import endpoint. Export bytes and live tokens/password hashes are never saved in these artifacts.

The single run executes **110 HTTP requests and 111 assertions: 103 passed, eight failed**, in 0.454679291 s. The full start/probe/source-inspection/cleanup driver takes 1.796036750 s. Maximum request time is 0.028116000 s. Measured start-to-health/source inspection is 0.387762167 s and 0.309572125 s. Both service processes remain running and healthy after all requests; neither is OOM-killed. Three own containers and one own network are removed with all four cleanup codes zero.

| Wrapper control | Create | Atomic moves | Captured raw export |
| --- | --- | --- | --- |
| 1,100 arrays | 201 | 201 | 6,888 bytes, contains both real deep request receipts |
| 1,100 objects | 201 | 201 | 15,690 bytes, contains both real deep request receipts |
| 10,000 arrays | 400 malformed_request | 400 malformed_request | Deep receipt flow blocked; shallow failed-key-reuse control only |
| 10,000 objects | 400 malformed_request | 400 malformed_request | Deep receipt flow blocked; shallow failed-key-reuse control only |
| 20,000 arrays | 400 malformed_request | 400 malformed_request | Deep receipt flow blocked; shallow failed-key-reuse control only |
| 20,000 objects | 400 malformed_request | 400 malformed_request | Deep receipt flow blocked; shallow failed-key-reuse control only |

The larger HTTP wrapper values contain 20,045–120,045 bytes before the ordinary booking envelope. All eight failed HTTP assertions expect 201 for a valid create or move with only an ignored field added; observed error message is `Body must be a JSON object`. Stage 1 §3.4 says unknown body fields are ignored, never an error; §§5/7 distinguish unparseable bodies and preserve parsed-body retry identity. There is no published nesting ceiling. The independently composed finite leaf and balanced wrappers are valid JSON, so an implementation recursion limit does not make these requests malformed. No 5xx or state/receipt copying defect is asserted by this run.

For each successful 1,100-wrapper control, the source issues a real token/reference/create receipt/move receipt. The client captures the actual HTTP export, then cancels the source reservation. It forwards the captured bytes unchanged into the other process, checks the imported token/reference and earlier confirmed assignment, and replays the original raw create/move bodies and keys in both processes. All original shallow public responses survive exactly as JSON values, including after cancellation in the destination. This is a real state transfer, not fixture reconstruction or a manufactured export.

For the larger refused writes, the same failed keys are successfully reused with shallow valid bodies, followed by analogous raw transfer and replay controls. Their exports are shallow and **do not prove larger-depth receipt/import handling**. Four deeper export/replay flows remain unverified because the initial valid create and move never succeeded. The saved cases explicitly record those blocked paths. Six trace-level export/import checks verify matching byte counts and SHA-256 values and `decoded: false` for each export; a client decoder limit cannot explain the observed server refusals.

## Commands and artifacts

From the absolute result repository, the exact commands are:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-large-depth-codec-run.py --image sha256:e84435e7048666224b36d3d8784d0e5c8545cbe9168def24876caa18a0646ae3 --candidate 4a92f3e7fcf009edc34f7c410a44ae405909e080 --out evidence/systems-engineer/systems-engineer-json-large-depth-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-large-depth-codec-run.py --image sha256:e84435e7048666224b36d3d8784d0e5c8545cbe9168def24876caa18a0646ae3 --candidate 4a92f3e7fcf009edc34f7c410a44ae405909e080 --out evidence/systems-engineer/systems-engineer-json-large-depth-cause-01 --depths 10000 --shapes array --operations decoder
../../.venv/bin/python -B evidence/systems-engineer/stage-1-large-depth-http-run.py --image sha256:e84435e7048666224b36d3d8784d0e5c8545cbe9168def24876caa18a0646ae3 --candidate ab0cf79767b6768153a73894bf5768bf3328491a --out evidence/systems-engineer/systems-engineer-json-large-depth-http-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-large-depth-evidence-audit.py
```

The first three commands return 1 for their preserved actual diagnostic failures, with no runner exception. Reproduction requires new unique output directories; no earlier output is replaced. Drivers preserve every executed Docker/Git argv, log, timing, source/resource identity, process state and cleanup. Each folder contains the exact executed probe/client source, so later evidence-source changes cannot rewrite the original observations. The cause-control source additionally captures `__cause__`; the original 24-process source remains separate.

Actual image/source hashes in both HTTP services match:

| File | SHA-256 |
| --- | --- |
| core.py | 2653bdc010129f91b33480ece36d43f30a81d8b6c214764745c9c0f722f4a84f |
| json_codec.py | ef81525f0611dab743b5858c98961f3871996df7dfdd4417830702028a124aad |
| server.py | fb8d9e41eb13c3a736d49573903253a6cb98284790cf5edc9caeb352f0e0946c |

The complete source files and earlier build/clean-clone identity remain bound by `stage-1-json-core-handoff-08.md`. This report adds evidence only. No new official harness run or coverage-row count is claimed. The prior passing diagnostics remain their measured observations; they cannot erase the new decoder failure or establish acceptance.

## Repair implication and remaining gate

The coherent repair would remove recursive container decoding while retaining the agreed bytes API, exact scalar-number representation, strict UTF-8/JSON grammar/constants, numeric provenance and receipt semantics. An explicit-stack container parser using standard-library JSON string scanning and exact scalar handling is one prospective approach. Raising a recursion limit or imposing a new nesting ceiling would not satisfy the source requirement. Any implementation must test malformed grammar, numeric fidelity, old/mixed receipts and raw cross-process export transfer at the observed depths, followed by applicable inherited regressions.

No implementation is applied under the current independent-review freeze. Coordinator must route the observed evidence through its source-repair sequence; independent acceptance remains pending. Historical exact-instant/minute-offset and immutable older receipt-string interpretations remain disclosed. These small measured payloads do not prove arbitrary-depth or arbitrary-size performance. Harness Codex, configured model gpt-6.1-sol; actual model override, effort, token usage, estimated cost and billed spend are unknown. Whole-factory elapsed time is coordinator-owned.
