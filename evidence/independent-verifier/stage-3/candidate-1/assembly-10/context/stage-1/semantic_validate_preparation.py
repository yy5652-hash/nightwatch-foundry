"""Client syntax/oracle/fixture/binding validation; zero service execution."""
import ast
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from semantic_oracle import Number,encode,parse,same,self_check
from semantic_requirements import BAD_JSON,CASES

HERE=Path(__file__).resolve().parent
TARGET=HERE/"candidate-6-preparation"
REPO=HERE.parents[2]
WORKSPACE=REPO.parents[1]

def main():
    files=["semantic_oracle.py","semantic_requirements.py","semantic_probe.py","semantic_prepare.py","semantic_runtime.py","semantic_validate_preparation.py"]
    syntax=[]
    for name in files:
        source=(HERE/name).read_text();ast.parse(source,filename=name)
        syntax.append(dict(path=name,sha256=hashlib.sha256(source.encode()).hexdigest(),syntax_valid=True))
    (TARGET/"syntax-check.json").write_text(json.dumps(dict(scope="AST parse only; no service import or execution",files=syntax),indent=2))
    checks=self_check()
    (TARGET/"oracle-self-check.json").write_text(json.dumps(dict(scope="Independent evidence-client oracle only; no service requests",cases=len(checks),passed=sum(x["passed"] for x in checks),checks=checks),indent=2))
    grammar=[]
    for label,raw in BAD_JSON.items():
        try:value=parse(raw);nonobject=not isinstance(value,dict);syntax_refused=False
        except (ValueError,UnicodeError):nonobject=False;syntax_refused=True
        expected_nonobject=label.startswith("nonobject-")
        assert (nonobject if expected_nonobject else syntax_refused),label
        grammar.append(dict(label=label,request_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),expected="object-only refusal" if expected_nonobject else "syntax/encoding refusal",client_fixture_valid=True))
    (TARGET/"raw-fixture-validation.json").write_text(json.dumps(dict(scope="Independent client syntax checks of planned inputs, not HTTP results",cases=len(grammar),fixtures=grammar),indent=2))
    probe_ast=ast.parse((HERE/"semantic_probe.py").read_text())
    cls=next(node for node in probe_ast.body if isinstance(node,ast.ClassDef) and node.name=="Probe")
    methods={node.name:node for node in cls.body if isinstance(node,ast.FunctionDef)}
    mapping={"syntax-":"syntax","count-":"counts","fraction-":"counts","wrong-":"counts","minimum-":"counts","missing-":"counts","bounded-":"counts","query-":"counts",
             "ignored-":"ignored","escaped-string":"ignored","valid-utf8":"ignored","identity-":"current","precedence-":"current","profile-new-":"current","archived-exact-":"current","ordering-":"current",
             "legacy-":"historical","mixed-":"historical","invalid-profile-":"historical"}
    bindings=[]
    for key,case in CASES.items():
        method=next((method for prefix,method in mapping.items() if key.startswith(prefix)),"finish")
        node=methods[method]
        anchors=[call.lineno for call in ast.walk(node) if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr in ["check","expect"]]
        assert anchors
        bindings.append(dict(requirement_id=case["requirement_id"],method="Probe."+method,source="semantic_probe.py",method_source_line=node.lineno,assertion_source_lines=sorted(anchors),status="planned binding; not executed"))
    assert len({row["requirement_id"] for row in bindings})==len(CASES)
    (TARGET/"planned-probe-bindings.json").write_text(json.dumps(dict(scope="Static method/assertion binding only; does not prove any service result or branch execution",rows=len(bindings),method_counts=dict(Counter(row["method"] for row in bindings)),bindings=bindings),indent=2))
    rows=list(csv.DictReader((TARGET/"coverage-prepared.csv").open(newline="")))
    assert len(rows)==967+len(CASES) and len({row["requirement_id"] for row in rows})==len(rows)
    assert all(row["verdict"]=="unverified" and row["candidate_full_revision"]=="PENDING_NAMED_CANDIDATE" and row["evidence_path"]=="UNVERIFIED" for row in rows)
    assert {case["requirement_id"] for case in CASES.values()}<=set(row["requirement_id"] for row in rows)
    guard_out=TARGET/"guard-must-not-create"
    assert not guard_out.exists()
    argv=[sys.executable,"-B",str(HERE/"semantic_runtime.py"),"--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate","0"*40,"--handoff",str(TARGET/"intake.json"),"--out",str(guard_out)]
    completed=subprocess.run(argv,cwd=REPO,capture_output=True,text=True)
    (TARGET/"execution-guard.log").write_text(completed.stdout+completed.stderr)
    assert completed.returncode==2 and "execution waits" in completed.stderr and not guard_out.exists()
    (TARGET/"execution-guard.json").write_text(json.dumps(dict(argv=argv,returncode=completed.returncode,expected_refusal=True,output_not_created=not guard_out.exists(),service_or_docker_executed=False),indent=2))
    history_paths=["evidence/independent-verifier/stage-1/candidate-5","evidence/independent-verifier/stage-1/candidate-5-supplemental-fraction","evidence/independent-verifier/stage-1/candidate-5-numeric-source-audit"]
    history=subprocess.run(["git","diff","--exit-code","--",*history_paths],cwd=REPO,capture_output=True,text=True)
    assert history.returncode==0 and not history.stdout
    provenance=dict(reviewed_at=dt.datetime.now(dt.timezone.utc).isoformat(),source_scope="Full received 14-part preparation task, Stage1 specification/guide/brief/adopted decisions, own historical matrix and own black-box clients.",
                    no_peer_tests_or_oracles=True,no_product_imports=True,no_external_domain_code=True,no_service_execution=True,no_official_execution=True,
                    historical_paths_unchanged=history_paths,prepared_rows=len(rows),new_static_bindings=len(bindings),oracle_cases=len(checks),raw_fixture_cases=len(grammar),syntax_files=len(files),execution_guard_passed=True)
    (TARGET/"preparation-validation.json").write_text(json.dumps(provenance,indent=2))
    print(json.dumps(provenance))

if __name__=="__main__":main()
