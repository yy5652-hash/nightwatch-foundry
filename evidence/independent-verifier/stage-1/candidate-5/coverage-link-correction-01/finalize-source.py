"""Interpretation-aware final rejection; raw failed observations stay unchanged."""
import copy
import csv
import datetime as dt
import hashlib
import json
import shlex
import sys
from pathlib import Path
from numeric_requirements import ROWS,QUESTION_IDS
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORKSPACE=REPO.parents[1]
TARGET=HERE/"candidate-5"
CANDIDATE="f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
observed=json.loads((TARGET/"observed-summary.json").read_text())
counts=json.loads((TARGET/"exact-counts.json").read_text())
numeric=json.loads((TARGET/"numeric-01/probes.json").read_text())
with (TARGET/"coverage-observed.csv").open() as f: existing={r["requirement_id"]:r for r in csv.DictReader(f)}
driver_argv=[str(WORKSPACE/".venv/bin/python"),"-B","evidence/independent-verifier/stage-1/numeric_forms_run.py","--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate",CANDIDATE,"--out",str(WORKSPACE/"band-work/final-checks/independent-verifier-s1-f5e0a532-numeric-01")]
rows=[]
for prepared in ROWS:
    row=copy.deepcopy(existing.get(prepared["requirement_id"],prepared))
    row["candidate_full_revision"]=CANDIDATE
    found=[x for x in numeric["results"] if x["requirement_id"]==row["requirement_id"]]
    if found:
        row.update(verdict="verified" if all(x["passed"] for x in found) else "failed",evidence_path=str((TARGET/"numeric-01/probes.json").relative_to(REPO))+"#"+row["requirement_id"],executable_command_or_interaction=shlex.join(driver_argv))
    if row["requirement_id"] in QUESTION_IDS:
        row["verdict"]="unverified"
        row["interpretation_note"]="Actual expected-versus-observed numeric-form failures are preserved; source applicability/status interpretation is pending. These rows do not establish a service failure or a pass merely from Python types."
    if row["requirement_id"]=="TK1-unknown-body":
        row["verdict"]="failed"
        row["evidence_path"]+="; "+str((TARGET/"numeric-01/probes.json").relative_to(REPO))+"#TK1-numeric-unknown-exponent-create;TK1-numeric-unknown-exponent-reset"
        row["executable_command_or_interaction"]+="\n"+shlex.join(driver_argv)
    rows.append(row)
with (TARGET/"coverage.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
now=dt.datetime.now(dt.timezone.utc)
started=dt.datetime.fromisoformat("2026-10-04T02:43:20.153+00:00")
summary=dict(candidate=CANDIDATE,production_revision="78732dde56ba6116d0722136beba74b674811105",verdict="reject",highest_independently_accepted_stage=0,
    rows=len(rows),verified=sum(r["verdict"]=="verified" for r in rows),failed=sum(r["verdict"]=="failed" for r in rows),unverified=sum(r["verdict"]=="unverified" for r in rows),
    failed_ids=[r["requirement_id"] for r in rows if r["verdict"]=="failed"],unverified_ids=[r["requirement_id"] for r in rows if r["verdict"]=="unverified"],
    raw_http_requests=counts["http_requests"]+numeric["http_operations"],raw_assertions=counts["assertions"]+numeric["assertions"],raw_failed_assertions=counts["raw_failed_assertions"]+numeric["failed_assertions"],
    observed_runs=observed["runs"],large_minutes=observed["large_minutes"],numeric_forms={k:numeric[k] for k in ["http_operations","assertions","failed_assertions","duration_seconds"]},
    official_stage1=observed["official_stage1"],official_stage2_overshoot=observed["official_stage2_overshoot"],official_wall_seconds=observed["official_wall_seconds"],
    default_readiness_seconds=0.409092708996468,override_readiness_seconds=0.34185825000167824,
    decimal_max_ordinary_seconds=counts["decimal_max_ordinary_seconds"],decimal_max_control_seconds=counts["decimal_max_control_seconds"],
    clean_clone=True,source_image_hashes_match=True,resources="2CPU/2GiB; internal offline networks or network-none; no service mounts; cleanup successful",
    review_started_at=started.isoformat(),review_finished_at=now.isoformat(),elapsed_seconds=(now-started).total_seconds(),
    harness="Codex",configured_model="gpt-6.1-sol",actual_model="unknown",reasoning_effort="unknown",token_usage="unknown",catalog_estimated_cost="unknown",billed_spend="unknown",
    known_limitations=["Fourteen numeric field/error interpretations await coordinator source adjudication; raw assertions are not relabeled into passes.","Historical wire timestamps follow the exact-instant nearest minute-offset decision, with unchanged original local fields and immutable legacy strings/receipts; literal historic subminute wire-offset compliance is not claimed.","Modest decimal tests do not establish arbitrary payload performance; resource/startup/build used available cache.","Hidden judging suite unavailable; full room export/publication/submission remain operator-controlled."],
    rejection_basis="Valid JSON finite number1e4300 in an unknown create/reset field yields400 malformed_request, contrary to Stage1§3.4. This is independent of the fourteen unresolved numeric-type interpretations.")
assert summary["rows"]==932 and summary["failed"]==3 and summary["unverified"]==14
(TARGET/"summary.json").write_text(json.dumps(summary,indent=2))
table="\n".join(f"| {label} | {v['requests']} | {v['assertions']} | {v['failures']} | {v['duration_seconds']:.6f} |" for label,v in observed["runs"].items())
report=f"""# Stage 1 candidate 5: reject

Exact full candidate `{CANDIDATE}`, production source `78732dde56ba6116d0722136beba74b674811105`: **reject**. Highest independently accepted consecutive stage remains **0**. The original five 4,301-digit refusals are repaired, but this candidate rejects valid JSON numbers in unknown fields. No Stage 2 promotion or Stage 3 extension follows this report.

The smallest reproduced failure adds only `\"unused\":1e4300` to an otherwise valid create body or reset fixture. This is a valid JSON number and finite mathematically; its short spelling is a modest payload. Stage 1 §3.4 says unknown request-body fields are ignored, never an error. Expected create201/reset204; observed both400 `malformed_request`, message `Invalid JSON value`. Signup with that same unknown value returns201. An ordinary create using the failed key succeeds201, confirming that the refusal consumed no key. These two endpoint failures also invalidate the inherited general `TK1-unknown-body` obligation. They do not depend on any interpretation of fractional or integral field types.

The independent client and exact command are in [numeric_forms.py](../numeric_forms.py) and [numeric_forms_run.py](../numeric_forms_run.py). From the result root, the executed command was:

```sh
{shlex.join(driver_argv)}
```

Use a new unique `--out` directory to reproduce. Actual raw create/reset bodies, responses and counts are in `numeric-01/probes.json`; `commands.json`, `identity.json`, `inspect.json`, `image-hashes.json` and `client-source-proof.json` bind the clean detached clone, named source/image, client code, constraints and cleanup. Tokens/passwords/export payloads are redacted or fingerprinted, not published.

The final matrix has **{summary['rows']} rows: {summary['verified']} verified, {summary['failed']} failed, {summary['unverified']} unverified**. Every previous806 row was retested or freshly reviewed with current-candidate evidence; none of the old801 passes was reused as current proof. The111 decimal rows and15 numeric-form rows are independently derived additions. Fourteen additional raw expectation failures remain source questions: base-field1.5 gives400 rather than provisional422 (four), base-field1.0/1e0 gives400 rather than provisional204 (eight), and party1.0/1e0 gives422 rather than provisional201 (two). Their observed responses are preserved; the final matrix marks these interpretations **unverified**, not established service failures. Coordinator source-question messages are `af72866f-e5ae-4b5e-9c92-a2a90ab2102b` and `d09328ff-60fd-416a-8ee7-d33da74aa86c`. Earlier917-row observed counts remain separately unchanged.

Current independent execution totals **{summary['raw_http_requests']} HTTP requests, {summary['raw_assertions']} assertions and {summary['raw_failed_assertions']} raw expected-versus-observed failures**. Raw failures comprise the two clear unknown-field failures and fourteen interpretation questions; these are not sixteen established distinct normative defects.

| Run | Requests | Assertions | Raw failures | Seconds |
|---|---:|---:|---:|---:|
{table}
| 10^18 minute boundaries | 39 | 26 | 0 | {observed['large_minutes']['duration_seconds']:.6f} |
| JSON numeric forms | {numeric['http_operations']} | {numeric['assertions']} | {numeric['failed_assertions']} | {numeric['duration_seconds']:.6f} |

Unchanged official isolated Stage1: **120 collected,120 passed,0 failed/errors/skipped/deselected/xfailed**, {observed['official_wall_seconds']:.6f}s. Stage2 overshoot: **25 collected,0 passed,1 failed,24 not executed**,0 errors/skips/deselections/xfailed. The unchanged Stage1 service correctly claims1 on shipped checks; passing those checks does not override this independent rejection. Earlier-stage regression: none applies. Official output is preserved under `official/` and the original unique final-checks directory. The harness/test selection was not modified.

Fresh default8080 and override18309 startup/cross-container health measured0.409093s and0.341858s respectively. Current source/destination and genuine pre-serializer source `49287b4a5a1481f995c470ccae31776f03d4b863` ran in constrained offline images; current and legacy core/server hashes matched. Tests include separately staged50-client traffic, deterministic seed20261004/160-operation occupancy trace, atomic rollback/read snapshots, calendar/DST boundaries, genuine old tokens/references/create+batch receipts, and independent destination replacement. Full current configuration, giant integer request/receipt values and original receipt replay survive import. The decimal suite's maximum ordinary/control request times were{counts['decimal_max_ordinary_seconds']:.6f}s/{counts['decimal_max_control_seconds']:.6f}s. These modest values do not prove arbitrary-size performance.

All own service containers and networks were removed with successful cleanup; images and clean clones remain. No other seat's process was touched. The clean exact candidate's five-file Stage1 subtree matches named production78732dde; four Interface runtime files match the revoked original2a4 source byte-for-byte. Source declarations, complete handoffs, empty original intake, both builder contributions, dependency imports and history are reviewed in `source-audit.json` and `source-inputs/`. No builder test/oracle implementation or external domain code was read. Build cache was available; no uncached-build claim is made.

Preserved verifier runner mistakes are separate: an AST selector chose the wrong `__init__`, the first decimal client's helper argument collided with `key`, the next driver used a relative Dockerfile path from the wrong directory, and an overlong container DNS label prevented a health client from reaching the service. Original error artifacts/source versions remain under `source-runner-error-01`, `decimal-runner-error-01/02/03`, `runtime-01/decimal-client.log`, `decimal-02` and `decimal-03`. Decimal04 and numeric01 are newly executed observations, not relabeled earlier runs.

Historical timestamps follow the recorded exact-instant/nearest representable minute-offset interpretation; original wall fields and genuine old offset-seconds receipt strings remain immutable. Literal historic IANA subminute wire offsets cannot simultaneously satisfy the minute-only RFC3339 grammar and are an explicitly disclosed interpretation risk. No receipt schema/value is enriched on historical replay.

This review elapsed{summary['elapsed_seconds']:.3f}s from{started.isoformat()} to{now.isoformat()}; per-run durations are measured separately. Whole factory elapsed is coordinator-owned. HarnessCodex; operator-configured modelgpt-6.1-sol. Actual model override, effort, token usage, catalog-estimated cost and billed spend are unknown. Hidden judging results, full genuine room export, publication and final submission remain operator-controlled. A new complete repair-candidate handoff and independent exact-revision reexecution are required before acceptance.
"""
(TARGET/"VERDICT.md").write_text(report)
with (HERE.parent/"ledger.jsonl").open("a") as f:
    f.write(json.dumps(dict(utc=now.isoformat(),phase="stage-1-candidate-5-verdict",**summary))+"\n")
print(json.dumps({k:summary[k] for k in ["candidate","verdict","rows","verified","failed","unverified","raw_http_requests","raw_assertions","raw_failed_assertions","elapsed_seconds"]}))
