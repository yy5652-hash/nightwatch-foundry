"""Scoped own output hashes/credential-fingerprint audit, not a room export scan."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.set_int_max_str_digits(0)
root = Path(__file__).resolve().parent
directories = [root / name for name in ("systems-engineer-json-service-01", "systems-engineer-json-service-02",
                                       "systems-engineer-json-reset-extra-01", "systems-engineer-json-reset-extra-02",
                                       "systems-engineer-json-decoder-depth-extra-01")]
records, files, findings, redactions = 0, [], [], 0
private_names = {"password", "password_hash", "token", "tokens", "state", "authorization"}
for directory in directories:
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        files.append({"path": str(path.relative_to(root)), "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest()})
        if path.suffix != ".json":
            continue
        tree = json.loads(raw)
        pending = [(tree, str(path.relative_to(root)))]
        while pending:
            item, at = pending.pop()
            if type(item) is dict:
                records += 1
                for key, value in item.items():
                    location = at + "/" + key
                    if key.lower() in private_names:
                        if (type(value) is dict and len(value) == 1 and
                                next(iter(value)) in {"fingerprint", "private_state_sha256"} and
                                type(next(iter(value.values()))) is str and len(next(iter(value.values()))) == 64):
                            redactions += 1
                        else:
                            findings.append(location)
                    pending.append((value, location))
            elif type(item) is list:
                pending.extend((child, at + "/" + str(index)) for index, child in enumerate(item))
summary = {"recorded_utc": datetime.now(timezone.utc).isoformat(), "directories": [str(p) for p in directories],
           "json_object_records": records, "files_hashed": len(files), "credential_state_fingerprints": redactions,
           "raw_private_payload_findings": findings,
           "scope": "Own JSON records only; logs/source strings not credential inventories; genuine room export not reviewed."}
(root / "stage-1-json-service-evidence-audit.json").write_text(json.dumps({"summary": summary, "files": files}, indent=2) + "\n")
print(json.dumps(summary))
sys.exit(bool(findings))
