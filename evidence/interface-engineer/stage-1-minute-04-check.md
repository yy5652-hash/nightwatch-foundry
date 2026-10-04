# Stage 1 MINUTE-BOUNDARY-4 interface regression

Named service candidate: `a1eeb79bcd4a21eb6bc43057311afa1ef674f313`.
Actual build HEAD: `2c29e2d647bd98aa9e9dfd31bb1bf9aaf9151e66`.
Their complete Stage 1 Git subtree hashes are identical, and container core.py
and server.py hashes match the named service candidate. Stage 1 was clean at
build. The later HEAD only affects non-service evidence; both full revisions
are recorded rather than relabeling the build revision.

Command: `python3 evidence/interface-engineer/stage-1-container-check.py`.
Evidence: `evidence/interface-engineer/interface-engineer-s1-20261004T012257494925Z/`.
Exact Docker argv, source hashes, limits, logs and results remain in that run.
Candidate equivalence is reproducible with:

```sh
git rev-parse a1eeb79bcd4a21eb6bc43057311afa1ef674f313:stage-1
git rev-parse 2c29e2d647bd98aa9e9dfd31bb1bf9aaf9151e66:stage-1
```

Observed: **577/577 assertions passed, zero failures**. Probe: 0.1394 seconds;
cached build/start/probe/evidence/cleanup: 1.7544 seconds. No networking, 2 vCPU,
2 GiB, nondefault PORT 9090 and 0.0.0.0 listener confirmed. Only this invocation's
own container was removed. No Interface service or probe changes were made.

The unchanged scope covers strict JSON/response framing, concurrent retry and
occupancy races, committed dropped-response recovery, replacement/replay, modern
DST and historical timestamp/calendar interpretation. Assertion counts include
repeated framing/timing checks and are not requirement or official-check counts.
The huge minute-configuration cases are covered by Systems' separate repair
diagnostics and independent verification, not newly asserted by this interface run.

Original Engine boundary and coordinator timestamp interpretation remain unchanged.
Historical minute-aligned wire offsets preserve exact instants/original wall
fields; the literal historical offset exception remains a final-report risk.
Prior successful strings and receipts remain immutable. The independent verdict,
official isolated and fresh-clone gates remain pending; no promotion or Stage 2
extension is claimed. Previous artifacts and failure observations are preserved.

Harness Codex; configured model gpt-6.1-sol; actual override/effort/usage/spend unknown.
