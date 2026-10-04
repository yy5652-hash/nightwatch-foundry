# Candidate 3 supplemental verdict: reject

Tested full candidate: `b4a124e3671ec22a4df0780343f6389ff4b70d05`. **Reject**. This supplemental source audit revokes the acceptance recorded in `../candidate-3/VERDICT.md` at evidence revision `b829a433957bc785e0dd2598316ce1b358303a91`. That original report and every earlier trace remain unchanged. Highest independently accepted consecutive stage is now **0**, pending a repaired candidate and full review.

Stage 1 §4 defines the three restaurant minute fields without an upper maximum. §5 assigns errors for stated rules and invalid values; it does not establish a hidden maximum from Python's datetime representation. Stage 3 policy limits are not a Stage 1 fixture restriction. A positive JSON integer `10^18` therefore remains applicable to this source-derived boundary audit. Expected behavior is a valid reset, one fitting opening slot for a huge grid, no fitting slots for a huge duration, and cutoff refusal for a huge cutoff. The reset failures prevented the latter behaviors from being executed; those rows remain unverified.

| Atomic requirement | Smallest changed input to the otherwise valid fixture | Expected | Observed |
|---|---|---|---|
| `TK1-large-slot_minutes-reset` | `slot_minutes: 1000000000000000000` | 204, no body | 422 `validation_failed`, message `validation failed` |
| `TK1-large-reservation_duration_minutes-reset` | `reservation_duration_minutes: 1000000000000000000` | 204, no body | 422 `validation_failed`, message `validation failed` |
| `TK1-large-cancellation_cutoff_minutes-reset` | `cancellation_cutoff_minutes: 1000000000000000000` | 204, no body | 422 `validation_failed`, message `validation failed` |

The fixture uses UTC, Tuesday 18:10–23:10, one capacity-2 table, ordinary 30-minute grid/90-minute duration/zero cutoff before changing only the named field. `large_minutes.py` contains the exact independently authored client and complete fixtures. `runtime-02/probes.json` preserves the first three operations: three assertions, three failures, 0.014409 s. Another fresh exact-revision process reproduced all three failures in `runtime-03/probes.json`: four operations/four assertions/three failures, 0.039324 s. Its first operation is the normal-value control, which returned 204. Request/response traces, full Docker argv and measured timing remain inspectable. No exported credentials were saved; trace credentials use fingerprints.

Exact repeat command, from the result repository, choosing a new output directory instead of reusing a retained one:

```sh
/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/.venv/bin/python -B /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-result/evidence/independent-verifier/stage-1/large_minutes_run.py --repo /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-result --workspace /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory --candidate b4a124e3671ec22a4df0780343f6389ff4b70d05 --out /Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-checks/independent-verifier-s1-b4a124e-large-minutes-03
```

The executable exited 1 on the final reproduced service failures. The first run was stopped before startup by an uppercase Docker image tag; `runtime-01/build.log` preserves that verifier-runner error. The tag was corrected, without any service edit. `runtime-02` preserved the probe's failed assertions despite its original wrapper exit 0; the wrapper was corrected to propagate the actual probe exit code. No failed assertion was converted to a pass. The independently repeated `runtime-03` control and three failures establish the current rejection.

Fresh detached clones of the exact candidate built per RUN.md. Both executed service processes had matching committed/image core and server hashes, `--network none`, no mounts, 2 CPU, 2 GiB and override PORT 18320. Startup-to-health was 0.329 and 0.248 seconds. Own containers were removed successfully; no other seat's process was touched. Builds used ordinary cache. Exact clone identities, inspections, command timings and cleanup are preserved.

The current expanded matrix has **797 atomic rows: 776 verified, 3 failed, 18 unverified**. The earlier 776 passing observations against this same revision remain valid evidence for those behaviors; they cannot establish these new boundary obligations. Its independently executed official 120/120 count and Stage 2 overshoot failure are unchanged historical observations, not acceptance after these source failures. The official suite was not repeated because no production revision changed and the three independent failures already reject promotion.

Owning-builder repair must preserve the published value range and implement the intended small-window semantics, including cutoff, opening-duration fit and grid iteration, without adding a timedelta-derived fixture maximum. Full candidate review must rerun these probes plus earlier independent and official checks. No implementation file was modified by the verifier. Historical timestamp interpretation/immutable imported-string risk remains as documented in the original candidate report and is independent of these failures.

Harness Codex; configured model gpt-6.1-sol. Actual runtime override, effort, usage, estimated cost and billed spend unknown. Complete factory elapsed time is coordinator-owned; the per-run durations above are observed. Genuine room export/publication/submission remain operator-controlled.
