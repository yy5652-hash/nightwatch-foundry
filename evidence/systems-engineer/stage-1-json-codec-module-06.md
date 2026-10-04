# Exact JSON codec: module-only handoff

Implementation revision: `00940d4777c316c1369e744109885d58c85373ec`.
Package: `TK-20261004-S1-systems-engineer-JSON-REPAIR-1`, source release
`1789cad6-7d95-40f2-a33a-926f30ed2002`, shared card 10.
This is the released standalone module step, **not a complete repaired HTTP
candidate or an acceptance claim**. Highest independently accepted stage is 0.

Only graded change: `stage-1/json_codec.py`. Own diagnostics, driver, synthetic
traces and append-only design evidence are outside the graded folders. Core,
Interface's four existing Stage 1 runtime files and the entire Stage 2 tree
remain byte-identical to rejected candidate `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250`.
No core import or adapter/image wiring is included in this commit.

## Committed callable contract

| Callable | Result and boundary |
|---|---|
| `JsonCodecError(ValueError)` | Codec syntax/tree/profile error; no HTTP mapping |
| `loads(bytes \| str)` | Strict UTF-8/JSON exact tree; integer-token native ints and immutable decimal/exponent `JsonNumber` leaves |
| `dumps(tree)` | Compact ASCII-escaped UTF-8 bytes, with finite numeric tokens; use directly for HTTP byte length and write |
| `validate_json(tree)` | None for a valid tree; otherwise `JsonCodecError` |
| `same_value(left, right, *, profile='exact-v1')` | Exact recursive JSON equality; explicit `python-json-v1` for historical receipt comparison |

Core helper names: `is_number`, `number_key`, `is_integral`, `compare_numbers`,
`to_integer`, `multiply_integer`, `EXACT_PROFILE`, `LEGACY_PROFILE`. The constants
are `exact-v1` and `python-json-v1`. Interface needs only the shared codec
functions/error class and should implement no numeric field policy.

Parsing and comparison use normalized sign/coefficient/exponent metadata, with
no Decimal arithmetic context or expansion of compact exponent values. Integer
I/O uses a process-local Python digit-conversion setting; no persistent host
configuration changes. Unknown finite numeric values remain valid. Literal
NaN/Infinity, malformed JSON and invalid UTF-8 fail. Numeric aliases and signed
zeros compare by exact value; booleans and strings remain separate. Arrays retain
order; object mappings include all ignored fields and ignore key order.

The historical profile projects decimal/exponent leaves through the actual old
float semantics and keeps integer-token leaves exact. This preserves ordinary
old rounding, underflow and numeric cross-type equality while a finite incoming
overflow projection conflicts rather than becoming malformed. Original emitted
old numeric values are not expanded to binary ratios. These are module comparison
capabilities; core's required receipt-profile/schema-2 persistence is not wired yet.

## Executed diagnostics

Own separately derived codec probes use independent Decimal/Fraction comparisons
at modest arithmetic bounds, deterministic seed 20261004, 180 saved pairs and
50 parallel codec tasks. They cover 4,301-digit integers and true fractions,
compact huge exponent metadata, exact ignored values, current aliases/type
distinctions, historical projection/integer provenance, encoding, malformed
constants/syntax/UTF-8, deep copies and immutability. No peer test/oracle source
was read or copied. No HTTP request is counted as a codec assertion.

Commands from the result repository:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-codec-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-codec-host-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-codec-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-codec-host-02
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-codec-run.py --revision 00940d4777c316c1369e744109885d58c85373ec --out evidence/systems-engineer/systems-engineer-json-codec-container-01
```

| Run | Assertions | Passed | Failed | Probe seconds |
|---|---:|---:|---:|---:|
| Host 01 | 1,442 | 1,442 | 0 | 0.007475250 |
| Host 02 | 1,442 | 1,442 | 0 | 0.006904583 |
| Committed diagnostic image | 1,442 | 1,442 | 0 | 0.007223375 |

Host 01 used the initial diagnostic script; removing one dead no-op line produced
Host 02's independently saved result. The codec bytes are identical throughout.
The container uses the committed Host 02 probe. The complete container
build/start/probe/copy/cleanup command took **2.991893458 s**. Its maximum measured
parallel task took 0.000039458 s. Three Python AST syntax checks, owned document
whitespace checks and the frozen production-path diff also passed. The failed
document patch attempt did not change files or test observations; the corrected
append is preserved normally in history.

## Source and runtime identity

Module SHA-256:
`913800d80172392e6357b4a9c6d2b5a80d47859779e4b0c7024b5e6e61a71078`.
Probe SHA-256:
`787f9e8fbd423580c3081c6d7d3275f22320791f496fcdf4a693059065156680`.
Diagnostic image tag: `systems-engineer-json-codec:20261004t032958055068`.
Image ID: `sha256:5c53c55a05531c1f557b7d81803c91c74d3f1e9af2c545792f64bb6a31d3291c`.

The driver extracts only the exact committed module/probe blobs into its own
temporary build context. The diagnostic Dockerfile uses
`python:3.12-slim-bookworm` and is outside graded folders. It installs no host
dependency. Build cache was available; no uncached-build claim is made.
The process ran as 65532:65532, network none, 2 CPU, 2 GiB and no mounts. Packaged
module/probe bytes copied from the stopped container match the committed blobs;
image ID matches container inspection. Probe exit and own container cleanup both
returned 0; the own temporary context was removed, image retained. No other seat's
process was inspected, stopped or changed.

Artifacts under `evidence/systems-engineer/systems-engineer-json-codec-container-01/`
include `runtime.json` with every argv/timing/result, image/container inspection,
the diagnostic Dockerfile, packaged source bytes, per-command logs, assertions,
summary and deterministic trace. All numeric fixtures are synthetic; no live
credential, token, password hash or exported service state was produced by this run.

## Next sequence and remaining risk

Interface can wire this committed API and package the module under its coordinator
authorization. Core remains frozen until the subsequent explicit release. In the
unwired intermediate service, the old core still rejects exact numeric leaves;
no HTTP correctness improvement is asserted yet. Private schema 2/per-receipt
profiles, real old-service retries, independent-process replacement and inherited
service regressions remain part of the later complete integration.

`to_integer` materializes an integral value. Future core callers must establish a
bounded need before using it; ignored values and huge duration/grid/cutoff/capacity
comparisons must retain symbolic representation. Modest codec probes do not prove
arbitrary-size or arbitrary-depth resource performance. Historical minute-offset
and immutable old receipt-string interpretations remain unchanged. Independent
exact-candidate review, official isolated checks and full service acceptance remain
pending. Harness Codex; configured gpt-6.1-sol; actual override, effort, token usage,
estimated cost and billed spend are unknown. Scoped command times are not factory
elapsed time.
