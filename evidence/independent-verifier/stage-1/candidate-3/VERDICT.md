# Candidate 3: accept under the recorded timestamp interpretation

Tested full revision: `b4a124e3671ec22a4df0780343f6389ff4b70d05`.
Stage 1 verdict: **accept** under the explicit coordinator timestamp interpretation and immutable legacy-string exception described below. Highest independently accepted consecutive stage: **1**.

The independently executed matrix has **776 atomic rows, 776 verified, 0 failed, 0 unverified**. Every row names the full candidate, source section, separate implementation/verification owners, method, actual executable command, artifact path and verdict. The original missing-array errors, maximum UTC date failure, New York maximum-date failures, Berlin minimum-date failures and historical-format observations were rerun on this production revision. New evidence passes; all earlier failed candidates and traces remain unchanged.

The complete source/history and documented startup were reviewed. Only Systems' `core.py` changed between candidate 2 and this candidate; Interface's transport, Dockerfile and RUN.md stayed unchanged. Both builders' substantive commits, genuine rejections and repairs remain in history. The candidate was built from clean detached clones without host service files, symlinks, submodules or nested service Git repositories. The image's core/server hashes matched the exact current and legacy commits.

Official command, executed from kickoff using workspace Python:

```sh
<workspace>/.venv/bin/python -m harness run --track tablekeeper \
  --repo <workspace>/band-work/independent-verifier-s1-b4a124e3671e-20261004t010536 \
  --stage 1 --mode isolated \
  --out <workspace>/band-work/final-checks/independent-verifier-s1-b4a124e-official-01
```

The unchanged isolated harness collected **120**, passed **120**, and reported **0 failed/errors/skipped/deselected**. It claimed Stage 1. Official wall time was **30.417 seconds**, including build and next-stage probe. The Stage 2 overshoot collected 25 checks, failed its first browser check and stopped: **0 passed, 1 failed, 24 not executed**. The report's overshoot field is null; the count file and preserved log establish the observed outcome. No checker, suite selection or official test source was changed. Shipped checks are not the unseen judging suite or a judging score.

| Final independent execution | HTTP operations | Assertions | Failures | Probe wall time |
|---|---:|---:|---:|---:|
| Full source-derived suite and timestamp oracle | 1,485 | 1,497 | 0 | 8.077 s |
| Original three-defect minimal reproduction | 4 | 9 | 0 | 0.015 s |
| Four calendar-endpoint minimal reproductions | 8 | 12 | 0 | 0.112 s |
| Staged 50-request HTTP workload | 55 | 11 | 0 | 0.122 s |
| Genuine legacy export/receipt/mixed-state transfer | 26 | 24 | 0 | 0.202 s |

These assertion counts include repeated checks and are not unique normative counts. The main suite also preserved deterministic 160-operation occupancy traces with seed `20261004` and a separate half-open occupancy oracle. Time, validation, idempotency, concurrent occupancy, swaps/rollback, error order, cutoff, cancellation, failed-key reuse, replacement/reset, password hashing and original receipts were exercised through HTTP. All four required DST transitions passed. The offset oracle independently searches all legal RFC3339 numeric minute offsets; it does not call the production serializer.

The staged workload initiated 50 valid Content-Length-framed HTTP requests before releasing their final body bytes. Measured peak overlap was **50**, exactly one response was 201 and 49 were 200 with the original receipt; one reservation resulted. All final main-suite ordinary calls took at most 0.025 seconds and test controls at most 0.048 seconds, below their 5/10-second limits. Per-request traces and race timings are saved. Client staging is explicit in `../race50.py`; no service delay or production edit was introduced.

Docker inspection verified **2 CPU and 2 GiB per current and legacy service**, an internal network, and no service mounts. Default port 8080 and override 18309 were reached from separate containers, exercising the container interface. Final current startup-to-health times were **0.326 and 0.411 seconds**; the independently rebuilt legacy service took **0.376 seconds**. Own host ports were 18300–18302. Builds used ordinary Docker cache; this is a fresh-clone build claim, not an uncached-build claim. Every own container/network was removed with successful cleanup recorded in `runtime-02/extra-commands.json`.

The legacy source was a new clean clone/build of this run's actual pre-serializer implementation `49287b4a5a1481f995c470ccae31776f03d4b863`. Its HTTP service generated genuine historical offset-second records and original create/batch receipts, including a subsequently cancelled booking. Exports stayed in client memory. Current import preserved the exported JSON exactly, old tokens/references/strings and original create/batch receipts; replaced destination sessions became invalid. A new historical write followed the new serialization rule. Mixed old/new state then transferred to the second current process with old lookups and original receipt replays unchanged. No hand-edited export was presented as prior-version evidence. Commands, source hashes, fixtures and fingerprinted traces are under `runtime-02/legacy*`.

**Explicit interpretation and legacy risk.** Published §3.4 RFC3339 minute-offset grammar conflicts with literal historic IANA offsets containing seconds in §9. Decision `b81b8a32de2faa330d60db9f671de56073f25042` resolves new output by preserving the exact IANA instant and unchanged `starts_at_local`, while selecting the nearest representable minute-aligned fixed offset, adjusting its displayed clock, and choosing the lower numerical offset on ties. Modern minute offsets remain unchanged. Calendar-boundary selection, exact start/end instants, availability wires, original local fields, RFC3339 syntax, a genuine half-minute tie, replay and import all passed independent probes. This verdict explicitly follows that interpretation; it does not assert literal equality between a historical IANA second offset and the minute wire offset.

Successful original imported record/receipt strings remain immutable, including historical offset seconds. They may therefore retain the earlier grammar when returned after upgrade. They are not rewritten to claim new canonical formatting. This backward-preservation exception is part of the recorded decision and is supported by the genuine legacy probe. Literal historical wire-offset judging interpretation remains a known risk.

The source-provenance audit preserves complete task/spec handoffs, fresh-empty root intake, current committed seat input declarations, authored-path history, imports and source review. No existing domain-product input was identified in that evidence. Declared exclusions are seat declarations rather than machine-wide forensic proof. Genuine final room export is still operator-controlled; none was fabricated. Test exports, hashes and tokens remained in memory; durable traces contain fingerprints.

Two verifier-runner issues in `runtime-01` are preserved and classified in `runner-issues.json`: a supplementary client used the name of the already running legacy service, and an all-success minimal trace incorrectly asserted that an error envelope had been observed. The first prevented that legacy client from starting; the second was a probe assertion bug. Client names were separated and error-envelope evidence is now recorded only when an error response is observed. No service change was made for either issue. `runtime-02` repeats the complete suite and all supplementary probes successfully. No prior raw failure was erased or changed to a pass in place.

Stage 1 can now be frozen at the tested revision before extending its copy. This verdict grants no later-stage acceptance. Harness Codex; configured model `gpt-6.1-sol`; actual override, effort, token usage, estimated cost and billed spend unknown. Per-run timings are measured above; complete factory elapsed time remains coordinator-owned.
