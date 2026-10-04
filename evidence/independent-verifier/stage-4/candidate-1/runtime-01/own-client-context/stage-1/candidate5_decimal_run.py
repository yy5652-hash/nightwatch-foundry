"""Sequential decimal-only retry after preserved verifier argument-name error."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--runtime",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
meta=json.loads((Path(a.runtime)/"preflight.json").read_text())
out=Path(a.out).resolve()
out.mkdir(parents=True,exist_ok=False)
prefix="independent-verifier-s1-decimal"+out.name.rsplit("-",1)[-1]+"-"+time.strftime("%Y%m%dT%H%M%S",time.gmtime()).lower()
image=meta["image"]
helper=prefix+":client"
network=prefix+"-net"
assert len(prefix+"-source") <= 63
commands=[]
names=[]
created=False
began=time.monotonic()
def run(argv,filename,required=True):
    start=time.monotonic()
    with (out/filename).open("w") as f:
        rc=subprocess.call(argv,cwd=REPO,stdout=f,stderr=subprocess.STDOUT)
    commands.append(dict(argv=argv,cwd=str(REPO),log=filename,returncode=rc,duration_seconds=time.monotonic()-start))
    (out/"commands.json").write_text(json.dumps(commands,indent=2))
    if required and rc: raise RuntimeError("see "+str(out/filename))
    return rc
try:
    run(["docker","build","-f",str(HERE/"Candidate5.Probe.Dockerfile"),"-t",helper,str(HERE)],"client-build.log")
    run(["docker","network","create","--internal",network],"network.log")
    created=True
    for suffix,port in [("source",18329),("peer",18330)]:
        name=prefix+"-"+suffix
        run(["docker","run","-d","--name",name,"--network",network,"--cpus","2","--memory","2g","-e","PORT="+str(port),image],suffix+"-start.log")
        names.append(name)
        started=time.monotonic()
        run(["docker","run","--rm","--name",name+"-health","--network",network,"--cpus","2","--memory","2g","--entrypoint","python",helper,"/verifier/health.py","--url",f"http://{name}:{port}/health","--timeout","57"],suffix+"-health.json")
        run(["docker","inspect",name],suffix+"-inspect.json")
        observed=json.loads((out/(suffix+"-inspect.json")).read_text())[0]
        assert observed["HostConfig"]["NanoCpus"]==2_000_000_000 and observed["HostConfig"]["Memory"]==2_147_483_648 and not observed["Mounts"]
        run(["docker","exec",name,"python","-c","import json,hashlib;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['core.py','server.py']}))"],suffix+"-hashes.json")
        expected={f:hashlib.sha256((Path(meta["clone"])/"stage-1"/f).read_bytes()).hexdigest() for f in ["core.py","server.py"]}
        assert json.loads((out/(suffix+"-hashes.json")).read_text())==expected
    run(["docker","network","inspect",network],"network-inspect.json")
    assert json.loads((out/"network-inspect.json").read_text())[0]["Internal"] is True
    source_versions=out/"helper-source-versions"
    source_versions.mkdir()
    helper_hashes={}
    for file in ["decimal_probe.py","decimal_requirements.py","probe.py","requirements.py"]:
        data=(HERE/file).read_bytes()
        (source_versions/file).write_bytes(data)
        helper_hashes[file]=hashlib.sha256(data).hexdigest()
    argv=["docker","run","--rm","--name",prefix+"-probe","--network",network,"--cpus","2","--memory","2g","-v",str(out)+":/evidence","--entrypoint","python",helper,"/verifier/decimal_probe.py","--base",f"http://{names[0]}:18329","--peer",f"http://{names[1]}:18330","--candidate",meta["candidate"],"--out","/evidence/probes"]
    code=run(argv,"client.log",required=False)
    (out/"source-proof.json").write_text(json.dumps(dict(candidate=meta["candidate"],clone=meta["clone"],matching_service_image=image,expected_hashes=expected,helper_hashes=helper_hashes,client_only_decimal_configuration=True),indent=2))
finally:
    for name in names:
        run(["docker","logs",name],name+"-service.log",required=False)
        run(["docker","rm","-f",name],name+"-cleanup.log")
    if created: run(["docker","network","rm",network],"network-cleanup.log")
    (out/"timing.json").write_text(json.dumps(dict(total_seconds=time.monotonic()-began)))
print(json.dumps(dict(candidate=meta["candidate"],probe_exit_code=code,out=str(out))))
raise SystemExit(code)
