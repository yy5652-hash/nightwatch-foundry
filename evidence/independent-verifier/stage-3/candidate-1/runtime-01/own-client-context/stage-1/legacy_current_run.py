"""Repeat genuine historical receipt migration with adopted schema2 metadata.

Retain the earlier obsolete whole-private-envelope expectation separately.
Reuses own exact-source proven images; no new service build claim.
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument("--runtime",required=True);p.add_argument("--out",required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;repo=here.parents[2];runtime=Path(a.runtime).resolve();out=Path(a.out).resolve()
meta=json.loads((runtime/"preflight.json").read_text());old=json.loads((runtime/"legacy-identity.json").read_text())
assert meta["candidate"]=="ab0cf79767b6768153a73894bf5768bf3328491a"
out.mkdir(parents=True,exist_ok=False);prefix="independent-verifier-legacy-"+time.strftime("%m%d%H%M%S");network=prefix+"-net";client=prefix+":client"
commands=[];names=[];created=False;began=time.monotonic()
def run(argv,label,cwd=repo,required=True):
    start=time.monotonic()
    with (out/(label+".log")).open("w") as f:r=subprocess.run(argv,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
    commands.append(dict(argv=argv,cwd=str(cwd),log=label+".log",returncode=r.returncode,duration_seconds=time.monotonic()-start))
    (out/"commands.json").write_text(json.dumps(commands,indent=2))
    if required and r.returncode:raise RuntimeError("see "+str(out/(label+".log")))
    return r.returncode
try:
    run(["docker","build","-f","LegacyCurrent.Probe.Dockerfile","-t",client,"."],"client-build",here)
    run(["docker","network","create","--internal",network],"network-create");created=True
    run(["docker","network","inspect",network],"network-inspect")
    assert json.loads((out/"network-inspect.log").read_text())[0]["Internal"]
    urls={};proof=[]
    for role,image,clone,port,override in [("base",meta["image"],Path(meta["clone"]),18350,True),("peer",meta["image"],Path(meta["clone"]),8080,False),("legacy",meta["runtime_prefix"]+":legacy",Path(old["legacy_clone"]),18352,True)]:
        name=prefix+"-"+role;argv=["docker","run","-d","--name",name,"--network",network,"--cpus","2","--memory","2g"]
        if override:argv.extend(["-e","PORT="+str(port)])
        argv.append(image);run(argv,role+"-start");names.append(name);urls[role]=f"http://{name}:{port}"
        run(["docker","run","--rm","--network",network,"--cpus","2","--memory","2g","--entrypoint","python",client,"/verifier/health.py","--url",urls[role]+"/health","--timeout","55"],role+"-health")
        run(["docker","inspect",name],role+"-inspect")
        info=json.loads((out/(role+"-inspect.log")).read_text())[0]
        assert info["HostConfig"]["NanoCpus"]==2000000000 and info["HostConfig"]["Memory"]==2147483648 and not info["Mounts"]
        files=["core.py","server.py"]+(["json_codec.py"] if role!="legacy" else [])
        expected={f:hashlib.sha256((clone/"stage-1"/f).read_bytes()).hexdigest() for f in files}
        code="import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in "+repr(files)+"}))"
        run(["docker","exec",name,"python","-c",code],role+"-hashes")
        assert json.loads((out/(role+"-hashes.log")).read_text())==expected
        proof.append(dict(role=role,image_id=info["Image"],clone=str(clone),files=expected))
    argv=["docker","run","--rm","--name",prefix+"-probe","--network",network,"--cpus","2","--memory","2g","-v",str(out)+":/evidence",client]
    for role,url in urls.items():argv.extend(["--"+role,url])
    argv.extend(["--candidate",meta["candidate"],"--out","/evidence/probes"])
    code=run(argv,"client",required=False)
    (out/"identity.json").write_text(json.dumps(dict(candidate=meta["candidate"],legacy_revision=old["legacy_revision"],proof=proof,source_runtime=str(runtime),client_files={f:hashlib.sha256((here/f).read_bytes()).hexdigest() for f in ["LegacyCurrent.Probe.Dockerfile","legacy_receipts_current.py","probe.py","requirements.py","wire_oracle.py"]}),indent=2))
finally:
    for name in names:
        run(["docker","logs",name],name+"-service",required=False);run(["docker","rm","-f",name],name+"-cleanup")
    if created:run(["docker","network","rm",network],"network-cleanup")
    (out/"timing.json").write_text(json.dumps(dict(wall_seconds=time.monotonic()-began)))
print(json.dumps(dict(candidate=meta["candidate"],returncode=code,out=str(out))))
raise SystemExit(code)
