# Candidate 1: reject

Tested full revision: `439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd`.
Stage: 1. Verdict: **reject**. Highest independently accepted consecutive stage: **0**.

The service starts cleanly and passes the shipped Stage 1 checks, but violates three independently reproduced requirements. Production code was not modified by the verifier.

| Requirement | Minimal interaction | Expected | Observed |
|---|---|---|---|
| `TK1-reset-missing-restaurant-opening_hours` — §4 fixture fields and §5 required-field errors | `POST /_test/reset` with an otherwise valid restaurant and only `opening_hours` omitted | 422 `validation_failed` | 400 `malformed_request` |
| `TK1-reset-missing-restaurant-tables` — same sections | Same valid fixture with only `tables` omitted | 422 `validation_failed` | 400 `malformed_request` |
| `TK1-calendar-year-max` — §4 any calendar date and §8 availability slot/end boundaries | Reset UTC Friday hours 18:00–23:00, 30-minute grid, 90-minute duration, one capacity-2 table; `GET /availability?restaurant_id=r&date=9999-12-31&party_size=2` | 200; eight slots from 18:00 through 21:30 | 422 `validation_failed` |

All three failures were reproduced in four HTTP operations against another fresh exact-revision container. `runtime-03/reproductions-command.json` preserves the exact executed Docker argv; `runtime-03/reproductions/operations.jsonl` and `assertions.json` contain the complete smallest trace, request bodies and expected/observed results. The reusable runner is `../reproduce.py`. Repeat with a new output directory and newly started verifier containers; old networks and containers were removed after recording evidence.

Official command, run from kickoff with workspace `.venv/bin/python`:

```sh
<workspace>/.venv/bin/python -m harness run --track tablekeeper \
  --repo <workspace>/band-work/independent-verifier-s1-439b04e62325-20261004t003230 \
  --stage 1 --mode isolated \
  --out <workspace>/band-work/final-checks/independent-verifier-s1-439b04e-official-01
```

Observed official results: **120 collected, 120 passed, 0 failed/errors/skipped/deselected**. Official wall time was **155.916 seconds**, including build/runtime/overshoot work; the Stage 1 pytest log reports 18.22 seconds. The unchanged overshoot invocation collected 25 Stage 2 checks, ran one failing browser check and stopped: 0 passed, 1 failed, 24 not executed. It claimed Stage 1. The report's `overshoot` field is null; the observed overshoot result comes from the count file and log, not an invented report field.

| Independent execution | HTTP requests | Assertions | Failures | Probe wall time |
|---|---:|---:|---:|---:|
| Initial prepared suite | 1,206 | 1,235 | 0 | 5.408 s |
| Expanded full suite | 1,431 | 1,422 | 3: two requirement failures plus an aborted supplemental case | 7.159 s |
| Completed supplemental rerun | 235 | 202 | 4 assertions on 3 distinct requirements | 2.922 s |
| Minimal reproductions | 4 | 9 | 3 | 0.018 s |

Assertion counts are not unique requirement counts or unseen judging checks. The merged atomic matrix has **701 rows: 697 verified, 3 failed, 1 unverified**. The unverified source-provenance row is explicitly retained pending the complete room/source audit. No unsupported row was converted to a pass. The earlier supplemental abort was caused by the unexpected 422 at the maximum date; the probe was changed to record that failure and continue, and the original failed run remains intact.

Two separately built exact-revision clones started independent service processes. Docker inspection confirmed **2 CPU and 2 GiB per service**, with an internal network. Cross-container clients reached both `PORT=18309` and the absent-PORT default 8080 listener, verifying external container-interface access. In the expanded run, startup to health took **0.405 seconds and 0.460 seconds**. Fifty-client workloads attained **50 overlapping client request intervals** and every measured request stayed below 5 seconds; test controls stayed below 10 seconds. Builds used normal Docker cache and unique image tags; no claim of an uncached build is made. All own containers/networks were removed, with cleanup results preserved.

The clone was clean, had all required files and no symlink/submodule entries. History preserves the intake, both substantive implementation commits, diagnostics and verifier preparation. Systems owns `core.py`; Interface owns the concurrent JSON adapter, Dockerfile and RUN.md. No browser or later-stage surface was added to Stage 1. Export state, password hashes and bearer tokens stayed in memory; saved traces use fingerprints. The scrypt digests were independently recomputed from synthetic test passwords without publishing digest/salt/token values.

Risk and next step: repair the three named violations through the owning builder, retain this revision and failure evidence, then independently rerun the complete repaired candidate and unchanged isolated harness. The unseen judging suite is unavailable, and passing public checks is not a judging score. No Stage 1 freeze or Stage 2 extension is authorized by this verdict.

Harness: Codex. Operator-configured model: `gpt-6.1-sol`. Actual runtime override, effort, token usage, catalog-estimated cost and billed spend: unknown. Precise all-factory elapsed time remains coordinator-owned; per-run observed durations are above.
