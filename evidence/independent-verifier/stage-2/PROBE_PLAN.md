# Stage 2 independent verification preparation

Package `TK-20261004-S2-independent-verifier-VERIFY-PREP-1`, all six direct parts and final marker, was acknowledged before preparation in Band message `8439c939-88ae-4ca6-b5e5-a68df41d27ce`. Shared assignment is card #6. This is prepared verifier work, not a candidate verdict. No Stage 2 implementation, builder test/oracle or shipped test source was consulted to author these probes. The only harness files consulted were its runtime Dockerfile and dependency pins for the ordinary browser runner.

The matrix has **1,166 distinct rows: 801 inherited Stage 1 obligations and 365 Stage 2 additions**. Every row is presently `unverified`, with `UNASSIGNED` candidate and no execution evidence. Counts describe this ledger, not unique hidden checks or a judging score. Stage 1 remains accepted at `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`, under its recorded timestamp interpretation; that pass is never substituted for new execution on Stage 2.

`requirements.py` records source file, section, line, introduced/applicable stages, inheritance, implementation owner, independent verification owner, method, command, interpretation note and verdict. Candidate reports must replace placeholders with the full tested revision and actual artifacts. Bundled success, errors, order, atomicity, privacy, identity, retry and recovery duties are split. Any unsupported row remains unverified and blocks acceptance.

## Prepared executable probes

| Asset | Independent method and actual observations to collect |
|---|---|
| `api.py` | Singles, canonical reversed pairs, summed capacity, declared ordering, nontransitive/undeclared/invalid sets, fixture seeding, exact response shape, member occupancy, DST, transitions, cancellation, atomic pair swaps, rollback and original receipts. Export/import uses separate current processes. |
| `oracle.py` | Pure integer half-open occupancy and independently ordered options. Small transaction model exhausts all serial permutations constrained by observed real-time completion. It never imports production code. |
| `api.py --case concurrency` | Fifty actual Content-Length requests each with the final byte withheld until all are initiated; release together. Test competing shared-member requests and identical successful retry keys. Record timing, statuses, original receipts and resulting records. Concurrent create/PATCH/moves/cancel plus list, availability and transferable export reads must admit an oracle serial order. |
| `api.py --case invariants` | Seed `20261005`; 160 saved mixed single/pair create operations, each followed by authoritative availability checks against the independent capacity/occupancy oracle. |
| `browser.py` | Direct HTML routes, actual signup/login/logout, public browsing, every required single grid cell against independently fetched API data, pair cells, confirmations, lookup/cancel/privacy/cutoff and unchanged/edited request identity. |
| `browser.py --case race-single,race-pair` | Fetch and hold actual search A, complete B and open B's form, then deliver A. Preserve B's grid, distinct human labels and form. Another actual HTTP diner takes selected seating; observe real 409, refusal, availability refresh, retained inputs and a new selectable choice. |
| `browser.py --case lost-single,lost-pair` | Abort the original browser request before commit, and separately fetch its actual successful server response then abort delivery. Observe uncertainty without refusal/success. An unchanged real retry retains the original body/key and recovers the authoritative reference with one record. No mock success is supplied. |
| `browser.py --case visual` | Actual screenshots at 375 and 1280 CSS pixels on all four routes, pair form/success, keyboard Tab focus, visible labels, page width and computed styles. Screenshot review separately judges usability, contrast, focus, hospitality hierarchy, state distinction, human labels and unsupported claims. These subjective rows are never auto-passed from CSS presence. |
| `upgrade_api.py` | An independently built frozen Stage 1 process creates genuine single bookings and batch receipts, changes/cancels current records and exports in memory. Both current processes import that unchanged export. Check tokens, hashed-password login, identities, owner privacy, statuses, timestamps and unchanged original JSON receipts. |
| `browser_upgrade.py` | Forward the browser's actual login and legacy-compatible singleton request unchanged to the real frozen API; drop its actual committed response, import the genuine export between browser requests, retry unchanged and look up the recovered original reference. A non-legacy actual UI body produces an explicit pending-protocol result, not fabricated legacy receipt evidence or an automatic service rejection. |
| `runtime.py` | Exact detached clean clone, source history and full file hashes, unchanged frozen Stage 1, RUN.md, no nested Git/submodules/symlinks. Separately built current default/override listeners and genuine frozen Stage 1 process run at 2 CPU/2 GiB on an internal offline network, without service mounts. Observe health from another container and save Docker argv/inspection/cleanup. |

All original Stage 1 executable suites, original rejection reproductions, historical offset oracle, maximum/minimum calendars, unbounded minute-count probes, genuine legacy receipt probes and staged fifty-request workload must also run against the current service. Preserve the old failed runs without rewriting verdicts. Use the original Stage 1 deterministic seed `20261004` for that inherited suite.

## Timestamp and cross-version receipt interpretation

The recorded timestamp decision remains applicable: exact IANA instants and original wall fields survive; new historical strings use the nearest representable minute fixed offset with clock adjustment and lower numerical offset ties. Modern minute offsets stay unchanged. Genuine imported original strings and saved receipts retain their original representations, including historical seconds offsets. Literal historical wire-offset interpretation remains a judging risk.

A separate question was sent to the coordinator in messages `5817ecdd-2b15-491c-9bb9-d436e46a47f3` and `8a5030ed-2e00-4777-973f-7a5893f67755`: Stage 2's current response `table_ids` addition cannot retroactively change successful Stage 1 receipt JSON under inherited §7/§10. Proposed interpretation is unchanged imported successful receipts, with the new shape for current record responses/new receipts. The two old-receipt rows explicitly remain pending that decision and actual evidence.

Browser upgrade orchestration must retain a **genuine** Stage 1 source, a real already signed-in browser, the retained reference/form and exact pending body/key. The prepared API upgrade probe does not alone establish those browser rows. If the UI sends the legacy singleton `table_id` body, route its real login/create to the frozen API without changing that body; import the genuine state between browser requests, then retry unchanged against Stage 2. If the UI uses only singleton `table_ids`, the frozen Stage 1 API cannot create that exact body. Do not adapt it and call the result an identical original receipt, hand-edit an export, fabricate authentication, or silently impose an undocumented browser implementation requirement. Resolve and document the applicable real upgrade protocol with the coordinator before claiming these rows. Existing API receipt proof, browser current-to-current recovery and import/form continuity are separate observations.

## Execution gates and commands

No candidate is named in this preparation. Collect and acknowledge the coordinator's complete numbered committed candidate package before source review/build/execution. Do not run a dirty service tree. Use a new output directory for every execution, including errors and reruns.

Preparation checks (no candidate calls):

```sh
python3 -B evidence/independent-verifier/stage-2/prep_check.py
python3 -B evidence/independent-verifier/stage-2/oracle.py
```

After the full candidate handoff, use the exact workspace/repository/check-output roots from the assignment:

```sh
<workspace>/.venv/bin/python -B evidence/independent-verifier/stage-2/runtime.py \
  --workspace <workspace> --repo <result> --candidate <full40revision> \
  --out <checks>/independent-verifier-s2-<revision>-preflight-01
```

Inspect the saved RUN.md, authored source/history and preflight before invoking the execution mode with a separate output directory and `--execute --keep-running`. Run helper clients inside the saved internal network, using actual container URLs from preflight. Helper evidence mounts are not product dependencies. No service mount or outbound runtime access is allowed. Build cache availability must be stated; no uncached claim is inferred.

```sh
python /verifier/stage-2/api.py --base <current-source> --peer <current-peer> \
  --candidate <full40revision> --out /evidence/api --case all
python /verifier/stage-2/browser.py --base <current-source> \
  --candidate <full40revision> --out /evidence/browser --case all
python /verifier/stage-2/upgrade_api.py --base <current-source> --peer <current-peer> \
  --legacy <frozen-stage1-source> --candidate <full40revision> --out /evidence/upgrade
python /verifier/stage-2/browser_upgrade.py --base <current-source> \
  --legacy <frozen-stage1-source> --legacy-revision 2a4b0408a3453bc87d86bca3d0ec571f479e03ca \
  --candidate <full40revision> --out /evidence/browser-upgrade
```

Run the unchanged official command from kickoff, with a fresh output:

```sh
<workspace>/.venv/bin/python -m harness run --track tablekeeper \
  --repo <exact-clean-clone> --stage 2 --mode isolated \
  --out <checks>/independent-verifier-s2-<revision>-official-01
```

The documented harness runs Stage N and applicable earlier suites against that folder. Record actual collection/pass/fail/error/skip/deselection counts, claimed stage, duration and any next-stage probe actually invoked; do not invent an overshoot result from a null report field. Neither independent assertion totals nor public percentages are hidden judging scores.

## Evidence and verdict

Traces fingerprint credentials and opaque exported state; exports/tokens/password hashes remain in memory. Save screenshots of real product interactions, request body/key comparisons, deterministic seeds, source/image hashes, exact argv, measured start/request/wall times, cleanup outcomes, failed observations and probe-runner errors separately. Merge only evidence against the same named candidate; never promote an unsupported row using a builder summary. A final accept requires all applicable rows verified, official/current/inherited regression, clean startup and a committed named verdict. Stage 3 work is outside this assignment.

Harness Codex; configured model `gpt-6.1-sol`. Actual runtime override, effort, usage, estimated cost and billed spend are unknown. Factory-wide elapsed time remains coordinator-owned.

## Observed preparation controls

The final local preparation control parses nine Python files, imports the own HTTP client, validates unique all-unverified ledger rows and passes eight hand-derived oracle controls. It calls no candidate. The helper dependency image built successfully in 105.181 s with ordinary Docker cache available. Its first smoke failed before any browser or candidate interaction because the Stage 2 ledger omitted the `RESPONSE_FIELDS` export expected by the reused verifier HTTP client. `helper-smoke-01.log/json` preserve that verifier error. The ledger now exports the original own Stage 1 field constant. A separately tagged build `independent-verifier-s2:prepared-runner-02` took 0.538 s; smoke attempt 02 passed API/browser imports and a real blank Chromium viewport at 375 CSS pixels in an offline 2 CPU/2 GiB helper container (0.495 s). The smoke container was removed by `--rm`. These are verifier infrastructure controls, not Stage 2 behavior evidence, screenshots or startup proof. No prior failed output was overwritten.
