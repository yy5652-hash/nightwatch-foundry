# Stage 1 candidate 5: reject

Exact full candidate `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250`, production source `78732dde56ba6116d0722136beba74b674811105`: **reject**. Highest independently accepted consecutive stage remains **0**. The original five 4,301-digit refusals are repaired, but this candidate rejects valid JSON numbers in unknown fields. No Stage 2 promotion or Stage 3 extension follows this report.

The smallest reproduced failure adds only `"unused":1e4300` to an otherwise valid create body or reset fixture. This is a valid JSON number and finite mathematically; its short spelling is a modest payload. Stage 1 §3.4 says unknown request-body fields are ignored, never an error. Expected create201/reset204; observed both400 `malformed_request`, message `Invalid JSON value`. Signup with that same unknown value returns201. An ordinary create using the failed key succeeds201, confirming that the refusal consumed no key. These two endpoint failures also invalidate the inherited general `TK1-unknown-body` obligation. They do not depend on any interpretation of fractional or integral field types. The inherited endpoint-specific unknown-create and unknown-reset rows are also failed; an earlier draft linking only the general row is preserved in coverage-link-correction-01, with no new raw observation.

The independent client and exact command are in [numeric_forms.py](../numeric_forms.py) and [numeric_forms_run.py](../numeric_forms_run.py). From the result root, the executed command was:

```sh
/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/.venv/bin/python -B evidence/independent-verifier/stage-1/numeric_forms_run.py --repo /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-result --workspace /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory --candidate f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250 --out /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-checks/independent-verifier-s1-f5e0a532-numeric-01
```

Use a new unique `--out` directory to reproduce. Actual raw create/reset bodies, responses and counts are in `numeric-01/probes.json`; `commands.json`, `identity.json`, `inspect.json`, `image-hashes.json` and `client-source-proof.json` bind the clean detached clone, named source/image, client code, constraints and cleanup. Tokens/passwords/export payloads are redacted or fingerprinted, not published.

The final matrix has **932 rows: 913 verified, 5 failed, 14 unverified**. Every previous806 row was retested or freshly reviewed with current-candidate evidence; none of the old801 passes was reused as current proof. The111 decimal rows and15 numeric-form rows are independently derived additions. Fourteen additional raw expectation failures remain source questions: base-field1.5 gives400 rather than provisional422 (four), base-field1.0/1e0 gives400 rather than provisional204 (eight), and party1.0/1e0 gives422 rather than provisional201 (two). Their observed responses are preserved; the final matrix marks these interpretations **unverified**, not established service failures. Coordinator source-question messages are `af72866f-e5ae-4b5e-9c92-a2a90ab2102b` and `d09328ff-60fd-416a-8ee7-d33da74aa86c`. Earlier917-row observed counts remain separately unchanged.

Current independent execution totals **1841 HTTP requests, 1728 assertions and 16 raw expected-versus-observed failures**. Raw failures comprise the two clear unknown-field failures and fourteen interpretation questions; these are not sixteen established distinct normative defects.

| Run | Requests | Assertions | Raw failures | Seconds |
|---|---:|---:|---:|---:|
| probes | 1485 | 1497 | 0 | 7.626438 |
| original-minimal | 4 | 9 | 0 | 0.015322 |
| calendar-minimal | 8 | 12 | 0 | 0.101923 |
| race50 | 55 | 11 | 0 | 0.116309 |
| legacy | 26 | 24 | 0 | 0.193448 |
| decimal-04 | 196 | 124 | 4 | 1.146868 |
| 10^18 minute boundaries | 39 | 26 | 0 | 0.178628 |
| JSON numeric forms | 28 | 25 | 12 | 0.112498 |

Unchanged official isolated Stage1: **120 collected,120 passed,0 failed/errors/skipped/deselected/xfailed**, 30.943953s. Stage2 overshoot: **25 collected,0 passed,1 failed,24 not executed**,0 errors/skips/deselections/xfailed. The unchanged Stage1 service correctly claims1 on shipped checks; passing those checks does not override this independent rejection. Earlier-stage regression: none applies. Official output is preserved under `official/` and the original unique final-checks directory. The harness/test selection was not modified.

Fresh default8080 and override18309 startup/cross-container health measured0.409093s and0.341858s respectively. Current source/destination and genuine pre-serializer source `49287b4a5a1481f995c470ccae31776f03d4b863` ran in constrained offline images; current and legacy core/server hashes matched. Tests include separately staged50-client traffic, deterministic seed20261004/160-operation occupancy trace, atomic rollback/read snapshots, calendar/DST boundaries, genuine old tokens/references/create+batch receipts, and independent destination replacement. Full current configuration, giant integer request/receipt values and original receipt replay survive import. The decimal suite's maximum ordinary/control request times were0.021956s/0.050374s. These modest values do not prove arbitrary-size performance.

All own service containers and networks were removed with successful cleanup; images and clean clones remain. No other seat's process was touched. The clean exact candidate's five-file Stage1 subtree matches named production78732dde; four Interface runtime files match the revoked original2a4 source byte-for-byte. Source declarations, complete handoffs, empty original intake, both builder contributions, dependency imports and history are reviewed in `source-audit.json` and `source-inputs/`. No builder test/oracle implementation or external domain code was read. Build cache was available; no uncached-build claim is made.

Preserved verifier runner mistakes are separate: an AST selector chose the wrong `__init__`, the first decimal client's helper argument collided with `key`, the next driver used a relative Dockerfile path from the wrong directory, and an overlong container DNS label prevented a health client from reaching the service. Original error artifacts/source versions remain under `source-runner-error-01`, `decimal-runner-error-01/02/03`, `runtime-01/decimal-client.log`, `decimal-02` and `decimal-03`. Decimal04 and numeric01 are newly executed observations, not relabeled earlier runs.

Historical timestamps follow the recorded exact-instant/nearest representable minute-offset interpretation; original wall fields and genuine old offset-seconds receipt strings remain immutable. Literal historic IANA subminute wire offsets cannot simultaneously satisfy the minute-only RFC3339 grammar and are an explicitly disclosed interpretation risk. No receipt schema/value is enriched on historical replay.

This review elapsed880.605s from2026-10-04T02:43:20.153000+00:00 to2026-10-04T02:58:00.757771+00:00; per-run durations are measured separately. Whole factory elapsed is coordinator-owned. HarnessCodex; operator-configured modelgpt-6.1-sol. Actual model override, effort, token usage, catalog-estimated cost and billed spend are unknown. Hidden judging results, full genuine room export, publication and final submission remain operator-controlled. A new complete repair-candidate handoff and independent exact-revision reexecution are required before acceptance.
