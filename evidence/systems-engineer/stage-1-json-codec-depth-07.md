# Exact JSON codec: nested traversal correction

Current module revision: `c2fcedc853e0fe33e96f9d3f39c0c807b4e08d9f`.
Preserved pre-repair evidence: `c061c7a9f1cc4fde6ffdd34b2e75bab1fb02a633`.
This supersedes module `00940d4777c316c1369e744109885d58c85373ec` for final image
source checks. Earlier module reports, successful numeric checks and actual
nested failures remain unchanged. This is still an **unpromoted module step**,
not a repaired HTTP candidate or acceptance.

Coordinator message `967c90be-6337-455c-aea6-3c9b209b6b99` requested independently
derived depth-1100 unknown-field diagnostics within complete JSON-REPAIR-1 and
authorized an owned module correction if necessary. Only `stage-1/json_codec.py`
and Systems evidence were edited. Core and Stage 2 remain held; Interface owns
its separately released adapter/runtime paths.

## Actual failure and repair

The pre-repair codec recursively validated, encoded and compared complete trees.
Valid object/array/alternating wrappers around an independently checked finite
JSON leaf failed at ordinary modest depths. Run 01 had 60 assertions, 3 passed,
57 failed; run 02 isolated decoding and had 90 assertions, 18 passed, 72 failed.
Both raw runs and payloads remain in separate `systems-engineer-json-depth-before-*`
folders. The full explanation is `stage-1-json-depth-before.md`.

The initial composed parse/round-trip check did not isolate parsing. All 15
decoder-only observations through depth 1600 passed; separate valid arrays at
2500/3000 also decoded. The earlier interim reference to parsing as a failed
boundary is explicitly corrected. No decoder failure was observed or invented;
the standard JSON decoder is retained.

Tree validation, encoding and equality now use explicit stacks. Validation
tracks active ancestors, refusing cycles while permitting repeated acyclic
subtrees. Encoding retains dict insertion order, array order, compact punctuation,
ASCII string escapes and exact numeric tokens. Equality retains complete object
mapping semantics, ordered arrays and the exact/legacy leaf rules without Python
recursion. No traversal depth ceiling or recursion-limit change was introduced.

Public API remains identical: `JsonCodecError(ValueError)`,
`loads(bytes | str) -> tree`, `dumps(tree) -> UTF-8 bytes`,
`validate_json(tree) -> None`, keyword-only
`same_value(left, right, *, profile='exact-v1') -> bool`, with `exact-v1` and
`python-json-v1`. Numeric helper names and source-profile behavior are unchanged.
No adapter change is required for this correction.

## Executed checks

Commands from the result repository:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-depth-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-depth-after-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-depth-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-depth-after-02
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-codec-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-codec-host-03
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-codec-run.py --revision c2fcedc853e0fe33e96f9d3f39c0c807b4e08d9f --depth --out evidence/systems-engineer/systems-engineer-json-codec-container-02
```

| Run | Assertions | Passed | Failed | Probe seconds |
|---|---:|---:|---:|---:|
| Repaired host depth 01 | 90 | 90 | 0 | 0.122367875 |
| Expanded host depth 02 | 155 | 155 | 0 | 0.142695334 |
| Host numeric regression 03 | 1442 | 1442 | 0 | 0.006317709 |
| Committed image numeric regression | 1442 | 1442 | 0 | 0.007052667 |
| Same committed image depth process | 155 | 155 | 0 | 0.159239459 |

Depth cases cover wrappers at 750, 1000, 1100, 1200 and 1600. At 1100 the valid
payloads are 2242, 7192 and 12142 UTF-8 bytes; the maximum saved payload is 17642
bytes. Grammar follows composition of valid wrappers around a shallow leaf
independently decoded with Decimal. The tests include deep round-trip/equality,
changed values, numeric aliases, missing closing tails, nested empty containers,
repeated subtrees and mapping cycles. The recursion limit stays 1000. Numeric
regressions retain seed 20261004, 180 saved pairs and 50 parallel codec tasks.
These are own module assertions, not HTTP operations or normative row counts.
No peer probe implementation was read/copied.

The complete committed-image driver took **1.540007750 s**. Both independent
diagnostic processes ran as 65532:65532 with network none, 2 CPU/2 GiB and no mounts.
Both probe exits and both cleanup commands were 0. Image and packaged module/probe
bytes match the exact committed blobs. The temporary context was removed and
the image retained; no other seat's process was changed. Build cache was available.
Three Python syntax checks, owned whitespace checks and the frozen core/Stage 2
diff also passed.

## Identity and artifacts

Module SHA-256:
`771cd5c2ccd4e11bb74808998de65605845576d0bc6172fb2d428421bc83895c`.
Image ID:
`sha256:bd04bd492ef297bbdc95904299d6aa5fc5c81583cfe0bd30af083e468f8e7447`.
Exact tag, all source hashes, executed argv, timings, source copies, image/container
inspections and cleanup are in
`evidence/systems-engineer/systems-engineer-json-codec-container-02/runtime.json`.
Raw diagnostic payloads are synthetic and contain no token, credential, hash or
exported service state.

## Remaining work and limits

The final adapter/image source checks must use this module revision. Its public
API is stable while Interface completes its own integration. Core remains held
until the coordinator's explicit release. Real deeply nested create/move full-body
receipts, snapshot copying, mixed historical profiles, export/import and replacement
remain mandatory pending core work, with their own HTTP evidence. The pending
private integration task now records that requirement. No real HTTP nested failure
or passing service result is claimed by these diagnostics.

`to_integer` still requires a bounded operational need; ignored compact values
must not be expanded. The standard decoder is verified at the measured depths,
not claimed to support arbitrary-size/depth resource workloads. Full service
regression, independent exact-candidate review and official isolated acceptance
remain pending. Highest accepted stage is 0. Original timestamp/receipt-string
interpretations and withdrawn verdicts remain unchanged. Harness Codex, configured
gpt-6.1-sol; actual override, effort, usage and estimated/billed spend unknown.
