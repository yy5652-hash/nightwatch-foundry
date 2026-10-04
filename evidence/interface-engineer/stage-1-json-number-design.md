# Stage 1 JSON-number source assessment and Interface boundary proposal

Current status: **design and evidence only; graded source remains frozen**.
Highest independently accepted consecutive stage is **0**. Candidate
`f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250` was independently rejected at
`6c01976c7b1b910f748efc97be7cc468b5963b18`. The original reports, failures and
manifests remain unchanged. This document does not restore acceptance.

The initial assessment answers coordinator messages `55184e52-c974-4ffa-8fcc-4b0344c8bf43`
and `444b5cb1-a416-49f5-8977-d3941272c062`. The complete eight-part assignment
`TK-20261004-S1-interface-engineer-JSON-REPAIR-1`, including END marker, was
acknowledged before new-package work in room message
`c292ade9-dda9-4a72-b134-a18c0b93463e`. Interface joined shared card #11.
Production release and reciprocal final callable API agreement remain pending.

## Published requirements and interpretation

| Published source | Consequence supported by that text |
| --- | --- |
| Stage 1 §3.4: unknown request fields are ignored, never an error | A syntactically valid finite number in an unknown field cannot make an otherwise valid operation malformed. Its complete value still participates in retry-body identity under §7. |
| §5: wrong JSON type gives 400; correct type with invalid value gives 422 unless a more specific rule applies | Numeric magnitude cannot turn the JSON number type into a malformed value merely because binary float conversion overflows. |
| §5 explicitly restricts integer-valued **query** parameters to plain decimal digits | Keep `1e9`, `4.0`, `+4` invalid in integer queries. The text does not impose that lexical restriction on body numbers. |
| §§5/8: invalid party values, including booleans/strings or a noninteger party, give 422 | A mathematically true fractional party is a valid JSON number but an invalid party value, regardless of magnitude. |
| §7: same JSON value after parsing; body key order and whitespace do not matter | Numeric equality needs a JSON-value comparison rather than Python token-class or serialization-string comparison. Booleans and strings remain different types. |
| §§7/10: preserve successful original parsed bodies, responses and retries through state replacement | New exact semantics cannot silently redefine the meaning of a genuinely old successful receipt. |

My recommended interpretation is **value-based integer semantics for body fields**.
`1`, `1.0` and `1e0` are JSON numbers with the same mathematical value. For a
field requiring an integer, all three satisfy integrality and should then undergo
the same range and endpoint checks. The Python decoder's `int`/`float` classes
are implementation details. Strings and booleans do not acquire integer meaning.
For new exact receipts, those equal-valued number spellings should compare equal;
`true`, `"1"`, and unequal exact fractions should not.

This is an interpretation of the published JSON-value wording, not a verbatim
additional spelling rule. The coordinator must record the final source decision.
The base fixture's true fractional count status was explicitly left as a source
question in candidate 5's independent verdict. If the count's integrality rule is
adopted, a numeric fraction has the correct JSON type but an invalid field value,
so 422 follows §5. The existing Python `type(value) is int` check does not itself
establish a published type or lexical constraint. This assessment does not turn
the earlier fourteen unverified rows into passes or independently established
failures.

Malformed UTF-8/JSON and literal `NaN`, `Infinity`, `-Infinity` remain transport
400 refusals. A finite fraction must reach the ordinary application ordering:
authentication, required key or original receipt comparison, then endpoint
validation. A used key with a different valid body must produce 409 before party
validation. No failed request consumes a key. PATCH/cancel/batch cutoff and
cancelled-state ordering remain owned by Systems and unchanged by the codec.

## Exact decoder, encoder and equality boundary

A complete repair needs one representation across raw decoding, portable-value
validation, complete parsed request bodies, canonical equality, successful
receipt storage, private exports/imports and response encoding. Merely using
`parse_float=Decimal` is a useful experiment, not proof of a complete solution.
The encoder must emit JSON numeric tokens, rather than quoted strings or binary
infinity. It must preserve finite overflow, underflow, large fractional values,
negative zero's numeric meaning and compact exponent forms. It must handle
strings, escaped Unicode, arrays, objects, booleans and null normally.

I propose a token-backed exact numeric representation retaining sign,
coefficient digits, decimal exponent and original integer-token versus
decimal/exponent-token provenance. Canonical numeric comparison can strip
coefficient trailing zeros and adjust an exact exponent without expanding all
zeros or using a rounding arithmetic context. Zero normalizes to one numeric
value. Recursive equality keeps booleans separate, arrays ordered, object member
order irrelevant, and every ignored numeric leaf included. Compact exponent
metadata must not inherit a binary-float or Decimal constructor/context ceiling.
The chosen implementation remains Systems' responsibility; this document adds
no production class or codec.

The proposed adapter-facing callable API is:

| Callable | Boundary contract |
| --- | --- |
| `loads(raw: bytes | str) -> JSON tree` | Strict JSON grammar, exact finite numbers and token provenance; raises a documented `ValueError`-compatible decode error for malformed syntax/constants/encoding. The HTTP adapter continues to require an object. |
| `dumps(value) -> bytes` | Complete JSON tree to UTF-8 bytes; finite numeric leaves remain bare exact numeric tokens. ASCII string escapes are permitted and preserve existing surrogate-string handling. No permissive NaN/Infinity output. |

If Systems chooses a text-returning encoder instead, the owners must explicitly
agree that return type before wiring. There should be no ambiguous mixture of
bytes and strings. Core helper names for portable validation, integral-value
conversion, exact equality and legacy projection must be supplied in the shared
contract by Systems. The server will not invent parallel helpers or retry state.

Interface retains Content-Length framing, strict UTF-8 and nonobject refusal,
case-insensitive headers, original target/query forwarding, byte-accurate JSON
response lengths and charset, zero-byte 204, one shared Engine, disconnected
response recovery, concurrency and default/override PORT on 0.0.0.0. The codec
must be packaged inside the image; no host or runtime download is introduced.

## Genuine historical numeric receipts

The old state schema is 1. Successful receipts contain parsed body/response data
but no numeric parser profile or original numeric lexemes. A genuine old export
can preserve a float leaf `9007199254740992.0` that came from the request spelling
`9007199254740993.0`. The latter spelling cannot be reconstructed from that
export. Integer-token values remain exact under the old decoder. It would be
incorrect to project every incoming numeric leaf through float or to compare
every old receipt using the new exact interpretation.

For genuinely unmarked old receipts, my proposal agrees with Systems' room
analysis `f79bb5ab-ef6b-44fb-a567-25789aa2d298`: persist a **receipt-scoped legacy
numeric profile** in private state. Project incoming decimal/exponent leaves
through the source decoder's finite binary-float meaning only for that legacy
body comparison. Leave incoming integer-token leaves exact. New writes receive
the adopted exact profile; do not globally enable legacy behavior. The public
original response body, shape, numeric values and historic strings stay unchanged.
Future exports/imports must preserve profiles, including mixed old/new receipts.

Legacy equality must compare the old stored parsed value faithfully. For example,
the old float value 9007199254740992 compares numerically equal to an exact integer
of that same value; integer 9007199254740993 must conflict. Bool-versus-number
identity remains distinct. The general implementation must also account for old
ordinary binary-float rounding and underflow-to-zero receipts, not only this one
large example. Unsupported reconstruction of a request's lost raw spelling is
neither required nor possible.

## Own executable assessment and measured observations

Own evidence script revision:
`199542f5345d0462aec738bf86caaba23d25ec6e`,
`evidence/interface-engineer/stage-1-numeric-semantics-assessment.py`.
No production codec or core is imported by its HTTP client. No verifier probe
implementation or shipped test source was opened or copied.

Executed from the result repository:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-1-numeric-semantics-assessment.py
```

Artifacts:
`evidence/interface-engineer/interface-engineer-num-20261004t030557637457z/`.
The stdlib exact-number experiments record ten values and six comparisons,
including `1.0`, `1e0`, true fractions, overflow/underflow exponents and bool/string
controls. Every recorded numeric-token round trip retained its value. These are
representation experiments, not service implementation or arbitrary-exponent
performance proof.

A separately running genuine old source
`49287b4a5a1481f995c470ccae31776f03d4b863` actually issued the login token,
reference and successful ignored-number receipt. Its unchanged in-memory HTTP
export was imported into a separately running frozen candidate-5 process. The
run reused our retained, previously proven exact images and rechecked immutable
image IDs and runtime core/server hashes. It did **not** rebuild a repaired
candidate or execute a future codec.

Observed **18 HTTP operations / 37 assertions / 37 passed / 0 failed** in
**0.056631625 s**. On both genuine source and current imported destination:

| Incoming ignored-number token | Observed original-key result |
| --- | --- |
| Original `9007199254740993.0` | 200, exact original successful response |
| `9007199254740992.0` | 200, same old parsed numeric value |
| `9007199254740994.0` | 409 idempotency_key_reuse |
| Integer token `9007199254740993` | 409 idempotency_key_reuse |
| Integer token `9007199254740992` | 200, same old parsed numeric value |

Real token/reference recovery, original receipt equality, exact old integer
leaf, rounded float leaf, framing and complete replacement state fingerprints
also passed. The output reports state fingerprints only, without full exports,
password hashes or bearer tokens.

`run.json` records total run/start/probe/log/cleanup **19.445315 s**, every
Docker argv, source/image identities and constraints. Two own service processes
and an independent own client ran on an internal offline network with 2 CPU and
2 GiB; services had no mounts. Host port mappings were 18228 and 18229.
All three explicit service/network cleanup commands exited 0, the client used
`--rm`, and the retained images remain. No other seat's resource was touched.

An earlier attempt used bare host `python3` and failed immediately because that
interpreter lacks `sys.set_int_max_str_digits`. The error is preserved in
`stage-1-number-assessment-host-startup-error.log`. It occurred before any Docker
resource or assessment output directory was created. No source workaround or host
installation was made; the existing workspace Python executed the recorded run.
This is an own runner/interpreter issue, not a service failure or a passing run.

The first evidence field-name scan flagged ten fields named `token` in the
semantic examples. These contain JSON lexical examples such as `1.0`, rather
than authentication tokens. Its failed assertion/output is preserved in
`assessment-source-secret-proof.json`. A separate scoped classification in
`assessment-classified-secret-proof.json` checks only those ten explicit example
leaves; no other raw sensitive field remains. All five Stage 1 and eight Stage 2
working files match the frozen candidate's exact committed bytes. The initial
scan failure was an evidence-check false positive; no HTTP run was repeated or
rewritten. The ledger entry was appended only after this classification passed.

## Ownership, sequence and remaining gates

Under the complete repair package, Systems owns `stage-1/json_codec.py` and
`core.py`; Interface owns `server.py`, `Dockerfile`, `.dockerignore`, `RUN.md`.
Room participants were checked before API coordination. Proposal message
`a00c6c45-f122-45f8-ad04-d22b793374fd` requested Systems' reciprocal agreement.
The required sequence is final contract, explicit coordinator source release,
Systems codec-module-only commit, Interface packaging/transport commit, Systems
core integration, then complete named-context probes. Intermediate commits are
not promoted candidates. No Stage 2 source or Stage 3 work is authorized.

The final repaired integration must separately exercise new exact receipts,
equal-valued aliases, true fractions and precedence, nested ignored values,
overflow/underflow/compact exponents, literal constants, failed-state rollback,
create and move receipts, original public responses, genuine ordinary rounded
and underflow legacy requests, mixed-profile exports and two independent repaired
destinations. Existing meaningful transport/concurrency/calendar regressions
remain required. Builder measurements cannot replace independent coverage,
official checks or clean-clone acceptance.

Historical exact-instant/nearest representable minute-offset interpretation,
immutable older timestamp strings and successful original receipt shapes remain
explicit risks. Modest payload experiments do not prove arbitrary-size resource
performance. Harness: Codex; configured model: gpt-6.1-sol. Actual runtime override,
reasoning effort, token usage, catalog-estimated and billed spend are unknown.

## Reciprocal codec API agreement

Systems' proposal in room message `28a09e83-62bd-4074-9bfa-f1397bf4c7c5` is
accepted for Interface integration. This section supersedes the earlier proposed
bytes-returning encoder with an explicitly agreed **text-returning** codec:

| Systems-owned callable | Agreed behavior and Interface use |
| --- | --- |
| `JsonCodecError(ValueError)` | A codec refusal belongs to the existing transport's ValueError-compatible malformed-body handling. |
| `loads(text: str) -> JSON tree` | Interface performs its existing strict UTF-8 decode after HTTP framing, then calls this function and retains its object-body check. Numeric leaves are exact integer-token ints or immutable provenance-carrying `JsonNumber`; booleans remain separate. |
| `dumps(value) -> str` | ASCII string escapes, compact separators, exact finite bare numeric tokens. Interface encodes the returned text as UTF-8 before sending headers; it calculates Content-Length from those bytes. A 204 response bypasses encoding and stays zero bytes. |
| `validate_json(value) -> None` | Systems owns portable JSON validation and raises `JsonCodecError` on unsupported/malformed values. The server does not add a separate numeric traversal or narrow the accepted number set. |
| `same_value(left, right, profile='exact-v1')` | Systems-owned recursive exact JSON-value equality; object order does not matter, array order does, boolean/string values remain distinct from numbers. |
| `same_value(left, right, profile='python-json-v1')` | Receipt-specific genuine historical comparison: project decimal/exponent provenance only; retain exact incoming integers and old parsed-body meaning. |

`JsonNumber` carries immutable exact coefficient/exponent information plus
decimal/exponent-token provenance. Unknown finite numbers do not pass through
float, or expand their exponent merely to parse, compare or encode. Systems owns
numeric predicates, integer normalization, archived response preservation and
persisted per-receipt profile metadata. The existing Engine request signature and
`(status, value)` result remain unchanged. I identify no adapter mismatch with
this callable contract. It does not change key/auth/framing order or authorize
source editing.

Archived response numeric values still require the original emitted JSON value
on replay. For example, legacy `0.1` remains `0.1`, rather than the exact decimal
expansion of a binary floating ratio. That compatibility responsibility is inside
the shared codec/core contract, not an adapter-specific float conversion.
Systems' separately authored genuine evidence at
`302e2c00a2e433302d92289cd8172cc3a7325168` observes original
`0.100000000000000005` and `9007199254740993.0` retries before and after import:
16 HTTP operations / 24 assertions / 0 failures. These are **received Systems
builder observations**, not additional Interface execution. Its design and
evidence were read to agree the module interface; its probe implementation was
not opened or copied.

Independent supplemental evidence
`f371edd40eb4a336b87a3358a6616d6c6dd6aabb`, received in room message
`dd9b0b68-14dc-4df6-956a-4a9b07b4daf6`, establishes eight true fractional-party
and create/move precedence failures for frozen candidate 5: 38 HTTP requests,
35 assertions, 8 failed assertions in 0.056724500 s. This now independently
confirms the explicit party rules, separate from the fourteen unresolved
base/integral-number questions. The original 932-row candidate-5 verdict and
official 120/120 remain unchanged. No independent executable probe source was
read, and this section is not a new Interface run or repaired-candidate result.

Both owners agree the module-first, adapter/package-next, core-last sequence.
The next source step still requires the coordinator's explicit release and
Systems' committed module revision. Stage 1 and Stage 2 production remain
unchanged, shared #11 stays active, and highest accepted stage remains 0.
