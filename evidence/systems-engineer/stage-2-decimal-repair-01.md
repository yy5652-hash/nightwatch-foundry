# Stage 2 decimal conversion repair

The written base fixture/query integer rules apply beyond Python's default 4300-digit decimal conversion ceiling. Source reasoning is recorded separately in `stage-1-2-decimal-applicability.md` at full revision `69135c8fd1b4f3a1399b09217ec46d58032dd995`. The independent failures reported in room message `aecc8522-615f-4006-ad0b-a42920d28f81` prompted this owning-builder reproduction and repair. No independent probe implementation was read or copied.

## Preserved owning-builder reproduction

Command from the result repository:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-2-decimal-reproduce.py --out evidence/systems-engineer/systems-engineer-decimal-reproduction-01
```

The retained complete Stage 2 image matched `ff8472b5edc8513c1cd994678ea01471e7fb1ddc`; the genuine accepted Stage 1 image matched frozen revision `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`. Each process had 2 CPU, 2 GiB, no mounts and network none. Core and server image hashes matched each named revision. Each independent process executed seven HTTP operations/seven assertions with **five failed assertions**: four valid huge-count/capacity resets returned 400 malformed_request; the huge plain-digit party query returned 422 validation_failed. Normal reset controls returned 204. The Stage 1 probe took 0.062868167 s; Stage 2 took 0.064379959 s. Raw observations remain in `systems-engineer-decimal-reproduction-01/stage-{1,2}.json`; commands, resources and successful own-container cleanup are in `runtime.json`. The client enabled its own decimal conversion independently, and could not change either service process.

## Scoped change and invariant

Only current `stage-2/core.py` production behavior changes: Engine construction configures `sys.set_int_max_str_digits(0)` in the service process before the HTTP transport accepts requests. This removes the unpublished conversion ceiling consistently from standard JSON decode/encode and core query conversion. Integer values remain exact JSON numbers. Existing field type, lexical query, capacity, opening/grid/cutoff, idempotency and atomic state rules remain applicable. No adapter, image, host or Docker configuration changes were made. Frozen Stage 1 is untouched; repairing it requires the explicitly requested coordinator freeze exception and a new independently reviewed revision.

This uses Python 3.12's process-local standard-library setting in the packaged service, whose Engine is constructed before request parsing. There is no arbitrary numeric maximum, conversion to strings, rounding or large-duration endpoint synthesis. The resource limits still apply to supported requests; these probes use modest roughly 5 KB decimal payloads and bounded opening windows.

Authored inputs for this repair: the complete existing Stage 1/2 package, supplied specification and guide, recorded receipt/timestamp decisions, own accepted implementation and diagnostic files, the verifier's room failure report, and Interface's coordination message `fbf23bd4-fdf9-4ec0-aeb2-a417d4599544` suggesting the process-local setting. Systems selected and announced this boundary in room message `5fe7bfdc-53c9-471e-8a3f-0650b4219259` before editing. No external domain product code/API/schema, abandoned result, toy solution, outside-workspace implementation, shipped test source, or verifier probe source was used.

## Builder regression before named-image run

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-2-builder-probes.py
../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py --stage 2
```

The existing Stage 2 integrity scenarios passed **11/11** in 0.881 s; inherited scenarios passed **15/15** in 1.900 s, without skips. Logs are `stage-2-decimal-direct-01.log` and `stage-2-decimal-inherited-direct-01.log`. The new independently authored HTTP decimal probe checks configuration types, giant capacity and declared pair sums, grid/duration/cutoff semantics, exact query filtering, failure-key reuse, original receipts, cross-process replacement and invalid-type/lexical errors. It is outside graded folders, and the container driver now runs it after the ordinary and inherited regressions. Its constrained named-image result follows as an append-only entry after execution. No acceptance or hidden-suite result is claimed.

Harness Codex; configured model gpt-6.1-sol. Actual runtime override, effort, usage, estimated cost and billed spend remain unknown. Historical timestamp and original receipt interpretations remain unchanged. Independent review and the frozen Stage 1 repair gate remain pending.

## Named complete-image HTTP result

Production repair full revision: `cf10edbcd2fc43a4458b1c8a12d441c3a292d7bf`.

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-2-container-check.py --revision cf10edbcd2fc43a4458b1c8a12d441c3a292d7bf --integrated --out evidence/systems-engineer/systems-engineer-s2-decimal-integrated-01
```

The complete committed Stage 2 subtree built successfully. Existing Stage 2 HTTP scenarios passed **11/11** in 1.190 s; inherited scenarios passed **15/15** in 2.432 s, without skips. The new decimal suite executed **70 HTTP operations/108 assertions/0 failures** in 0.449887750 s. Total build/start/probe/cleanup wall time was 7.561144250 s. Both current source and destination independently held exact giant values, configuration, hashes, tokens and original receipts. Accepted Stage 1 and genuine earlier timestamp-receipt source processes continued to pass ordinary migration checks; this does not claim those unchanged old services accepted giant decimal resets.

Four own processes had 2 CPU/2 GiB, no mounts and an internal offline network; image core/server hashes matched their recorded exact revisions. Every own container/network cleanup returned zero. Commands, hashes, configuration, measured health probes and timings are in `systems-engineer-s2-decimal-integrated-01/runtime.json`. The independently seeded 160-operation member oracle trace remains alongside the HTTP logs. Browser review and official independent acceptance are separately owned.

The initial decimal trace logger recursively exposed private export state within its uncommitted local trace. Before any commit/public handoff, those private state payloads were replaced with fingerprints; HTTP statuses, assertions and timing observations remain unchanged. The logger now fingerprints state at capture, so future traces never contain token-map keys or exported account/session state. This logging correction is evidence-only; no response or production result changed. A separately named follow-up run verifies corrected capture below.

## Corrected capture validation

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-2-container-check.py --revision 6aff0b1a59796eb3aa218a3b26b38751977ef2c0 --integrated --out evidence/systems-engineer/systems-engineer-s2-decimal-integrated-02
```

This evidence-only successor has the same repaired Stage 2 production source. The separate complete-image run passed **11/11** current HTTP scenarios in 1.185 s and **15/15** inherited HTTP scenarios in 2.442 s, with no skips. The decimal suite again passed **70 operations/108 assertions/0 failures**, in 0.440892209 s; total build/start/probe/cleanup was 7.289113000 s. Named image hashes, constraints and zero-return cleanup remain recorded in its new `runtime.json`. Earlier outputs were not reused.

A recursive inspection of the resulting `decimal-regression.json` verified that every state/tokens payload consists only of `private_state_sha256`, and each password/token/password_hash field consists only of `fingerprint`: 20 private-state fingerprints and 30 credential fingerprints were checked. Assertions, expected exact-integer equality and observed HTTP statuses remained executable and passed. Exports and live credentials are not committed. The corrected capture and its separate result are preserved independently from the initial trace redaction.

Systems scope is complete for the current Stage 2 decimal repair. Stage 1 remains byte-for-byte frozen; the coordinator must supply the explicit exception and complete applicable package before any Stage 1 production edit. A new full independent Stage 2 review/official run is also required before promotion. No new browser/transport behavior, timestamp decision or historical receipt schema was changed by Systems.
