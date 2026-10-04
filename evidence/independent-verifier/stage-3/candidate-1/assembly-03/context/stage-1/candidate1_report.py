"""Preserve Candidate 1 evidence and merge executed atomic assertions."""
import copy
import csv
import datetime as dt
import hashlib
import json
import shutil
import shlex
import subprocess
from pathlib import Path
from requirements import ROWS

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parents[1]
CHECKS = WORKSPACE / "band-work/final-checks"
CANDIDATE = "439b04e62325e7ddd82ea36bc6c9a07b8aaf94cd"
TARGET = HERE / "candidate-1"
TARGET.mkdir(exist_ok=False)
sources = {
    "preflight": "independent-verifier-s1-439b04e-preflight-01",
    "official": "independent-verifier-s1-439b04e-official-01",
    "runtime-01": "independent-verifier-s1-439b04e-runtime-01",
    "runtime-02": "independent-verifier-s1-439b04e-runtime-02",
    "runtime-03": "independent-verifier-s1-439b04e-runtime-03",
}
for target, source in sources.items():
    shutil.copytree(CHECKS / source, TARGET / target)
evidence = []
for label in ["runtime-02/probes", "runtime-03/probes-extra", "runtime-03/reproductions"]:
    path = TARGET / label / "assertions.json"
    for assertion in json.loads(path.read_text()):
        assertion["evidence_path"] = str(path.relative_to(REPO))
        evidence.append(assertion)

runtime = TARGET / "runtime-02"
metadata = json.loads((runtime / "preflight.json").read_text())
commands = json.loads((runtime / "commands.json").read_text())
inspections = [json.loads((runtime / x["log"]).read_text())[0] for x in commands if x["command"][:2] == ["docker", "inspect"]]
network_cmd = next(x for x in commands if x["command"][:3] == ["docker", "network", "inspect"])
network = json.loads((runtime / network_cmd["log"]).read_text())[0]
health = [value for value in metadata.values() if isinstance(value, dict) and "readiness_seconds" in value]
audit_path = str((TARGET / "runtime-audit.json").relative_to(REPO))
audit = {
    "dockerfile": all(x["returncode"] == 0 for x in commands if x["command"][:2] == ["docker", "build"]),
    "run-document": bool((TARGET / "preflight/RUN-reviewed-source.md").read_text()) and all(x["returncode"] == 0 for x in commands),
    "single-image": len(inspections) == 2 and all(not x.get("Mounts") for x in inspections),
    "offline": network.get("Internal") is True and (runtime / "probes/summary.json").exists(),
    "cpu": all(x["HostConfig"]["NanoCpus"] == 2_000_000_000 for x in inspections),
    "memory": all(x["HostConfig"]["Memory"] == 2_147_483_648 for x in inspections),
    "startup": len(health) == 2 and all(x["healthy"] and x["readiness_seconds"] < 60 for x in health),
    "packaged-assets": len(health) == 2 and network.get("Internal") is True,
    "listen-all": len(health) == 2 and all(x["healthy"] for x in health),
    "port-override": any("PORT=18309" in x["Config"]["Env"] for x in inspections) and any(x["healthy"] and x["port_override"] for x in health),
    "port-default": any(not any(v.startswith("PORT=") for v in x["Config"]["Env"]) for x in inspections) and any(x["healthy"] and not x["port_override"] and x["internal_port"] == 8080 for x in health),
}
# Runtime command success includes the intentionally failing independent probe;
# RUN.md startup itself is assessed separately from product acceptance.
audit["run-document"] = bool((TARGET / "preflight/RUN-reviewed-source.md").read_text()) and all(x["returncode"] == 0 for x in commands if x["command"][:2] in [["docker", "build"], ["docker", "inspect"]]) and all(x["healthy"] for x in health)
clone = Path(metadata["clone"])
git_tree = subprocess.check_output(["git", "ls-tree", "-r", CANDIDATE], cwd=clone, text=True)
git_history = subprocess.check_output(["git", "log", "--format=%H %an <%ae> %s", CANDIDATE], cwd=clone, text=True)
git_status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=clone, text=True)
(TARGET / "committed-tree.txt").write_text(git_tree)
(TARGET / "committed-history.txt").write_text(git_history)
audit.update({
    "complete-clone": not git_status and not any(x.startswith(("120000", "160000")) for x in git_tree.splitlines()) and metadata["tree_issues"] == [],
    "two-builders": all(rev in git_history for rev in ["e9e15076a762ab437d349cb3e6768b4786e1432f", "9d53de905fdd498ee34dfa7c4d814b13dda7a921"]),
    "history-preserved": all(rev in git_history for rev in ["2f691e8c7c43b3489717eb3ede1dadf0b0651b74", "a6d90ba140a5f2d6eb926376edc8b4fef07b5f7c", "4bad4a8da97b777547349df9198268e9ff150108"]),
})
official = json.loads((TARGET / "official/report.json").read_text())
audit["own-stage"] = official["claimed_stage"] == "1" and official["state"] == "completed"
audit_data = dict(candidate=CANDIDATE, checks=audit, inspected_resources=[dict(name=x["Name"], cpus=x["HostConfig"]["NanoCpus"], memory=x["HostConfig"]["Memory"]) for x in inspections],
                  network_internal=network["Internal"], readiness=health,
                  note="Network-separated clients exercised both listener ports. RUN.md used with verifier names/host ports; builds used cache. Product failures are preserved, not converted to passes. Source provenance is still unverified pending complete room audit.")
(TARGET / "runtime-audit.json").write_text(json.dumps(audit_data, indent=2))
for key, passed in audit.items():
    evidence.append(dict(requirement_id="TK1-" + key, passed=passed, evidence_path=audit_path))
rows = copy.deepcopy(ROWS)
by_id = {}
for item in evidence:
    by_id.setdefault(item["requirement_id"], []).append(item)
for row in rows:
    row["candidate_full_revision"] = CANDIDATE
    found = by_id.get(row["requirement_id"], [])
    row["verdict"] = "verified" if found and all(x["passed"] for x in found) else "failed" if found else "unverified"
    if found:
        row["evidence_path"] = "; ".join(sorted({x["evidence_path"] for x in found})) + "#" + row["requirement_id"]
        invocations = []
        for item in found:
            path = item["evidence_path"]
            if "runtime-02/probes" in path:
                invocations.append(next(x["command"] for x in commands if "--out" in x["command"]))
            elif "probes-extra" in path:
                invocations.append(json.loads((TARGET / "runtime-03/extra-command.json").read_text())["command"])
            elif "reproductions" in path:
                invocations.append(json.loads((TARGET / "runtime-03/reproductions-command.json").read_text())["command"])
            else:
                invocations.append([str(WORKSPACE / ".venv/bin/python"), "-B", str(HERE / "runtime.py"), "--repo", str(REPO), "--workspace", str(WORKSPACE), "--candidate", CANDIDATE, "--out", str(CHECKS / sources["runtime-02"]), "--execute", "--run-probes"])
        if row["requirement_id"] == "TK1-own-stage":
            invocations = [[str(WORKSPACE / ".venv/bin/python"), "-m", "harness", "run", "--track", "tablekeeper", "--repo", str(json.loads((TARGET / "preflight/preflight.json").read_text())["clone"]), "--stage", "1", "--mode", "isolated", "--out", str(CHECKS / sources["official"])]]
        row["executable_command_or_interaction"] = "\n".join(sorted({shlex.join(command) for command in invocations}))
with (TARGET / "coverage.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
summary = dict(candidate=CANDIDATE, verdict="reject", rows=len(rows), verified=sum(x["verdict"] == "verified" for x in rows),
               failed=sum(x["verdict"] == "failed" for x in rows), unverified=sum(x["verdict"] == "unverified" for x in rows),
               failed_ids=[x["requirement_id"] for x in rows if x["verdict"] == "failed"],
               unverified_ids=[x["requirement_id"] for x in rows if x["verdict"] == "unverified"],
               official_stage_1=official["checks"]["1"], official_claimed_stage=official["claimed_stage"],
               official_overshoot_observed=json.loads((TARGET / "official/stage-2.counts.json").read_text()),
               official_wall_seconds=(dt.datetime.fromisoformat(official["finished_at"])-dt.datetime.fromisoformat(official["started_at"])).total_seconds(),
               runs={k: json.loads((TARGET / v / "summary.json").read_text()) for k, v in {"initial":"runtime-01/probes", "expanded":"runtime-02/probes", "supplemental":"runtime-03/probes-extra", "minimal":"runtime-03/reproductions"}.items()},
               harness="Codex", configured_model="gpt-6.1-sol", actual_model="unknown", effort="unknown", usage="unknown", spend="unknown")
(TARGET / "summary.json").write_text(json.dumps(summary, indent=2))
manifest = [{"path":str(f.relative_to(TARGET)), "sha256":hashlib.sha256(f.read_bytes()).hexdigest()} for f in TARGET.rglob("*") if f.is_file()]
(TARGET / "artifact-manifest.json").write_text(json.dumps(manifest, indent=2))
with (HERE.parent / "ledger.jsonl").open("a") as f:
    f.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), phase="stage-1-candidate-1-verdict", **summary)) + "\n")
print(json.dumps({k: summary[k] for k in ["candidate", "verdict", "rows", "verified", "failed", "unverified", "failed_ids", "unverified_ids", "official_wall_seconds"]}))
