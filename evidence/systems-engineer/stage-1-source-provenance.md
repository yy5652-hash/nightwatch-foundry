# Systems Engineer Stage 1 source-provenance declaration

This factual declaration concerns `stage-1/core.py` and its rejection repair in run TK-20261004. All referenced files are inside the assigned dark-factory workspace. It adds evidence only; no service changes are authorized or made by this declaration.

## Inputs before initial implementation

1. Complete direct room package `TK-20261004-S1-systems-engineer-A`, parts 1/4 through 4/4 and its completion marker. This supplied the full factory task, full official Stage 1 specification, supplementary acceptance brief, Stage 1 ownership, and the Python `Engine.request` integration contract. Completeness was acknowledged before substantive execution and later posted again through `jam_send` for immediate visibility.
2. `kickoff/docs/participant-guide.md`, read completely as lines 1–300, 301–600 and 601–877. Intermediate tool truncation was followed by separate reads of the affected sections. The guide's toy walkthrough was read as part of the required complete guide; no toy implementation or solution file was opened or copied.
3. `factory/PRODUCT_ACCEPTANCE.md` and its full text in the direct package. The brief includes later-stage summaries; they were context only and supplied no later-stage implementation to Stage 1.
4. `kickoff/tablekeeper/spec/stage-1.md`, local lines 1–250, in addition to the complete official specification text supplied across the direct package. The implementation requirements came from the full specification, not merely those local lines.
5. This run's `architecture.json` node IDs and labels, read for task/component correlation. This was bookkeeping context, not a domain implementation input.
6. Runtime-provided mandates/instructions and the user's provided global working conventions. Python standard-library API knowledge was used without fetching external documentation or product source.

The design invariants were recorded in `evidence/systems-engineer/stage-1-invariants.md` before `core.py` was written. Initial implementation commit: `e9e15076a762ab437d349cb3e6768b4786e1432f`.

## Later initial implementation diagnostics

- After `core.py` existed, I wrote and ran `evidence/systems-engineer/stage-1-builder-probes.py` from the specification and my declared invariants. The first nine scenario tests were builder checks, not independent acceptance.
- I inspected this run's Interface Engineer-authored `stage-1/server.py` and `stage-1/Dockerfile` for integration. These were read after the core was authored; I did not edit or copy them into core. The adapter boundary had already been supplied in the complete handoff and room coordination.
- I read my own core, Git diffs, builder outputs, build logs, container health/settings and HTTP diagnostics. Two-process HTTP and export/import diagnostics used the newly authored service, with synthetic fixtures.
- Interface Engineer's assertion counts and the verifier's official harness counts were received as reported results. I did not open any shipped `tablekeeper/tests` test source, checker implementation or toy source file to implement the engine. No official test suite was imported into my builder probes.

## Inputs to the rejection repair

1. Independent Verifier rejection message `2901be08-327e-402e-b3b0-b23e85053724` for candidate `439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd`: two missing-required-array status errors and the maximum-calendar-year availability error.
2. Verifier-owned `evidence/independent-verifier/stage-1/reproduce.py`, read as a minimal diagnostic reproduction. I did not read or reuse the verifier's broader `probe.py`, `supplemental.py`, coverage or oracle implementation.
3. Verifier evidence files `band-work/final-checks/independent-verifier-s1-439b04e-runtime-03/reproductions-command.json` and `reproductions/summary.json`, read to establish the exact runner and observed failures.
4. The already supplied full Stage 1 specification, my own core and `git diff 439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd -- stage-1/core.py` (empty before edits). I added independent builder regressions, reproduced all three failures before repair, then changed the general required-field/type distinction and bounded-calendar arithmetic. No fixture-specific production branch was added.

Repair implementation commit: `6442d6d5aa3187aa090107733e41f685946044f1`. Builder evidence-only successor: `2e2e35b5ab0198fbaac3f96ac457ba9ef0a9c09d`. Repair details and preserved failure/regression outputs are in `evidence/systems-engineer/stage-1-repair-01.md` and the adjacent named logs. The broader verifier probes were not executed or copied by this seat.

## Libraries, examples and excluded sources

Production imports are Python standard library modules: `collections.abc`, `copy`, `datetime`, `hashlib`, `hmac`, `math`, `re`, `secrets`, `threading`, `urllib.parse`, `uuid` and `zoneinfo`. No third-party runtime package was used for core. IANA zone data is supplied in the Interface-owned container image. The supplied workspace `.venv/bin/python`, Git, Docker and configured Jam CLI were execution tools.

No existing domain product source code, API documentation or schema was accessed or reused. No toy solution, abandoned `band-work/result` implementation, outside-workspace implementation, prior-run implementation, web search or memory file was read or reused. No source code from another competition or project was inspected. Runtime dependency stack paths appearing in failure logs were not authoring inputs.

Harness: Codex. Operator-configured model: gpt-6.1-sol. Actual runtime model override, reasoning effort, usage and spend: unknown (not exposed). Current independent candidate-review status and acceptance belong to the coordinator and verifier; this declaration makes no acceptance claim.

## Later calendar repair diagnostic input

After this declaration's first commit, I received verifier message `dcfe2eef-3041-4189-8adb-c1bd69ad973a` and read `band-work/final-checks/independent-verifier-s1-dd64419-runtime-01/calendar/assertions.json` to inspect expected/observed endpoint results. I did not read or copy the calendar probe implementation. Own new builder regressions reproduced four failures before the absolute-instant repair. The full original Stage 1 specification remains the authoring authority; `stage-1-calendar-repair-02.md` records the mathematical change and the historical-offset grammar conflict raised with the coordinator.

## Timestamp interpretation repair inputs

Received the complete six-part package `TK-20261004-S1-systems-engineer-TIMESTAMP-3`, containing the complete task/specification, coordinator timestamp decision, full candidate-2 verdict and this seat's calendar repair report. The serializer was derived from that decision and integer/calendar constraints. Own new builder oracle exhausts allowed minute offsets; it does not use the production selection algorithm. For legacy receipt diagnostics only, own prior committed `stage-1/core.py` at `49287b4a5a1481f995c470ccae31776f03d4b863` is loaded or run from the retained image as a source process. This is the same run's authored implementation, not outside-domain source. Standard-library ZoneInfo supplies the actual historic Brussels/Berlin/New York offsets used in tests. No shipped tests, broader verifier probe implementation or external documentation/code was consulted for this repair.
