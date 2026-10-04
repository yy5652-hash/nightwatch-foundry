"""Finalize measured Candidate 4 facts, interpretation notes and artifact hashes."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from requirements import ROWS

here = Path(__file__).resolve().parent
target = here/"candidate-4"
summary = json.loads((target/"summary.json").read_text())
assert summary["rows"] == summary["verified"] == 801 and summary["failed"] == summary["unverified"] == 0
matrix = target/"coverage.csv"
rows = list(csv.DictReader(matrix.open()))
notes = {row["requirement_id"]:row["interpretation_note"] for row in ROWS}
for row in rows:
    row["interpretation_note"] = notes[row["requirement_id"]]
with matrix.open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
issue = dict(classification="verifier probe error, not a service failure", evidence="runtime-01/large-minutes.json",
             observed="TypeError: expect() got multiple values for argument key; client aborted before recording its result object.",
             correction="Rename the assertion identifier parameter to rid, separating it from the Idempotency-Key client argument.",
             rerun="runtime-02/large-minutes.json: two fresh exact-revision current processes, 39 HTTP operations, 26 assertions, 0 failures.")
(target/"runner-issues.json").write_text(json.dumps([issue], indent=2))
report = """# Candidate 4: accept under the recorded timestamp interpretation

Tested full revision: `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`. Stage 1 verdict: **accept** under the explicit historical timestamp interpretation and immutable original imported-string exception below. Highest independently accepted consecutive stage: **1**.

The merged independent matrix has **801 atomic rows: 801 verified, 0 failed, 0 unverified**. All rows identify the complete source/candidate revision, applicable stages, separate implementation and verification owners, method, executable command, evidence and verdict. This includes the earlier 797 rows and four additional current/destination original-receipt checks for huge grid/cutoff configurations. The earlier candidate-3 acceptance at `b829a433957bc785e0dd2598316ce1b358303a91` and its supplemental revocation at `86c745913b073eb1ac70698ff6c6deee19d72e56` remain unchanged. This verdict follows fresh execution on the repaired source, not conversion of any earlier failure.

The repaired source removes only five lines enforcing an unpublished timedelta maximum in the base fixture validator. Interface transport/Dockerfile/RUN.md and the timestamp decision remain unchanged. The service was reviewed and built from fresh clean detached clones of the named full revision; source/image hashes matched. Both builders' substantive source contributions, every genuine rejection, repairs and source declarations remain inspectable in preserved history. No implementation file was modified by this verifier.

Official command, executed from kickoff with the workspace Python (workspace is `/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory`):

```sh
<workspace>/.venv/bin/python -m harness run --track tablekeeper \
  --repo <workspace>/band-work/independent-verifier-s1-2a4b0408a345-20261004t012302 \
  --stage 1 --mode isolated \
  --out <workspace>/band-work/final-checks/independent-verifier-s1-2a4b040-official-01
```

Observed unchanged official results: **120 collected, 120 passed, 0 failed/errors/skipped/deselected/xfailed**; claimed Stage 1. Official wall time **30.391 seconds**, including build and next-stage probe. Stage 2 overshoot collected 25 checks and stopped after its first browser failure: **0 passed, 1 failed, 24 not executed**. Report overshoot is null; preserved counts/log establish that outcome. No official runner/test/suite selection was changed. Shipped checks are not the unseen judging suite or a judging score.

| Independently executed probe | HTTP operations | Assertions | Failures | Probe wall time |
|---|---:|---:|---:|---:|
| Complete source-derived suite and offset/occupancy oracles | 1,485 | 1,497 | 0 | 10.211 s |
| Original three-defect minimal reproduction | 4 | 9 | 0 | 0.017 s |
| Four calendar-endpoint minimal reproductions | 8 | 12 | 0 | 0.108 s |
| Staged 50-request HTTP workload | 55 | 11 | 0 | 0.121 s |
| Genuine earlier-service receipt/export/mixed-state transfer | 26 | 24 | 0 | 0.206 s |
| Huge-count behavior and cross-process original receipts | 39 | 26 | 0 | 0.180 s |

Assertions include repeated observations and are not unique requirements. The full suite reran wrong-type/value precedence, idempotency scoping/order/original responses/failure reuse, occupancy and half-open boundaries, concurrent identical/competing requests, cancellation/amendment/current-start cutoff, atomic swaps and input-order errors, independent-process replacement/import/reset, password hashing and all four required DST transitions. The deterministic occupancy probe saves seed `20261004` and 160 operations with a separate interval oracle. The independent timestamp oracle enumerates legal numeric minute offsets, filters representable clocks and selects by distance/lower-offset tie; it never calls production code.

Each `10^18` base minute count now resets successfully and remains exact in restaurant detail and an independently running destination after export/import. A huge grid offers only the fitting opening start, accepts that start and refuses an off-grid time. A huge duration offers no fitting slots and refuses create with `outside_opening_hours`. A huge cutoff permits initial future create and then gives `cutoff_passed` on cancel, PATCH and batch; export fingerprints show no record/occupancy/retry-key mutation. Original huge-grid receipts survive amendment and import/replay; huge-cutoff receipts survive refused operations and destination replay. Actual traces are in `runtime-02/large-minutes.json`; the source-derived planned rows are now backed by HTTP evidence rather than implementation arithmetic.

The staged workload held each valid request's final Content-Length-framed body byte until all 50 requests were initiated, then released them. It measured peak overlap **50**, exactly one 201 and 49 original 200 receipts, one resulting reservation and request times below 5 seconds. No service delay was added. Main-suite ordinary HTTP calls took at most **0.0432 seconds**, test controls **0.0692 seconds**, below their 5/10-second limits; raw timings are saved.

The full-suite current processes ran on an internal offline network with 2 CPU/2 GiB, no mounts, and cross-container health access to PORT override18309 and absent-PORT default8080. Startup-to-health was **0.447/0.419 seconds**. The fresh legacy process took **0.391 seconds**. The corrected boundary probe used two further fresh current processes with **0.317/0.397 seconds** startup. Own host ports were18300–18302. Docker inspections, clean source trees, exact argv/hashes and successful own-container/network cleanup are preserved. Build cache was available; no uncached-build claim is made. No host service dependency, escaping symlink, submodule or nested service repository was used.

The genuine legacy source was this run's own earlier implementation `49287b4a5a1481f995c470ccae31776f03d4b863`, independently cloned, built and started. Its HTTP service generated old historical offset-second records and successful original create/batch receipts, including later cancellation. Current import retained exact exported state, old tokens/references/strings and receipts, invalidated replaced destination credentials, and then produced a new historical write under the new rule. Mixed old/new state transferred to the second current process with original old receipts unchanged. Exports, password hashes and tokens stayed in memory; saved traces contain fingerprints. No hand-edited state was presented as an actual legacy export.

**Explicit interpretation and remaining risk.** Stage 1 §3.4's RFC3339 minute-offset grammar conflicts with literal historical IANA offsets containing seconds in §9. Coordinator decision `b81b8a32de2faa330d60db9f671de56073f25042` resolves new output using the nearest representable minute-aligned fixed offset and adjusted displayed clock, retaining exact IANA instants and unchanged `starts_at_local`; ties choose the lower numerical offset. Modern minute-aligned offsets remain unchanged. The independently rerun minimum/maximum calendars, historical syntax/exact-instant/wall fields, absolute DST duration, true half-minute tie, import and replay pass under that decision. Literal historic wire-offset judging interpretation remains an explicit risk; this verdict does not assert incompatible grammars simultaneously.

Successful original imported record/receipt strings remain immutable, including historical offset seconds. They may retain their earlier wire grammar when returned after upgrade. This backward-preservation exception is explicit in the timestamp decision, matrix notes and genuine legacy probes. Those strings were not rewritten to claim new canonical formatting.

The source audit retains complete direct task/spec handoffs, fresh-empty root intake, committed builder input declarations, authored-path history, imports and current-source review. No foreign domain-product input was identified in that evidence. Builder exclusions are seat declarations, not machine-wide forensic proof. Final genuine room export remains operator-controlled; none was fabricated.

The first large-minute client aborted with a verifier `expect` argument-name collision, preserved unchanged in `runtime-01/large-minutes.json`. It is classified in `runner-issues.json`, not as a service refusal. The corrected client reran only the affected boundary scope on two fresh processes and recorded all 26 passing assertions; earlier full-suite/concurrency/legacy observations remain against this same exact revision. No raw error was erased or converted to pass.

Stage 1 can be frozen at this tested revision before extending its copy. This verdict grants no later-stage acceptance. Harness Codex; configured model gpt-6.1-sol. Actual runtime override, effort, usage, estimated cost and billed spend unknown. Per-run durations above are measured; complete factory elapsed time remains coordinator-owned. Genuine room export, public release and final submission remain operator-controlled.
"""
(target/"VERDICT.md").write_text(report)
summary["runner_issues"] = [issue]
summary["highest_independently_accepted_stage"] = 1
(target/"summary.json").write_text(json.dumps(summary, indent=2))
manifest = [dict(path=str(p.relative_to(target)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(target.rglob("*")) if p.is_file() and p.name != "artifact-manifest.json"]
(target/"artifact-manifest.json").write_text(json.dumps(manifest, indent=2))
with (here.parent/"ledger.jsonl").open("a") as stream:
    stream.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), phase="stage-1-candidate-4-final-verdict", **summary))+"\n")
print(json.dumps(dict(rows=len(rows), verified=801, failed=0, unverified=0, artifact_files=len(manifest))))
