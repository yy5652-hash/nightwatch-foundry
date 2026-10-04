"""Preserve independently executed repaired-candidate evidence and source audit."""
import ast
import copy
import csv
import datetime as dt
import hashlib
import json
import shlex
import shutil
import subprocess
from pathlib import Path
from requirements import ROWS

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parents[1]
CHECKS = WORKSPACE / "band-work/final-checks"
CANDIDATE = "dd644198b6c0c24cebaee74435ac13d4dc33bd99"
TARGET = HERE / "candidate-2"
TARGET.mkdir(exist_ok=False)
sources = {label:"independent-verifier-s1-dd64419-"+label+"-01" for label in ["preflight", "official"]}
sources.update({"runtime-01":"independent-verifier-s1-dd64419-runtime-01", "runtime-02":"independent-verifier-s1-dd64419-runtime-02"})
for label, folder in sources.items():
    shutil.copytree(CHECKS / folder, TARGET / label)


def git(*args, cwd=REPO):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True)


source_dir = TARGET / "source-inputs"
source_dir.mkdir()
source_items = []
for label, path in [("systems", "evidence/systems-engineer/stage-1-source-provenance.md"),
                    ("interface", "evidence/interface-engineer/stage-1-source-provenance.md"),
                    ("systems-handoff", "evidence/coordinator/handoffs/TK-20261004-S1-systems-engineer-A.txt"),
                    ("interface-handoff", "evidence/coordinator/handoffs/TK-20261004-S1-interface-engineer-A.txt"),
                    ("candidate-handoff", "evidence/coordinator/handoffs/TK-20261004-S1-independent-verifier-CANDIDATE-2.txt")]:
    data = (REPO / path).read_bytes()
    snapshot = source_dir / (label+Path(path).suffix)
    snapshot.write_bytes(data)
    revision = git("log", "-1", "--format=%H", "--", path).strip()
    source_items.append(dict(label=label, input_path=path, recorded_revision=revision,
                             snapshot=str(snapshot.relative_to(REPO)), sha256=hashlib.sha256(data).hexdigest()))
intake = "2f691e8c7c43b3489717eb3ede1dadf0b0651b74"
(source_dir / "intake-tree.txt").write_text(git("ls-tree", "-r", intake))
(source_dir / "intake-record.jsonl").write_text(git("show", intake+":evidence/coordinator/run-ledger.jsonl"))
spec = (WORKSPACE / "kickoff/tablekeeper/spec/stage-1.md").read_text().strip()
handoff_complete = all(spec in (source_dir / (label+".txt")).read_text() for label in ["systems-handoff", "interface-handoff", "candidate-handoff"])
intake_root = len(git("rev-list", "--parents", "-1", intake).split()) == 1
intake_no_service = "stage-1/" not in (source_dir / "intake-tree.txt").read_text()
declared_inputs = all("No existing" in (source_dir / (label+".md")).read_text() for label in ["systems", "interface"])
metadata = json.loads((TARGET / "runtime-01/preflight.json").read_text())
clone = Path(metadata["clone"])
history = git("log", "--format=%H %an <%ae> %s", CANDIDATE, cwd=clone)
tree = git("ls-tree", "-r", CANDIDATE, cwd=clone)
(TARGET / "committed-history.txt").write_text(history)
(TARGET / "committed-tree.txt").write_text(tree)
modules = {}
for name in ["core.py", "server.py"]:
    parsed = ast.parse((clone / "stage-1" / name).read_text())
    modules[name] = sorted({module for node in ast.walk(parsed) for module in
                            ([x.name for x in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else [])})
source_audit = dict(candidate=CANDIDATE, source_items=source_items, full_spec_handoffs=handoff_complete,
                    intake_is_root=intake_root, intake_has_no_service=intake_no_service,
                    explicit_builder_input_declarations=declared_inputs, reviewed_imports=modules,
                    implementation_commit_authors=git("show", "-s", "--format=%H %an <%ae> %aI %s", "e9e15076a762ab437d349cb3e6768b4786e1432f", "9d53de905fdd498ee34dfa7c4d814b13dda7a921", "6442d6d5aa3187aa090107733e41f685946044f1"),
                    method="Inspect preserved complete requirements handoffs, fresh-empty root intake, seat input declarations, authored-path history and complete current source. No foreign product inputs found in this evidence.",
                    limits="Builder exclusions are factual seat declarations, not a machine-wide forensic claim. The genuine final room export remains operator-controlled. Post-candidate declarations are evidence about unchanged candidate source, not candidate runtime inputs.")
(TARGET / "source-audit.json").write_text(json.dumps(source_audit, indent=2))

commands = json.loads((TARGET / "runtime-01/commands.json").read_text())
inspections = [json.loads((TARGET / "runtime-01" / c["log"]).read_text())[0] for c in commands if c["command"][:2] == ["docker", "inspect"]]
network_command = next(c for c in commands if c["command"][:3] == ["docker", "network", "inspect"])
network = json.loads((TARGET / "runtime-01" / network_command["log"]).read_text())[0]
health = [v for v in metadata.values() if isinstance(v, dict) and "readiness_seconds" in v]
official = json.loads((TARGET / "official/report.json").read_text())
audit = {
    "dockerfile":all(c["returncode"] == 0 for c in commands if c["command"][:2] == ["docker", "build"]),
    "run-document":bool((TARGET / "preflight/RUN-reviewed-source.md").read_text()) and all(v["healthy"] for v in health),
    "single-image":len(inspections) == 2 and all(not x.get("Mounts") for x in inspections),
    "offline":network["Internal"] is True,
    "cpu":all(x["HostConfig"]["NanoCpus"] == 2_000_000_000 for x in inspections),
    "memory":all(x["HostConfig"]["Memory"] == 2_147_483_648 for x in inspections),
    "startup":len(health) == 2 and all(v["healthy"] and v["readiness_seconds"] < 60 for v in health),
    "packaged-assets":len(health) == 2 and network["Internal"] is True,
    "listen-all":len(health) == 2 and all(v["healthy"] for v in health),
    "port-override":any("PORT=18309" in x["Config"]["Env"] for x in inspections) and any(v["healthy"] and v["port_override"] for v in health),
    "port-default":any(not any(s.startswith("PORT=") for s in x["Config"]["Env"]) for x in inspections) and any(v["healthy"] and not v["port_override"] and v["internal_port"] == 8080 for v in health),
    "complete-clone":not git("status", "--porcelain=v1", cwd=clone) and not any(s.startswith(("120000", "160000")) for s in tree.splitlines()) and metadata["tree_issues"] == [],
    "two-builders":all(r in history for r in ["e9e15076a762ab437d349cb3e6768b4786e1432f", "9d53de905fdd498ee34dfa7c4d814b13dda7a921"]),
    "history-preserved":all(r in history for r in [intake, "439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd", "6442d6d5aa3187aa090107733e41f685946044f1"]),
    "own-stage":official["state"] == "completed" and official["claimed_stage"] == "1",
}
(TARGET / "runtime-audit.json").write_text(json.dumps(dict(candidate=CANDIDATE, checks=audit, readiness=health, network_internal=network["Internal"], resource_limits=[dict(name=x["Name"], cpus=x["HostConfig"]["NanoCpus"], memory=x["HostConfig"]["Memory"]) for x in inspections]), indent=2))
evidence = []
for label in ["runtime-01/probes", "runtime-01/reproductions", "runtime-01/calendar", "runtime-02/calendar-minimal"]:
    path = TARGET / label / "assertions.json"
    if label.endswith("probes"):
        command = metadata["probe_command"]
    else:
        extra = json.loads((TARGET / label.split("/")[0] / "extra-commands.json").read_text())
        command = next(c["command"] for c in extra if c["command"][:3] == ["docker", "run", "--rm"] and c["log"] == label.split("/")[1]+"-client.log")
    for item in json.loads(path.read_text()):
        item.update(evidence_path=str(path.relative_to(REPO)), command=shlex.join(command))
        evidence.append(item)
runtime_command = [str(WORKSPACE / ".venv/bin/python"), "-B", str(HERE / "runtime.py"), "--repo", str(REPO), "--workspace", str(WORKSPACE), "--candidate", CANDIDATE, "--out", str(CHECKS / sources["runtime-01"]), "--execute", "--run-probes", "--keep-running"]
for key, passed in audit.items():
    command = runtime_command
    if key == "own-stage":
        command = [str(WORKSPACE / ".venv/bin/python"), "-m", "harness", "run", "--track", "tablekeeper", "--repo", json.loads((TARGET / "preflight/preflight.json").read_text())["clone"], "--stage", "1", "--mode", "isolated", "--out", str(CHECKS / sources["official"])]
    evidence.append(dict(requirement_id="TK1-"+key, passed=passed, evidence_path=str((TARGET / "runtime-audit.json").relative_to(REPO)), command=shlex.join(command)))
evidence.append(dict(requirement_id="TK1-source-provenance", passed=handoff_complete and intake_root and intake_no_service and declared_inputs,
                     evidence_path=str((TARGET / "source-audit.json").relative_to(REPO)), command=shlex.join([str(WORKSPACE / ".venv/bin/python"), "-B", str(HERE / "candidate2_report.py")])))
rows = copy.deepcopy(ROWS)
for row in rows:
    found = [e for e in evidence if e["requirement_id"] == row["requirement_id"]]
    row["candidate_full_revision"] = CANDIDATE
    row["verdict"] = "verified" if found and all(e["passed"] for e in found) else "failed" if found else "unverified"
    if found:
        row["evidence_path"] = "; ".join(sorted({e["evidence_path"] for e in found}))+"#"+row["requirement_id"]
        row["executable_command_or_interaction"] = "\n".join(sorted({e["command"] for e in found}))
with (TARGET / "coverage.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
summary = dict(candidate=CANDIDATE, verdict="reject", rows=len(rows), verified=sum(r["verdict"] == "verified" for r in rows),
               failed=sum(r["verdict"] == "failed" for r in rows), unverified=sum(r["verdict"] == "unverified" for r in rows),
               failed_ids=[r["requirement_id"] for r in rows if r["verdict"] == "failed"], unverified_ids=[r["requirement_id"] for r in rows if r["verdict"] == "unverified"],
               official_stage_1=official["checks"]["1"], official_claimed_stage=official["claimed_stage"], official_overshoot_observed=json.loads((TARGET / "official/stage-2.counts.json").read_text()),
               official_wall_seconds=(dt.datetime.fromisoformat(official["finished_at"])-dt.datetime.fromisoformat(official["started_at"])).total_seconds(),
               runs={label:json.loads((TARGET / label / "summary.json").read_text()) for label in ["runtime-01/probes", "runtime-01/reproductions", "runtime-01/calendar", "runtime-02/calendar-minimal"]},
               harness="Codex", configured_model="gpt-6.1-sol", actual_model="unknown", effort="unknown", usage="unknown", spend="unknown",
               representation_question="Two historical RFC3339 failures retained pending explicit coordinator interpretation. Seven other failed rows cover two valid-local-date refusal families.")
(TARGET / "summary.json").write_text(json.dumps(summary, indent=2))
with (HERE.parent / "ledger.jsonl").open("a") as f:
    f.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), phase="stage-1-candidate-2-verdict", **summary))+"\n")
manifest = [dict(path=str(f.relative_to(TARGET)), sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in TARGET.rglob("*") if f.is_file()]
(TARGET / "artifact-manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps({k:summary[k] for k in ["candidate", "rows", "verified", "failed", "unverified", "failed_ids"]}))
