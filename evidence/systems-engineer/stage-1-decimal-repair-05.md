# Stage 1 serialized decimal repair

Package: `TK-20261004-S1-systems-engineer-DECIMAL-REPAIR-1`, all six parts and END marker received. Completeness acknowledgement room message: `74c5a7e1-f533-4a3e-9ff3-c93864ea1511`. Shared Systems repair card: #7. This initial entry is analysis before explicit source release; it changes no production source. The original accepted/frozen source `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`, its revoked acceptance and all failure artifacts remain preserved.

## Invariants and chosen boundary

Stage 1 sections 4/5/8 impose no numeric/digit ceiling on positive base grid/duration/capacity, nonnegative cutoff or a positive plain-digit party query. The exact 4301-digit integer is a correct JSON number and a modest payload. Existing applicability and conversion analysis is committed in `stage-1-2-decimal-applicability.md` (`69135c8fd1b4f3a1399b09217ec46d58032dd995`) and `stage-1-2-decimal-checkpoint.md` (`5c0b96e9d19db680059401237a3361569455cd2d`).

The required invariant is exact integer representation through JSON parse/encode, query conversion, configuration, reservations, successful original parsed retry bodies/receipts and exported/imported state. Wrong types, booleans, fractions, invalid query lexical forms, nonpositive values, capacity/grid/opening/cutoff checks and their error precedence remain independent of conversion setup. A huge duration cannot fit an ordinary same-day window, so no huge endpoint timestamp is created. All local-calendar/timestamp and original-receipt decisions remain applicable.

The chosen narrow repair, after explicit release, is the service-process standard-library decimal setting at Engine initialization, before the unchanged transport begins accepting requests. This covers the packaged JSON decoder/encoder and validated query conversion together without changing JSON number types, transaction boundaries or the schema. It makes no host/Docker/network change and touches no Interface-owned adapter/runtime files. This is the same independently justified boundary already implemented in Stage 2; that source and its diagnostics remain preserved.

Reset/import continue to validate an entire proposed state before replacement under the Engine lock. Failed create/move requests retain reusable keys; successful create/move receipts preserve their original bodies and values after mutation and across independent-process import. No parsing shortcut, weakened grammar, new cap or receipt enrichment is authorized.

## Preserved pre-repair observation and probe scope

The own separately authored exact-image reproduction already executed unchanged genuine Stage 1: `systems-engineer-decimal-reproduction-01/stage-1.json` contains seven operations/seven assertions/five actual failures in 0.062868167 s. Four huge integer resets were 400 malformed_request, the plain-digit query was 422 validation_failed, and normal reset controls were 204. Its core/server hashes, 2 CPU/2 GiB, network none/no mounts and zero cleanup return codes are in that directory's `runtime.json`. This evidence remains unchanged; the coordinator-supplied independent reports are distinct. No verifier probe implementation was read or copied.

After release the own black-box decimal regression will use `--stage 1`, two independent current processes and a separately built historical receipt source. It will cover the five actual boundaries, exact capacity/party values, giant grid/fit/cutoff outcomes, invalid type/fraction/query forms, failed reset atomicity, successful move receipts and full parsed giant request-body identity, cross-process replacement and original replay after mutations. Existing 15 inherited builder scenarios cover authentication, owner privacy, concurrency, half-open occupancy, rollback, DST/calendar extremes, legacy timestamp receipts and the earlier huge-minute repair.

The service/client conversion settings are separate. A client enabling decimal parsing must never be mistaken for configuring the old source process. Traces retain credential/export fingerprints only. Modest 4301-digit passing probes do not imply arbitrary payload sizes meet CPU/memory/time requirements. The process-wide setting stays inside the single service interpreter and must be initialized before future transport request parsing.

No Stage 1 source edit occurs until the explicit release. A named coherent production commit, fresh constrained exact-image evidence and full handoff will be appended after execution. Builder diagnostics do not restore acceptance; coordinator-owned Interface and independent official/806+ requirement review must precede renewed freeze or Stage 2 promotion. Harness Codex; configured model gpt-6.1-sol; actual override/effort/usage/spend unknown.

## Released implementation

Explicit source release was received as room message `ea8542d2-24c7-4fba-b157-1ca8807cfbba`, after completeness acknowledgement. The append-only revocation manifest `evidence/coordinator/accepted/revoked-stage-1-2a4b0408a3453bc87d86bca3d0ec571f479e03ca.json` is committed at `583e5d079e6681b00b8c370f95ccf97cd7ba162f` and names independent evidence `fe68f4ef60580d73c17ba2a21c6a4d20b77e8e41`. Original accepted source was verified unchanged immediately before this repair.

Only `stage-1/core.py` production changes: an import of sys and initialization of `sys.set_int_max_str_digits(0)` before Engine state/lock setup. This matches the independently derived service-process boundary in the pre-release analysis; Stage 2's existing Engine boundary remains untouched. Interface-owned Stage 1 server/image/RUN files are unchanged. All schemas, current-state responses, successful historical receipts, timestamp serialization and lock behavior are unchanged.

The own shared decimal probe now adds successful giant-party move receipts and replay after edits/import, altered ignored giant integers conflicting before invalid party validation, fractional base/party refusal, four malformed raw bodies and complete-state equality after each invalid reset. Its earlier Stage 2 results remain historical observations of that earlier probe revision; no passing count is silently rewritten. No independent test source was consulted.

Command `../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py` passed all **15/15** current Stage 1 Engine scenarios in 1.879 s without skips; log `stage-1-decimal-direct-05.log`. The new owned driver builds the complete five-file Stage 1 subtree at a named full commit into its own image, starts two independent repaired processes plus a genuine old receipt source at 2 CPU/2 GiB on an internal offline network, and executes the decimal plus inherited HTTP suites. Its observed named-image result will follow below after execution.

Inputs for this repair are the full six-part authorized package/specification/guide/brief and recorded decisions, Systems' existing implementation/own diagnostics and prior applicability analysis, coordinator source-release/revocation manifest and verifier's supplied failure report/assertions. No verifier probe implementation, external product code/API/schema, toy/abandoned implementation, shipped test source or outside-workspace project was accessed or reused.

## Named constrained HTTP result

Production full revision: `78732dde56ba6116d0722136beba74b674811105`.

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-decimal-container-check.py --revision 78732dde56ba6116d0722136beba74b674811105 --out evidence/systems-engineer/systems-engineer-s1-decimal-05
```

The complete five-file committed Stage 1 context built successfully as `systems-engineer-tablekeeper-s1:decimal-05-20261004t023841`. The separately running repaired source and destination passed **92 decimal HTTP operations/146 assertions/0 failures** in 0.453509375 s. All five actual inherited failures are repaired; exact configuration/capacity/party JSON numbers, duration/grid/cutoff refusal, invalid type/fraction/grammar, atomic malformed/invalid reset, successful create/move full-body original receipts and independently running replacement/replay passed. The maximum observed decimal-suite request duration was 0.036123250 s, below the ordinary/control limits for this scope.

All **15/15 inherited Stage 1 HTTP scenarios** passed in 2.430 s without skips, including concurrent retries/occupancy, swaps/rollback, DST, local-calendar extrema and genuine pre-serializer legacy export/original receipt behavior from separately running source revision `49287b4a5a1481f995c470ccae31776f03d4b863`. The old source was not edited or configured by the repaired service/client.

Total complete-context build/start/probe/cleanup wall time was **7.029625042 s**. Three own service containers had 2 CPU, 2 GiB, no mounts and an internal offline network, using nondefault ports 18119/18120/18121. Core/server runtime hashes matched each named source revision. The post-launch health probe durations were 0.148657708, 0.138211959 and 0.130762708 s; these are measured probe durations after docker run, not a fresh-clone or uncached-build claim. All own containers/network were removed with zero cleanup return codes; images remain retained. No other seat's process was touched.

Artifacts: `systems-engineer-s1-decimal-05/{build.log,decimal-http.log,decimal-regression.json,inherited-http.log,runtime.json}`. Runtime JSON contains exact executed argv, build-source hashes, image identities, constraints, timings and cleanup. The driver's recursive inspection verified that every captured state/tokens and password/token/password_hash payload is fingerprinted; no full export, token-map key or password-hash payload is committed.

`stage-1-2-decimal-inheritance-05.json` independently checks the committed Engine initialization AST is identical between this repaired Stage 1 and existing Stage 2 boundary revision `cf10edbcd2fc43a4458b1c8a12d441c3a292d7bf`. All four Interface-owned Stage 1 runtime files remain byte-identical to original source `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`. This is inspectable inherited-boundary evidence; a renewed accepted Stage 1 manifest and independent later Stage 2 review are still required. No Stage 2 production path was edited or committed by this repair.

Remaining risk/gates: the historical timestamp/immutable legacy-string interpretation and original-receipt shape remain disclosed; process-wide initialization must precede request parsing; modest decimal probes do not establish arbitrary-payload performance. These are owning-builder diagnostics from exact committed contexts, not a clean-clone independent verdict, official isolated test count or restored acceptance. Coordinator will route full Interface and independent requirement/startup/official/regression review. Highest independently accepted consecutive stage remains 0 until a named renewed verdict. Configured model gpt-6.1-sol; actual override/effort/usage/estimated/billed spend unknown.
