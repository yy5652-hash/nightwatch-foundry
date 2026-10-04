"""Exact committed adapter-image step; core-dependent repair checks stay pending."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--revision", required=True)
parser.add_argument("--probe-revision", help="Named own diagnostic source revision; defaults to service revision")
args = parser.parse_args()
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
slug = "interface-engineer-json-adapter-"+stamp
resource = "interface-engineer-ja-"+stamp
out = ROOT / "evidence/interface-engineer" / slug
out.mkdir()
clone = ROOT.parent / slug
image = "interface-engineer-tablekeeper-s1:json-adapter-"+stamp
network = slug
commands, checks, errors, resources, created = [], [], [], [], []
network_created = False
start = time.monotonic()
baseline = "f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
module_revision = "00940d4777c316c1369e744109885d58c85373ec"
files = ("core.py", "server.py", "json_codec.py", "Dockerfile", "RUN.md", ".dockerignore")
probe_files = ("stage-1-json-adapter-container-check.py", "stage-1-json-adapter-probe.py",
               "stage-1-json-repair-probe.py", "stage-1-transport-probe.py")


def execute(argv, *, cwd=ROOT, stdin=None, output=None, required=True):
    t = time.monotonic()
    r = subprocess.run(argv, cwd=cwd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    entry = {"argv": argv, "cwd": str(cwd), "seconds": time.monotonic()-t, "returncode": r.returncode}
    if stdin is not None:
        entry["stdin_sha256"] = hashlib.sha256(stdin).hexdigest()
    if output:
        (out / output).write_bytes(r.stdout)
        entry["output"] = output
    commands.append(entry)
    if required and r.returncode:
        raise RuntimeError("Command failed: "+" ".join(argv[:4]))
    return r.stdout


def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
    if not condition:
        errors.append(name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


health = """import json,time,urllib.request,sys
t=time.monotonic()
while True:
 try:
  with urllib.request.urlopen('http://127.0.0.1:'+sys.argv[1]+'/health',timeout=2) as r:
   if r.status==200 and json.loads(r.read())=={'status':'ok'}: break
 except Exception:
  if time.monotonic()-t>50: raise
  time.sleep(.05)
print(json.dumps({'status':200,'probe_seconds':time.monotonic()-t}))
"""
try:
    execute(["git", "clone", "--no-hardlinks", str(ROOT), str(clone)], output="clone.log")
    execute(["git", "checkout", "--detach", args.revision], cwd=clone, output="checkout.log")
    candidate = execute(["git", "rev-parse", "HEAD"], cwd=clone).decode().strip()
    check("Named full revision and clean detached clone", candidate == args.revision and execute(["git", "status", "--porcelain"], cwd=clone) == b'')
    tree = execute(["git", "rev-parse", "HEAD:stage-1"], cwd=clone).decode().strip()
    source = {f: sha((clone / "stage-1" / f).read_bytes()) for f in files}
    check("Systems codec is byte-identical to released module", execute(["git", "show", module_revision+":stage-1/json_codec.py"]) == (clone / "stage-1/json_codec.py").read_bytes())
    check("Frozen core and entire Stage2 remain unchanged", execute(["git", "diff", baseline, "--", "stage-1/core.py", "stage-2"], cwd=clone) == b'')
    for f in files[:3]:
        ast.parse((clone / "stage-1" / f).read_text())
    probe_revision = args.probe_revision or candidate
    probe_source = {f: execute(["git", "show", probe_revision+":evidence/interface-engineer/"+f]) for f in probe_files}
    (out / "source-proof.json").write_text(json.dumps({"candidate":candidate,"stage1_tree":tree,"clone":str(clone),
        "source_sha256":source,"module_revision":module_revision,"frozen_core_stage2_baseline":baseline,
        "probe_revision":probe_revision,"driver_sha256":sha(Path(__file__).read_bytes()),
        "probe_sha256":{f:sha(data) for f,data in probe_source.items()},
        "scope":"Adapter/image intermediate only; complete codec/core receipt integration pending"},indent=2)+'\n')
    execute(["docker", "build", "-t", image, str(clone / "stage-1")], output="build.log")
    execute(["docker", "network", "create", "--internal", network], output="network.log")
    network_created = True
    for label, port, host, override in (("default",8080,18234,False),("override",9090,18235,True)):
        name = resource+'-'+label
        assert len(name) <= 63
        argv = ["docker","run","-d","--name",name,"--network",network,"--cpus","2","--memory","2g","-p",str(host)+":"+str(port)]
        if override:
            argv += ["-e","PORT="+str(port)]
        launch = time.monotonic()
        execute(argv+[image],output="run-"+label+".log")
        created.append(name)
        ready = json.loads(execute(["docker","exec",name,"python","-c",health,str(port)],output="health-"+label+".json"))
        seconds = time.monotonic()-launch
        check(label+" healthy within 60 seconds from launch", seconds<60 and ready["status"]==200)
        inspect = json.loads(execute(["docker","inspect",name]))[0]
        config = inspect["HostConfig"]
        check(label+" 2 CPU/2GiB/no service mounts",config["NanoCpus"]==2000000000 and config["Memory"]==2147483648 and inspect["Mounts"]==[])
        hashes = json.loads(execute(["docker","exec",name,"python","-c","import pathlib,hashlib,json;print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').glob('*.py')}))"],output="hash-"+label+".json"))
        check(label+" packaged three Python files match Git",all(hashes[f]==source[f] for f in files[:3]))
        listener = execute(["docker","exec",name,"python","-c","import pathlib;print(pathlib.Path('/proc/net/tcp').read_text())"],output="listener-"+label+".txt")
        check(label+" binds 0.0.0.0 selected PORT",('00000000:'+f'{port:04X}').encode() in listener)
        resources.append({"name":name,"image":inspect["Image"],"port":port,"host_port":host,"port_override":override,
                          "health_from_launch_seconds":seconds,"nano_cpus":config["NanoCpus"],"memory":config["Memory"],
                          "network":config["NetworkMode"],"mounts":inspect["Mounts"],"source_sha256":hashes})
    check("Internal service network blocks outbound routing",json.loads(execute(["docker","network","inspect",network]))[0]["Internal"] is True)
    inherited = json.loads(execute(["docker","exec","-i",created[1],"python","-","http://127.0.0.1:9090"],stdin=probe_source["stage-1-transport-probe.py"],output="inherited-http.json",required=False))
    check("Real Engine inherited HTTP checks",inherited["failed"]==0)
    script = ("h={'__name__':'own_client_helpers'};exec("+repr(probe_source["stage-1-json-repair-probe.py"].decode())+",h)\n").encode()+probe_source["stage-1-json-adapter-probe.py"]
    # Synthetic fixture uses packaged Handler/codec, not the live Engine. Its
    # requests are counted separately and never labelled reservation evidence.
    fixture_output = execute(["docker","exec","-i",created[1],"python","-"],stdin=script,output="synthetic-adapter.log",required=False).decode()
    # The intentional unsupported fixture leaf writes one diagnostic to stderr;
    # keep it intact while reading the following structured JSON result.
    fixture = json.loads(fixture_output[fixture_output.index("{\n"):])
    check("Synthetic adapter exact decode/encode/framing checks",fixture["failed"]==0)
    check("Detached clone stays clean after checks",execute(["git","status","--porcelain"],cwd=clone)==b'')
    (out / "summary.json").write_text(json.dumps({"candidate":candidate,"stage1_tree":tree,
       "inherited":{k:inherited[k] for k in ("checks","passed","failed","elapsed_seconds")},
       "synthetic_adapter":{k:fixture[k] for k in ("scope","operations","assertions","passed","failed","elapsed_seconds")},
       "runtime_checks":checks,"pending":"Core exact field/value/receipt/profile/import integration and genuine old service probes"},indent=2)+'\n')
except Exception as exc:
    errors.append(type(exc).__name__+": "+str(exc))
finally:
    cleanup=[]
    for name in reversed(created):
        execute(["docker","logs",name],output="logs-"+name.rsplit('-',1)[1]+".txt",required=False)
        execute(["docker","rm","-f",name],output="cleanup-"+name.rsplit('-',1)[1]+".log",required=False)
        cleanup.append(commands[-1])
    if network_created:
        execute(["docker","network","rm",network],output="cleanup-network.log",required=False)
        cleanup.append(commands[-1])
    if any(r["returncode"] for r in cleanup):
        errors.append("Own cleanup returned nonzero")
    elapsed=time.monotonic()-start
    (out / "run.json").write_text(json.dumps({"candidate":args.revision,"probe_revision":args.probe_revision or args.revision,"commands":commands,"checks":checks,"errors":errors,
        "resources":resources,"cleanup":cleanup,"elapsed_seconds":elapsed,"clone":str(clone),"image_retained":image,
        "model":"operator-configured gpt-6.1-sol","runtime_override_effort_usage_cost":"unknown","build_cache":"available; actual log retained"},indent=2)+'\n')
    print(json.dumps({"candidate":args.revision,"out":str(out),"seconds":elapsed,"failures":errors}))
sys.exit(1 if errors else 0)
