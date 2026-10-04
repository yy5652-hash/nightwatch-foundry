"""Audit own saved repair outputs; never decode a private service export."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.set_int_max_str_digits(0)
root = Path(__file__).resolve().parent
repo = root.parents[1]
candidate = "9e6143bd4ff8d4429f51728cd3b3d96fd1f088de"
before = "ab0cf79767b6768153a73894bf5768bf3328491a"
names = (
    "systems-engineer-json-parser-host-01",
    "systems-engineer-json-parser-host-02",
    "systems-engineer-json-parser-numeric-host-01",
    "systems-engineer-json-parser-copy-host-01",
    "systems-engineer-json-decoder-service-01",
    "systems-engineer-json-parser-container-01",
    "systems-engineer-json-deep-decoder-http-01",
    "systems-engineer-json-large-depth-after-01",
)
files, findings, records, fingerprints = [], [], 0, 0
for name in names:
    for path in sorted((root / name).rglob("*")):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        files.append({"path": str(path.relative_to(root)), "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest()})
        if path.suffix != ".json":
            continue
        pending = [(json.loads(raw), str(path.relative_to(root)))]
        while pending:
            item, location = pending.pop()
            if type(item) is dict:
                records += 1
                for key, value in item.items():
                    at = location + "/" + key
                    if key.lower() in {"password", "password_hash", "token", "tokens", "state", "authorization"}:
                        if (type(value) is dict and len(value) == 1
                                and next(iter(value)) in {"fingerprint", "private_state_sha256"}
                                and type(next(iter(value.values()))) is str
                                and len(next(iter(value.values()))) == 64):
                            fingerprints += 1
                        else:
                            findings.append(at)
                    pending.append((value, at))
            elif type(item) is list:
                pending.extend((value, location + "/" + str(i)) for i, value in enumerate(item))

probe = json.loads((root / "systems-engineer-json-deep-decoder-http-01/probe.json").read_text())
forwarding = []
for case in probe["cases"]:
    exported = [(i, e) for i, e in enumerate(probe["trace"])
                if e["path"] == "/_test/export" and e["process"] == "source"
                and e["response_sha256"] == case["export_sha256"]]
    index, event = exported[0]
    imported = next(e for e in probe["trace"][index + 1:]
                    if e["path"] == "/_test/import" and e["process"] == "destination")
    passed = (not case["blocked"] and case["deep_create_status"] == case["deep_move_status"] == 201
              and event["decoded"] is False and event["status"] == 200 and imported["status"] == 204
              and event["response_bytes"] == imported["request_bytes"] == case["export_bytes"]
              and event["response_sha256"] == imported["request_sha256"] == case["forwarded_sha256"])
    forwarding.append({"case": case["label"], "export_trace_index": index,
                       "unchanged_bytes": case["export_bytes"], "sha256": case["export_sha256"], "passed": passed})
raw_export_only = all(e["decoded"] is False for e in probe["trace"] if e["path"] == "/_test/export")
timeouts = all(e["seconds"] < (10 if e["path"] in {"/_test/reset", "/_test/import"} else 5)
               for e in probe["trace"])
graded_diff = subprocess.check_output(["git", "diff", candidate, "--", "stage-1", "stage-2"], cwd=repo)
changed = subprocess.check_output(["git", "diff", "--name-only", before, candidate, "--", "stage-1", "stage-2"], cwd=repo).decode().splitlines()
runtime_names = names[-4:]
runtimes = [json.loads((root / name / "runtime.json").read_text()) for name in runtime_names]
cleanup = [c["returncode"] for runtime in runtimes for c in runtime["cleanup"]]
large_results = [e["result"] for run in runtimes[-1]["runs"] for e in run["emitted_results"] if "result" in e]
summary = {
    "recorded_utc": datetime.now(timezone.utc).isoformat(), "candidate": candidate,
    "stage1_tree": subprocess.check_output(["git", "rev-parse", candidate + ":stage-1"], cwd=repo).decode().strip(),
    "json_object_records": records, "files_hashed": len(files), "credential_state_fingerprints": fingerprints,
    "raw_private_payload_findings": findings, "forwarding_checks": forwarding,
    "every_export_trace_not_decoded": raw_export_only, "all_deep_http_requests_within_applicable_timeout": timeouts,
    "maximum_deep_request_seconds": max(e["seconds"] for e in probe["trace"]),
    "maximum_deep_request_bytes": max(e["request_bytes"] for e in probe["trace"]),
    "graded_diff_against_tested_candidate_empty": graded_diff == b"",
    "graded_changes_against_rejected_candidate": changed,
    "cleanup_exit_codes": cleanup,
    "large_isolated_assertions": sum(len(x["assertions"]) for x in large_results),
    "large_isolated_failed_assertions": sum(x["failed"] for x in large_results),
    "large_isolated_maximum_seconds": max(x["seconds"] for x in large_results),
    "large_isolated_maximum_rss_linux_kib": max(x["maximum_rss_linux_kib"] for x in large_results),
    "scope": "Own saved JSON records and file hashes only; logs/source strings are not credential inventories; no genuine room-export review. Direct codec checks are distinct from real HTTP transfer.",
}
(root / "stage-1-decoder-repair-evidence-audit.json").write_text(json.dumps({"summary": summary, "files": files}, indent=2) + "\n")
passed = (not findings and raw_export_only and timeouts and not graded_diff
          and changed == ["stage-1/json_codec.py"] and all(c == 0 for c in cleanup)
          and len(forwarding) == 6 and all(c["passed"] for c in forwarding)
          and not summary["large_isolated_failed_assertions"])
print(json.dumps({"passed": passed, "summary": summary}))
raise SystemExit(not passed)
