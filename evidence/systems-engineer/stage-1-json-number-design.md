# Stage 1 JSON number design — append-only source assessment

## Entry 1: coordinator numeric-value questions

Requested by messages `57734b7a-1f7c-4ef2-a988-67607f0f61ce` and `c0d2f0e9-2e73-48f9-bc58-58f46a8cbff0`. This entry supplies a source-only answer and proposed joint codec boundary. Production remains frozen. It neither authorizes implementation nor changes acceptance. Full Stage 1 specification in the supplied package is authoritative; future stages are outside this assessment.

### Published rules

Stage 1 §3.4 says unknown body fields are ignored and never an error. Section 5 assigns 400 to unparseable bodies or wrong JSON types, and 422 to correct-type invalid values. Its special party-size rule gives 422 even for strings and booleans. Its numeric spelling restriction expressly concerns integer-valued **query parameters**: only plain decimal digits, with `1e9`, `4.0` and `+4` refused regardless of numeric value. Section 8 requires integer party sizes at least one. Section 4 defines grid, duration, cutoff and capacity counts without a language-derived maximum.

Section 7 compares the same JSON value after parsing, ignoring object key order and whitespace. After object parsing and authentication, retry resolution precedes endpoint validation and current-resource checks. Successful retries return the original response and make no changes; failed keys remain reusable. Section 10 requires unchanged exports, original completed bodies/responses, credentials, sessions, identities and timestamps to survive atomic replacement. These are source facts. The text does not state a body integer-token grammar, identify Python classes as JSON types, or specify a decimal codec.

### Interpretation and recommended statuses

My interpretation is value-based body integer validation. Exact numeric `1`, `1.0` and `1e0` all mean one, so they satisfy an integer-valued body field. The existing Python `type(value) is int` rule adds a spelling/class restriction not stated for bodies. This is a recommendation for the coordinator's decision, not an independently accepted behavior of the frozen service.

| Body value in a count field | Recommended party-size result | Recommended base count/capacity result | Reason |
|---|---|---|---|
| Exact positive integer value, including decimal/exponent spelling | Accept subject to endpoint rules | Accept subject to the field's minimum | Number with an integral valid value |
| Finite genuine fraction, including a 4,301-digit integer part plus `.5` | 422 `validation_failed` | 422 `validation_failed` | Correct JSON number type; invalid integral-count value |
| Negative value, or zero where the minimum is one | 422 `validation_failed` | 422 `validation_failed` | Correct type; invalid minimum |
| Boolean or string | 422 `validation_failed` | 400 `malformed_request` | Party-size override; otherwise wrong JSON type |
| Null, array or object | 422 `validation_failed` | 400 `malformed_request` | Same type distinction |
| Literal `NaN`, `Infinity` or `-Infinity` | 400 `malformed_request` | 400 `malformed_request` | Not valid JSON numeric syntax |

Zero is valid for nonnegative cutoff. A missing required field remains 422. The base fractional-count status is an interpretation requiring explicit coordinator resolution; old diagnostics expecting 400 remain historical and must not be relabeled. Magnitude never changes JSON type. No digit or numeric ceiling is recommended. Query grammar stays unchanged and does not inherit the body interpretation.

### Full JSON-value equality and ignored fields

For newly executed receipts, compare numbers by exact mathematical value: `1 == 1.0 == 1e0`; a genuine fraction stays distinct; numeric zero spellings are equal. Booleans remain a separate JSON type (`true != 1`). Strings, null and booleans compare within their types; arrays preserve order; objects compare the same key/value mapping recursively, including nested unknown fields. Unknown fields are ignored by endpoint behavior but remain part of the full retry body, so changing one can cause 409 on a used key.

A valid finite `1e4300` in an unknown field must be representable without binary-float infinity and must not invalidate reset/create. A true large fractional party must reach ordinary field validation. Missing auth, missing keys, different-body used keys and current batch cutoff/cancelled checks retain their existing order. Syntax-invalid constants still fail at parsing, including before authentication. A finite value's overflow in a host float is not a syntax error. No successful key is recorded for a refused write.

### Proposed codec and API boundary

Recommend one shared exact JSON codec and numeric representation used by transport, Engine validation, receipt comparison and export/import. The transport continues to frame/decode UTF-8, require an object and reject invalid constants before calling `Engine.request(method, target, headers, body)`. Engine still owns authentication, validation/error precedence and transactions. Its call signature and response tuple remain unchanged; its JSON tree contract explicitly includes exact numeric leaves.

The codec should retain finite decimal values as an immutable signed coefficient/exponent representation, plus integer-token versus decimal/exponent-token provenance. Ordinary integer tokens can remain Python integers. Normalize numeric value for current equality independently of that provenance. Keep compact exponent forms for ignored numbers; do not expand `1e4300` or larger exponents merely to parse, archive or compare them. Known integer-valued fields can normalize into the engine's integer arithmetic when required, with resource behavior verified rather than adding a hidden bound. Arithmetic on fields must not introduce float rounding.

The same encoder emits exact **numeric JSON tokens** for configuration, detail, receipts and export. It handles exact leaves explicitly alongside strings, booleans, null, objects and arrays. Using `default=str`, replacing public numbers with strings, or routing them through float would violate the intended boundary. Decimal is an alternative implementation only if context/exponent limits and encoding are proved suitable; using it by name does not establish correctness. A coefficient/exponent representation avoids relying on a fixed Decimal context. This recommendation does not assert arbitrary-payload performance.

Systems would own the exact numeric helpers, value predicates/equality and receipt/import semantics; Interface would integrate decoding/encoding into its owned adapter. A subsequent complete joint repair contract must release both paths and specify the packaged helper location. No such helper or adapter edit is made here. JSON serialization must finish before response headers, preserving the existing transport behavior for committed-but-lost responses. Reads and writes remain under the shared engine lock, and import validates all codec/profile state before replacing destination state.

### Genuine old rounded-float receipts

Evidence commit `302e2c00a2e433302d92289cd8172cc3a7325168` contains a genuine old-service HTTP probe, not a fabricated archive. Source revision `49287b4a5a1481f995c470ccae31776f03d4b863` issued actual successful receipts. Its schema-1 export has no parser/numeric profile and only the original six receipt fields. Original ignored decimal `0.100000000000000005` was exported as `0.1`; original ignored `9007199254740993.0` was exported as `9007199254740992.0`. Both original retries return 200 before and after unchanged import into candidate 5. The original decimal precision is irrecoverable. Exact-only historical comparison would refuse those genuine original retries.

Recommend a private persisted **per-receipt source numeric profile**. Imported unmarked genuine old receipts use source parser projection during comparison; newly created receipts use exact value comparison. In the legacy profile, incoming integer tokens remain exact integers, while decimal/exponent tokens undergo the old binary-float projection before recursive comparison. Preserve boolean distinctions and old numeric cross-type equality. This reproduces the observed alias integer `9007199254740992` while keeping integer `9007199254740993` distinct; projecting every number to float would merge the latter incorrectly. Underflow, rounding and overflow must follow the old profile only for matching that historical receipt. A finite token projected to infinity cannot match any saved infinite receipt, because the old service refused non-finite values before saving one; the used different-body key therefore receives 409 rather than global malformed JSON.

The source comparison archive is separate from the immutable original response/body values. Keep the original emitted JSON number `0.1`; never replace it with the decimal expansion of its binary float ratio. Numeric-kind/binary comparison metadata may be private opaque state, but public numbers and archived original JSON values remain numbers. Do not invent the lost original lexeme. Newly exported mixed legacy/exact state must identify each receipt's semantics and preserve them through another import. Current stage, response shape or a global import flag cannot distinguish mixed origins. No enrichment of old successful response schemas is allowed.

This is a narrowly required compatibility interpretation: historic parser equivalences persist for historic successful receipts, while current receipts use exact equality. It needs disclosure and independently executed genuine-source evidence. Existing original-receipt and historical timestamp decisions remain unchanged.

### Evidence, limits and freeze status

Own previous command, from the result repository:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-legacy-number-run.py --out evidence/systems-engineer/systems-engineer-s1-legacy-number-01
```

Observed 16 HTTP operations, 24 assertions, zero failures, 0.061681459 seconds; driver 1.212972709 seconds. Two separately running matching-hash old/current services, each 2 CPU/2 GiB, internal offline network, no service mounts; own cleanup all zero. These totals establish the reported legacy behavior and analytical information-loss comparison, not a new exact production codec. Paths: `stage-1-json-number-decision.md`, `systems-engineer-s1-legacy-number-01/probe.json` and `runtime.json`, adjacent to this document. Exports and tokens stayed in memory. No new HTTP execution is claimed for this append.

Future repair verification must cover exact integer-valued spellings, true fractions and wrong types, complete nested JSON equality, unknown finite values, strict query grammar, invalid constants, key/error precedence, rollback/failed-key reuse and mixed genuine legacy/new exact receipts through two independent-process replacements. Existing calendar/timestamp/occupancy/auth/concurrency behavior must remain intact. Reviewers must independently derive these checks. No broad verifier oracle or probe code was read/copied.

Only this Systems-owned document is added by the current request. Both production trees remain byte-identical to candidate `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250`; highest independently accepted consecutive stage remains 0. This assessment needs a joint scoped release before implementation and independent named review before renewed acceptance. Harness Codex; configured model gpt-6.1-sol; actual runtime override, effort, usage and estimated/billed spend unknown. Factory elapsed is coordinator-owned.
