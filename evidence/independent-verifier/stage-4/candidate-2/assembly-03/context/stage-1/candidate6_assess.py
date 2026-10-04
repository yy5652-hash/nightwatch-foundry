"""Seal only freshly executed evidence for the named candidate6 review."""
import copy
import csv
import datetime as dt
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
sys.set_int_max_str_digits(0)  # Evidence-reader interpreter only.
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1];TARGET=HERE/"candidate-6"
CANDIDATE="ab0cf79767b6768153a73894bf5768bf3328491a"
evidence=[];runs={};excluded=[]
def load(path):return json.loads(path.read_text())
def relative(path):return str(path.relative_to(REPO))
def add(assertions,path,argv,label,exclude=None):
    for row in assertions:
        item=dict(**row,evidence_path=relative(path)+"#"+row["requirement_id"],command=shlex.join(argv),run=label)
        if exclude and row["requirement_id"] in exclude:
            excluded.append(dict(**item,classification="obsolete whole private envelope equality; adopted schema2/profile metadata changes private representation, while original state values remain required"))
        else:evidence.append(item)
meta=load(TARGET/"baseline-01/preflight.json");base_commands=load(TARGET/"baseline-01/commands.json");extras=load(TARGET/"baseline-01/extra-commands.json")
for label in ["probes","original-minimal","calendar-minimal","race50","legacy","decimal"]:
    p=TARGET/"baseline-01"/label;summary=load(p/"summary.json");assert summary["candidate"]==CANDIDATE
    runs["baseline-"+label]=dict(requests=summary["requests"],assertions=summary["assertions"],raw_failed_assertions=summary["failures"],seconds=summary["duration_seconds"])
    argv=meta["probe_command"] if label=="probes" else next(c["command"] for c in extras if c["log"]==label+"-client.log")
    add(load(p/"assertions.json"),p/"assertions.json",argv,"baseline-"+label,{"TK1-legacy-export-equality"} if label=="legacy" else None)
large=load(TARGET/"baseline-01/large-minutes.json")
runs["large-minutes"]=dict(requests=large["http_operations"],assertions=large["assertions"],raw_failed_assertions=large["failed_assertions"],seconds=large["duration_seconds"])
add(large["results"],TARGET/"baseline-01/large-minutes.json",next(c["command"] for c in extras if c["log"]=="large-minutes.json"),"large-minutes")
for family in ["semantic","opaque-ids","nesting","snapshot"]:
    folder=TARGET/(family+"-01");summary=load(folder/"probes/summary.json");assert summary["candidate"]==CANDIDATE and not summary["flow_errors"]
    runs[family]=dict(requests=summary["requests"],assertions=summary["assertions"],raw_failed_assertions=summary["failed_assertions"],seconds=summary["duration_seconds"])
    commands=load(folder/"commands.json");argv=next(c["argv"] for c in commands if c["log"]=="semantic-probe.log")
    add(load(folder/"probes/assertions.json"),folder/"probes/assertions.json",argv,family)
for family in ["numeric","fractional"]:
    folder=TARGET/(family+"-01");data=load(folder/"probes.json");assert data["candidate_full_revision"]==CANDIDATE
    runs[family]=dict(requests=data["http_operations"],assertions=data["assertions"],raw_failed_assertions=data["failed_assertions"],seconds=data["duration_seconds"])
    commands=load(folder/"commands.json");argv=next(c["argv"] for c in commands if c["log"]=="probes.json")
    add(data["results"],folder/"probes.json",argv,family)
folder=TARGET/"legacy-current-01";data=load(folder/"probes/summary.json");assert data["candidate"]==CANDIDATE
runs["legacy-current"]=dict(requests=data["requests"],assertions=data["assertions"],raw_failed_assertions=data["failures"],seconds=data["duration_seconds"])
argv=next(c["argv"] for c in load(folder/"commands.json") if c["log"]=="client.log")
add(load(folder/"probes/assertions.json"),folder/"probes/assertions.json",argv,"legacy-current")
deep=load(TARGET/"very-deep-01/probes.json");assert deep["candidate"]==CANDIDATE
runs["very-deep"]=dict(requests=deep["requests"],assertions=deep["assertions"],raw_failed_assertions=deep["failed_assertions"],seconds=deep["duration_seconds"])
deep_argv=load(TARGET/"very-deep-01/command.json")["argv"]
add(deep["checks"],TARGET/"very-deep-01/probes.json",deep_argv,"very-deep")

source=load(TARGET/"source-audit.json");failure_image=load(TARGET/"failure-image-proof.json")
official=load(TARGET/"official/report.json");s1=load(TARGET/"official/stage-1.counts.json");s2=load(TARGET/"official/stage-2.counts.json")
assert official["revision"]==CANDIDATE and official["mode"]=="isolated" and official["pytest_args"]==[]
inspections=[load(TARGET/"baseline-01"/c["log"])[0] for c in base_commands if c["command"][:2]==["docker","inspect"]]
network=load(TARGET/"baseline-01"/next(c["log"] for c in base_commands if c["command"][:3]==["docker","network","inspect"]))[0]
health=[v for v in meta.values() if isinstance(v,dict) and "readiness_seconds" in v]
clone=Path(meta["clone"]);clean_status=subprocess.check_output(["git","status","--porcelain=v1"],cwd=clone,text=True)
clean_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=clone,text=True).strip()
all_proofs=[load(TARGET/(f+"-01")/"source-runtime-proof.json") for f in ["semantic","opaque-ids","nesting","snapshot"]]
cleanup=[dict(command=c["command"],returncode=c["returncode"]) for c in extras if c["command"][:3] in [["docker","rm","-f"],["docker","network","rm"]]]
for proof in all_proofs:
    assert proof["status"]=="completed" and proof["candidate"]==CANDIDATE and all(x["returncode"]==0 for x in proof["cleanup"])
    cleanup.extend(proof["cleanup"])
for family in ["numeric-01","fractional-01","legacy-current-01"]:
    for c in load(TARGET/family/"commands.json"):
        if c["argv"][:3] in [["docker","rm","-f"],["docker","network","rm"]]:cleanup.append(dict(command=c["argv"],returncode=c["returncode"]))
assert cleanup and all(c["returncode"]==0 for c in cleanup)
audit={
    "dockerfile":all(c["returncode"]==0 for c in base_commands if c["command"][:2]==["docker","build"]),
    "run-document":bool((TARGET/"source-inputs/RUN.md").read_text()) and all(v["healthy"] for v in health),
    "single-image":len(inspections)==2 and all(not x["Mounts"] for x in inspections),
    "offline":network["Internal"] is True,
    "cpu":all(x["HostConfig"]["NanoCpus"]==2000000000 for x in inspections),
    "memory":all(x["HostConfig"]["Memory"]==2147483648 for x in inspections),
    "startup":len(health)==2 and all(v["healthy"] and v["readiness_seconds"]<60 for v in health),
    "packaged-assets":network["Internal"] is True and failure_image["observed"]==failure_image["expected"]=={f:source["files"][f] for f in failure_image["observed"]},
    "listen-all":all_proofs[0]["startup"]["base"]["cross_container_health"] and all_proofs[0]["startup"]["peer"]["cross_container_health"],
    "port-default":any(not v["port_override"] and v["internal_port"]==8080 for v in health),
    "port-override":any(v["port_override"] and v["internal_port"]==18309 for v in health),
    "complete-clone":clean_head==CANDIDATE and not clean_status and not meta["tree_issues"] and not source["symlink_or_submodule_entries"],
    "two-builders":source["two_builders"],"history-preserved":source["history_preserved"],
    "own-stage":official["state"]=="completed" and official["claimed_stage"]=="1" and s1["passed"]==s1["collected"]==120,
    "source-provenance":source["complete_initial_handoffs"] and source["empty_root_intake"] and source["unchanged_interface_runtime"] and source["stage_tree_matches_production_revision"],
}
assert all(audit.values()),audit
(TARGET/"runtime-audit.json").write_text(json.dumps(dict(candidate=CANDIDATE,checks=audit,readiness=health,source_image_proof=failure_image,
    clean_clone_head=clean_head,clean_clone_status=clean_status,cleanup=cleanup,cache="Available; no uncached claim",scope="Equivalent documented build/start with verifier-owned identities, 2CPU/2GiB and offline isolation"),indent=2))
for key,passed in audit.items():
    evidence.append(dict(requirement_id="TK1-"+key,passed=passed,evidence_path=relative(TARGET/"runtime-audit.json")+"#checks."+key,
        command=shlex.join([str(WORKSPACE/".venv/bin/python"),"-B","evidence/independent-verifier/stage-1/candidate6_assess.py"]),run="source/runtime/official audit"))
with (HERE/"candidate-6-snapshot-preparation/coverage-cumulative-prepared.csv").open() as f:rows=list(csv.DictReader(f))
assert len(rows)==2625
template=copy.deepcopy(rows[0]);existing_ids={r["requirement_id"] for r in rows}
for check in deep["checks"]:
    assert check["requirement_id"] not in existing_ids
    row=copy.deepcopy(template);row.update(requirement_id=check["requirement_id"],source_section="3.4 / 5 / 7 / 10; complete candidate6 depth boundary assignment",source_line="86",
        requirement_text="Raw bounded array-chain protocol: "+check["requirement_id"].removeprefix("TK1-very-deep-")+". Replay/import controls use the actual original successful receipt; when deep create refuses, the observed recovered ordinary receipt is explicitly used.",
        owner="systems-engineer / interface-engineer",implementation_owner="systems-engineer / interface-engineer",verification_method="inductive JSON grammar and separate constrained raw HTTP client",case="very-deep",
        inherited_from="",historical_verdict="",historical_candidate="",historical_evidence_path="",normative="True",preparation_origin="Independent high-depth protocol at c771649 before execution",
        interpretation_note="Balanced JSON arrays around a shallow independently parsed finite numeric leaf are valid by the JSON array grammar. Finite sampled depths do not prove arbitrary-depth performance.")
    rows.append(row)
for depth in [10000,20000]:
    for behavior in ["accepted-body-alias-replay","deep-original-receipt-transfer"]:
        row=copy.deepcopy(template);row.update(requirement_id=f"TK1-very-deep-{depth}-dependent-{behavior}",source_section="3.4 / 7 / 10",source_line="86",
            requirement_text=f"A successful depth{depth} ignored-body receipt supports {behavior} without loss of complete body semantics.",owner="systems-engineer / interface-engineer",implementation_owner="systems-engineer / interface-engineer",
            verification_method="dependent raw HTTP operation",case="very-deep-dependent",inherited_from="",historical_verdict="",historical_candidate="",historical_evidence_path="",normative="True",preparation_origin="Current source-derived dependent boundary",
            interpretation_note="Unverified: valid deep create refused before a deep successful receipt existed. Successful ordinary fallback replays/imports do not establish this deep success behavior.")
        rows.append(row)

# General inherited obligations must reflect newly observed valid unknown-field
# refusals, even though their smaller fresh controls pass.
mapping={"ignored-reset":"TK1-unknown-field-reset","ignored-signup":"TK1-unknown-field-signup","ignored-create":"TK1-unknown-field-create","ignored-move":"TK1-unknown-field-batch"}
for check in deep["checks"]:
    if check["passed"]:continue
    matched=next((target for ending,target in mapping.items() if check["requirement_id"].endswith(ending)),None)
    if matched:
        original=next(e for e in evidence if e["requirement_id"]==check["requirement_id"])
        for rid in [matched,"TK1-unknown-body"]:evidence.append(dict(**{k:v for k,v in original.items() if k!="requirement_id"},requirement_id=rid,linked_observed_assertion=check["requirement_id"]))
bindings={};diagnostics=load(TARGET/"opaque-ids-01/probes/admission-diagnostics.json")
for row in rows:
    row["candidate_full_revision"]=CANDIDATE
    found=[e for e in evidence if e["requirement_id"]==row["requirement_id"]]
    bindings[row["requirement_id"]]=found
    row["verdict"]="verified" if found and all(e["passed"] for e in found) else "failed" if found else "unverified"
    row["evidence_path"]="; ".join(sorted({e["evidence_path"] for e in found})) if found else relative(TARGET/"opaque-ids-01/probes/admission-diagnostics.json")+"#"+row["requirement_id"] if row["normative"]!="True" else relative(TARGET/"very-deep-01/probes.json")
    row["executable_command_or_interaction"]="\n".join(sorted({e["command"] for e in found})) if found else shlex.join(deep_argv) if row["normative"]=="True" else "Observed fixture admission diagnostic; each actual HTTP status is preserved separately."
    if row["requirement_id"]=="TK1-legacy-export-equality":row["interpretation_note"]+=" Current adopted private schema2/profile normalization is checked in a fresh corrected run. Original obsolete private-envelope assertion remains an excluded raw expectation failure."
    if row["requirement_id"]=="TK1-numeric-unknown-failed-key-control":row["interpretation_note"]+=" Current finite ignored-number write succeeds; a separate actually refused party-zero request now establishes failed-key reuse. Removed ignored-field change on the successful key correctly conflicts. Old source/observations remain unchanged."
normative=[r for r in rows if r["normative"]=="True"]
assert len(normative)==2657 and len(rows)==2679 and len({r["requirement_id"] for r in rows})==len(rows)
with (TARGET/"coverage.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(TARGET/"coverage-bindings.json").write_text(json.dumps(bindings,indent=2));(TARGET/"excluded-raw-expectations.json").write_text(json.dumps(excluded,indent=2))
now=dt.datetime.now(dt.timezone.utc);started=dt.datetime.fromisoformat(load(TARGET/"intake.json")["review_started_at"])
execution_started=min([dt.datetime.fromisoformat(official["started_at"])]+[dt.datetime.fromisoformat(p["started_at"]) for p in all_proofs])
summary=dict(candidate=CANDIDATE,production_revision="debff0bbf2625936d30e1e11066b966a46320137",stage_tree="d2905df39546a619afbad3547b10205bb6c01610",verdict="reject",highest_independently_accepted_stage=0,
    normative_rows=len(normative),verified=sum(r["verdict"]=="verified" for r in normative),failed=sum(r["verdict"]=="failed" for r in normative),unverified=sum(r["verdict"]=="unverified" for r in normative),
    diagnostic_rows=22,diagnostic_classification="Non-normative chosen fixture ID admission observations;22/22 admitted, all308 conditional usability obligations independently passed.",
    failed_ids=[r["requirement_id"] for r in normative if r["verdict"]=="failed"],unverified_ids=[r["requirement_id"] for r in normative if r["verdict"]=="unverified"],
    raw_http_requests=sum(r["requests"] for r in runs.values()),raw_assertions=sum(r["assertions"] for r in runs.values()),raw_failed_assertions=sum(r["raw_failed_assertions"] for r in runs.values()),
    established_failed_assertions=10,excluded_obsolete_expected_failures=len(excluded),observed_runs=runs,
    official_stage1=s1,official_stage2_overshoot=dict(**s2,not_executed=s2["collected"]-s2["passed"]-s2["failed"]-s2["skipped"]-s2["errors"]),
    official_wall_seconds=(dt.datetime.fromisoformat(official["finished_at"])-dt.datetime.fromisoformat(official["started_at"])).total_seconds(),
    clean_clone=True,source_image_hashes_match=True,default_readiness_seconds=next(v["readiness_seconds"] for v in health if not v["port_override"]),override_readiness_seconds=next(v["readiness_seconds"] for v in health if v["port_override"]),
    constraints="2CPU/2GiB; internal offline networks or network-none; no service mounts; all own cleanup commands exit0",cleanup_commands=len(cleanup),
    rejection_basis="Valid ignored depth10000/20000 balanced JSON arrays produce400 malformed_request on reset/signup/create/moves and changed-body used-key comparison. No published nesting maximum; actual sampled failures are not an arbitrary-depth claim.",
    review_started_at=started.isoformat(),review_finished_at=now.isoformat(),review_start_is_approximate=True,recorded_review_interval_seconds=(now-started).total_seconds(),
    execution_started_at=execution_started.isoformat(),execution_finished_at=now.isoformat(),elapsed_seconds=(now-execution_started).total_seconds(),elapsed_scope="Measured check-execution window from first recorded official/runtime start to evidence aggregation; prior intake/source review interval is approximate. Whole factory interval is coordinator-owned.",
    harness="Codex",configured_model="gpt-6.1-sol",actual_model="unknown",reasoning_effort="unknown",token_usage="unknown",catalog_estimated_cost="unknown",billed_spend="unknown",
    limits=["Four successful deep receipt alias/transfer paths remain unverified because required deep admission failed.","Historical exact-instant/nearest representable minute-offset interpretation and immutable legacy offset-seconds strings remain an explicit exception; literal incompatible offset grammars are not simultaneously claimed.","Finite depth/numeric samples do not prove arbitrary-size performance; available build cache was used.","Source cutoff supplements are not clock-controlled HTTP boundary observations; captured client schedules do not expose internal serializer timing.","Hidden judging suite, genuine full room export, public release and submission remain unavailable/operator-controlled."])
assert summary["failed"]==15 and summary["unverified"]==4 and summary["verified"]==2638
assert summary["raw_http_requests"]==4284 and summary["raw_assertions"]==3644 and summary["raw_failed_assertions"]==11
(TARGET/"summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps({k:summary[k] for k in ["candidate","verdict","normative_rows","verified","failed","unverified","raw_http_requests","raw_assertions","raw_failed_assertions","elapsed_seconds"]}))
