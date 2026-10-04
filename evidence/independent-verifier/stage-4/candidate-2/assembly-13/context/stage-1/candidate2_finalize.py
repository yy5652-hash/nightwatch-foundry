"""Add separately measured peak-50 evidence and finalize immutable artifacts."""
import csv
import datetime as dt
import hashlib
import json
import shlex
import shutil
from pathlib import Path

here = Path(__file__).resolve().parent
repo = here.parents[2]
target = here / "candidate-2"
source = repo.parents[1] / "band-work/final-checks/independent-verifier-s1-dd64419-runtime-03"
shutil.copytree(source, target / "runtime-03")
path = target / "runtime-03/race50/assertions.json"
assertions = json.loads(path.read_text())
assert all(a["passed"] for a in assertions)
commands = json.loads((target / "runtime-03/extra-commands.json").read_text())
command = shlex.join(next(c["command"] for c in commands if c["log"] == "race50-client.log"))
with (target / "coverage.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
for row in rows:
    found = [a for a in assertions if a["requirement_id"] == row["requirement_id"]]
    if found:
        row["evidence_path"] += "; "+str(path.relative_to(repo))+"#"+row["requirement_id"]
        row["executable_command_or_interaction"] += "\n"+command
        assert row["verdict"] == "verified"
with (target / "coverage.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
summary = json.loads((target / "summary.json").read_text())
summary["runs"]["runtime-03/race50"] = json.loads((target / "runtime-03/race50/summary.json").read_text())
summary["concurrency_note"] = "Unstaged client intervals peaked at 49; explicitly staged final-body-byte workload attained peak 50 with one 201 and 49 200 receipts. Both traces retained."
(target / "summary.json").write_text(json.dumps(summary, indent=2))
with (here.parent / "ledger.jsonl").open("a") as f:
    f.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), phase="stage-1-candidate-2-final-evidence", **summary))+"\n")
manifest = [dict(path=str(f.relative_to(target)), sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in target.rglob("*") if f.is_file() and f.name != "artifact-manifest.json"]
(target / "artifact-manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(dict(files=len(manifest), rows=len(rows), verified=summary["verified"], failed=summary["failed"], unverified=summary["unverified"])))
