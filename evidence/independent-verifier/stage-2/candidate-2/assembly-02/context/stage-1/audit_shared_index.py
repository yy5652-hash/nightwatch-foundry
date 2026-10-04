"""Read-only named Git attribution audit; does not execute any service code."""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

CAPTURE="182582c41d21a23d8ccd95688fa7f1afa0437460"
WIRING="3dae12788ff59dce8c4ce8a6faa71394f140e3d2"
REPAIR="c2fcedc853e0fe33e96f9d3f39c0c807b4e08d9f"
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--out",required=True);args=parser.parse_args()
    out=Path(args.out).resolve()
    if not out.is_relative_to(HERE):parser.error("output must stay inside owned Stage1 evidence")
    out.mkdir(parents=True,exist_ok=False);commands=[]
    def git(*arguments):
        argv=["git",*arguments];result=subprocess.run(argv,cwd=REPO,capture_output=True,check=True)
        commands.append(dict(argv=argv,cwd=str(REPO),returncode=result.returncode))
        return result.stdout
    parent=git("rev-parse",CAPTURE+"^").decode().strip()
    paths=git("diff-tree","--no-commit-id","--name-only","-r",CAPTURE).decode().splitlines()
    prior_path=HERE/"candidate-6-preparation/shared-index-provenance.json"
    prior=json.loads(prior_path.read_text())
    identity={}
    for name,revision in [("capture",CAPTURE),("parent",parent),("wiring",WIRING),("systems_repair",REPAIR)]:
        blob=git("rev-parse",revision+":stage-1/json_codec.py").decode().strip()
        data=git("show",revision+":stage-1/json_codec.py")
        identity[name]=dict(revision=revision,stage1_tree=git("rev-parse",revision+":stage-1").decode().strip(),module_blob=blob,module_sha256=hashlib.sha256(data).hexdigest())
    proof=dict(scope="Named Git metadata/blob hashes only; no product execution",source_notice="56a18863-6f39-438f-a825-96eae1b24196",capturing_commit=CAPTURE,
        capturing_git_author=git("show","-s","--format=%an <%ae>",CAPTURE).decode().strip(),parent=parent,
        changed_paths=paths,changed_path_count=len(paths),verifier_changed_path_count=sum(path.startswith("evidence/independent-verifier/") for path in paths),
        production_paths_in_parent_delta=[path for path in paths if path.startswith("stage-")],
        stage1_changed_since_wiring=git("diff","--name-only",WIRING,CAPTURE,"--","stage-1").decode().splitlines(),identities=identity,
        module_history=git("log","-4","--format=%H %an <%ae> %s",CAPTURE,"--","stage-1/json_codec.py").decode().splitlines(),
        prior_provenance_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),prior_path_listing_complete=set(prior["all_capturing_commit_paths"])==set(paths),
        audit_at=dt.datetime.now(dt.timezone.utc).isoformat(),http_operations=0,official_checks=0,service_resources_started=0,
        candidate_acceptance="not-executed",highest_accepted_stage=0,configured_model="gpt-6.1-sol",actual_override_effort_usage_spend="unknown")
    assert parent==REPAIR and identity["capture"]["stage1_tree"]==identity["parent"]["stage1_tree"]
    assert len(paths)==33 and proof["verifier_changed_path_count"]==32 and not proof["production_paths_in_parent_delta"]
    assert proof["prior_path_listing_complete"] and proof["stage1_changed_since_wiring"]==["stage-1/json_codec.py"]
    assert identity["capture"]["module_blob"]==identity["systems_repair"]["module_blob"]!=identity["wiring"]["module_blob"]
    (out/"proof.json").write_text(json.dumps(proof,indent=2));(out/"commands.json").write_text(json.dumps(commands,indent=2))
    print(json.dumps(dict(capturing_commit=CAPTURE,parent=parent,changed_paths=len(paths),verifier_paths=32,production_delta_paths=0,stage1_parent_identical=True,systems_module_inherited=True,wiring_tree_different=True,prior_provenance_complete=True,http_operations=0)))

if __name__=="__main__":main()
