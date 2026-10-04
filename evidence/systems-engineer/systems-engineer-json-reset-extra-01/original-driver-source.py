"""Narrow HTTP reset regression on the already verified retained service image."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", required=True)
parser.add_argument("--image", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
repo = Path.cwd().resolve()
out = Path(args.out).resolve()
out.relative_to(repo / "evidence/systems-engineer")
out.mkdir(exist_ok=False)
name = "systems-engineer-reset-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f").lower()
commands = []
started = time.monotonic()
created = False


def run(argv, body=None, required=True):
    before = time.monotonic()
    result = subprocess.run(argv, input=body, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    path = out / ("command-%02d.log" % len(commands))
    path.write_bytes(result.stdout)
    commands.append({"argv": argv, "returncode": result.returncode, "seconds": time.monotonic() - before,
                     "log": str(path), "stdin_sha256": None if body is None else hashlib.sha256(body).hexdigest()})
    if required and result.returncode:
        raise RuntimeError("Command failed; see " + str(path))
    return result.stdout


record = {"candidate": args.candidate, "image_id": args.image, "commands": commands, "scope": "narrow own HTTP unknown-reset regression"}
try:
    run(["docker", "run", "-d", "--name", name, "--cpus", "2", "--memory", "2g", "--network", "none",
         "-e", "PORT=18145", args.image])
    created = True
    inspection = json.loads(run(["docker", "inspect", name]))[0]
    assert inspection["Image"] == args.image and inspection["Mounts"] == []
    assert inspection["HostConfig"]["NanoCpus"] == 2_000_000_000
    assert inspection["HostConfig"]["Memory"] == 2_147_483_648
    assert inspection["HostConfig"]["NetworkMode"] == "none"
    record["source_sha256"] = {}
    for filename in ("core.py", "server.py", "json_codec.py"):
        expected = hashlib.sha256(run(["git", "show", args.candidate + ":stage-1/" + filename])).hexdigest()
        actual = run(["docker", "exec", name, "python", "-c", "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())" % filename]).decode().strip()
        assert actual == expected
        record["source_sha256"][filename] = actual
    program = '''import hashlib,json,time,urllib.request,urllib.error
events=[];assertions=[];begin=time.monotonic()
def check(label,passed): assertions.append({"label":label,"passed":bool(passed)})
def http(method,path,wire=None,expected=200,code=None):
 start=time.monotonic()
 try:r=urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:18145"+path,data=wire,headers={"Content-Type":"application/json; charset=utf-8"},method=method),timeout=10)
 except urllib.error.HTTPError as error:r=error
 raw=r.read(); value=json.loads(raw) if raw else None
 events.append({"method":method,"path":path,"status":r.status,"request_bytes":0 if wire is None else len(wire),"request_sha256":None if wire is None else hashlib.sha256(wire).hexdigest(),"response_sha256":hashlib.sha256(raw).hexdigest(),"seconds":time.monotonic()-start})
 check(path+" status",r.status==expected)
 check(path+" framing",r.headers.get("Content-Length")==str(len(raw)) and "application/json" in r.headers.get("Content-Type",""))
 if expected==204:check("empty 204",raw==b"")
 if code:check("error code",value["error"]["code"]==code)
 return value,raw
for attempt in range(120):
 try:urllib.request.urlopen("http://127.0.0.1:18145/health",timeout=.5);break
 except Exception:time.sleep(.05)
else:raise RuntimeError("health timeout")
http("GET","/health")
fixture={"users":[],"restaurants":[{"id":"r","name":"Room","timezone":"UTC","slot_minutes":30,"reservation_duration_minutes":90,"cancellation_cutoff_minutes":0,"opening_hours":[{"weekday":"mon","opens":"18:00","closes":"23:00"}],"tables":[{"id":"a","label":"A","capacity":4}]}],"reservations":[]}
base=json.dumps(fixture,separators=(",",":")).encode()
http("POST","/_test/reset",base,204)
for token in ("1e4300","1"+"0"*4299+"1.5","1e"+"9"*80):
 wire=base[:-1]+b',"unused":{"number":'+token.encode()+b',"nested":[true,null,{"also":'+token.encode()+b'}]}}}'
 http("POST","/_test/reset",wire,204)
 detail=http("GET","/restaurants/r")[0]
 check("ignored finite unknown preserves ordinary configuration",detail["slot_minutes"]==30 and detail["tables"][0]["capacity"]==4 and "unused" not in detail)
for token in ("NaN","Infinity","-Infinity"):
 before=http("GET","/_test/export")[1]
 http("POST","/_test/reset",base[:-1]+b',"unused":'+token.encode()+b'}',400,"malformed_request")
 check("forbidden literal reset atomic",http("GET","/_test/export")[1]==before)
summary={"http_requests":len(events),"assertions":len(assertions),"failed":sum(not x["passed"] for x in assertions),"seconds":time.monotonic()-begin,"maximum_payload_bytes":max(x["request_bytes"] for x in events)}
print(json.dumps({"summary":summary,"operations":events,"assertions":assertions}))
raise SystemExit(bool(summary["failed"]))
'''
    raw = run(["docker", "exec", "-i", name, "python", "-B", "-"], program.encode(), required=False)
    (out / "probe.json").write_bytes(raw)
    record["probe_exit_code"] = commands[-1]["returncode"]
    record["summary"] = json.loads(raw)["summary"]
finally:
    if created:
        run(["docker", "logs", name], required=False)
        run(["docker", "rm", "-f", name], required=False)
        record["cleanup_exit_code"] = commands[-1]["returncode"]
    record["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k:record.get(k) for k in ("candidate","summary","probe_exit_code","cleanup_exit_code","wall_seconds")}))
    if record.get("probe_exit_code") != 0:
        raise SystemExit(1)
