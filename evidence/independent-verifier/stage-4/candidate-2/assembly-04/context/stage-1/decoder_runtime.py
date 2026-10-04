"""Prepared decoder runtime derived only from own semantic_runtime.py.

Requires the future complete named handoff intake, rather than inferring a
candidate from HEAD or an intermediate module/adapter/core commit.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

LEGACY="49287b4a5a1481f995c470ccae31776f03d4b863"
HERE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    for name in ["repo","workspace","candidate","handoff","out"]:
        parser.add_argument("--"+name,required=True)
    parser.add_argument("--probe-family",choices=["decoder"],default="decoder")
    args=parser.parse_args()
    workspace=Path(args.workspace).resolve();repo=Path(args.repo).resolve()
    out=Path(args.out).resolve();handoff=Path(args.handoff).resolve()
    if not all(path.is_relative_to(workspace) for path in [repo,out,handoff,HERE]):
        parser.error("all task inputs and outputs must be inside the supplied workspace")
    if re.fullmatch(r"[0-9a-f]{40}",args.candidate) is None:
        parser.error("candidate must be a full named commit")
    intake=json.loads(handoff.read_text())
    if not (intake.get("execution_authorized") is True and intake.get("complete_task") is True
            and intake.get("candidate")==args.candidate
            and all(re.fullmatch(r"[0-9a-f]{40}",intake.get(field,"")) for field in ["systems_handoff_revision","interface_handoff_revision"])):
        parser.error("execution waits for the explicit complete final candidate and both complete builder handoffs")
    if not (intake.get("package_id")=="TK-20261004-S1-independent-verifier-CANDIDATE-7"
            and re.fullmatch(r"[0-9a-f]{40}",intake.get("stage_1_tree",""))
            and re.fullmatch(r"[0-9a-f]{40}",intake.get("probe_revision",""))
            and isinstance(intake.get("stage_files_sha256"),dict)
            and set(intake["stage_files_sha256"])=={"core.py","server.py","json_codec.py","Dockerfile","RUN.md",".dockerignore"}
            and all(re.fullmatch(r"[0-9a-f]{64}",v) for v in intake["stage_files_sha256"].values())):
        parser.error("execution waits for full candidate7 source bindings and both committed handoffs")
    out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();started_at=dt.datetime.now(dt.timezone.utc).isoformat()
    # Long timestamps/candidate hashes formerly broke DNS labels. Keep every
    # resource name below 63 chars without borrowing another seat's namespace.
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%m%d%H%M%S%f")
    prefix="independent-verifier-dec-"+stamp
    network=prefix+"-net";runner=prefix+":client"
    clones={};commands=[];containers=[];created_network=False;created_client=False
    result_code=1;proof={"candidate":args.candidate,"legacy_revision":LEGACY if args.probe_family=="semantic" else None,"probe_family":args.probe_family,"handoff":intake,
                         "started_at":started_at,"runtime_prefix":prefix,"status":"running","startup":{},"source":{}}
    def save():
        (out/"commands.json").write_text(json.dumps(commands,indent=2))
        (out/"source-runtime-proof.json").write_text(json.dumps(proof,indent=2))
    def run(argv,label,cwd=repo,required=True):
        began=time.monotonic();log=label+".log"
        with (out/log).open("w") as stream:
            completed=subprocess.run(argv,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT)
        commands.append(dict(argv=argv,cwd=str(cwd),log=log,returncode=completed.returncode,duration_seconds=time.monotonic()-began))
        save()
        if required and completed.returncode:raise RuntimeError("Command failed; retained "+str(out/log))
        return completed.returncode
    try:
        families=[("current",args.candidate)]+([("legacy",LEGACY)] if args.probe_family=="semantic" else [])
        for family,revision in families:
            clone=workspace/"band-work"/(prefix+"-"+family);clones[family]=clone
            run(["git","clone","--no-hardlinks","--no-checkout",str(repo),str(clone)],family+"-clone")
            run(["git","checkout","--detach",revision],family+"-checkout",clone)
            run(["git","rev-parse","HEAD"],family+"-head",clone)
            run(["git","status","--porcelain=v1"],family+"-status",clone)
            assert (out/(family+"-head.log")).read_text().strip()==revision
            assert not (out/(family+"-status.log")).read_text()
            run(["git","ls-tree","-r",revision],family+"-tree",clone)
            stage=clone/"stage-1"
            issues=[str(p.relative_to(clone)) for p in clone.rglob("*") if p.is_symlink() or (p.name in [".gitmodules"] or p.name==".git" and p!=clone/".git")]
            if issues:raise RuntimeError("Nested Git metadata or symlink: "+str(issues))
            files={str(path.relative_to(stage)):hashlib.sha256(path.read_bytes()).hexdigest() for path in stage.rglob("*") if path.is_file()}
            required_files={"core.py","server.py","Dockerfile","RUN.md"}
            if family=="current":required_files.add("json_codec.py")
            assert required_files<=files.keys()
            if family=="current":
                assert files==intake["stage_files_sha256"],"Named six-file source binding mismatch"
                run(["git","rev-parse",revision+":stage-1"],"current-stage-tree",clone)
                assert (out/"current-stage-tree.log").read_text().strip()==intake["stage_1_tree"]
            (out/(family+"-RUN.md")).write_bytes((stage/"RUN.md").read_bytes())
            image=prefix+":"+family
            proof["source"][family]=dict(revision=revision,clone=str(clone),stage_files_sha256=files,image_tag=image,clean=True)
            run(["docker","build","-t",image,"."],family+"-build",stage)
            run(["docker","image","inspect",image],family+"-image")
            image_data=json.loads((out/(family+"-image.log")).read_text())[0]
            proof["source"][family]["image_id"]=image_data["Id"]
        dockerfile="Decoder.Probe.Dockerfile"
        client_files=[dockerfile,"decoder_probe.py","decoder_oracle.py","decoder_requirements.py","semantic_oracle.py","health.py"]
        # Bind client bytes to a separately sealed own probe revision. Building
        # from that saved context avoids a mutable shared-tree source race.
        client_context=out/"own-client-context";client_context.mkdir()
        client_paths={name:str((HERE/name).relative_to(repo)) for name in client_files}
        for name,path in client_paths.items():
            assert path.startswith("evidence/independent-verifier/")
            argv=["git","show",intake["probe_revision"]+":"+path]
            began=time.monotonic();blob=subprocess.run(argv,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            commands.append(dict(argv=argv,cwd=str(repo),returncode=blob.returncode,duration_seconds=time.monotonic()-began,
                                 saved_blob=str(client_context/name)))
            if blob.returncode:raise RuntimeError("Sealed own probe blob unavailable")
            (client_context/name).write_bytes(blob.stdout)
        proof["probe_revision"]=intake["probe_revision"]
        proof["client_files_sha256"]={name:hashlib.sha256((client_context/name).read_bytes()).hexdigest() for name in client_files}
        run(["docker","build","-f",dockerfile,"-t",runner,"."],"client-build",client_context)
        code="import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in "+repr(client_files[1:])+"}))"
        run(["docker","run","--rm","--name",prefix+"-client-hashes","--network","none","--cpus","2","--memory","2g","--entrypoint","python",runner,"-c",code],"client-image-hashes")
        assert json.loads((out/"client-image-hashes.log").read_text())=={name:proof["client_files_sha256"][name] for name in client_files[1:]}
        run(["docker","network","create","--internal",network],"network-create");created_network=True
        run(["docker","network","inspect",network],"network-inspect")
        assert json.loads((out/"network-inspect.log").read_text())[0]["Internal"] is True
        urls={}
        roles=[("base","current",18335,18335,True),("peer","current",18336,8080,False)]+([("third","current",18337,18337,True)] if args.probe_family in ["semantic","snapshot","decoder"] else [])+([("legacy","legacy",18338,18338,True)] if args.probe_family=="semantic" else [])
        for role,family,host_port,internal_port,override in roles:
            name=prefix+"-"+role;assert len(name)<=63
            image=proof["source"][family]["image_tag"]
            argv=["docker","run","-d","--name",name,"--network",network,"--cpus","2","--memory","2g","-p",f"127.0.0.1:{host_port}:{internal_port}"]
            if override:argv.extend(["-e","PORT="+str(internal_port)])
            argv.append(image);began=time.monotonic();run(argv,role+"-start");containers.append(name)
            urls[role]=f"http://{name}:{internal_port}"
            run(["docker","run","--rm","--name",prefix+"-health","--network",network,"--cpus","2","--memory","2g","--entrypoint","python",runner,"/verifier/health.py","--url",urls[role]+"/health","--timeout","4.5"],role+"-health")
            readiness=time.monotonic()-began
            proof["startup"][role]=dict(readiness_seconds=readiness,default_port=not override,host_port=host_port,internal_port=internal_port,cross_container_health=True)
            assert readiness<5, "Task startup target5s exceeded; official limit remains60s"
            run(["docker","inspect",name],role+"-inspect")
            info=json.loads((out/(role+"-inspect.log")).read_text())[0]
            assert info["HostConfig"]["NanoCpus"]==2000000000 and info["HostConfig"]["Memory"]==2147483648
            assert info["HostConfig"]["NetworkMode"]==network and not info["Mounts"]
            assert info["Image"]==proof["source"][family]["image_id"]
            names=["core.py","server.py"]+(["json_codec.py"] if family=="current" else [])
            code="import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in "+repr(names)+"}))"
            run(["docker","exec",name,"python","-c",code],role+"-image-hashes")
            hashes=json.loads((out/(role+"-image-hashes.log")).read_text())
            assert hashes=={name:proof["source"][family]["stage_files_sha256"][name] for name in names}
            proof["startup"][role].update(container=name,image_hashes=hashes,cpu=2,memory_bytes=2147483648,service_mounts=[])
        argv=["docker","run","--name",prefix+"-probe","--network",network,"--cpus","2","--memory","2g","-v",str(out)+":/evidence",runner]
        for role in urls:argv.extend(["--"+role,urls[role]])
        argv.extend(["--candidate",args.candidate,"--out","/evidence/probes"])
        # Register before start so a partial Docker run is still cleaned up.
        created_client=True
        result_code=run(argv,"decoder-probe",required=False)
        for family,clone in clones.items():
            run(["git","status","--porcelain=v1"],family+"-post-status",clone)
            assert not (out/(family+"-post-status.log")).read_text()
        proof["status"]="completed";proof["probe_returncode"]=result_code
    except Exception as error:
        proof["status"]="runner_error";proof["runner_error"]={"type":type(error).__name__,"message":str(error)}
        raise
    finally:
        cleanup=[]
        if created_client:
            cleanup.append(dict(resource=prefix+"-probe",returncode=run(["docker","rm","-f",prefix+"-probe"],"client-cleanup",required=False)))
        for name in containers:
            run(["docker","logs",name],name+"-service",required=False)
            cleanup.append(dict(resource=name,returncode=run(["docker","rm","-f",name],name+"-cleanup",required=False)))
        if created_network:cleanup.append(dict(resource=network,returncode=run(["docker","network","rm",network],"network-cleanup",required=False)))
        proof.update(cleanup=cleanup,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),wall_seconds=time.monotonic()-started,
                     retained="Own image tags and exact clean clones; only own containers/network removed.",
                     build_cache="May be available; no uncached-build claim.")
        save()
    print(json.dumps(dict(candidate=args.candidate,status=proof["status"],probe_returncode=result_code,wall_seconds=proof["wall_seconds"],output=str(out))))
    raise SystemExit(result_code)

if __name__=="__main__":main()
