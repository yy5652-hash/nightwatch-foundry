"""Prepare ID rows and validate URI/input syntax; no HTTP or Docker execution."""
import ast
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs,unquote,urlsplit
from opaque_id_requirements import CASES,VARIANTS,availability_path,detail_path,fixture,rows
from semantic_oracle import encode,parse,same

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2];WORKSPACE=REPO.parents[1]
OUT=HERE/"candidate-6-opaque-id-preparation"

def write_csv(path,values):
    keys=list(dict.fromkeys(key for row in values for key in row))
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,lineterminator="\n");writer.writeheader();writer.writerows(values)

def main():
    OUT.mkdir(exist_ok=True);validation=[];sources=[]
    for name in ["opaque_id_requirements.py","opaque_id_probe.py","opaque_id_prepare.py","semantic_runtime.py"]:
        data=(HERE/name).read_bytes();ast.parse(data.decode(),filename=name)
        sources.append(dict(path=str((HERE/name).relative_to(REPO)),sha256=hashlib.sha256(data).hexdigest(),syntax_valid=True))
    for name in ["OpaqueId.Probe.Dockerfile","semantic_probe.py","semantic_oracle.py","semantic_requirements.py","health.py"]:
        path=HERE/name;sources.append(dict(path=str(path.relative_to(REPO)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for surface in ["restaurant","table"]:
        for label,value in VARIANTS.items():
            assert 1<=len(value)<=64
            f=fixture(surface,value);rid=f["restaurants"][0]["id"]
            assert same(parse(encode(f)),f)
            route=detail_path(rid);query=availability_path(rid)
            assert unquote(route[len("/restaurants/"):],encoding="utf-8",errors="strict")==rid
            assert urlsplit(route).query=="" and urlsplit(route).fragment==""
            assert parse_qs(urlsplit(query).query)["restaurant_id"]==[rid]
            assert urlsplit(query).fragment==""
            if surface=="restaurant" and label=="literal-percent":assert "%252F" in route
            validation.append(dict(surface=surface,label=label,characters=len(value),utf8_bytes=len(value.encode()),input_roundtrip=True,detail_path=route,availability_path=query,exact_decode_once=True))
    supplement=rows();write_csv(OUT/"coverage-prepared.csv",supplement)
    previous_path=HERE/"candidate-6-preparation/coverage-prepared.csv"
    previous=list(csv.DictReader(previous_path.open(newline="")))
    for row in previous:row["normative"]=True;row["preparation_origin"]="candidate-6-preparation at b9174e1e7f8661dab6147bd662af540197cc12b4"
    for row in supplement:row["preparation_origin"]="opaque ID supplement from source note45bfa6ba"
    combined=previous+supplement
    assert len({row["requirement_id"] for row in combined})==len(combined)
    assert all(row["verdict"]=="unverified" for row in combined)
    write_csv(OUT/"coverage-cumulative-prepared.csv",combined)
    guard_out=OUT/"guard-must-not-create";assert not guard_out.exists()
    argv=[sys.executable,"-B",str(HERE/"semantic_runtime.py"),"--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate","0"*40,"--handoff",str(HERE/"candidate-6-preparation/intake.json"),"--probe-family","opaque-ids","--out",str(guard_out)]
    guard=subprocess.run(argv,cwd=REPO,capture_output=True,text=True)
    (OUT/"execution-guard.log").write_text(guard.stdout+guard.stderr)
    assert guard.returncode==2 and "execution waits" in guard.stderr and not guard_out.exists()
    summary=dict(scope="Preparation only; no observed service acceptance or lexical defect",source_note_message="45bfa6ba-4d7c-4789-abf3-e9a21d1fec87",source_assessment_message="93702729-daaa-4918-a180-b9100bbe0a94",candidate="pending complete named handoff",
                 variants=len(VARIANTS),surfaces=2,fixture_and_uri_self_checks=len(validation),syntax_files=4,supplement_normative_rows=sum(row["normative"] for row in supplement),supplement_admission_diagnostics=sum(not row["normative"] for row in supplement),supplement_all_records=len(supplement),
                 cumulative_normative_rows=len(previous)+sum(row["normative"] for row in supplement),cumulative_admission_diagnostics=sum(not row["normative"] for row in supplement),cumulative_all_records=len(combined),verified=0,failed=0,unverified=len(combined),service_requests=0,official_checks=0,
                 guard_expected_refusal=True,guard_argv=argv,previous_matrix_sha256=hashlib.sha256(previous_path.read_bytes()).hexdigest(),reviewed_at=dt.datetime.now(dt.timezone.utc).isoformat(),harness="Codex",configured_model="gpt-6.1-sol",actual_model="unknown",effort="unknown",usage_and_spend="unknown")
    (OUT/"preparation-summary.json").write_text(json.dumps(summary,indent=2))
    (OUT/"input-uri-validation.json").write_text(json.dumps(dict(scope="Input/client URI self-checks only, zero service requests",checks=validation),indent=2))
    (OUT/"source-proof.json").write_text(json.dumps(dict(scope="Independent own client source; no builder probe/oracle or product imports",sources=sources,official_source="kickoff/tablekeeper/spec/stage-1.md:90-91,275-359,411-472",normative_ids=[row["requirement_id"] for row in supplement if row["normative"]],diagnostic_ids=[row["requirement_id"] for row in supplement if not row["normative"]]),indent=2))
    print(json.dumps(summary))

if __name__=="__main__":main()
