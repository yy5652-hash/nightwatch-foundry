# Stage 2 integrity builder handoff

Package `TK-20261004-S2-systems-engineer-IMPLEMENT-1` was complete and acknowledged before work. Source Stage 1 is accepted/frozen at `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`, verified against `evidence/coordinator/accepted/stage-1.json` and its independent verdict SHA-256. One complete five-file copy preceded Stage 2 editing; the manifest comparison is `stage-2-source-copy.json`. Systems owns only new core and Systems evidence. Interface owns all transport/runtime/browser files. The existing Engine constructor/request contract and one-lock state boundary are unchanged.

## Implemented behavior

Member-set seating selects singles or declared unordered pairs, canonicalizes pair output to declaration order, sums capacity, and forbids undeclared/transitive/three-member combinations. Availability preserves the singles-only compatibility list and adds all eligible options, singles first in fixture order then declared pairs in declaration order. Occupancy uses member intersections with half-open exact-instant intervals, shared by create, amend, batch, seed and import validation.

New singleton responses have both table_id and table_ids; pair responses omit table_id. Real single/pair transitions remove obsolete fields. No-op/reverse-order amendments retain stored values. Batch candidates validate first and replace all records together under the same lock, allowing swaps while rejecting any overlap with changed, unchanged or external bookings. Cancellation releases every member; seeded cancelled singles/pairs do not occupy tables.

Genuine Stage 1 state retains its exact stored shape, tokens, hashes, timestamps and original receipts. Current public views add table_ids; original successful receipts replay their original JSON without new fields. Import also preserves the original meaning of newly recognized fields: a Stage 1 receipt body could include an ignored table_ids value. Only validation of those old snapshots ignores that formerly unknown field; the full parsed request is preserved for retry identity. New requests follow current Stage 2 validation.

## Diagnostic observations before container execution

Initial commands passed 11/11 new integrity scenarios in 0.879 s and 15/15 inherited scenarios in 1.945 s. Self-review added a genuine accepted-Stage-1 source case with formerly ignored table_ids values in create and batch bodies. It reproduced an import refusal before the historical request interpretation repair: one scenario failed, 0.183 s, preserved unchanged in `stage-2-legacy-ignored-reproduction-01.log`. This was an uncommitted builder diagnostic, not an independent candidate rejection.

After repair, commands:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-2-builder-probes.py --trace evidence/systems-engineer/stage-2-builder-oracle-engine-final.json
../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py --stage 2
```

Results: 11/11 new scenarios, no skips, 1.024 s (`stage-2-engine-final.log`); 15/15 inherited scenarios, no skips, 1.923 s (`stage-2-inherited-engine-final.log`). Scenario counts are not counts of independent normative requirements or individual assertions. New tests cover exact option order/capacity/canonicalization/nontransitivity, validation and failed-key reuse, pair/single conflicts and half-open cancellation, atomic transitions/swaps/rollback/no-ops, cancelled fixtures, invalid replacement, original pair receipts, genuine accepted Stage 1 accounts/tokens/create+batch bodies/receipts, 50 identical and 50 competing requests, and a concurrent pair amendment/single create. The separate member/interval oracle uses seed 20261004 and saves all 160 operations plus exact expected/observed outcomes; it uses only raw fixture sets and integer interval arithmetic, not production helpers.

Inherited probes add only a stage selector and the specified new singleton lookup field; original legacy receipt/export equality remains checked. Existing DST/calendar extremes, exact RFC3339 historical interpretation, true old offset-second receipt imports, huge base counts, typing, authentication, concurrency, rollback and snapshot preservation remain exercised.

## Source inputs and limits

Authoring inputs were the complete current task, inherited Stage 1/full Stage 2 specs, supplementary brief, timestamp decision, authoritative room plan, accepted manifest/verdict, own frozen Stage 1 code and own earlier diagnostics. No shipped tests or broader verifier probes/oracles were read or copied. No external domain product code/docs/schema, toy implementation, abandoned result or outside-run implementation was used. No memory files or web sources were used. Standard library only; runtime IANA data comes from the existing buildable image.

The recorded historical timestamp interpretation/immutable old-string exception remains inherited. Browser behavior is Interface-owned; these engine diagnostics claim no UI acceptance, hidden-suite result or stage promotion. Independent exact-revision review, official isolated checks, product interactions and final integrated image are separate gates. Harness Codex; configured gpt-6.1-sol; actual runtime override, effort, usage and spend unknown.

## Committed core and constrained HTTP result

Implementation revision: `e683361513d9af1d576e38dc79b04b44e4de6756`. A Systems-only temporary build context combined that committed Stage 2 core with the exact accepted Stage 1 Dockerfile/server/.dockerignore. This isolates API diagnostics from Interface's concurrent product work; it is explicitly not the final integrated browser image. The temporary context was removed after build. Build cache was available; no uncached-build claim is made.

Executed command:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-2-container-check.py --revision e683361513d9af1d576e38dc79b04b44e4de6756 --out evidence/systems-engineer/systems-engineer-s2-api-01
```

Results: new integrity HTTP suite **11/11 scenarios**, no skips, 1.183 s; inherited HTTP suite **15/15 scenarios**, no skips, 2.408 s. Total setup/build/probes/cleanup wall time: 8.182394459 s. Saved HTTP oracle trace again contains all 160 operations at seed 20261004. Artifacts are `systems-engineer-s2-api-01/{build.log,stage-2-http.log,inherited-http.log,member-oracle.json,runtime.json,timing-note.md}`. Exact Docker and suite argv, per-command time, image hashes, resource/network/mount observations and cleanup codes are recorded in runtime.json. The timing note corrects a metadata label without changing observed values or verdicts.

Four independently running service processes used ports 18113/18114 (current source/destination), 18115 (genuine accepted Stage 1 source) and 18116 (genuine pre-serializer legacy source). Each had 2 CPU/2 GiB, no mounts and an internal offline network. Current core hashes match e683361; accepted source matches 2a4b040; legacy source matches 49287b4. Frozen transport hashes also match their full named revisions. No exports/tokens/password hashes were written to artifacts. All four own containers and network were removed with zero cleanup return codes; own images remain. After the run all five frozen Stage 1 files still match the acceptance manifest.

Systems' integrity scope is complete. The Interface-owned Stage 2 transport/browser/runtime files must be committed and integrated before a complete independent Stage 2 candidate can be reviewed; this evidence successor alone is not a product acceptance candidate. The coordinator owns that sequencing and the complete numbered review handoff. No Stage 1 edit or Stage 3/4 extension was made.
