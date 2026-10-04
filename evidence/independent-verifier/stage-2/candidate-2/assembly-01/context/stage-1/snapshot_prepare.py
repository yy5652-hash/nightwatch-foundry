"""Local oracle/schedule self-checks only; never creates a service resource."""
import ast
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from semantic_oracle import encode,parse,same
from snapshot_oracle import MEMBERS,MODES,PAD_BYTES,SEED,STEPS,WAVES,schedule,self_check
from snapshot_requirements import rows

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1]
OUT=HERE/"candidate-6-snapshot-preparation"
def write_csv(path,values):
    keys=list(dict.fromkeys(key for row in values for key in row))
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,lineterminator="\n");writer.writeheader();writer.writerows(values)

def main():
    OUT.mkdir(exist_ok=True);source=[]
    for name in ["snapshot_oracle.py","snapshot_requirements.py","snapshot_probe.py","snapshot_prepare.py","semantic_runtime.py"]:
        data=(HERE/name).read_bytes();ast.parse(data.decode(),filename=name)
        source.append(dict(path=str((HERE/name).relative_to(REPO)),sha256=hashlib.sha256(data).hexdigest(),syntax_valid=True))
    checks=self_check();planned=schedule()
    assert same(parse(encode(planned)),planned)
    checks.append(dict(case="schedule-exact-json-roundtrip",passed=True))
    for item in planned:
        assert item["upper"]-item["lower"]==STEPS and len(set(item["route_launch_order"]))==3
        assert item["write_generations"]==list(range(item["lower"]+1,item["upper"]+1))
        checks.append(dict(case=item["mode"]+"-"+str(item["wave"])+"-schedule-gates",passed=True))
    supplement=rows();previous_path=HERE/"candidate-6-nesting-preparation/coverage-cumulative-prepared.csv"
    previous=list(csv.DictReader(previous_path.open(newline="")))
    for row in previous:row["preparation_origin"]=row.get("preparation_origin","") or "Earlier preparation"
    for row in supplement:row["preparation_origin"]="Snapshot concurrency supplement from source note22b8029c"
    combined=previous+supplement
    assert len({row["requirement_id"] for row in combined})==len(combined) and all(row["verdict"]=="unverified" for row in combined)
    write_csv(OUT/"coverage-prepared.csv",supplement);write_csv(OUT/"coverage-cumulative-prepared.csv",combined)
    guard_out=OUT/"guard-must-not-create";assert not guard_out.exists()
    argv=[sys.executable,"-B",str(HERE/"semantic_runtime.py"),"--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate","0"*40,"--handoff",str(HERE/"candidate-6-preparation/intake.json"),"--probe-family","snapshot","--out",str(guard_out)]
    guard=subprocess.run(argv,cwd=REPO,capture_output=True,text=True)
    (OUT/"execution-guard.log").write_text(guard.stdout+guard.stderr)
    assert guard.returncode==2 and "execution waits" in guard.stderr and not guard_out.exists()
    summary=dict(scope="Local independent state oracle/schedule/AST only; zero service execution",source_note="22b8029c-5250-46dc-8b1f-1e5c74f4d46d",candidate="pending explicit complete named handoff",seed=SEED,modes=MODES,waves_per_mode=WAVES,steps_per_wave=STEPS,members_per_atomic_move=MEMBERS,padding_bytes_per_receipt_body=PAD_BYTES,planned_read_captures=len(planned)*3,planned_export_captures=len(planned),independent_destinations_per_capture=2,
        oracle_and_schedule_checks=len(checks),syntax_files=5,supplement_normative_rows=len(supplement),cumulative_normative_rows=sum(str(row.get("normative",True)).lower()=="true" for row in combined),admission_diagnostics=sum(str(row.get("normative",True)).lower()=="false" for row in combined),cumulative_all_records=len(combined),verified=0,failed=0,unverified=len(combined),service_requests=0,official_checks=0,images_or_containers_started=0,guard_expected_refusal=True,guard_argv=argv,
        server_internal_interleaving="unobserved; deterministic client gates and measured events only",controlled_receive_excluded_from_server_latency_claim=True,previous_matrix_sha256=hashlib.sha256(previous_path.read_bytes()).hexdigest(),prepared_at=dt.datetime.now(dt.timezone.utc).isoformat(),harness="Codex",configured_model="gpt-6.1-sol",actual_model="unknown",effort="unknown",usage_and_spend="unknown")
    for name,data in [("preparation-summary.json",summary),("oracle-validation.json",dict(scope="Synthetic observable local states only; no fabricated service export",checks=checks)),("schedule.json",dict(seed=SEED,schedule=planned)),("source-proof.json",dict(scope="Own source-derived client code; no product or builder test/oracle imports",files=source,source_sections="Stage1 §§1/2/3.4/5/6/7/8/10/11",required_methods="SnapshotProbe.wave / replace_capture and Capture.run",requirement_ids=[row["requirement_id"] for row in supplement]))]:
        (OUT/name).write_text(json.dumps(data,indent=2))
    print(json.dumps(summary))

if __name__=="__main__":main()
