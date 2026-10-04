"""Audit candidate coverage metadata before promotion; no service behavior is tested.
Usage: python audit_candidate_coverage.py STAGE FULL_REV MATRIX_PATH NEW_OUTPUT_PATH
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
stage, revision = int(sys.argv[1]), sys.argv[2]
matrix, destination = Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
matrix.relative_to(ROOT)
destination.relative_to(ROOT)
if stage not in range(1, 5) or not re.fullmatch(r"[0-9a-f]{40}", revision):
    raise ValueError("Stage 1..4 and full hexadecimal revision required")
if subprocess.check_output(["git", "rev-parse", revision], cwd=ROOT, text=True).strip() != revision:
    raise ValueError("Candidate revision does not resolve exactly")
# Bindings may contain complete executed command lists; retain exact full cells.
csv.field_size_limit(sys.maxsize)
rows = list(csv.DictReader(matrix.open()))
required = ("requirement_id", "source_section", "source_line", "introduced_stage",
            "applicable_stages", "owner", "implementation_owner", "verification_owner",
            "requirement_text", "candidate_full_revision", "verification_method",
            "executable_command_or_interaction", "evidence_path", "verdict")
errors, seen = [], set()
counts = {"normative": {}, "diagnostic": {}}
for row in rows:
    label = row.get("requirement_id", "<missing id>")
    if label in seen:
        errors.append(label + ": duplicate ID")
    seen.add(label)
    for field in required:
        if not row.get(field, "").strip():
            errors.append(label + ": missing " + field)
    if row.get("candidate_full_revision") != revision:
        errors.append(label + ": revision mismatch")
    normative = row.get("normative", "True").strip().lower() != "false"
    family = "normative" if normative else "diagnostic"
    verdict = row.get("verdict", "")
    counts[family][verdict] = counts[family].get(verdict, 0) + 1
    if normative and verdict != "verified":
        errors.append(label + ": normative verdict " + verdict)
    if str(stage) not in {x.strip() for x in row.get("applicable_stages", "").split(",")}:
        errors.append(label + ": current stage applicability absent")
    for field in ("executable_command_or_interaction", "evidence_path"):
        value = row.get(field, "")
        if any(marker in value for marker in ("PENDING_FRESH", "FULL_NAMED_STAGE", "CURRENT_CANDIDATE_REQUIRED")):
            errors.append(label + ": placeholder in " + field)
    for evidence in row.get("evidence_path", "").split(";"):
        file_part = evidence.strip().split("#", 1)[0]
        artifact = Path(file_part)
        if not artifact.is_absolute():
            artifact = ROOT / artifact
        try:
            artifact.resolve().relative_to(ROOT)
        except ValueError:
            errors.append(label + ": artifact outside result")
        if not file_part or not artifact.is_file():
            errors.append(label + ": missing artifact " + file_part)
record = {"wall_time_utc": datetime.now(timezone.utc).isoformat(),
          "scope": "Coordinator metadata and file-existence audit; not independent execution or source completeness certification",
          "stage": stage, "candidate_full_revision": revision,
          "matrix": str(matrix.relative_to(ROOT)),
          "matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
          "required_metadata_fields": list(required), "rows": len(rows),
          "unique_ids": len(seen), "counts": counts,
          "errors": errors, "status": "pass" if rows and not errors else "fail"}
with destination.open("x") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({"output": str(destination.relative_to(ROOT)), "rows": len(rows),
                  "counts": counts, "error_count": len(errors), "status": record["status"]}))
raise SystemExit(record["status"] != "pass")
