"""Scoped saved-evidence integrity and private payload review; not room export."""
import ast
from coverage_metadata import validate
import csv
import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
sys.set_int_max_str_digits(0);sys.setrecursionlimit(20000)  # This reader only.
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];TARGET=HERE/"candidate-7"
findings=[];records=0;masked=0
for path in TARGET.rglob("*.json"):
    if path.name in ["artifact-audit.json","artifact-initial-field-scan.json"]:continue
    value=json.loads(path.read_text(),parse_float=Decimal);pending=[(value,"")]
    while pending:
        item,location=pending.pop()
        if isinstance(item,dict):
            records+=1
            for key,child in item.items():
                if key.lower() in ["token","tokens","password","password_hash","authorization","state"]:
                    redacted=(isinstance(child,str) and any(s in child.lower() for s in ["private","redact","hash","omitted"])) or isinstance(child,dict) and all(any(s in k for s in ["sha256","digest","fingerprint"]) for k in child)
                    if redacted:masked+=1
                    else:findings.append(dict(file=str(path.relative_to(TARGET)),path=location+"/"+key,type=type(child).__name__,keys=list(child) if isinstance(child,dict) else None,value=child if isinstance(child,str) else None))
                pending.append((child,location+"/"+key))
        elif isinstance(item,list):pending.extend((child,location+"/"+str(i)) for i,child in enumerate(item))
allowed={("numeric-01/inspect.json","/0/State"),("fractional-01/inspect.json","/0/State"),("baseline-01/legacy-inspect.json","/0/State"),("official/report.json","/state")}
assert {(f["file"],f["path"]) for f in findings}==allowed
for f in findings:
    if f["file"]=="official/report.json":assert f["value"]=="completed"
    else:assert {"Status","Running","Paused","OOMKilled","Pid","ExitCode"}<=set(f["keys"])
(TARGET/"artifact-initial-field-scan.json").write_text(json.dumps(dict(object_records=records,initial_unclassified_findings=findings,classification="Three Docker container State metadata objects and one harness state=completed; no private service snapshot or credential content."),indent=2))
summary=json.loads((TARGET/"summary.json").read_text())
with (TARGET/"coverage.csv").open() as f:rows=list(csv.DictReader(f))
assert len(rows)==4275 and len({r["requirement_id"] for r in rows})==4275
metadata=validate(rows)
assert metadata["empty_required_fields"]==0
assert all(r["candidate_full_revision"]==summary["candidate"] for r in rows)
assert all(r["evidence_path"]!="UNVERIFIED" and r["executable_command_or_interaction"] for r in rows)
assert not any("FULL_NAMED_CANDIDATE" in r["executable_command_or_interaction"] or "f5e0a532" in r["executable_command_or_interaction"] for r in rows)
for row in rows:
    for reference in row["evidence_path"].split("; "):
        assert (REPO/reference.split("#",1)[0]).is_file(),reference
syntax_files=["candidate7_source.py","candidate7_assess.py","candidate7_artifact_audit.py","very_deep_probe_c7.py","very_deep_run_c7.py","numeric_forms_current.py","numeric_forms_current_run.py","legacy_receipts_current.py","legacy_current_run.py"]
syntax_files += ["decoder_probe.py","decoder_oracle.py","decoder_requirements.py","decoder_runtime.py","deep_race_c7.py","deep_race_c7_run.py","candidate7_execute.py","coverage_metadata.py"]
for name in syntax_files:ast.parse((HERE/name).read_text())
argv=["docker","ps","-a","--filter","name=independent-verifier-","--format","{{.ID}} {{.Names}} {{.Status}}"]
inventory=subprocess.check_output(argv,text=True);assert not inventory.strip()
(TARGET/"final-resource-inventory.json").write_text(json.dumps(dict(argv=argv,returncode=0,output=inventory,scope="verifier-prefixed containers only; images/clones retained"),indent=2))
files={str(path.relative_to(REPO)):dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in TARGET.rglob("*") if path.is_file() and path.name!="artifact-audit.json"}
proof=dict(candidate=summary["candidate"],records_inspected=records,redacted_or_fingerprinted_sensitive_fields=masked,classified_nonprivate_state_fields=len(findings),unclassified_private_payload_findings=0,
    normative_rows=summary["normative_rows"],diagnostics=summary["diagnostic_rows"],metadata=metadata,syntax_files=syntax_files,
    own_source_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in syntax_files},manifest=files,
    scope="Saved JSON records plus byte manifest only. Source/log text and genuine full room export are not a complete secret audit. No bearer token/full export/password hash payload is intentionally stored.")
(TARGET/"artifact-audit.json").write_text(json.dumps(proof,indent=2))
print(json.dumps(dict(records=records,masked_fields=masked,classified_nonprivate_fields=len(findings),unclassified_findings=0,manifest_files=len(files),coverage_rows=len(rows),syntax_files=len(syntax_files),own_container_inventory_empty=True)))
