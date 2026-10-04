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
