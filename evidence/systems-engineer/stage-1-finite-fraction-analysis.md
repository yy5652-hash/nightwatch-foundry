# Finite JSON fraction classification: applicable defect

Interface notification: `42c1bc6d-6731-4cfe-a19d-73527ee2a91f`. Tested candidate: `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250`, with unchanged Stage 1 source from `78732dde56ba6116d0722136beba74b674811105`. This is evidence-only analysis under the production review freeze; no graded source was edited.

## Applicability and actual classification

The literal `str(10**4300+1)+'.5'` has valid JSON number grammar and is a mathematically finite, noninteger decimal. Stage 1 section 5 explicitly prioritizes endpoint-specific party rules; section 8 assigns 422 validation_failed to a noninteger party_size. A valid numeric token overflowing the implementation's binary float representation does not become malformed JSON or a literal NaN/Infinity constant. The expected 422 is applicable.

Current standard json.loads converts the literal to Python float infinity, while an independently checked Decimal constructor retains a finite exact decimal with exponent -1. The Engine's global json_value check rejects nonfinite float values as 400 malformed_request before ordinary party/idempotency handling. The earlier process-local integer conversion repair covers JSON integer tokens and int(query) only; it cannot change parse_float behavior. Input grammar and actual numerical value must survive this conversion boundary before correct field/error rules can apply.

## Owning-builder black-box reproduction

Command from the result repository:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-finite-fraction-run.py --out evidence/systems-engineer/systems-engineer-s1-finite-fraction-01
```

The retained own image `systems-engineer-tablekeeper-s1:decimal-05-20261004t023841` started independently with 2 CPU, 2 GiB, network none, no mounts and port 18122. Runtime core/server hashes matched the named candidate. The client imports no service implementation, independently checks the JSON number grammar/finite exact value, and saves request hashes rather than live credentials or exports. No Interface/verifier probe implementation was read or copied.

Eight HTTP operations/eight assertions produced **three genuine failures** in 0.058199792 s:

| Applicable behavior | Expected | Observed |
|---|---|---|
| Section 5/8: huge finite fractional party_size, valid normal fixture/token/new key | 422 validation_failed | 400 malformed_request |
| Section 3.4: valid ordinary create, unknown ignored_number containing that finite fraction | 201 | 400 malformed_request |
| Section 7: successful key reused with a different body containing the unknown finite fraction | 409 idempotency_key_reuse | 400 malformed_request |

Normal reset/login, ordinary 1.5 party refusal, an ordinary successful create, and forbidden raw NaN constant all pass their expected 204/200/422/201/400 controls. Exact raw construction is executable in `stage-1-finite-fraction-client.py`; `systems-engineer-s1-finite-fraction-01/probe.json` preserves status/code/body, lexical/value checks, hashes and timing. `runtime.json` preserves executed argv, candidate hashes, resource proof and cleanup. Total run/start/probe/cleanup was 0.598636375 s; the only own container was removed successfully. This is source-review evidence, not a new repaired candidate or acceptance claim.

## Required general boundary and ownership

A general repair must preserve finite JSON numeric values through decoding, ignored fields, full parsed retry-body equality, storage, export/import and response serialization while keeping actual NaN/Infinity tokens and malformed JSON refused. Merely changing the party error mapping, permitting Python infinity in json_value, or reordering one field check would leave unknown-field/idempotency behavior incorrect; json.dumps(allow_nan=False) would also fail on successful stored receipts/exports if infinity were admitted. Clamping/rounding or converting numeric tokens to JSON strings would lose original-body semantics.

Interface owns transport decoding/encoding. Systems owns portable JSON-value validation/equality and transaction/receipt import behavior. A coherent exact finite-number representation/codec must cross that boundary without allowing extra unsupported numeric types to escape wire encoding or changing bool/type/field/error precedence. Using a standard exact decimal representation is one candidate, but parser/encoder and import/equality behavior require explicit joint design and executable probes; Decimal construction alone is not a complete codec or arbitrary-exponent/resource proof. No implementation is selected or applied by this analysis.

Coordinator must route the scoped complete repair package and release the respective owned paths before production edits. Stage 2 carries the same source pattern but was not executed by this new probe, so its finite-fraction result remains unverified here. Existing integer-only passes, earlier failures, current named verdicts and historical timestamp/original receipt interpretations remain preserved. No numeric cap, rounding, weaker grammar or endpoint-only special case is authorized by this finding. Highest accepted stage remains 0. Harness Codex; configured gpt-6.1-sol; actual override/effort/usage/spend unknown.
