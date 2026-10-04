"""Run independently authored raw HTTP client on own proven constrained runtime."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument("--runtime",required=True);p.add_argument("--out",required=True);a=p.parse_args()
runtime=Path(a.runtime).resolve();out=Path(a.out).resolve();here=Path(__file__).resolve().parent
meta=json.loads((runtime/"preflight.json").read_text());assert meta["candidate"]=="75005d57fe0904753eac4eab5bf4e4c9a78b6d1b"
assert meta["runtime_prefix"].startswith("independent-verifier-") and meta["runtime_started"]
out.mkdir(parents=True,exist_ok=False)
source=subprocess.check_output(["git","show",meta["probe_revision"]+":evidence/independent-verifier/stage-1/very_deep_probe_c7.py"],cwd=here.parents[2]);(out/"very_deep_probe_c7.py").write_bytes(source)
argv=["docker","run","--rm","-i","--name","independent-verifier-very-deep-"+time.strftime("%H%M%S"),"--network",meta["network"],
    "--cpus","2","--memory","2g","--entrypoint","python",meta["runner_image"],"-",
    "http://"+meta["containers"][0]+":18309","http://"+meta["containers"][1]+":8080",meta["candidate"]]
began=time.monotonic()
with (out/"probes.json").open("wb") as f:
    result=subprocess.run(argv,input=source,stdout=f,stderr=subprocess.PIPE)
(out/"client.log").write_bytes(result.stderr)
(out/"command.json").write_text(json.dumps(dict(argv=argv,source_sha256=hashlib.sha256(source).hexdigest(),source="very_deep_probe_c7.py",source_revision=meta["probe_revision"],returncode=result.returncode,
    wall_seconds=time.monotonic()-began,service_runtime=str(runtime),candidate=meta["candidate"],scope="real HTTP from separate 2CPU/2GiB client; no service interpreter imports"),indent=2))
if result.stderr: print(result.stderr.decode())
if (out/"probes.json").stat().st_size:
    data=json.loads((out/"probes.json").read_text())
    print(json.dumps({k:data[k] for k in ["candidate","requests","assertions","failed_assertions","duration_seconds","max_request_bytes","max_request_seconds"]}))
raise SystemExit(result.returncode)
