# Stage 1 candidate 5 Interface integration handoff

Current outcome: **integration refusal remains unresolved; no acceptance claimed**.
Highest independently accepted consecutive stage remains **0** after the preserved
supplemental rejection `fe68f4ef60580d73c17ba2a21c6a4d20b77e8e41`.
Stage 2 production remains frozen. No Stage 3 work was started.

Package `TK-20261004-S1-interface-engineer-CANDIDATE-5`, parts 1–7 and END marker,
was acknowledged complete in room message `19f3cda1-9705-4ba0-800e-8cbea7a060ec`
before execution. Shared assignment is #8. This review changes only Interface
evidence; no graded source, Engine, verifier file or Stage 2 file was edited.

Exact reviewed full candidate: `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250`.
Stage 1 implementation source: `78732dde56ba6116d0722136beba74b674811105`.
Reviewed Stage 1 tree: `938fe8d78be5650b989d18fe7540b0aa1cff4e80`.
Own initial probe commit: `76763bb2cbf54d5da8780768ae89399d3106a8fc`.
Own runner-only DNS-label repair: `74dff654931980cdacbb63dec61a649fa47a9a81`.
The commit containing this report is the evidence handoff revision; its full hash
is supplied in the room handoff, avoiding a self-referential commit hash.

## Observed results and actual failure

The completed corrected-run result is:

| Observation | Measured result |
| --- | --- |
| Runtime/source/clone checks, excluding the two suite aggregate flags | 20/20 passed |
| Own inherited transport/concurrency/time assertions | 577/577 passed, 0 failures, 0.1186 s |
| New own decimal/legacy HTTP interactions | 132 operations, 518 assertions, 517 passed, 1 failed, 0.530112459 s |
| Complete build/start/probes/cleanup | 53.305537584 s |
| Candidate default 8080 health, measured from `docker run` start | 3.271080792 s |
| Candidate overridden 9090 health, measured from `docker run` start | 3.251947708 s |
| Genuine older service health | 3.251559333 s |
| Own service/network cleanup | Four removal commands, all exit 0 |

These are assertions, with repeated HTTP media-type/framing/timing assertions;
they are not normative requirement counts or an independent promotion verdict.
There are no skipped cases or flow exceptions in the corrected run.

The failed interaction uses a normal capacity-4 fixture, an authenticated diner
and a previously unused key. Its raw create body contains a **JSON number**, not
a string: `party_size` is the decimal digits of `10**4300 + 1` followed by `.5`.
The complete body is generated explicitly in `stage-1-candidate-5-probe.py`.
This is a finite, syntactically valid JSON fractional value with a 4,301-digit
integer part. Observed: **400 `malformed_request`**. Expected from Stage 1 §§5/8:
**422 `validation_failed`**, because `party_size` is not an integer. Ordinary
`1.5`, boolean/string/zero/negative party controls return the expected 422.

Diagnosis from read-only inspection: the unchanged adapter's default
`json.loads` floating decoder represents this valid decimal fraction as Python
positive infinity. Core's `json_value` then refuses a non-finite float with 400
before endpoint party validation. This diagnosis does not make an explicit
`NaN`/`Infinity` token legal: those malformed constants continue to be rejected.
The integer conversion repair therefore resolves the tested integer ceilings
but does not resolve this floating-decimal transport boundary.

The failure and source applicability were sent to the coordinator and Systems in
room message `42c1bc6d-6731-4cfe-a19d-73527ee2a91f`. No repair was performed in
an owned runtime or overlapping Engine path. Source coordination and independent
review must resolve this remaining refusal before this report can support a
passing integration claim. Existing accepted/rejected reports remain unchanged.

## Passing integration scope

All four isolated 4,301-digit base-field resets return an empty 204, and public
restaurant responses retain the exact JSON integer. A huge grid produces one
bounded opening candidate; a huge duration produces no fitting starts and the
ordinary fit refusal; huge cutoff amendments/cancellation refuse atomically.
Exact giant party queries correctly offer a fitting singleton or empty lists for
ordinary capacities. No undocumented safe-integer or digit cap was introduced.

Giant party JSON values survive create, amendment, batch move, cancellation,
current-state lookup, public response encoding and independent-process import.
Full parsed retry bodies retain giant ignored integers and nested JSON types.
Key-order/whitespace replay, changed-body conflicts before invalid field/resource
checks, failed-key reuse and immutable original create/move receipts pass.

Strict malformed UTF-8/JSON/constants/nonobject behavior, other wrong field
types, booleans/ordinary fractions, query lexical/value refusals, failed reset/import
atomicity, HTTP JSON charset/byte lengths and zero-byte 204 responses pass.
Inherited probes exercise two 50-client barriers (identical retry and occupancy
competition), partial committed-response loss followed by recovery, Unicode and
case-insensitive headers, public browsing, bodyless cancel, reset/session clearing,
both repeated-hour IANA cases, a skipped local time, and historical/calendar
timestamp serialization under the recorded interpretation.

A separately built, genuinely running older source at full revision
`49287b4a5a1481f995c470ccae31776f03d4b863` issued two active sessions, original
create references and an atomic swap receipt. That source then amended and
cancelled the records. Its unchanged HTTP export was imported into **each of two
independent candidate processes**. Both retain exact source state, current record
identities/statuses/timestamps, both tokens, password login and original create
and batch receipt JSON, including a field ignored by that old Stage 1 source.
Repeated replacement adds no duplicate; previous destination sessions disappear;
reset removes imported sessions and credentials. A later source write leaves the
captured snapshot unchanged. No state was manufactured from fixture reconstruction.

## Exact build, runtime and commands

Both executions ran this command from the result repository:

```sh
python3 -B evidence/interface-engineer/stage-1-candidate-5-container-check.py \
  --revision f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250
```

The host runs only standard-library evidence orchestration. The driver creates
a clean detached clone at the named full candidate, reads/hashes the exact source
and RUN instructions, parses both service files with AST without importing host
service dependencies, and builds the complete five-file Stage 1 folder using its
Dockerfile. The old build context is generated from its exact committed five files.
Build cache was available and reused; no uncached-build claim is made.

Current and older image core/server hashes match the named source revisions.
All three service processes ran with 2 CPU, 2 GiB, no mounts and an internal
offline network. Candidate listeners were observed at `0.0.0.0:8080` and
`0.0.0.0:9090`; the decimal client reached them by their internal network names,
so loopback-only binding cannot explain the passing remote HTTP interactions.
Host mappings used only 18225–18227. Host-published access was not asserted;
the already observed host mapping limitation is not relabelled as success.
The separate stdlib client also ran with 2 CPU/2 GiB and no service interpreter
sharing; its own integer-conversion setting cannot configure any source service.

Both clones remain clean after builds and checks. Retained corrected clone:
`/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/interface-engineer-s1-candidate5-20261004t024832530922z`.
The four Interface runtime files are byte-identical to the original revoked source
`2a4b0408a3453bc87d86bca3d0ec571f479e03ca`; the repaired core is explicitly different.
Per-file original/candidate SHA-256 values are in `source-proof.json`.

## Preserved runner failure and artifacts

Initial run: `interface-engineer-s1-candidate5-20261004t024714780674z/`.
The destination DNS label was 67 characters, exceeding the 63-character label
bound. Python's HTTP client raised `UnicodeError` before that destination could
be addressed. Partial results were 64 operations/250 assertions/248 passes and
two flow exceptions; inherited assertions were 577/577. Wall time was
53.052897584 s. All own cleanup commands exited 0. This is an own runner defect,
not a passing service run or two manufactured production failures.

The runner-only commit shortens resource labels and validates their length.
The corrected output is separate:
`interface-engineer-s1-candidate5-20261004t024832530922z/`.
Each folder retains `run.json` (every executed argv, timing, source/resource/cleanup
proof), `source-proof.json`, both build logs, health/listener/image hash observations,
`inherited-http.json`, `decimal-legacy-http.json`, `summary.json` and service logs.
Own service containers, client and network were removed; image tags and clean
clones remain. Temporary old build contexts were removed. No other seat's resource
was stopped or changed.

Durable HTTP traces contain statuses, error codes and request/response digests;
full exports, token values/maps and password hashes stay only in client memory.
A recursive inspection of 2,450 saved JSON object records found zero raw fields
named password/password_hash/token/tokens/state/authorization. This scoped scan
is not a secret review of the final room export or unrelated evidence.

## Inputs, assumptions and remaining risk

Inputs were the complete seven-part assigned task/spec/brief/decisions, the
participant guide and active room plan, own existing authored probes, exact current
and older runtime files, Systems' supplied handoff and independent failure
descriptions supplied in the package. After the new failure, bounded read-only
core inspection examined `json_value` and write dispatch for diagnosis. No shipped
test or verifier probe implementation was opened/copied/executed; no external
domain code/API/schema, toy/abandoned result, outside-workspace implementation or
memory source was used. No host dependency was installed.

Ordinary transport uses Content-Length-framed JSON; unsupported transfer encoding
is refused. Modest 4,301-digit payloads do not establish arbitrary-size request
performance. Historical exact-instant/wall-field serialization still follows the
coordinator's adjusted minute-offset interpretation; literal historic wire offsets
and immutable older strings remain disclosed exceptions. Successful old receipts
retain their original representation. Official isolated checks, renewed complete
coverage and independent acceptance remain verifier/coordinator gates.

Harness Codex; operator-configured model gpt-6.1-sol. Actual runtime override,
reasoning effort, token usage, estimated or billed spend remain unknown. Measured
run times above are scoped command times, not whole-factory elapsed time.
