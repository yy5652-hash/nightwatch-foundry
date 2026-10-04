"""Prepare cumulative rows; no candidate execution and no historical pass reuse."""
import csv
import hashlib
import json
import shutil
from pathlib import Path
from semantic_requirements import row_list

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORKSPACE=REPO.parents[1]
TARGET=HERE/"candidate-6-preparation"
TARGET.mkdir(exist_ok=True)
rows=[]
for family,filename in [("candidate5-full","candidate-5/coverage.csv"),("candidate5-finite-party-supplement","candidate-5-supplemental-fraction/coverage.csv")]:
    with (HERE/filename).open(newline="") as stream: inherited=list(csv.DictReader(stream))
    for row in inherited:
        row["inherited_from"]=family
        row["historical_verdict"]=row["verdict"]
        row["historical_candidate"]=row["candidate_full_revision"]
        row["historical_evidence_path"]=row["evidence_path"]
        row["candidate_full_revision"]="PENDING_NAMED_CANDIDATE"
        row["evidence_path"]="UNVERIFIED"
        row["verdict"]="unverified"
        row["executable_command_or_interaction"]=row["executable_command_or_interaction"].replace("f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250","FULL_NAMED_CANDIDATE")
        row["interpretation_note"] += " Fresh execution required; candidate5 is historical. Adopted body numeric-value decision applies prospectively."
    rows.extend(inherited)
for row in row_list():
    row.update(inherited_from="new-source-derived-numeric-decision",historical_verdict="none",historical_candidate="none",historical_evidence_path="none")
    row["executable_command_or_interaction"]="../../.venv/bin/python -B evidence/independent-verifier/stage-1/semantic_probe.py --base CURRENT_URL --peer PEER_URL --third THIRD_URL --legacy GENUINE_49287b4_URL --candidate FULL_NAMED_CANDIDATE --out NEW_UNIQUE_DIRECTORY"
    rows.append(row)
assert len({row["requirement_id"] for row in rows})==len(rows)
keys=list(rows[0])
with (TARGET/"coverage-prepared.csv").open("w",newline="") as stream:
    writer=csv.DictWriter(stream,fieldnames=keys,lineterminator="\n")
    writer.writeheader();writer.writerows(rows)
sources=[WORKSPACE/"kickoff/docs/participant-guide.md",WORKSPACE/"kickoff/tablekeeper/spec/stage-1.md",
         WORKSPACE/"factory/PRODUCT_ACCEPTANCE.md",REPO/"evidence/coordinator/json-number-semantics-decision.md",
         REPO/"evidence/coordinator/handoffs/TK-20261004-S1-independent-verifier-CANDIDATE-6-PREP.txt",
         REPO/"evidence/coordinator/handoffs/TK-20261004-S1-independent-verifier-CANDIDATE-6-PREP.delivery.json"]
proof=[]
inputs=TARGET/"source-inputs";inputs.mkdir(exist_ok=True)
for path in sources:
    data=path.read_bytes()
    proof.append(dict(path=str(path.relative_to(WORKSPACE)),sha256=hashlib.sha256(data).hexdigest()))
    name=path.name
    shutil.copyfile(path,inputs/name)
(TARGET/"source-inputs.json").write_text(json.dumps(dict(sources=proof,scope="Complete received assignment/spec/guide/brief/recorded numeric decision plus own previous evidence; no builder probe, oracle or shipped test source used.",historical_receipt_and_timestamp_decisions="Full text preserved in the complete received preparation package."),indent=2))
summary=dict(package="TK-20261004-S1-independent-verifier-CANDIDATE-6-PREP",candidate="pending explicit complete named handoff",
             rows=len(rows),inherited_rows=967,new_numeric_decision_rows=len(row_list()),verified=0,failed=0,unverified=len(rows),
             service_http_requests=0,official_checks_executed=0,highest_accepted_stage=0,
             note="Preparation only; every historical pass is reset to unverified for the pending candidate.")
assert len(rows)==967+len(row_list())
(TARGET/"coverage-summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
