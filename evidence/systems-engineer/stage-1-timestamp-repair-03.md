# Stage 1 timestamp interpretation repair 3

Complete package: `TK-20261004-S1-systems-engineer-TIMESTAMP-3`, parts 1/6 through 6/6 and completion marker; immediately visible completeness acknowledgement `1544872a-fd41-4807-bda5-b6fd58829605` preceded editing. This carries the complete existing task/specification and the coordinator's explicit historical-offset representation decision. The accepted-stage count remains coordinator/verifier-owned; no Stage 2 work was performed.

## Decision implemented

Resolve the start and duration using exact IANA offsets/folds. Keep `starts_at_local` unchanged. Minute-aligned IANA timestamps retain their existing local clock/offset representation. For subminute offsets, select the nearest minute-aligned fixed offset whose adjusted clock fits years 1–9999; equal distances select the lower numerical offset. The adjusted clock represents exactly the original integer instant. Neither the instant nor offset seconds are truncated or rounded.

The implementation derives the allowed offset interval mathematically from the instant and representable clock bounds, then checks the clamped floor/ceiling neighbors of the exact offset. There are no zone/date-specific production branches. Availability and newly computed starts/ends use the same serializer; UTC creation timestamps retain their existing form.

An independent builder oracle exhausts all legal numeric minute offsets -23:59 through +23:59, filters those with representable clocks and selects by distance then offset. It verifies syntax, exact instant, both start/end selections, unchanged wall fields, all availability start instants and receipt replay. Fixtures include Berlin midnight in year 0001, New York historical subminute offsets, Brussels' half-minute tie, New York year 9999 and modern Berlin fall-back duration.

## Original timestamp and receipt preservation

Import verifies starts/ends by exact instant rather than requiring their strings to equal newly generated canonical strings. It preserves the original stored strings. The same applies to successful create receipts, whose original strings remain immutable on replay. Unchanged timestamp instants in amendments retain their existing representations, preserving no-op values. All other booking, identity, occupancy and replacement validation remains in place.

The builder legacy probe loads this run's own earlier core from commit `49287b4a5a1481f995c470ccae31776f03d4b863` as a diagnostic source service. It creates a genuine old-format receipt/export in memory, then imports it into the repaired engine and checks exact export equality, lookup and replay. A newer booking in the imported state uses the minute-aligned representation. The mixed state transfers to another repaired engine and retains old receipts. For container probes, a separate service from the retained pre-serializer image supplies the same legacy export; no hand-edited export is presented as an actual prior-service result.

Existing successful historical receipts/records may therefore retain offset seconds when returned after upgrade, as required by immutable-receipt/import preservation. New serialization follows the explicit coordinator interpretation. The literal historical wire offset is minute-aligned instead of the exact IANA subminute offset; the exact instant and restaurant wall field preserve resolution. This is a recorded interpretation exception, not simultaneous literal compliance with the originally incompatible grammars.

## Observed builder checks

Before service edits, `StageOne.test_exact_rfc3339_historical_representation` reproduced three historical wire-format failures (Berlin, New York, Brussels); modern and maximum-year cases passed. Command: `../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py StageOne.test_exact_rfc3339_historical_representation`. Evidence: `stage-1-timestamp-reproduction-03.log`, three failing subcases, 0.349 s.

Initial full post-repair builder run: 14/14 scenarios passed, no skipped tests, 1.851 s (`stage-1-timestamp-regression-03.log`). The final extended oracle and constrained HTTP run are recorded in the next append-only entry. Prior failure artifacts remain unchanged. Only `stage-1/core.py` and Systems-owned evidence paths changed; Engine.request, export schema and Stage 1 scope remain unchanged.

Independent exact-revision acceptance, official isolated regression and clean-clone review remain pending. Harness Codex; configured gpt-6.1-sol; actual runtime model override, effort, usage and spend unknown.

## Final implementation/container evidence

Implementation revision: `f4eeac50227a59ce785768dbb37bb4641d83c88a`. Final extended-oracle Engine run passes 14/14 scenarios without skips, 1.675 s (`stage-1-timestamp-final-regression-03.log`). New image build `docker build -t systems-engineer-tablekeeper-s1:timestamp-03 stage-1` passed (`stage-1-timestamp-build-03.log`).

Two repaired service processes and one actual prior-version service process ran on an internal network, each limited to 2 CPU and 2 GiB. Nondefault ports were 18106 (current source), 18107 (current destination) and 18108 (legacy source). Current containers used `systems-engineer-tablekeeper-s1:timestamp-03`; legacy used the retained `systems-engineer-tablekeeper-s1:calendar-02` image from implementation `49287b4a5a1481f995c470ccae31776f03d4b863`.

Command: `docker exec -i systems-engineer-s1-timestamp-source-03 python - --url http://127.0.0.1:18106 --destination-url http://systems-engineer-s1-timestamp-destination-03:18107 --legacy-url http://systems-engineer-s1-timestamp-legacy-03:18108 < evidence/systems-engineer/stage-1-builder-probes.py`. All 14 HTTP scenarios passed without skips in 2.309 s (`stage-1-timestamp-http-03.log`), including exhaustive offset-oracle checks and genuine old receipt/export transfer to repaired processes. Exports and credentials stayed in memory.

`stage-1-timestamp-runtime-03.log` contains expected/current image core hashes, expected/legacy image core hashes, all three constrained running states and Internal=true network setting. Both hash pairs match. All Systems-owned timestamp containers and network were removed after successful checks; images remain available. Service changes only affect core; the original Engine contract and deployment surface remain Interface-owned and unchanged.

Builder completion does not promote the stage. The new full revision must receive the complete numbered review handoff and independent re-execution. Acceptance must retain the explicit interpretation exception: the subminute IANA offset is represented by a minute-aligned fixed offset plus an adjusted clock preserving its exact instant; imported successful old receipt strings are not rewritten.
