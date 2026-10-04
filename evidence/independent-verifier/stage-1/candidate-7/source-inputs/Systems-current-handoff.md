# Stage 1 nonrecursive decoder repair handoff

The repaired complete service passes the scoped owning-builder checks below, including genuine 10,000/20,000-wrapper receipts and unchanged raw export/import. **Highest independently accepted consecutive stage remains 0.** This is a new implementation and new execution after candidate 6 rejection; it does not alter any historical verdict or establish acceptance.

All ten parts and END marker of `TK-20261004-S1-systems-engineer-JSON-REPAIR-2` were acknowledged complete before work. Shared card 13 authorizes Systems' disjoint codec/core repair. Interface execution and a complete independent named review remain coordinator-controlled sequence steps. No Stage 2 source was edited or later stage extended.

## Exact source and smallest coherent change

Implementation and complete tested candidate: **`9e6143bd4ff8d4429f51728cd3b3d96fd1f088de`**. Stage 1 tree: **`75f6ece6952c570eedf8a548f4428a5b2c986128`**.

The only production change against rejected `ab0cf79767b6768153a73894bf5768bf3328491a` is `stage-1/json_codec.py`, 89 added/3 removed lines. `core.py`, Interface's four runtime paths and all Stage 2 source remain byte-identical. The implementation commit also records Systems' design, own diagnostics and preserved reference correction. No peer probe/oracle implementation, external domain code, toy/abandoned result or outside-workspace source was read/copied/executed. No host dependency was installed.

`loads(bytes | str)` now uses explicit container frames instead of recursive `json.loads` container descent. Each frame records its mutable container, grammar state and current object key. Arrays distinguish initial empty-close, value required after a comma, and delimiter/close after a value. Objects distinguish initial empty-close, required string key, colon, value and delimiter/close. A child container attaches to its parent before its frame is pushed; the parent resumes after that child closes. A root returns only after all frames close and trailing JSON whitespace is exhausted. This rejects trailing commas/data, missing/wrong delimiters, non-string keys and invalid scalar prefixes without a nesting ceiling or recursion-setting change.

Strict standard-library string scanning preserves escape/control-character handling and duplicate keys retain the source decoder's last-key-wins semantics, including escaped equivalent keys. Only space/tab/CR/LF count as JSON whitespace. Bytes still require strict UTF-8. Existing exact numeric grammar and scalar handling preserve integer-token ints and immutable decimal/exponent `JsonNumber` provenance; ignored exponents are not eagerly expanded. Literal NaN/Infinity/-Infinity and malformed syntax/encoding remain refused.

The callable contract is unchanged: `loads(bytes | str) -> exact/provenance JSON tree`; `dumps(tree) -> UTF-8 bytes`; `JsonCodecError(ValueError)`; `validate_json`; keyword-only `same_value(..., profile='exact-v1')`; and iterative `copy_json`. Existing numeric helpers, current exact equality, genuine legacy receipt comparison, detached response snapshots and transaction code are unchanged. No transport endpoint validation was moved into the codec.

Private schema 2 still requires each receipt's `numeric_profile` (`exact-v1` or `python-json-v1`); genuine schema 1 imports as legacy. Public `track: tablekeeper`, `format_version: 1` stays unchanged. Integral body aliases, boolean/type distinctions, fractional value errors, strict decimal query spelling, auth/key/current-resource ordering, failed-key reuse and immutable original public response values remain governed by the complete adopted decision `5e7bd528b51542d8f5357cc8d8d926ea1dfc0f0d`.

## Actual new measurements

| Own executed scope | Observed result | Scoped seconds |
| --- | --- | ---: |
| Complete exact numeric/type/precedence/migration/export HTTP suite | 373 requests, 1,773 assertions, all passed; 7/7 scenarios | 1.273030167 |
| Inherited real HTTP scenarios | 15/15 tests passed, no skips | 2.671 |
| 4,301-digit integer HTTP suite | 92 operations, 146 assertions, 0 failed | 0.507278375 |
| Supplemental deterministic Engine ownership in image; not HTTP | 15/15 assertions | 0.071878917 |
| Complete clean-context build/start/probes/cleanup | Passed; all four diagnostic clients exited 0 | 79.736101250 |
| Actual large-depth HTTP/state-transfer/race suite | 249 requests, 202 assertions, 0 failed; six genuine deep receipt flows | 7.381416587 |
| Large-depth service/client start/probe/cleanup | Passed, no runner exception | 8.926954875 |
| Packaged codec grammar/reference diagnostics; not HTTP | 722/722 assertions, seed 2026100402 | 0.278432875 |
| Packaged exact numeric diagnostics; not HTTP | 1,442/1,442 assertions, seed 20261004 | 0.007609875 |
| Packaged depth/copy diagnostics; not HTTP | 171/171 assertions, depth up to 1,600 | 0.237575833 |
| Three packaged diagnostic processes/start/cleanup | Passed | 1.497877791 |
| Isolated 10,000/20,000-wrapper operation controls; not HTTP | 24/24 processes, 36/36 assertions | 6.002229625 |

These are own executable assertions/scenarios, not normative coverage rows, independent acceptance or hidden-suite results. No official harness was run by this handoff. Previous official 120/120 observations belong to their named rejected candidates and are not reused as acceptance of this revision.

The grammar corpus independently compares modest payloads against a strict UTF-8 standard-library reference with exact Decimal scalar values, includes 180 seeded original trees and their 180 mutations, and checks malformed constants, lexical numbers, trailing data, delimiters, string escapes/controls, Unicode/encoding and duplicate-key behavior. Deep arrays, objects and alternating wrappers at 10,000/20,000 are valid by inductive composition from a valid finite leaf; no recursive reference decoder is needed to establish their grammar. Deep malformed EOF/closing/comma/trailing-data controls are separate. Integer versus decimal/exponent provenance is checked explicitly.

The isolated large-depth run repeats the same six operations (decode, validate, equality, encode, copy and serialization round trip) on arrays/objects at both observed depths. All eight previously refused decoder/round-trip processes now pass; all sixteen direct-operation controls pass. Input sizes are 20,056–220,056 bytes. Default recursion limit stays 1,000 in the packaged Python 3.12.15 interpreter. Maximum operation time is 0.048538708 s and maximum measured RSS is 31,976 Linux KiB; no process is OOM-killed or exits without its result. These direct checks remain distinct from HTTP evidence.

## Genuine deep HTTP receipts and raw replacement

Two independent matching-image services and a separate standard-library HTTP client construct finite exact-number leaves inside balanced wrappers. The client parses shallow public responses only and never decodes private exports. Unknown deep reset/signup fields succeed. Actual create and move receipts, numeric aliases, unequal fractions, boolean/number differences, missing auth/key ordering, failed fractional-key recovery and malformed deep refusal are exercised through HTTP.

| Case | Ignored nested value bytes | Create / move | Actual unchanged captured export bytes |
| --- | ---: | --- | ---: |
| 1,100 arrays | 2,245 | 201 / 201 | 10,346 |
| 1,100 objects | 6,645 | 201 / 201 | 23,549 |
| 10,000 arrays | 20,045 | 201 / 201 | 63,749 |
| 10,000 objects | 60,045 | 201 / 201 | 183,752 |
| 20,000 arrays | 40,045 | 201 / 201 | 123,749 |
| 20,000 objects | 120,045 | 201 / 201 | 484,663 |

Every case issues real tokens/references/create/move receipts, captures its actual HTTP export, then cancels the source booking. The identical bytes go directly to the other process's import. Imported tokens/references and the earlier confirmed assignment remain valid; the unchanged raw create/move bodies and keys replay their original shallow response JSON in both processes after mutation. Destination cancellation also leaves the original receipt unchanged. The six saved trace-level forwarding checks match export response/import request byte counts and SHA-256 values and explicitly record `decoded: false`. No deeper path is blocked or passed by fallback shallow state.

At 20,000 object wrappers, fifty staged identical writes return exactly one 201 and forty-nine 200 with the same original receipt; that additional receipt also survives raw replacement and replay. Malformed deep import gives 400 and changing a required profile inside genuine captured bytes gives 422, each preserving the entire destination snapshot. Both services remain healthy and not OOM-killed. Maximum HTTP request time is 3.260601460 s; every observed request is below its applicable 5/10-second limit. Largest valid captured/imported snapshot is 484,663 bytes; the largest request, 484,665 bytes, is the malformed-import control. These measured bounds do not establish arbitrary-size/depth performance.

## Fresh numeric, historical, snapshot and inherited regressions

The separately built and genuinely running old services at `49287b4a5a1481f995c470ccae31776f03d4b863` and `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250` issue real sessions, references and create/swap receipts before changes/cancellation. Their actual unchanged HTTP exports transfer to the repaired independent destinations. Original precise/rounded decimals, 9007199254740993.0 and underflow request forms replay according to their receipt-scoped legacy meaning; distinct exact integer values conflict. Tokens/password login, original timestamps/statuses/identities and original public responses survive. New exact receipts join the legacy state, and mixed profiles persist through another independent replacement. Missing/wrong/null profiles reject atomically; repeated replacement and reset clearing pass. No old receipt or state is manufactured from a reconstructed fixture.

The new-source complete suite again covers exact body aliases/zero signs, ignored finite overflow/underflow/exponents, full current body equality, wrong types/fractions, malformed encoding/constants/nonobjects, request ordering and atomic rollback. Twenty captured exports overlap thirty writes; a separately defined prefix oracle checks complete record/receipt/reference relationships and imports each captured snapshot into the independent peer. Supplemental image-only ownership probes verify detached request/response/current/replay/move/import containers and remain explicitly separate from the black-box HTTP clients.

Inherited checks cover both fifty-client identical and competing writes, authentication/privacy/public browsing, half-open occupancy, capacity/grid/opening constraints, cancelled/cutoff/current-start rules, no-op and atomic batch ordering/rollback, immutable original receipts, both required DST zones, historical/calendar boundaries and large base counts. Existing RLock/transaction/snapshot implementation was not changed.

## Reproduction, image identity and cleanup

Commands executed from the absolute result repository:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-container-check.py --revision 9e6143bd4ff8d4429f51728cd3b3d96fd1f088de --out evidence/systems-engineer/systems-engineer-json-decoder-service-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-parser-container-run.py --image sha256:bb38e67289a3af6a8a09b1f99016003284b8cf3bcdb6d27655d8bc6379cd4666 --candidate 9e6143bd4ff8d4429f51728cd3b3d96fd1f088de --out evidence/systems-engineer/systems-engineer-json-parser-container-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-large-depth-http-run.py --image sha256:bb38e67289a3af6a8a09b1f99016003284b8cf3bcdb6d27655d8bc6379cd4666 --candidate 9e6143bd4ff8d4429f51728cd3b3d96fd1f088de --client evidence/systems-engineer/stage-1-deep-decoder-http-client.py --out evidence/systems-engineer/systems-engineer-json-deep-decoder-http-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-large-depth-codec-run.py --image sha256:bb38e67289a3af6a8a09b1f99016003284b8cf3bcdb6d27655d8bc6379cd4666 --candidate 9e6143bd4ff8d4429f51728cd3b3d96fd1f088de --out evidence/systems-engineer/systems-engineer-json-large-depth-after-01
../../.venv/bin/python -B evidence/systems-engineer/stage-1-decoder-repair-evidence-audit.py
```

Use new unique output folders when reproducing. Each runtime.json preserves actual clone/build/Docker/probe/inspection/cleanup argv, hashes, exits and timing. Executed diagnostic source copies preserve original observations if later runner files change.

The complete six-file Stage 1 context builds from a clean detached clone at the exact candidate. Image ID is **`sha256:bb38e67289a3af6a8a09b1f99016003284b8cf3bcdb6d27655d8bc6379cd4666`**. Current actual packaged hashes match:

| File | SHA-256 |
| --- | --- |
| json_codec.py | 6a063cf3a93b7e022b1fdace3d6357088cb7197b07a6f69c1c12d64d57a16263 |
| core.py | 2653bdc010129f91b33480ece36d43f30a81d8b6c214764745c9c0f722f4a84f |
| server.py | fb8d9e41eb13c3a736d49573903253a6cb98284790cf5edc9caeb352f0e0946c |

All six context hashes and genuine old image/source identities are in runtime.json. The new complete service clone remains clean before/after checks at `/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/systems-engineer-json-20261004t044158049514`. Available build cache was reused; no uncached-build claim is made.

Four complete-run services/four clients each have inspected 2 CPU/2 GiB, no mounts, on an internal offline network. Cross-container default 8080 and override 18141 service readiness/source-inspection intervals are 6.289362375/6.290911542 s; old-source intervals are 6.295696750/6.288545209 s. The separate deep run starts two matching services plus a client under the same constraints; readiness/source-inspection intervals are 0.387118292/0.374265833 s. Own host port mappings use only 18140–18143 and 18161–18162. Cross-container access is observed; host-published reachability is not claimed. The packaged and large direct-operation processes use network none/2 CPU/2 GiB/no mounts and import the codec only for their labelled unit diagnostics.

All **40** recorded own service/client/network removals return zero (9 complete-run, 3 packaged diagnostic, 4 deep HTTP, 24 large isolated). Temporary contexts are removed; images and the clean clone remain. No other seat's resource was stopped. Production stayed unchanged after 9e6143b throughout these runs.

## Preserved failures, audit and remaining risk

Independent candidate 6 rejection `7db8085f06bd6aa53443f5cf647ff4111bbaa771` and owning-builder decoder failure handoff `10467fde293ef36513b100ad4f86fcf1483fd81a` remain unchanged. Their actual RecursionError/400 observations at 10,000/20,000 are distinct from older traversal/equality/encoding defects and from smaller-depth passing decoder controls. No old result is relabelled as a new pass.

The first new host grammar run has 665 assertions, 664 passed and one reference disagreement. Its reference auto-detected UTF-16 bytes through json.loads, contrary to the agreed strict-UTF-8 wire contract; the codec correctly refused them. The original executed reference/results remain in systems-engineer-json-parser-host-01. The corrected independent reference explicitly decodes UTF-8; the separately executed run passes 722/722. A seeded renderer's separator pair was also corrected to keep its intended original trees valid. `stage-1-json-parser-reference-correction.md` documents both own harness issues; no production repair or concealed service failure followed them. All constrained runs completed without test or runner failures.

`stage-1-decoder-repair-evidence-audit.json` hashes 349 files from eight own output folders and inspects 29,205 saved JSON object records: 62 credential/private-state fingerprints and zero raw private payload findings. The scoped scan covers saved JSON, not source/log strings or the genuine final room export. Live tokens/password hashes/private exports remain in client memory. It also binds six unchanged raw transfers, applicable request time limits, forty cleanup exits and the exact one-file production diff. Every implementation/evidence commit uses --only explicit owned pathspecs with changed-file inspection.

The remaining gates are Interface's independently authored complete-service integration after coordinator release, then a complete new named independent startup/official/regression/spec coverage verdict. Historical exact-instant/nearest-minute wire-offset interpretation, original wall fields and immutable older timestamp strings remain disclosed; incompatible literal historical offset grammars are not claimed simultaneously. No arbitrary input-size/depth performance, hidden judging result or independent acceptance is claimed. Whole-factory elapsed is coordinator-owned; durations above are measured scoped runs. Harness Codex/configured model gpt-6.1-sol; actual runtime override, effort, usage, catalog-estimated and billed spend are unknown. Genuine room export, public release and submission remain operator-controlled.
