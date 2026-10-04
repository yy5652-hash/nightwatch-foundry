"""Run unchanged isolated checks for consecutive accepted stages in a fresh clone.
Usage: python final_clone_checks.py FULL_REV HIGHEST_ACCEPTED UNIQUE_LABEL
This creates new clone/output paths, preserves every output, and changes no source.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT.parents[1]
KICKOFF = WORKSPACE / "kickoff"
PYTHON = WORKSPACE / ".venv/bin/python"
revision, highest, label = sys.argv[1], int(sys.argv[2]), sys.argv[3]
if len(revision) != 40 or not 1 <= highest <= 4 or not re.fullmatch(r"[a-z0-9-]+", label):
    raise ValueError("Full revision, highest 1..4 and lowercase safe unique label required")
def capture(argv, cwd):
    return subprocess.check_output(argv, cwd=cwd, text=True).strip()
if capture(["git", "rev-parse", revision], ROOT) != revision:
    raise ValueError("Revision does not resolve exactly")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dt%H%M%Sz").lower()
run_label = f"foundry-coordinator-final-{label}-{stamp}"
clone = WORKSPACE / "band-work" / run_label
output_root = WORKSPACE / "band-work/final-checks" / run_label
if clone.exists() or output_root.exists():
    raise ValueError("Fresh paths required; never reuse or delete prior outputs")
output_root.mkdir()
record = {"started_utc": datetime.now(timezone.utc).isoformat(),
          "candidate_full_revision": revision, "highest_accepted": highest,
          "clone": str(clone), "output_root": str(output_root), "commands": [],
          "harness": "Codex", "configured_model": "gpt-6.1-sol",
          "actual_model": None, "effort": None, "usage": None, "estimated_cost": None,
          "billed_spend": None, "claim": "Observed fresh-clone checks, not an independent verdict or unseen score"}
record_path = output_root / "coordinator-driver.json"
def save():
    record_path.write_text(json.dumps(record, indent=2) + "\n")
def run(argv, cwd, log):
    begun = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    with (output_root / log).open("x") as stream:
        result = subprocess.run(argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
    record["commands"].append({"argv": [str(x) for x in argv], "cwd": str(cwd),
                              "started_utc": started, "returncode": result.returncode,
                              "wall_seconds": time.monotonic() - begun, "log": log})
    save()
    return result.returncode
save()
if run(["git", "clone", "--no-hardlinks", "--no-checkout", str(ROOT), str(clone)], WORKSPACE, "clone.log"):
    raise RuntimeError("Fresh clone failed; preserved log")
if run(["git", "checkout", "--detach", revision], clone, "checkout.log"):
    raise RuntimeError("Detached checkout failed; preserved log")
if capture(["git", "rev-parse", "HEAD"], clone) != revision or capture(["git", "status", "--porcelain"], clone):
    raise RuntimeError("Clone revision/cleanliness mismatch")
if run([str(PYTHON), "-B", "evidence/coordinator/freeze_stage.py", "verify"], clone, "freeze-history.log"):
    raise RuntimeError("Accepted freeze/history proof failed")
# The cloned manifest helper must establish the requested consecutive acceptance.
sys.path.insert(0, str(clone / "evidence/coordinator"))
from acceptance_state import current_manifests
accepted = {data["stage"]: data for _, data in current_manifests()}
if any(stage not in accepted for stage in range(1, highest + 1)):
    raise RuntimeError("Requested stage is not consecutively accepted")
record["accepted_stage_revisions"] = {str(stage): accepted[stage]["candidate_full_revision"] for stage in range(1, highest + 1)}
save()
for stage in range(1, highest + 1):
    argv = [str(PYTHON), "-m", "harness", "run", "--track", "tablekeeper", "--repo",
            str(clone), "--stage", str(stage), "--mode", "isolated", "--out",
            str(output_root / f"stage-{stage}")]
    run(argv, KICKOFF, f"stage-{stage}-command.log")
record["clone_status_after"] = capture(["git", "status", "--porcelain"], clone)
record["finished_utc"] = datetime.now(timezone.utc).isoformat()
record["verdict"] = "commands-completed-review-official-reports" if not record["clone_status_after"] else "dirty-clone"
save()
print(json.dumps({"record": str(record_path), "clone": str(clone), "command_returncodes": [r["returncode"] for r in record["commands"]], "clone_clean_after": not record["clone_status_after"]}))

