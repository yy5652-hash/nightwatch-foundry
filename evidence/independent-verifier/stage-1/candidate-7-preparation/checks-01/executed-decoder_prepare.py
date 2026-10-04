"""Prepare/self-check own evidence only; no service build/start/request."""
import argparse
import ast
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from decoder_oracle import DEPTHS, SHAPES, LEAF, LEAF_ALIAS, LEAF_DIFFERENT, LEAF_TYPED, grammar_cases, randomized_values, self_check, sha, wrap
from decoder_requirements import CASES, rows

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1]
INTAKE=HERE/"candidate-7-preparation/intake.json"
REJECTED="ab0cf79767b6768153a73894bf5768bf3328491a"
SEALED="7db8085f06bd6aa53443f5cf647ff4111bbaa771"
SOURCES=["decoder_oracle.py","decoder_requirements.py","decoder_probe.py","decoder_runtime.py","decoder_prepare.py","Decoder.Probe.Dockerfile"]

def write_csv(path, values):
    keys=list(dict.fromkeys(k for row in values for k in row))
    with path.open("w",newline="") as stream:
        w=csv.DictWriter(stream,fieldnames=keys,lineterminator="\n");w.writeheader();w.writerows(values)

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args()
    out=Path(a.out).resolve();assert out.is_relative_to(HERE) and out.name.startswith("checks-")
    intake=json.loads(INTAKE.read_text())
    assert intake["package_id"]=="TK-20261004-S1-independent-verifier-CANDIDATE-7-PREP" and intake["execution_authorized"] is False
    assert set(intake["parts"])==set(map(str,range(1,11))) and intake["end_received"] and intake["acknowledgement"]["all_parts_and_end_acknowledged"]
    out.mkdir(parents=True,exist_ok=False);began=time.monotonic();start=dt.datetime.now(dt.timezone.utc).isoformat()
    checks=self_check();proof=[]
    for name in SOURCES:
        raw=(HERE/name).read_bytes()
        if name.endswith(".py"):
            tree=ast.parse(raw.decode(),filename=name)
            imported=[]
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):imported.extend(item.name.split(".")[0] for item in node.names)
                if isinstance(node,ast.ImportFrom):imported.append((node.module or "").split(".")[0])
            assert not {"core","json_codec"}.intersection(imported)
            assert "setrecursionlimit" not in raw.decode()
            checks.append(dict(label="own-source-syntax-and-no-production-import-"+name,passed=True))
        proof.append(dict(path=str((HERE/name).relative_to(REPO)),sha256=sha(raw),bytes=len(raw)))
    samples=[];(out/"raw-ignored-values").mkdir()
    for shape in SHAPES:
        for depth in DEPTHS:
            for variant,leaf in [("original",LEAF),("alias",LEAF_ALIAS),("precision",LEAF_DIFFERENT),("boolean",LEAF_TYPED)]:
                raw=wrap(shape,depth,leaf)
                if shape=="array":reference=b"["*depth+leaf+b"]"*depth
                elif shape=="object":reference=b'{"v":'*depth+leaf+b"}"*depth
                else:reference=b'[{"v":'*(depth//2)+(b"[" if depth%2 else b"")+leaf+(b"]" if depth%2 else b"")+b"}]"*(depth//2)
                assert raw==reference
                path=out/"raw-ignored-values"/(f"{shape}-{depth}-{variant}.json");path.write_bytes(raw)
                samples.append(dict(shape=shape,depth=depth,variant=variant,bytes=len(raw),sha256=sha(raw),path=str(path.relative_to(REPO)),
                    grammar_proof="Strict shallow leaf plus balanced array/object productions; independent direct formula matches; no deep decoding"))
                checks.append(dict(label=f"direct-wrapper-formula-{shape}-{depth}-{variant}",passed=True))
    grammar=[dict(label=c.label,expected_valid=c.valid,category=c.category,bytes=len(c.raw),sha256=sha(c.raw),raw_hex=c.raw.hex(),
        http_scope="diagnostic grammar only; no new HTTP mandate" if c.label in ["empty","bom"] else "prospective HTTP obligation") for c in grammar_cases()]
    random_trace=[dict(label=item["label"],original_utf8=item["raw"].decode(),alias_utf8=item["alias"].decode(),different_utf8=item["different"].decode(),
        original_sha256=sha(item["raw"]),alias_sha256=sha(item["alias"]),different_sha256=sha(item["different"])) for item in randomized_values()]
    previous_path=HERE/"candidate-6/coverage.csv";previous=list(csv.DictReader(previous_path.open(newline="")))
    assert len(previous)==2679 and sum(row["normative"].lower()=="true" for row in previous)==2657
    commands=[]
    for relative in ["coverage.csv","VERDICT.md","summary.json"]:
        path=HERE/"candidate-6"/relative
        argv=["git","show",SEALED+":"+str(path.relative_to(REPO))]
        r=subprocess.run(argv,cwd=REPO,capture_output=True)
        commands.append(dict(argv=argv,returncode=r.returncode,stdout_sha256=sha(r.stdout),working_sha256=sha(path.read_bytes())))
        assert r.returncode==0 and r.stdout==path.read_bytes()
        checks.append(dict(label="preserved-sealed-candidate6-"+relative,passed=True))
    for row in previous:
        row.update(previous_candidate_full_revision=row["candidate_full_revision"],previous_verdict=row["verdict"],previous_evidence_path=row["evidence_path"],
            previous_executable_command=row["executable_command_or_interaction"],candidate_full_revision="PENDING_NAMED_CANDIDATE",verdict="unverified",evidence_path="UNVERIFIED",
            executable_command_or_interaction="Fresh full candidate7 execution/audit required; see PREPARATION.md inherited run families.",
            preparation_origin="Candidate6 independent sealed matrix, reset prospectively; historical results remain immutable.")
    supplement=rows();combined=previous+supplement
    assert len({r["requirement_id"] for r in combined})==len(combined)
    assert all(r["verdict"]=="unverified" and r["candidate_full_revision"]=="PENDING_NAMED_CANDIDATE" for r in combined)
    write_csv(out/"coverage-new-prepared.csv",supplement);write_csv(out/"coverage-cumulative-prepared.csv",combined)
    guard_out=out/"independent-verifier-guard-must-not-create";assert not guard_out.exists()
    argv=[sys.executable,"-B",str(HERE/"decoder_runtime.py"),"--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate",REJECTED,"--handoff",str(INTAKE),"--out",str(guard_out)]
    guard=subprocess.run(argv,cwd=REPO,capture_output=True,text=True)
    (out/"execution-guard.log").write_text(guard.stdout+guard.stderr)
    commands.append(dict(argv=argv,returncode=guard.returncode,expected_refusal=True))
    assert guard.returncode==2 and "execution waits" in guard.stderr and not guard_out.exists()
    checks.append(dict(label="prep-intake-refuses-execution-before-output-or-subprocesses",passed=True))
    summary=dict(scope="Preparation and own oracle/AST self-checks only",candidate="PENDING_NAMED_CANDIDATE",complete_preparation_package=True,execution_authorized=False,
        seed=20261004,shapes=SHAPES,depths=DEPTHS,raw_deep_samples=len(samples),raw_deep_min_bytes=min(s["bytes"] for s in samples),raw_deep_max_bytes=max(s["bytes"] for s in samples),
        grammar_cases=len(grammar),valid_grammar=sum(g["expected_valid"] for g in grammar),invalid_grammar=sum(not g["expected_valid"] for g in grammar),
        randomized_value_cases=len(random_trace),local_checks=len(checks),local_checks_passed=sum(c["passed"] for c in checks),syntax_files=5,
        inherited_normative_rows=2657,new_normative_rows=len(supplement),cumulative_normative_rows=2657+len(supplement),diagnostic_rows=22,
        all_records=len(combined),verified=0,failed=0,unverified=len(combined),service_requests=0,official_checks=0,images_built=0,containers_started=0,
        task_startup_target_seconds=5,official_startup_limit_seconds=60,prior_rejection_unchanged=True,task_activation_marker=intake["task_activation_marker"],
        self_check_started_at=start,self_check_finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),self_check_seconds=time.monotonic()-began,
        configured_model="gpt-6.1-sol",harness="Codex",actual_model="unknown",effort="unknown",tokens="unknown",estimated_and_billed_spend="unknown")
    for name,data in [("self-checks.json",dict(scope="Own oracle/grammar/source only, never service acceptance",checks=checks)),("deep-inputs.json",samples),
        ("grammar-inputs.json",grammar),("random-value-trace.json",dict(seed=20261004,cases=random_trace)),("source-proof.json",dict(files=proof,
        own_reused_helpers=[dict(path=str((HERE/n).relative_to(REPO)),sha256=sha((HERE/n).read_bytes())) for n in ["semantic_oracle.py","semantic_runtime.py","health.py"]],
        builder_test_oracle_reads=False,production_imports=False)),("commands.json",commands),("preparation-summary.json",summary)]:
        (out/name).write_text(json.dumps(data,indent=2))
    print(json.dumps(summary))

if __name__=="__main__":main()
