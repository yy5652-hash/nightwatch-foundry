# Candidate 2: reject

Tested full revision: `dd644198b6c0c24cebaee74435ac13d4dc33bd99`.
Stage 1 verdict: **reject**. Highest independently accepted consecutive stage: **0**.

The candidate includes repair `6442d6d5aa3187aa090107733e41f685946044f1`, and its Stage 1 tree is identical to builder candidate `2e2e35b5ab0198fbaac3f96ac457ba9ef0a9c09d`. All three original rejection reproductions now pass. New independent calendar-boundary probes show that valid local bookings are still refused when their UTC instant falls outside Python's datetime calendar. The verifier changed no implementation files.

| Source requirement and smallest interaction | Expected | Observed |
|---|---|---|
| §4 any calendar date, §8 fitting availability, §9 zone resolution: New York `9999-12-31`, Friday 18:00–23:00, 30-minute grid, 90-minute duration, capacity 2; `GET /availability?restaurant_id=r&date=9999-12-31&party_size=2` | 200; eight starts 18:00 through 21:30 | 422 `validation_failed`, message `Invalid value` |
| Same fixture; create `starts_at_local: "9999-12-31T21:30"` | 201; start `9999-12-31T21:30:00-05:00`, end `9999-12-31T23:00:00-05:00` | 422 `validation_failed` |
| Same source rules: Berlin `0001-01-01`, Monday 00:00–06:00; availability for that date | 200; fitting local slots | 422 `validation_failed` |
| Same fixture; create `starts_at_local: "0001-01-01T00:00"` | 201; a fitting local booking | 422 `validation_failed` |

These four HTTP failures reproduced in another fresh exact-revision process, in eight operations including each reset/login. The minimal fixture and command runner are `../reproduce_calendar.py`; full request/response trace is `runtime-02/calendar-minimal/operations.jsonl`. Exact executed Docker argv is in `runtime-02/extra-commands.json`. The wider probe is `../calendar_edges.py`, with `runtime-01/calendar/operations.jsonl` and `assertions.json`.

Two additional format observations are retained separately. Successful year-0001 afternoon bookings return `+00:53:28` for Berlin and `-04:56:02` for New York. Those follow historical IANA offsets but violate RFC3339's hours/minutes numeric-offset grammar in §3.4. §9 also requires offsets to follow the specified zone/date. The all-calendar-date, exact-zone-offset and RFC3339 demands conflict if the response must retain that historical zone offset. The coordinator was asked to resolve that representation interpretation explicitly, including Berlin midnight's UTC year-zero instant. No date restriction or failed-result conversion was silently introduced. The New York maximum-date refusal is sufficient to reject regardless of that interpretation.

The merged matrix has **735 atomic rows: 726 verified, 9 failed, 0 unverified**. Seven failed rows describe the two calendar-refusal families and their missing results; two are the unresolved historical format observations. Failed probe assertions remain failed observations, and the interpretation question is not an acceptance claim. Source-provenance coverage is now supported by the independent current-stage audit described below.

Official command, executed from kickoff:

```sh
<workspace>/.venv/bin/python -m harness run --track tablekeeper \
  --repo <workspace>/band-work/independent-verifier-s1-dd644198b6c0-20261004t004858 \
  --stage 1 --mode isolated \
  --out <workspace>/band-work/final-checks/independent-verifier-s1-dd64419-official-01
```

The unchanged isolated runner collected **120 Stage 1 checks, passed 120, failed/errors/skipped/deselected 0**, claimed Stage 1, and took **31.158 seconds** including build and overshoot. The next-stage invocation collected 25 checks, failed its first browser check and stopped: 0 passed, 1 failed, 24 not executed. The report's overshoot field is null; counts and log establish the observed outcome. This is public-check evidence, not a judging score.

| Independent run | HTTP operations | Assertions | Failed assertions | Probe wall time |
|---|---:|---:|---:|---:|
| Complete prepared suite | 1,441 | 1,430 | 0 | 7.061 s |
| Original three-defect reproduction | 4 | 9 | 0 | 0.016 s |
| Extended calendar edges | 35 | 39 | 9 | 0.605 s |
| New minimal date reproductions | 8 | 13 | 4 | 0.106 s |
| Staged 50-request HTTP workload | 55 | 11 | 0 | 0.135 s |

The complete suite's ordinary 50-client races reached 49 overlapping measured client intervals. An additional workload initiated 50 valid Content-Length-framed requests, held each final body byte until all 50 were in flight, then released them together. It achieved a measured peak of **50**, with one 201 and 49 original 200 receipts, one resulting reservation and all request durations below 5 seconds. This staging method is explicit in `../race50.py` and `runtime-03/race50/operations.jsonl`; no artificial service delay or production change was introduced. All complete-suite ordinary calls took at most 0.048 seconds and test controls at most 0.053 seconds. Request/timeout evidence is preserved, not inferred from source.

Clean clones and separately built single-image processes followed RUN.md with verifier-owned names and host ports 18300/18301. Docker inspection confirmed 2 CPU and 2 GiB, an internal network, no service mounts, default port 8080 and override 18309 reached from another container. First-run health took 0.348 and 0.379 seconds. Build cache was available; no uncached-build claim is made. All own containers/networks were removed and cleanup return codes were zero. No symlink/submodule/nested-service-repository entry or uncommitted service dependency was found.

`source-audit.json` preserves both builders' committed input declarations, the complete spec handoffs, root intake without service code, authored-path history, imports and source review. The intake commit is a root commit; Systems authored the engine/repair and Interface authored the transport/runtime documentation. The audit closes the current-stage source-input row using inspectable evidence. Builder exclusions remain seat declarations rather than a machine-wide forensic assertion. Post-candidate declarations concern unchanged candidate source. Genuine final room export is still operator-controlled; none was fabricated. Exports, password hashes and session tokens remained in memory; traces contain fingerprints.

Required next step: owning-builder repair of the calendar range handling, explicit coordinator resolution of historic timestamp representation, a complete new candidate handoff, and independent full rerun. Failure evidence and history must remain intact. No Stage 1 freeze or Stage 2 extension follows from this verdict.

Harness: Codex; operator model `gpt-6.1-sol`. Actual runtime override, effort, usage, estimated cost and billed spend are unknown. Per-run timings are measured above; complete factory elapsed time is coordinator-owned.
