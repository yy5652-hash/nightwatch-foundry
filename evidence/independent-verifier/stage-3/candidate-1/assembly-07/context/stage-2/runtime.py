"""Clean named-revision preflight and constrained offline Stage 2/Stage 1 processes."""
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

FROZEN="2a4b0408a3453bc87d86bca3d0ec571f479e03ca"


def main():
    parser=argparse.ArgumentParser()
    for name in ["repo","workspace","candidate","out"]:
        parser.add_argument("--"+name,required=True)
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--keep-running",action="store_true")
    args=parser.parse_args()
    if not re.fullmatch("[0-9a-f]{40}",args.candidate):
        parser.error("A full named committed Stage 2 candidate is required.")
    workspace=Path(args.workspace).resolve()
    repo=Path(args.repo).resolve()
    out=Path(args.out).resolve()
    if workspace not in repo.parents or workspace not in out.parents:
        parser.error("All paths must stay in the assigned workspace.")
    out.mkdir(parents=True,exist_ok=False)
    prefix=("independent-verifier-s2-"+args.candidate[:12]+"-"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")).lower()
    clone=workspace/"band-work"/prefix
    commands=[]
    def run(command,cwd=None,required=True):
        log=out/("command-%03d.log"%len(commands))
        began=time.monotonic()
        with log.open("w") as handle:
            result=subprocess.run(command,cwd=cwd or workspace,stdout=handle,stderr=subprocess.STDOUT)
        commands.append(dict(argv=command,cwd=str(cwd or workspace),returncode=result.returncode,seconds=time.monotonic()-began,log=str(log)))
        (out/"commands.json").write_text(json.dumps(commands,indent=2))
        if required and result.returncode:
            raise RuntimeError("Command failed; inspect "+str(log))
        return result.returncode,log.read_text()
    run(["git","clone","--no-hardlinks","--no-checkout",str(repo),str(clone)])
    run(["git","checkout","--detach",args.candidate],clone)
    _,dirty=run(["git","status","--porcelain=v1"],clone)
    _,revision=run(["git","rev-parse","HEAD"],clone)
    run(["git","log","--format=%H %an <%ae> %s","--all"],clone)
    _,tree=run(["git","ls-tree","-r",args.candidate],clone)
    _,frozen_diff=run(["git","diff",FROZEN,args.candidate,"--","stage-1"],clone)
    issues=[]
    for stage in [clone/"stage-1",clone/"stage-2"]:
        for path in stage.rglob("*"):
            if path.is_symlink() or path.name in [".git",".gitmodules"]:
                issues.append(str(path))
    if "160000 " in tree:
        issues.append("submodule tree entry")
    hashes={}
    for stage in ["stage-1","stage-2"]:
        for path in sorted((clone/stage).rglob("*")):
            if path.is_file():
                hashes[str(path.relative_to(clone))]=hashlib.sha256(path.read_bytes()).hexdigest()
    preflight=dict(candidate=args.candidate,clone=str(clone),prefix=prefix,clean=not dirty.strip(),exact_revision=revision.strip()==args.candidate,
                   frozen_stage1_unchanged=not frozen_diff.strip(),tree_issues=issues,source_hashes=hashes,verdict="unverified",
                   harness="Codex",configured_model="gpt-6.1-sol",actual_override_effort_usage_estimated_cost_billed_spend="unknown")
    (out/"RUN-reviewed-source.md").write_text((clone/"stage-2/RUN.md").read_text())
    (out/"preflight.json").write_text(json.dumps(preflight,indent=2))
    if dirty.strip() or revision.strip()!=args.candidate or frozen_diff.strip() or issues:
        raise RuntimeError("Preflight integrity failed; inspect saved facts")
    if not args.execute:
        print(json.dumps(preflight))
        return
    image=prefix+":candidate"
    legacy=prefix+":stage1-frozen"
    runner=prefix+":browser-runner"
    network=prefix+"-net"
    containers=[]
    created_network=False
    try:
        run(["docker","build","-t",image,"."],clone/"stage-2")
        run(["docker","build","-t",legacy,"."],clone/"stage-1")
        evidence_root=Path(__file__).resolve().parent.parent
        run(["docker","build","-f","stage-2/Browser.Dockerfile","-t",runner,"."],evidence_root)
        run(["docker","network","create","--internal",network])
        created_network=True
        states=[]
        for name,selected,port,host,override in [(prefix+"-source",image,18309,18300,True),(prefix+"-peer",image,8080,18301,False),(prefix+"-stage1",legacy,18310,18302,True)]:
            argv=["docker","run","-d","--name",name,"--network",network,"--cpus","2","--memory","2g","-p",f"127.0.0.1:{host}:{port}"]
            if override:
                argv.extend(["-e","PORT="+str(port)])
            began=time.monotonic()
            run(argv+[selected])
            containers.append(name)
            run(["docker","run","--rm","--name",name+"-health","--network",network,"--entrypoint","python",runner,"/verifier/stage-1/health.py","--url",f"http://{name}:{port}/health","--timeout","57"])
            elapsed=time.monotonic()-began
            run(["docker","inspect",name])
            states.append(dict(name=name,image=selected,url=f"http://{name}:{port}",startup_to_health_seconds=elapsed,port_override=override))
            if elapsed>=60:
                raise RuntimeError("Startup exceeded the published bound")
        run(["docker","network","inspect",network])
        preflight.update(runner_image=runner,network=network,containers=states,runtime_started=True,
                         note="Run own probes in this internal network; service containers have no mounts. Host source/evidence mounts apply only to verifier runner.")
        (out/"preflight.json").write_text(json.dumps(preflight,indent=2))
        print(json.dumps(preflight))
    finally:
        if not args.keep_running:
            for name in containers:
                run(["docker","rm","-f",name],required=False)
            if created_network:
                run(["docker","network","rm",network],required=False)
        (out/"preflight.json").write_text(json.dumps(preflight,indent=2))


if __name__=="__main__":
    main()
