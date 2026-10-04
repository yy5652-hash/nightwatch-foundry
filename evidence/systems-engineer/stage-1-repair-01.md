# Stage 1 rejection repair 1

Rejected candidate: `439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd`.
Verifier message: `2901be08-327e-402e-b3b0-b23e85053724`.

The verifier found three defects beyond the passing official suite: omitted restaurant `opening_hours` and `tables` gave 400 instead of the specified missing-field 422; UTC availability on 9999-12-31 aborted with 422 when a late slot's duration crossed the maximum representable date. The official 120/120 count is verifier-reported evidence for the rejected revision, not acceptance of this repair.

Before editing, `git diff 439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd -- stage-1/core.py` was empty. Added builder regressions reproduced exactly three failures across two tests. Command: `../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py StageOne.test_required_fixture_arrays_missing_versus_wrong_type StageOne.test_calendar_maximum_and_large_grid_steps`. Evidence: `stage-1-rejection-reproduction-01.log` (3 failures, 0.263 s). Verifier-owned probes and evidence were read, not edited.

## Invariant repairs

- Check required restaurant array presence separately from supplied JSON types. Missing arrays give 422 `validation_failed`; explicit null, object, boolean, number or string give 400 `malformed_request`. Invalid reset still leaves the prior state untouched.
- Bound availability grid offsets by the local opening window, rather than repeatedly adding an unrestricted step past the window. A large valid grid step can offer the opening slot without constructing a future year.
- Check absolute duration against the remaining interval to closing before adding it to the start. Apply the same comparison to availability and booking validation. A valid day cannot fail because an unbookable late candidate would overflow; requesting such a booking gives 422 `outside_opening_hours`.

After repair: `../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py` passes all 11 scenarios in 1.022 s (`stage-1-repair-regression-01.log`). New regressions assert all eight UTC starts 18:00 through 21:30 on 9999-12-31, correct fitting and non-fitting create behavior, large slot steps, wrong-type preservation and rollback. Existing DST, concurrency, atomic swaps, retry, cutoff, authentication and import scenarios all remain green. `git diff --check` passes.

Only `stage-1/core.py` and Systems-owned evidence changed. The Engine integration boundary, original receipt storage, fixture configuration and Stage 1 scope remain unchanged. Container regression and new full revision are reported in the next append-only evidence entry. Independent re-verification and promotion remain pending.

Harness Codex; configured model gpt-6.1-sol; actual runtime override, effort and spend unknown.

## Container regression completion

Repair implementation revision: `6442d6d5aa3187aa090107733e41f685946044f1`.
`docker build -t systems-engineer-tablekeeper-s1:repair-01 stage-1` passed; build output is `stage-1-repair-build-01.log`.

Started two independent containers on an internal network, each limited to 2 CPU and 2 GiB, with nondefault PORT values 18102 and 18103. Command: `docker exec -i systems-engineer-s1-repair-source-01 python - --url http://127.0.0.1:18102 --destination-url http://systems-engineer-s1-repair-destination-01:18103 < evidence/systems-engineer/stage-1-builder-probes.py`. All 11 HTTP scenario tests passed in 1.381 s; output is `stage-1-repair-http-01.log`. This includes the rejection regressions and the previous full builder scenarios, with cross-process import.

`stage-1-repair-runtime-01.log` records the committed core hash followed by the matching image file hash, both resource limits, running state and Internal=true network setting. Systems-owned repair containers and network were removed after the successful run. Images are retained. There are no engine contract changes. The new candidate still requires independent official checks, specification coverage and a named verdict; builder success does not promote it.
