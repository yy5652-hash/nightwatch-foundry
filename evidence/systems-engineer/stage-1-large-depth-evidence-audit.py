"""Saved traces prove forwarding identity without decoding exported state."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
names = ("systems-engineer-json-large-depth-01", "systems-engineer-json-large-depth-cause-01", "systems-engineer-json-large-depth-http-01")
files, findings, records = [], [], 0
for name in names:
    for path in sorted((root / name).rglob("*")):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        files.append({"path": str(path.relative_to(root)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        if path.suffix != ".json":
            continue
        pending = [(json.loads(raw), str(path.relative_to(root)))]
        while pending:
            item, location = pending.pop()
            if isinstance(item, dict):
                records += 1
                for key, value in item.items():
                    if key.lower() in {"password", "password_hash", "token", "tokens", "state", "authorization"}:
                        findings.append(location + "/" + key)
                    pending.append((value, location + "/" + key))
            elif isinstance(item, list):
                pending.extend((value, location + "/" + str(i)) for i, value in enumerate(item))
probe = json.loads((root / names[-1] / "probe.json").read_text())
forwarding = []
for index, event in enumerate(probe["trace"]):
    if event["path"] == "/_test/export":
        imported = next(x for x in probe["trace"][index + 1:] if x["path"] == "/_test/import")
        passed = (event["decoded"] is False and event["status"] == 200 and imported["status"] == 204
                  and event["response_bytes"] == imported["request_bytes"]
                  and event["response_sha256"] == imported["request_sha256"])
        forwarding.append({"export_trace_index": index, "unchanged_bytes": event["response_bytes"],
                           "sha256": event["response_sha256"], "passed": passed})
candidate = "ab0cf79767b6768153a73894bf5768bf3328491a"
diff = subprocess.check_output(["git", "diff", candidate, "--", "stage-1", "stage-2"], cwd=root.parents[1])
summary = {"recorded_utc": datetime.now(timezone.utc).isoformat(), "json_records": records, "files_hashed": len(files),
           "raw_credential_or_export_fields": findings, "forwarding_checks": forwarding,
           "graded_diff_against_frozen_candidate_empty": diff == b"",
           "scope": "Own saved JSON traces and hashes; no export bytes or live credentials decoded or saved; not a full room-export secret review."}
(root / "stage-1-large-depth-evidence-audit.json").write_text(json.dumps({"summary": summary, "files": files}, indent=2) + "\n")
print(json.dumps(summary))
raise SystemExit(bool(findings or diff or not all(x["passed"] for x in forwarding)))
