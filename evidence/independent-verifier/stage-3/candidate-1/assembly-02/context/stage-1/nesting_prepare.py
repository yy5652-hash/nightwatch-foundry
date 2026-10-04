"""Independent bounded-depth input/grammar self-check; zero HTTP execution."""
import ast
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from nesting_input import DEPTHS,SHAPES,configure_client,inspect_generated,max_container_depth,raw,tree
from nesting_requirements import CASES,rows
from semantic_oracle import encode,parse,same

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1]
OUT=HERE/"candidate-6-nesting-preparation"
def write_csv(path,values):
    keys=list(dict.fromkeys(key for row in values for key in row))
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,lineterminator="\n");writer.writeheader();writer.writerows(values)

def main():
    configure_client();OUT.mkdir(exist_ok=True);inputs=OUT/"raw-ignored-values";inputs.mkdir(exist_ok=True)
    validations=[];source=[]
    for name in ["nesting_input.py","nesting_requirements.py","nesting_probe.py","nesting_prepare.py","semantic_runtime.py"]:
        data=(HERE/name).read_bytes();ast.parse(data.decode(),filename=name)
        source.append(dict(path=str((HERE/name).relative_to(REPO)),sha256=hashlib.sha256(data).hexdigest(),syntax_valid=True))
    for shape in SHAPES:
        for depth in DEPTHS:
            original=tree(shape,depth)
            for variant in ["original","alias","number-difference","type-difference"]:
                literal=raw(shape,depth,variant);decoded=parse(literal)
                assert inspect_generated(decoded,shape,depth,variant)
                assert same(decoded,tree(shape,depth,variant))
                assert same(decoded,original)==(variant in ["original","alias"])
                assert max_container_depth(decoded)==depth+2
                validations.append(dict(shape=shape,wrapper_depth=depth,variant=variant,bytes=len(literal.encode()),actual_max_container_depth=max_container_depth(decoded),grammar_valid=True,independent_wrapper_inspection=True,exact_value_checked=True,sha256=hashlib.sha256(literal.encode()).hexdigest()))
            literal=raw(shape,depth)
            (inputs/(shape+"-"+str(depth)+".json")).write_bytes(literal.encode())
            refused=False
            try:parse(literal[:-1])
            except ValueError:refused=True
            assert refused
            validations.append(dict(shape=shape,wrapper_depth=depth,variant="truncated",bytes=len(literal[:-1].encode()),grammar_valid=False,expected_refusal=True,sha256=hashlib.sha256(literal[:-1].encode()).hexdigest()))
    supplement=rows();write_csv(OUT/"coverage-prepared.csv",supplement)
    previous_path=HERE/"candidate-6-opaque-id-preparation/coverage-cumulative-prepared.csv"
    previous=list(csv.DictReader(previous_path.open(newline="")))
    for row in previous:row["preparation_origin"]=row.get("preparation_origin","") or "Earlier preparation"
    for row in supplement:row["preparation_origin"]="Nesting supplement from source note1f3176df"
    combined=previous+supplement
    assert len({row["requirement_id"] for row in combined})==len(combined) and all(row["verdict"]=="unverified" for row in combined)
    write_csv(OUT/"coverage-cumulative-prepared.csv",combined)
    guard_out=OUT/"guard-must-not-create";assert not guard_out.exists()
    argv=[sys.executable,"-B",str(HERE/"semantic_runtime.py"),"--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate","0"*40,"--handoff",str(HERE/"candidate-6-preparation/intake.json"),"--probe-family","nesting","--out",str(guard_out)]
    guard=subprocess.run(argv,cwd=REPO,capture_output=True,text=True)
    (OUT/"execution-guard.log").write_text(guard.stdout+guard.stderr)
    assert guard.returncode==2 and "execution waits" in guard.stderr and not guard_out.exists()
    valid=[item for item in validations if item["grammar_valid"]]
    summary=dict(scope="Bounded input/client grammar self-checks only; no service execution",source_note="1f3176df-4062-4575-b9e6-59f502357d31",candidate="pending explicit complete named handoff",wrapper_depths=DEPTHS,shapes=SHAPES,input_checks=len(validations),valid_input_checks=len(valid),expected_malformed_checks=len(validations)-len(valid),syntax_files=5,
                 max_ignored_value_bytes=max(item["bytes"] for item in valid),max_generated_container_depth=max(item["actual_max_container_depth"] for item in valid),supplement_normative_rows=len(supplement),cumulative_normative_rows=sum(str(row.get("normative",True)).lower()=="true" for row in combined),admission_diagnostics=sum(str(row.get("normative",True)).lower()=="false" for row in combined),cumulative_all_records=len(combined),verified=0,failed=0,unverified=len(combined),service_requests=0,official_checks=0,
                 client_recursion_limit=20000,service_configuration_changed=False,guard_expected_refusal=True,guard_argv=argv,previous_matrix_sha256=hashlib.sha256(previous_path.read_bytes()).hexdigest(),reviewed_at=dt.datetime.now(dt.timezone.utc).isoformat(),harness="Codex",configured_model="gpt-6.1-sol",actual_model="unknown",effort="unknown",usage_and_spend="unknown")
    (OUT/"input-grammar-validation.json").write_text(json.dumps(dict(scope="Generated grammar/depth/value self-check only; no service requests",checks=validations),indent=2))
    (OUT/"source-proof.json").write_text(json.dumps(dict(scope="Own generated inputs/protocol and source requirements only; no product, builder probe or oracle imports",files=source,official_source="kickoff/tablekeeper/spec/stage-1.md:86-89,157-186,229-262,417-472",required_method="NestingProbe.scenario",declared_requirement_ids=[row["requirement_id"] for row in supplement]),indent=2))
    (OUT/"preparation-summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))

if __name__=="__main__":main()
