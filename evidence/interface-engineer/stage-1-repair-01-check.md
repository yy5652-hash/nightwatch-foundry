# Stage 1 repair 01: interface regression check

Tested candidate: `2e2e35b5ab0198fbaac3f96ac457ba9ef0a9c09d`.
Systems' implementation repair: `6442d6d5aa3187aa090107733e41f685946044f1`.
No interface service files or core files were changed for this check.

Command: `python3 evidence/interface-engineer/stage-1-container-check.py`.

Evidence: `evidence/interface-engineer/interface-engineer-s1-20261004T004209079869Z/`.
`run.json` records the exact candidate, clean Stage 1 paths and every Docker command.
`image-source-sha256.json` matches both core.py and server.py at the tested revision.
`container-limits.json` confirms networking disabled, 2 vCPU and 2 GiB.
The nondefault PORT 9090 listener was observed on 0.0.0.0.

Observed result: **489/489 assertions passed, zero failures**. The probe took
0.1176 seconds; build/start/probe/evidence/cleanup took 1.4735 seconds with build
cache available. Coverage is the same transport/runtime/retry/concurrency/
replacement/DST regression scope described in `stage-1-integration-handoff.md`.
The assertion count includes repeated wire-format and timing checks; it is not
a requirement count or an official check count.

The repair-specific missing-array/date-boundary tests belong to Systems' repair
report and independent verification. This interface run confirms the existing
integration flows still work against the repaired candidate; it does not claim
independent acceptance of every repaired boundary. Previous candidate evidence
is retained unchanged. Official isolated regression, fresh-clone checks and the
independent verdict remain promotion gates.

Assumptions remain unchanged: one shared Engine, unchanged request contract and
Content-Length-framed JSON bodies. No host dependency installation or runtime
downloads. The invocation removed only its own uniquely named container.

Harness: Codex. Configured model: gpt-6.1-sol. Actual model override, effort,
token usage, billed spend and catalog-estimated cost: unknown.
