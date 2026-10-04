"""Bind only current candidate execution to each independent requirement row."""
import copy
import csv
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path
from decimal_requirements import ROWS

sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORKSPACE=REPO.parents[1]
TARGET=HERE/"candidate-5"
CANDIDATE="f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
meta=json.loads((TARGET/"runtime-01/preflight.json").read_text())
commands=json.loads((TARGET/"runtime-01/commands.json").read_text())
extras=json.loads((TARGET/"runtime-01/extra-commands.json").read_text())
dc=json.loads((TARGET/"decimal-04/commands.json").read_text())
evidence=[]
for label in ["probes","original-minimal","calendar-minimal","race50","legacy"]:
    path=TARGET/"runtime-01"/label/"assertions.json"
    argv=meta["probe_command"] if label=="probes" else next(c["command"] for c in extras if c["log"]==label+"-client.log")
    for row in json.loads(path.read_text()):
        evidence.append(dict(**row,evidence_path=str(path.relative_to(REPO)),command=shlex.join(argv)))
path=TARGET/"decimal-04/probes/assertions.json"
argv=next(c["argv"] for c in dc if c["log"]=="client.log")
for row in json.loads(path.read_text()):
    evidence.append(dict(**row,evidence_path=str(path.relative_to(REPO)),command=shlex.join(argv)))
large=json.loads((TARGET/"runtime-01/large-minutes.json").read_text())
argv=next(c["command"] for c in extras if c["log"]=="large-minutes.json")
for row in large["results"]:
    evidence.append(dict(**row,evidence_path=str((TARGET/"runtime-01/large-minutes.json").relative_to(REPO)),command=shlex.join(argv)))
inspections=[json.loads((TARGET/"runtime-01"/c["log"]).read_text())[0] for c in commands if c["command"][:2]==["docker","inspect"]]
network=json.loads((TARGET/"runtime-01"/next(c["log"] for c in commands if c["command"][:3]==["docker","network","inspect"])).read_text())[0]
health=[v for v in meta.values() if isinstance(v,dict) and "readiness_seconds" in v]
clone=Path(meta["clone"])
status=subprocess.check_output(["git","status","--porcelain=v1"],cwd=clone,text=True)
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=clone,text=True).strip()
source=json.loads((TARGET/"source-audit.json").read_text())
history=(TARGET/"committed-history.txt").read_text()
official=json.loads((TARGET/"official/report.json").read_text())
identity=json.loads((TARGET/"runtime-01/legacy-identity.json").read_text())
audit={
    "dockerfile":all(c["returncode"]==0 for c in commands if c["command"][:2]==["docker","build"]),
    "run-document":bool((TARGET/"runtime-01/RUN-reviewed-source.md").read_text()) and all(v["healthy"] for v in health),
    "single-image":len(inspections)==2 and all(not x.get("Mounts") for x in inspections),
    "offline":network["Internal"] is True,
    "cpu":all(x["HostConfig"]["NanoCpus"]==2_000_000_000 for x in inspections),
    "memory":all(x["HostConfig"]["Memory"]==2_147_483_648 for x in inspections),
    "startup":len(health)==2 and all(v["healthy"] and v["readiness_seconds"]<60 for v in health),
    "packaged-assets":all(v["healthy"] for v in health) and network["Internal"] is True,
    "listen-all":len(health)==2 and all(v["healthy"] for v in health),
    "port-default":any(not any(s.startswith("PORT=") for s in x["Config"]["Env"]) for x in inspections) and any(not v["port_override"] and v["internal_port"]==8080 for v in health),
    "port-override":any("PORT=18309" in x["Config"]["Env"] for x in inspections) and any(v["port_override"] and v["healthy"] for v in health),
    "complete-clone":head==CANDIDATE and not status and meta["tree_issues"]==[] and source["symlink_or_submodule_entries"]==[],
    "two-builders":source["two_builders"],
    "history-preserved":source["history_preserved"] and all(x in history for x in ["439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd","2a4b0408a3453bc87d86bca3d0ec571f479e03ca","78732dde56ba6116d0722136beba74b674811105"]),
    "own-stage":official["state"]=="completed" and official["claimed_stage"]=="1",
    "source-provenance":source["complete_initial_handoffs"] and source["empty_root_intake"] and source["unchanged_interface_runtime"] and all(v["passed"] for v in identity["hash_checks"]),
}
assert all(audit.values()),audit
runtime_command=[str(WORKSPACE/".venv/bin/python"),"-B",str(HERE/"candidate5_runtime.py"),"--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate",CANDIDATE,"--out",str(WORKSPACE/"band-work/final-checks/independent-verifier-s1-f5e0a532-runtime-01"),"--execute","--run-probes","--keep-running"]
official_command=json.loads((TARGET/"preflight/official-command.json").read_text())
for key,passed in audit.items():
    argv=official_command if key=="own-stage" else [str(WORKSPACE/".venv/bin/python"),"-B",str(HERE/"candidate5_source.py")] if key=="source-provenance" else runtime_command
    evidence.append(dict(requirement_id="TK1-"+key,passed=passed,evidence_path=str((TARGET/"runtime-audit.json").relative_to(REPO)),command=shlex.join(argv)))
(TARGET/"runtime-audit.json").write_text(json.dumps(dict(candidate=CANDIDATE,checks=audit,readiness=health,network_internal=True,service_image_hashes=identity,clean_clone_head=head,clean_clone_status=status,cleanup=[c for c in extras if c["command"][:3]==["docker","rm","-f"] or c["command"][:3]==["docker","network","rm"]],run_scope="Equivalent documented single-image commands with required verifier-owned identities/ports and additional isolation constraints; cache available."),indent=2))
rows=copy.deepcopy(ROWS)
for row in rows:
    found=[e for e in evidence if e["requirement_id"]==row["requirement_id"]]
    row["candidate_full_revision"]=CANDIDATE
    row["verdict"]="verified" if found and all(e["passed"] for e in found) else "failed" if found else "unverified"
    if found:
        row["evidence_path"]="; ".join(sorted({e["evidence_path"] for e in found}))+"#"+row["requirement_id"]
        row["executable_command_or_interaction"]="\n".join(sorted({e["command"] for e in found}))
with (TARGET/"coverage-observed.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
summaries={label:json.loads((TARGET/"runtime-01"/label/"summary.json").read_text()) for label in ["probes","original-minimal","calendar-minimal","race50","legacy"]}
summaries["decimal-04"]=json.loads((TARGET/"decimal-04/probes/summary.json").read_text())
summary=dict(candidate=CANDIDATE,rows=len(rows),verified=sum(r["verdict"]=="verified" for r in rows),failed=sum(r["verdict"]=="failed" for r in rows),unverified=sum(r["verdict"]=="unverified" for r in rows),failed_ids=[r["requirement_id"] for r in rows if r["verdict"]=="failed"],unverified_ids=[r["requirement_id"] for r in rows if r["verdict"]=="unverified"],runs=summaries,large_minutes={k:large[k] for k in ["http_operations","assertions","failed_assertions","duration_seconds"]},official=official,official_stage1=json.loads((TARGET/"official/stage-1.counts.json").read_text()),official_stage2_overshoot=json.loads((TARGET/"official/stage-2.counts.json").read_text()),official_wall_seconds=(dt.datetime.fromisoformat(official["finished_at"])-dt.datetime.fromisoformat(official["started_at"])).total_seconds(),highest_independently_accepted_stage=0,source_question="Four base-field fractional-number refusal statuses await source applicability adjudication. Raw decimal04 assertions stay immutable.")
(TARGET/"observed-summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps({k:summary[k] for k in ["candidate","rows","verified","failed","unverified","failed_ids","unverified_ids","official_wall_seconds"]}))
