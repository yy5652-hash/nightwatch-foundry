# Stage 1 calendar-range rejection repair 2

Affected candidate: `dd644198b6c0c24cebaee74435ac13d4dc33bd99`.
Verifier notification: `dcfe2eef-3041-4189-8adb-c1bd69ad973a`.

The previous three repairs passed; independent calendar probes found that New York at year 9999 and Berlin at year 0001 still failed when valid local times mapped outside Python's UTC calendar range. Availability and create each failed in both cases. The verifier reported official Stage 1 120/120; this did not imply complete calendar coverage.

Before edits, `git diff dd644198b6c0c24cebaee74435ac13d4dc33bd99 -- stage-1/core.py` was empty. I read the verifier's calendar `assertions.json` as diagnostic evidence, not its probe implementation. Added a builder scenario and ran `../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py StageOne.test_local_calendar_extremes_outside_utc_range`. All four reported endpoint failures reproduced, preserved in `stage-1-calendar-reproduction-02.log` (one scenario, four failing subcases, 0.179 s).

## Shared absolute-time invariant

An absolute instant is now an exact integer count of microseconds computed from the local ordinal day, clock and IANA offset. Its integer range is not restricted to Python's datetime years. Occupancy, descending list order, cutoff, closing fit and duration all use this representation; there are no zone/date-specific application branches.

ZoneInfo fold 0 remains the first repeated-hour occurrence. A forward offset difference between folds identifies a skipped local time without converting it to a bounded UTC calendar. For endpoints, ordinary values use ZoneInfo.fromutc. At UTC calendar boundaries, the engine inverts the local-clock/offset relation using the start and closing offsets, discovers candidate offsets and validates the exact absolute instant. Both valid endpoint folds are permitted; gap candidates are rejected. This preserves absolute duration through clock transitions while keeping local response dates within the specified calendar.

The existing export shape and receipt values are unchanged. Imported bookings are revalidated through the same shared helpers. Existing confirmed/cancelled records, current-start cutoffs, immutable retry receipts and amendment identity rules remain applicable.

The full builder regression passes 12 scenarios (`stage-1-calendar-regression-02.log`, 1.186 s before the additional gap guard). The new scenario verifies eight New York maximum-year slots, ten Berlin minimum-year slots, creation, exact 90-minute duration by independent offset arithmetic, private listing, occupancy refusal, import/export preservation and cutoff/cancel behavior. Existing DST, 50-request concurrency, swaps, rollback and first rejection regressions also pass. A final post-guard/container run follows in append-only evidence.

## Specification interpretation requiring coordinator record

Europe/Berlin at year 0001 has the exact IANA offset +00:53:28. Section 9 requires IANA offsets; the general response convention says RFC 3339, whose offset grammar has only hours and minutes. Exact IANA local-offset serialization and that grammar cannot both describe this historical offset. This was escalated to the coordinator through room message `7d382ed1-9f46-4ae1-b989-88b51a4e5efd`. The range repair preserves the existing exact IANA ISO serialization, including offset seconds; it does not silently round or alter the instant. Acceptance must record the interpretation/limitation rather than claim simultaneous compliance with incompatible grammars.

Only Systems-owned service/evidence paths changed. Engine.request and Stage 1 scope remain unchanged. Independent re-verification and promotion are pending. Harness Codex; configured gpt-6.1-sol; actual runtime override, effort and spend unknown.

## Final builder/container result

Implementation revision `49287b4a5a1481f995c470ccae31776f03d4b863` includes the boundary inversion gap guard. The complete Engine run passed 12 scenarios in 1.343 s (`stage-1-calendar-final-regression-02.log`). Fresh image build `docker build -t systems-engineer-tablekeeper-s1:calendar-02 stage-1` passed (`stage-1-calendar-build-02.log`).

Two independent services ran with nondefault ports 18104/18105, 2 CPU/2 GiB each and an internal Docker network. Command: `docker exec -i systems-engineer-s1-calendar-source-02 python - --url http://127.0.0.1:18104 --destination-url http://systems-engineer-s1-calendar-destination-02:18105 < evidence/systems-engineer/stage-1-builder-probes.py`. All 12 HTTP scenarios passed in 1.625 s (`stage-1-calendar-http-02.log`), including cross-process import of both boundary-year records and prior concurrency/DST/rollback cases. Image core SHA-256 matches the implementation revision; resource/network settings and hashes are in `stage-1-calendar-runtime-02.log`.

Systems-owned calendar containers/network were removed; images are retained. The earlier failure logs remain committed. These are builder diagnostics; independent exact-revision re-execution, official isolated checks and the historical-offset interpretation remain acceptance responsibilities.
