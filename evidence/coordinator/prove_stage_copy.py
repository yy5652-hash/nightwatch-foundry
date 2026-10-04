"""Record an exact committed, clean copy of every accepted predecessor file.
Usage: python prove_stage_copy.py NEXT_STAGE ACCEPTED_FULL_REV NEW_EVIDENCE_PATH
Extra target files are retained and listed; the predecessor service is never written.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from acceptance_state import current_manifests, verify_history

ROOT = Path(__file__).resolve().parents[2]
def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)
def entries(rev, stage):
    result = {}
    for record in git("ls-tree", "-rz", rev, "--", f"stage-{stage}").split(b"\0"):
        if not record:
            continue
        meta, name = record.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        path = name.decode()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError("Unsupported stage object: " + path)
        result[path.split("/", 1)[1]] = {"mode": mode, "object_id": oid}
    return result

next_stage = int(sys.argv[1])
source_revision = sys.argv[2]
if next_stage < 2 or len(source_revision) != 40 or git("rev-parse", source_revision).decode().strip() != source_revision:
    raise ValueError("Provide next stage >= 2 and a full existing predecessor revision")
verify_history()
accepted = {data["stage"]: data for _, data in current_manifests()}
prior = next_stage - 1
if prior not in accepted or accepted[prior]["candidate_full_revision"] != source_revision:
    raise ValueError("Source is not the current accepted predecessor")
for stage, manifest in accepted.items():
    if entries("HEAD", stage) != entries(manifest["candidate_full_revision"], stage):
        raise ValueError(f"Accepted Stage {stage} changed")
    if git("status", "--porcelain", "--", f"stage-{stage}").strip():
        raise ValueError(f"Accepted Stage {stage} is dirty")
if git("status", "--porcelain", "--", f"stage-{next_stage}").strip():
    raise ValueError("Target stage has uncommitted files")
head = git("rev-parse", "HEAD").decode().strip()
source = entries(source_revision, prior)
target = entries(head, next_stage)
if not source:
    raise ValueError("Empty predecessor")
rows = []
for path, item in source.items():
    if target.get(path) != item:
        raise ValueError("Target file is not an exact committed copy: " + path)
    data = git("show", f"{source_revision}:stage-{prior}/{path}")
    destination = ROOT / f"stage-{next_stage}" / path
    if destination.read_bytes() != data:
        raise ValueError("Working file differs: " + path)
    rows.append({"path": path, **item, "sha256": hashlib.sha256(data).hexdigest(), "verdict": "identical"})
output = (ROOT / sys.argv[3]).resolve()
output.relative_to(ROOT / "evidence")
report = {"wall_time_utc": datetime.now(timezone.utc).isoformat(),
          "source_accepted_stage": prior, "source_full_revision": source_revision,
          "target_stage": next_stage, "target_base_full_revision": head,
          "copied_files": rows, "retained_extra_target_files": sorted(set(target) - set(source)),
          "verdict": "pass", "claim": "Exact predecessor file inheritance before extension; not stage acceptance"}
with output.open("x") as stream:
    json.dump(report, stream, indent=2)
    stream.write("\n")
print(json.dumps({"verdict": "pass", "copied_files": len(rows), "target_base_full_revision": head, "evidence": str(output.relative_to(ROOT))}))

