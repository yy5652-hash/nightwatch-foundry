# Stage 1 builder report

Engine candidate: `e9e15076a762ab437d349cb3e6768b4786e1432f`.
Engine path: `stage-1/core.py`. No other service path was edited by Systems Engineer.

## Observed checks

| Command or interaction | Result | Evidence |
|---|---|---|
| `../../.venv/bin/python -B -c 'import ast,pathlib; ast.parse(pathlib.Path("stage-1/core.py").read_text())'` | Syntax passed | Room tool result |
| `../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py` | 9 scenario tests passed, 0.819 s | `stage-1-builder-probes-01.log` |
| Same Engine probe command after imported move-body type validation | 9 scenario tests passed, 0.808 s | `stage-1-builder-probes-02.log` |
| `docker build -t systems-engineer-tablekeeper-s1:builder-01 stage-1` | Build passed | `stage-1-build-01.log` |
| Host HTTP probes against ports 18100/18101 on an internal Docker network | 9 connection errors, 0.015 s; no service behavior tested | `stage-1-http-probes-01.log` |
| `docker exec systems-engineer-s1-primary-01 python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8091/health").read().decode())'` | 200 healthy JSON inside container | Room tool result |
| `docker exec -i systems-engineer-s1-primary-01 python - --url http://127.0.0.1:8091 --destination-url http://systems-engineer-s1-destination-01:8092 < evidence/systems-engineer/stage-1-builder-probes.py` | 9 HTTP scenario tests passed, 1.115 s | `stage-1-http-probes-02.log` |

The host connection errors came from choosing an internal network whose containers had no published host bindings. Both processes were running and healthy. The retry executed over HTTP inside that network, with state exported from one service and imported into the second service process. Probe loading was adjusted to permit execution via stdin without reading production source when both HTTP URLs are supplied. No service-code repair was needed for this environment issue.

Both services ran with 2 CPU, 2 GiB, internal networking and nondefault ports 8091 and 8092. Settings are recorded in `stage-1-container-settings-01.log`. Systems-owned containers and their network were removed after checks; the builder image remains available. The probe resets private synthetic fixtures and writes neither complete exports nor session tokens to disk.

Covered builder scenarios include public browsing; multiple sessions; owner-only lookup; wrong types and invalid values; failed-key reuse; immutable receipts after edit/cancel; 50 concurrent identical creates with exactly one 201; 50 competing creates with one 201 and 49 occupancy refusals; half-open boundaries; unavailable and closed slots; atomic occupied-table swaps; failed amendment/batch rollback; ordered non-occupancy errors; no-op moves; current-start cutoff; past creation; spring skips and first fall occurrence in both specified zones; absolute duration; cross-process replacement; preserved tokens, hashes and original receipts; repeated import; invalid import rollback; reset clearing imported state.

These are builder diagnostics, not independent acceptance or hidden-test evidence. Independent official isolated checks, clean-clone review and full requirement coverage remain the verifier's responsibility. The assumptions and transaction design are in `stage-1-invariants.md`.

Harness: Codex. Configured model: gpt-6.1-sol. Actual runtime model override, reasoning effort, token usage and billed/catalog-estimated spend: unknown. Work start was approximately 2026-10-04 00:16 UTC; precise factory elapsed time is coordinator-owned.
