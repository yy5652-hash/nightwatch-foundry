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

## Entry 2: proposed callable contract for JSON-REPAIR-1

The complete package `TK-20261004-S1-systems-engineer-JSON-REPAIR-1`, parts 1–8 and END marker, was acknowledged before design work in room message `750d1c68-a380-48f8-b822-69c3c9d4b966`. Shared card 10 is in progress. Current room membership was refreshed: Interface is the existing participant responsible for the transport side. The proposal below was sent directly for reciprocal agreement in message `28a09e83-62bd-4074-9bfa-f1397bf4c7c5`. It is proposed until that agreement and the coordinator's numeric interpretation are recorded. Source release is pending; no graded path changes accompany this entry.

### Ownership and callables

Systems owns `stage-1/json_codec.py`. Interface can depend on these module callables after the committed module handoff:

| Callable/type | Contract |
|---|---|
| `JsonCodecError(ValueError)` | Syntax, invalid JSON tree, unsupported value or unknown comparison-profile failure; does not determine an endpoint HTTP status itself |
| `loads(text: str) -> object` | Decode one complete JSON value with exact finite numbers; reject invalid syntax and constants; leave object-only enforcement to the existing adapter |
| `dumps(value: object) -> str` | Encode a valid tree as compact JSON with ASCII escapes and exact numeric tokens; no string fallback, binary rounding or non-finite constants |
| `validate_json(value: object) -> None` | Recursively accept supported JSON leaves/containers or raise `JsonCodecError`; boolean is distinct from number |
| `same_value(left, right, *, profile="exact-v1") -> bool` | Recursive exact JSON value equality for current receipts; explicit `python-json-v1` reproduces old numeric parser comparison only for identified legacy receipts |
| `JsonNumber` | Immutable finite decimal/exponent leaf, retaining exact value and integer-token versus decimal/exponent-token provenance; no implicit float coercion |

These names, return shapes and profile identifiers are the proposed stable interface. Systems' core integration also owns integral-value predicates and normalization, minimum/capacity comparisons and any bounded-use numeric arithmetic. Interface need not access coefficient fields or implement numeric policy. The module must be independent of core, HTTP, authentication and storage, with no import cycle. Standard-library dependencies only are proposed.

`loads` does not reject mathematically finite numbers for overflowing a float or Decimal context. Parsing integer/exponent digit strings must avoid the interpreter's unstated conversion ceiling, preserving the already repaired integer boundary. Decimal/exponent leaves retain compact lexical and coefficient/exponent information rather than an expanded power of ten. Canonical value comparison may normalize zero, leading/trailing coefficient zeros and exponent arithmetic; token provenance remains separate. All zero numeric spellings are equal for the exact profile. Retaining provenance never makes exact aliases unequal.

Tree encoding preserves numerical values and decimal-versus-integer provenance where legacy comparison requires it. Existing finite native floats supplied by old in-memory diagnostics may be handled according to their ordinary emitted JSON decimal spelling; they must not be expanded to their binary rational value. New HTTP decoding creates no such float leaves. Non-finite native floats and unsupported objects are invalid trees. Immutability/deep-copy behavior must preserve leaves in snapshots without leaking state aliases.

### Adapter integration

Interface's adapter keeps existing framing, UTF-8 decoding, body-object enforcement, case-insensitive headers and response-loss handling. Replace only numeric JSON decoding/encoding through the agreed codec. The API boundary remains `Engine.request(method, target, headers, body) -> (status, value)`. Malformed syntax and invalid constants are refused by the adapter with 400 before Engine dispatch. Exact finite trees reach Engine authentication and endpoint ordering. Response encoding finishes before sending status/headers; status 204 still has no payload and no codec invocation is required for its body. Output remains UTF-8 `application/json; charset=utf-8` with byte-accurate Content-Length.

Do not introduce transport-side party/count validation, retry comparison or new body fields. Module `ValueError` inheritance lets the existing adapter's parse error handling remain narrow. Any finite valid JSON token refused by the codec is a codec defect to preserve and repair, not a new input bound. Intermediate module/adapter commits are unpromoted sequence steps; they do not establish full repaired service behavior while old core validation remains unwired.

### Receipt/private-state contract

Propose state schema 2 for new exports while preserving the public envelope `track: tablekeeper`, `format_version: 1`. Import accepts genuine unmodified schema-1 state and new schema-2 state. Each schema-2 receipt carries private `numeric_profile` equal to `exact-v1` or `python-json-v1`; missing/unknown profiles in schema 2 invalidate the state atomically. Schema-1 successful receipts without such metadata are the known old parser family and receive `python-json-v1` during validated import. New successes receive `exact-v1`. This marker is private implementation-defined state, not an API response field or source requirement. The coordinator/Interface agreement must bind the final private format before source integration.

The original six body/response/key identity fields remain preserved. A legacy receipt's numeric leaves retain the numeric-token kind of the actual old export: float exports such as `0.1`, `0.0` and `9007199254740992.0` remain decimal/exponent leaves; exact old integer tokens remain integers. This supplies old stored parser projection without inventing original input spellings or changing emitted JSON values. During legacy matching only, project decimal/exponent leaves to the source float result, retain integer leaves exactly and compare recursively with booleans distinct. Underflow/rounding equivalences remain historical; valid finite overflow cannot match an old successful non-finite leaf and yields normal different-body reuse refusal.

An exported mixed-origin state preserves every receipt profile and leaf provenance through a second import. New requests never inherit a global legacy parsing mode. Retrying a stored receipt returns its untouched archived response, not an enriched current view. Snapshots/current records remain separately validated; invalid profile/body/state replacement leaves destination state intact. Failed keys have no receipt to migrate. Genuine old create **and move** receipts, ignored nested fractions, underflow, higher-precision decimal spelling, integral float spelling and distinct integer/bool/string controls must be exercised on actual unmodified earlier services.

### Core implications and bounded arithmetic

Core will replace its float/int-only portable-value gate and Python-class body integer test with codec value handling under the adopted source interpretation. Retry equality passes the receipt's validated profile. Query grammar remains `[0-9]+`; authentication, idempotency precedence, batch input order/cutoff checks, occupancy and transaction locking do not move.

Compact unknown exponent leaves need no materialization. Known positive integral grid/duration/cutoff/capacity values must preserve exactness; where a value exceeds a bounded opening interval or elapsed cutoff interval, compare it before constructing an endpoint or expanding an unnecessary magnitude. The grid has only this day's bounded candidates; a huge positive step gives the opening candidate when duration fits. No huge-duration timestamp is manufactured. This is a required behavior/design constraint, not a claim that an arbitrary-exponent arithmetic implementation already exists. Numeric value normalization and any internal representation switching must never become a visible maximum.

### Sequence and remaining decisions

After reciprocal committed design agreement and explicit coordinator release, the specified sequence is: Systems commits the codec module without importing it into core; Interface commits image packaging/transport wiring against that exact revision/API; Systems commits core validation/equality/state integration. The final complete image is then built from a clean named context for constrained own HTTP checks. Only that complete candidate can be routed for independent acceptance; no intermediate success restores stage acceptance. Stage 2 remains untouched.

Outstanding before source edits: reciprocal Interface agreement on callable signatures/error boundary/profile encoding, coordinator adoption of integer-valued body/fractional-base statuses, and explicit source release. Own previous legacy evidence is retained at commit `302e2c00a2e433302d92289cd8172cc3a7325168`. This entry adds no new HTTP results and reads no other seat's probe implementation. Production diff against candidate 5 remains empty. Model/usage/spend and historical interpretation limitations remain as stated in Entry 1.

## Entry 3: reciprocal bytes-boundary reconciliation

Interface source-only coordination message `a00c6c45-f122-45f8-ad04-d22b793374fd` proposed bytes/string decoding and UTF-8 byte encoding. Systems explicitly agrees with its responsibility split and adopts that transport-facing shape. This supersedes only Entry 2's string-only decoder/string encoder proposal; the earlier proposal remains historical. The current callable contract is:

- `loads(raw: bytes | str) -> object`: bytes decode strictly as UTF-8, with no UTF-16/autodetection; one complete JSON value is parsed with exact numeric leaves. Invalid encoding, syntax or constants raise `JsonCodecError(ValueError)`.
- `dumps(value: object) -> bytes`: compact JSON with ASCII string escapes, emitted as UTF-8 bytes; exact numbers remain numeric tokens, unsupported/non-finite leaves raise `JsonCodecError`. The server uses the returned bytes directly for Content-Length and response writing, with no second encoding step.
- `validate_json(value) -> None` and `same_value(left, right, *, profile="exact-v1") -> bool` retain Entry 2's behavior; supported profiles remain `exact-v1` and `python-json-v1`. `JsonNumber` remains an immutable exact decimal/exponent leaf with token-kind provenance.

The shared decoder implements JSON lexical grammar and constant refusal. The server owns HTTP framing, object-only enforcement, error mapping to 400, headers and response emission. This is a coherent syntax boundary, not duplicated endpoint validation. Core retains authentication, status/order rules, exact current equality, identified old receipt comparison context and atomic state replacement. Neither transport nor codec changes missing/used-key precedence or field rules.

Legacy matching reconstructs the old stored float context from genuine exported decimal/exponent leaves, and projects incoming decimal/exponent leaves through that source parser only for the marked legacy receipt. Incoming integers remain exact. Original archived public numeric values and timestamp strings remain unchanged; a mixed state's persisted per-receipt profile survives subsequent import. Entry 2's private schema-2/`numeric_profile` proposal is still awaiting explicit reciprocal format agreement. The coordinator's final body-type decision and source release also remain pending.

Systems requested Interface's committed reciprocal callable/profile agreement in its owned design file. This append is the Systems side of that agreement, not a claim that the requested Interface commit has arrived. Only this evidence/design document changes; all production paths remain frozen and byte-identical to candidate 5. Document whitespace and production-tree diff checks apply; no codec or HTTP execution is newly claimed.

## Entry 4: committed reciprocal contract verified

Interface handoff `a807e9a7-c184-4e33-ba0b-4e7342b2c422` supplied its source-only assessment at `048a60a22130cc444bfd494931cdf12045472c73`. A bounded read of its authorized shared design, `evidence/interface-engineer/stage-1-json-number-design.md`, also found the subsequently committed final reconciliation `33458395d1e73d32fafa754fdd6402f20f200faa`. The earlier text/bytes proposals crossed; both historical sections remain intact. The final committed Interface entry expressly adopts the bytes contract from Systems Entry 3 (`f589b7361bb11f0b9a7eae7217c546cf0c6d2b3d`). Systems confirms that contract and its helper ownership in the direct reply to the handoff.

The current shared return types are unambiguous: `loads(bytes | str) -> tree`, `dumps(tree) -> UTF-8 bytes`. Shared lexical syntax/constants fail with `JsonCodecError(ValueError)`; the server owns framing, object enforcement and HTTP mapping. `validate_json` and keyword-only `same_value(..., profile=...)`, exact immutable numeric leaves, integer provenance and boolean distinctions match in both documents. Systems owns numeric predicates/normalization and receipt/state semantics; Interface owns adapter integration and image packaging. No production code uses the superseded text contract.

Interface's committed private-format agreement also matches: schema-2 state requires per-receipt `numeric_profile` (`exact-v1` or `python-json-v1`), genuine unmodified schema-1 receipts import under their source profile, the public envelope remains format_version 1, and mixed origins survive a second replacement without rewriting original JSON values or historic strings. Module-first, adapter-next, core-last remains the shared sequence.

The Interface document reports its adopted source-decision message `483e8e75-0620-4c5f-821e-e885006cba7a` at commit `bb2ef6b59f1dfc6f201963b147df501a4d928d61`. That statement is attributed to Interface; this append does not claim Systems has received the coordinator's complete direct source-decision/release message. The explicit Systems source release is still required. Shared card 10 remains in progress; source module work has not started.

Only design documents were read to establish the shared contract. Interface's own 18-operation/37-assertion legacy run remains received builder evidence, not new Systems execution. No peer probe or oracle code was read/copied. Production diff against candidate 5 and document whitespace checks still pass. This append changes only the Systems design; no repaired candidate or acceptance is claimed.

## Entry 5: complete adopted decision read and agreed

After Interface's final confirmation `08bd086c-7243-4077-b993-58ce919338b5`, Systems located and read the **complete** committed coordinator decision at `evidence/coordinator/json-number-semantics-decision.md`, revision `5e7bd528b51542d8f5357cc8d8d926ea1dfc0f0d`. The file has no uncommitted change. This is a later source read; Entry 4's earlier message-receipt distinction remains historical.

Systems agrees with the adopted exact value-based body integer semantics, positive whole base grid/duration/capacity and nonnegative whole cutoff, correct-type fractions 422, party wrong-type override, ordinary wrong types 400, missing fields 422 and unchanged plain-digit queries. Exact current recursive JSON equality includes numeric aliases and signed zero equivalence, excludes bool/string equivalence and retains every ignored field. Unknown finite values remain JSON numbers through storage/encoding/replacement; malformed syntax/encoding/constants remain 400. Legacy receipt-scoped source projection, exact incoming integers, unchanged original emitted responses and mixed-profile independent replacement agree with Entries 2–4. The fourteen old source-question observations remain unchanged rather than being retrospectively counted as passing repaired behavior.

The committed reciprocal callable/private-format documents and complete adopted source decision now satisfy the **design** gate. Module, adapter and core production integration have not started. The remaining next-step prerequisite is the coordinator's explicit Systems source-release message under the complete package. Shared card 10 remains in progress for the overall repair. No new HTTP run, service file, test count or acceptance follows this entry. Production-tree diff and document whitespace verification remain the only new checks.

## Entry 6: released standalone module implemented

Coordinator source release `1789cad6-7d95-40f2-a33a-926f30ed2002` authorizes only `stage-1/json_codec.py` and Systems evidence for this sequence step. The standalone standard-library module implements the final bytes contract. Existing `core.py`, all Interface runtime paths and all Stage 2 paths remain unchanged against candidate 5. There is no Engine import yet and no repaired HTTP candidate or acceptance claim.

`loads(bytes | str)` uses strict UTF-8 decoding, ordinary JSON grammar and constant rejection. Integer tokens become exact native integers; decimal/exponent tokens become frozen `JsonNumber` leaves retaining original token kind and canonical sign/coefficient/exponent. A process-local integer conversion setting removes Python's unstated digit ceiling for both coefficients and exponent metadata. There is no Decimal arithmetic context, binary decoding or numeric ceiling. Zero value normalization affects equality, while the original valid decimal/exponent token remains available for encoding and historical projection.

`dumps(tree)` returns compact ASCII-escaped UTF-8 **bytes**, emits numbers as numeric tokens and refuses non-finite or unsupported leaves. `validate_json(tree)` returns None or raises `JsonCodecError(ValueError)`. `same_value(left, right, *, profile="exact-v1")` compares complete recursive trees with exact numeric aliases, signed-zero equality, ordered arrays, order-independent complete object mappings and distinct booleans/strings. `python-json-v1` is an explicit comparison profile: only decimal/exponent-token leaves undergo the old finite float projection; integer tokens remain exact. Overflow cannot match an archived successful legacy receipt. Native finite diagnostic floats mean their ordinary emitted JSON decimal spelling rather than a binary-ratio expansion. New `loads` results contain no native floats.

Core-owned helpers supplied with this module are `is_number`, `number_key`, `is_integral`, `compare_numbers`, `to_integer` and `multiply_integer`, plus constants `EXACT_PROFILE` and `LEGACY_PROFILE`. Comparison and integer-factor multiplication operate on compact coefficient/exponent metadata. `to_integer` intentionally materializes an integral value; its caller must first establish that materialization is needed and bounded by the actual operation. A giant ignored value, huge duration/grid/cutoff or capacity comparison does not require that conversion. The future core integration must use symbolic comparisons before any bounded arithmetic and must never add a numeric maximum. These helpers add no HTTP/endpoint validation to the codec.

Own independently authored diagnostics use Decimal/Fraction only as a modest-bound reference, with seed 20261004 and 180 saved numeric pairs. Exact encoding/equality/classification/order/multiplication, 4,301-digit integers and fractions, compact positive/negative huge exponent metadata, unknown nested values, historical rounding/underflow/integer provenance, malformed JSON/constants/encoding, unsupported trees, immutability/deep copies and 50 parallel codec tasks are covered. Host run 01 passed 1,442/1,442 assertions in 0.007475250 s. A dead no-op line was removed from the diagnostic script; separate host run 02 passed the same 1,442 assertions in 0.006904583 s. Both outputs remain preserved. They are codec assertions, not HTTP operations or specification ledger rows.

Commands from the result root:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-codec-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-codec-host-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-codec-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-codec-host-02
```

An evidence-only driver builds these committed module/probe blobs in a separate diagnostic image, runs with network none, 2 CPU/2 GiB and no mounts, saves source/image/resource/timing/cleanup proof and removes only its own container/context. This is neither the submitted service image nor HTTP startup testing. Its actual result will be appended after the named source commit is exercised. No peer probe implementation or external domain code was read/copied.

Remaining gates are Interface's committed adapter/image wiring, explicit coordinator core release, Systems receipt/profile/state integration, complete constrained genuine-source/cross-process regressions and independent named review. Private schema-2 behavior is still an agreed contract to implement later, not module behavior. Highest independently accepted stage remains 0. Historical timestamp/immutable-string interpretations remain unchanged. Modest codec inputs do not prove arbitrary-payload performance. Harness Codex; configured gpt-6.1-sol; actual override, effort, usage and estimated/billed spend remain unknown.

## Entry 7: committed diagnostic image passed

The standalone implementation/probes were committed at `00940d4777c316c1369e744109885d58c85373ec`. Exact committed blobs were built and exercised by `stage-1-json-codec-run.py` in `systems-engineer-json-codec-container-01`: 1,442 assertions passed, zero failures, 0.007223375 s probe time and 2.991893458 s full driver time. Actual network none, 2 CPU/2 GiB, user 65532:65532, no mounts, packaged-source/image identity and cleanup exit 0 are saved in that folder's `runtime.json` and inspections. The module SHA-256 is `913800d80172392e6357b4a9c6d2b5a80d47859779e4b0c7024b5e6e61a71078`; no module change followed the earlier host checks.

The complete module-only handoff is `evidence/systems-engineer/stage-1-json-codec-module-06.md`. It names the API, source/image hashes, exact commands, scoped timing, assumptions and remaining risks. This is an evidence seal for the unpromoted module step. Core and all Interface/Stage 2 production paths remain frozen; shared card 10 remains active for the full repair. No new HTTP count, private-state implementation or acceptance is claimed.

## Entry 8: valid nested tree traversal correction

Coordinator boundary request `967c90be-6337-455c-aea6-3c9b209b6b99` authorized own modest nested-object/array diagnostics and any required module correction with unchanged API. Pre-repair evidence is committed at `c061c7a9f1cc4fde6ffdd34b2e75bab1fb02a633`. Initial composed checks had 60 assertions/57 failures; the isolated decoder follow-up had 90 assertions/72 failures. Valid wrappers at 1100 produce payloads of 2242–12142 bytes. All isolated decoder controls pass on this runtime; failures are recursive validation/encoding/equality. The earlier interim description included parsing too broadly, and the exact correction is preserved in `stage-1-json-depth-before.md` and the room.

The module now uses explicit pending stacks for tree validation, encoding and both equality profiles. Validation tracks the active ancestor path to refuse cycles while allowing shared acyclic subtrees; it introduces no depth bound. Encoding preserves container/key order and numeric tokens. Equality uses exact/legacy leaf rules and explicit paired traversal, retaining key-order equivalence and array order. The standard JSON decoder stays unchanged because no isolated decoder refusal was observed. Callable signatures, bytes return types, profiles, helpers and ownership remain identical to the reciprocal contract.

New host depth run 01 passes 90/90 assertions in 0.122367875 s; expanded run 02 passes 155/155 in 0.142695334 s, including deep differences/aliases, missing closing tails, empty containers, repeated subtrees and cyclic mapping refusal. Maximum saved valid payload is 17642 bytes at 1600 wrappers; Python recursion limit remains unchanged at 1000. Existing numeric/malformed/provenance diagnostics pass 1442/1442 in 0.006317709 s. Both failed runs and both repaired runs remain separate. Module SHA-256 is `771cd5c2ccd4e11bb74808998de65605845576d0bc6172fb2d428421bc83895c`.

`stage-1-json-codec-run.py --depth` can now build exact committed codec/numeric/depth probe blobs and exercise the two independent diagnostic processes in one constrained offline image. Its actual named-source result will be sealed separately. This is still module-only work; real deeply nested full request-body receipt/export/import handling is added to the pending core integration task and must receive its own HTTP evidence. Core and Stage 2 remain held. Interface's separately released adapter/image ownership is respected. No arbitrary-depth performance, full service correctness or acceptance is asserted.

## Entry 9: corrected module named image passed

Current module revision `c2fcedc853e0fe33e96f9d3f39c0c807b4e08d9f` passed its committed offline image checks: numeric suite 1442/1442, depth suite 155/155, zero failures, probe times 0.007052667 s and 0.159239459 s. Full driver time was 1.540007750 s. Both diagnostic processes had 2 CPU/2 GiB, network none, no mounts, packaged-source/image match and cleanup 0. Image ID is `sha256:bd04bd492ef297bbdc95904299d6aa5fc5c81583cfe0bd30af083e468f8e7447`. The source module SHA remains `771cd5c2ccd4e11bb74808998de65605845576d0bc6172fb2d428421bc83895c`.

`stage-1-json-codec-depth-07.md` is the inspectable current module handoff, with exact commands, original failures/correction, grammar/byte counts, changed-path ownership, timings, resource/cleanup proof and remaining risk. Prior module 00940 diagnostics stay historical. Core/private-state/real receipt integration is not yet released or verified. The stable public callable/API contract is unchanged; only source/image hashes advance. Highest accepted remains 0.
