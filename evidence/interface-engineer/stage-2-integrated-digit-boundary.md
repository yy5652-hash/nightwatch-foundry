# Stage 2 integrated integer-boundary verification

Final tested full revision: `16aee9f0ea10de5b8fa81a84429cc337c3c4490f`.
It combines the Interface's frozen exact-decimal display, exact status and
restaurant-local end-time repairs with Systems' startup revision
`cf10edbcd2fc43a4458b1c8a12d441c3a292d7bf`. Systems sets the process-local Python
integer conversion limit to zero in Engine construction before transport serves
requests. Interface edited no core, adapter or Docker behavior for this repair.

The historical run at `87b816c63b59032e2bea6130a0b0308c47e9f6b0` was correct for
its own named tree, but its evidence successor `c745621aa671a135693088dcf6e9820e28250dd6`
also contained the newly committed core repair. The differing source was explicitly
reported to the coordinator, then this fresh combined execution closed that gap.
No earlier test result was relabelled or overwritten.

Command from the result repository:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-2-container-check.py
```

Observed result: **34/34 scenarios PASS, no skips; 557 assertions; 24.769 seconds**.
Artifacts: `interface-engineer-s2-20261004t023240634093z/`. There are 71 genuine
screenshots. runtime-report.json includes exact candidate, source/probe/image
SHA-256, commands, network, resources, health and cleanup. browser-report.json
preserves deterministic traces, scenario results and browser version.

The two additional original diagnostics beyond the passing 32 scenarios check:

- Exact 4301-digit search query, semantic numeric prefill, keyboard increments,
  emitted JSON integer, server-issued reference, unchanged-key/body retry, displayed
  singleton/pair capacities and guest count. No safe-integer or finite-float cap.
- Raw JSON with 4301-digit numeric capacity and base grid/duration/cutoff values;
  exact integer response values, a single huge-grid candidate, no fitting slots for
  huge absolute duration, ordinary cutoff refusal with unchanged record, and an
  ignored huge numeric field in a successful original request.
- Unchanged huge-number HTTP export/import between two independent current service
  processes, retained token/current booking/original successful receipt and body/key.
  Exports stayed in memory and were not published as demo state.
- Wrong party-size string remains 422; reuse with a different parsed body remains
  409 before validation; exponent, fractional, signed and negative query spellings
  remain 422. The large-integer repair does not relax those lexical/type rules.

The containerized probe enables its own Python integer conversion limit solely to
represent the exact client oracle and payloads. This does not patch the service,
its responses, the official runner image, or any official/verifier test. Current
service core/server/browser hashes matched the committed sources. Genuine older
source core/server hashes also matched their named revision.

All existing scenarios passed again, including 50 identical and competing pair
requests, real Stage 1 migration/lost response recovery, search races/conflicts,
keyboard/mobile layouts, exact lowercase status and all historical/DST/legacy end
times. Four service processes and the browser each ran with 2 CPU/2 GiB on one
Interface-owned internal offline network. No host dependencies were installed.
Default 8080 and override 9090 health passed; override 3.535 seconds includes four
container starts. Own containers/network/historical context were removed; images
remain. Frozen Stage 1 bytes stayed unchanged by Interface and matched the earlier
accepted tree before/after this run.

This is builder evidence, not specification coverage, independent acceptance or
a judging score. The verifier's separate 4301-digit observations against frozen
Stage 1 are not erased by this Stage 2 result and still require coordinator-owned
freeze exception/review sequencing. Interface Stage 2 production files are frozen
pending independent review; no Stage 3 work. Numeric-control wording and historical
wire-offset/immutable old-string interpretations remain explicit review boundaries.
All genuine failures and probe mistakes/repairs remain in the append-only ledger
and Git. Harness Codex; configured gpt-6.1-sol; actual model override/effort/usage/
spend unknown. Official isolated/inherited checks and clean-clone verdict remain
independent requirements.
