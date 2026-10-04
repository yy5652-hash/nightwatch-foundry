"""Append a supplemental verdict without overwriting earlier accepted evidence."""
import csv
import datetime
import hashlib
import json
import shutil
from pathlib import Path
from requirements import ROWS

repo = Path(__file__).resolve().parents[3]
workspace = repo.parents[1]
candidate = "b4a124e3671ec22a4df0780343f6389ff4b70d05"
target = Path(__file__).with_name("candidate-3-large-minutes")
target.mkdir(exist_ok=False)
checks = workspace/"band-work/final-checks"
for number in [1, 2, 3]:
    source = checks/f"independent-verifier-s1-b4a124e-large-minutes-0{number}"
    shutil.copytree(source, target/f"runtime-0{number}")
old = {row["requirement_id"]: row for row in csv.DictReader((Path(__file__).with_name("candidate-3")/"coverage.csv").open())}
results = json.loads((target/"runtime-03/probes.json").read_text())
assert results["candidate_full_revision"] == candidate
assert results["http_operations"] == 4 and results["failed_assertions"] == 3
assert results["results"][0]["passed"]
observations = {row["requirement_id"]: row for row in results["results"]}
command = f"{workspace}/.venv/bin/python -B {repo}/evidence/independent-verifier/stage-1/large_minutes_run.py --repo {repo} --workspace {workspace} --candidate {candidate} --out {checks}/independent-verifier-s1-b4a124e-large-minutes-03"
rows = []
for requirement in ROWS:
    row = dict(requirement)
    rid = row["requirement_id"]
    if rid in old:
        row = old[rid]
    else:
        row.update(candidate_full_revision=candidate, executable_command_or_interaction=command,
                   evidence_path="evidence/independent-verifier/stage-1/candidate-3-large-minutes/runtime-03/probes.json#"+rid, verdict="unverified")
        if rid in observations:
            row["verdict"] = "verified" if observations[rid]["passed"] else "failed"
        else:
            row["verification_method"] = "Not executed: valid reset fixture was refused before this probe could run."
    rows.append(row)
counts = {status: sum(row["verdict"] == status for row in rows) for status in ["verified", "failed", "unverified"]}
assert counts == {"verified": 776, "failed": 3, "unverified": 18}
with (target/"coverage.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(ROWS[0]))
    writer.writeheader()
    writer.writerows(rows)
summary = dict(candidate_full_revision=candidate, verdict="reject", supersedes="candidate-3/VERDICT.md acceptance committed at b829a433957bc785e0dd2598316ce1b358303a91",
               highest_independently_accepted_stage=0, rows=len(rows), **counts, command=command,
               operations=results["http_operations"], assertions=results["assertions"], failures=results["failed_assertions"],
               duration_seconds=results["duration_seconds"], model="operator-configured gpt-6.1-sol", actual_override_effort_usage_cost_spend="unknown")
(target/"summary.json").write_text(json.dumps(summary, indent=2))
report = f"""# Candidate 3 supplemental verdict: reject

Tested full candidate: `{candidate}`. **Reject**. This supplemental source audit revokes the acceptance recorded in `../candidate-3/VERDICT.md` at evidence revision `b829a433957bc785e0dd2598316ce1b358303a91`. That original report and every earlier trace remain unchanged. Highest independently accepted consecutive stage is now **0**, pending a repaired candidate and full review.

Stage 1 §4 defines the three restaurant minute fields without an upper maximum. §5 assigns errors for stated rules and invalid values; it does not establish a hidden maximum from Python's datetime representation. Stage 3 policy limits are not a Stage 1 fixture restriction. A positive JSON integer `10^18` therefore remains applicable to this source-derived boundary audit. Expected behavior is a valid reset, one fitting opening slot for a huge grid, no fitting slots for a huge duration, and cutoff refusal for a huge cutoff. The reset failures prevented the latter behaviors from being executed; those rows remain unverified.

| Atomic requirement | Smallest changed input to the otherwise valid fixture | Expected | Observed |
|---|---|---|---|
| `TK1-large-slot_minutes-reset` | `slot_minutes: 1000000000000000000` | 204, no body | 422 `validation_failed`, message `validation failed` |
| `TK1-large-reservation_duration_minutes-reset` | `reservation_duration_minutes: 1000000000000000000` | 204, no body | 422 `validation_failed`, message `validation failed` |
| `TK1-large-cancellation_cutoff_minutes-reset` | `cancellation_cutoff_minutes: 1000000000000000000` | 204, no body | 422 `validation_failed`, message `validation failed` |

The fixture uses UTC, Tuesday 18:10–23:10, one capacity-2 table, ordinary 30-minute grid/90-minute duration/zero cutoff before changing only the named field. `large_minutes.py` contains the exact independently authored client and complete fixtures. `runtime-02/probes.json` preserves the first three operations: three assertions, three failures, 0.014409 s. Another fresh exact-revision process reproduced all three failures in `runtime-03/probes.json`: four operations/four assertions/three failures, 0.039324 s. Its first operation is the normal-value control, which returned 204. Request/response traces, full Docker argv and measured timing remain inspectable. No exported credentials were saved; trace credentials use fingerprints.

Exact repeat command, from the result repository, choosing a new output directory instead of reusing a retained one:

```sh
{command}
```

The executable exited 1 on the final reproduced service failures. The first run was stopped before startup by an uppercase Docker image tag; `runtime-01/build.log` preserves that verifier-runner error. The tag was corrected, without any service edit. `runtime-02` preserved the probe's failed assertions despite its original wrapper exit 0; the wrapper was corrected to propagate the actual probe exit code. No failed assertion was converted to a pass. The independently repeated `runtime-03` control and three failures establish the current rejection.

Fresh detached clones of the exact candidate built per RUN.md. Both executed service processes had matching committed/image core and server hashes, `--network none`, no mounts, 2 CPU, 2 GiB and override PORT 18320. Startup-to-health was 0.329 and 0.248 seconds. Own containers were removed successfully; no other seat's process was touched. Builds used ordinary cache. Exact clone identities, inspections, command timings and cleanup are preserved.

The current expanded matrix has **797 atomic rows: 776 verified, 3 failed, 18 unverified**. The earlier 776 passing observations against this same revision remain valid evidence for those behaviors; they cannot establish these new boundary obligations. Its independently executed official 120/120 count and Stage 2 overshoot failure are unchanged historical observations, not acceptance after these source failures. The official suite was not repeated because no production revision changed and the three independent failures already reject promotion.

Owning-builder repair must preserve the published value range and implement the intended small-window semantics, including cutoff, opening-duration fit and grid iteration, without adding a timedelta-derived fixture maximum. Full candidate review must rerun these probes plus earlier independent and official checks. No implementation file was modified by the verifier. Historical timestamp interpretation/immutable imported-string risk remains as documented in the original candidate report and is independent of these failures.

Harness Codex; configured model gpt-6.1-sol. Actual runtime override, effort, usage, estimated cost and billed spend unknown. Complete factory elapsed time is coordinator-owned; the per-run durations above are observed. Genuine room export/publication/submission remain operator-controlled.
"""
(target/"VERDICT.md").write_text(report)
manifest = [dict(path=str(path.relative_to(target)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(target.rglob("*")) if path.is_file()]
(target/"artifact-manifest.json").write_text(json.dumps(manifest, indent=2))
ledger = repo/"evidence/independent-verifier/ledger.jsonl"
with ledger.open("a") as stream:
    stream.write(json.dumps(dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), event="candidate-3-acceptance-revoked-large-minutes", **summary))+"\n")
print(json.dumps(summary, indent=2))
