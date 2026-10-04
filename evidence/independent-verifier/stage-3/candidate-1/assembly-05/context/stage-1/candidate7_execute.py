"""Execute only independently authored protocols after the named official run."""
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1];OUT=HERE/"candidate-7"
CANDIDATE="75005d57fe0904753eac4eab5bf4e4c9a78b6d1b"
intake=json.loads((OUT/"intake.json").read_text());assert intake["execution_authorized"] and intake["complete_task"] and intake["candidate"]==CANDIDATE
official=json.loads((OUT/"official-command.json").read_text());assert "finished_at" in official
commands=[];started=time.monotonic();began_at=dt.datetime.now(dt.timezone.utc).isoformat()

def run(argv,label):
    beginning=time.monotonic()
    with (OUT/(label+".log")).open("w") as stream:
        result=subprocess.run(argv,cwd=REPO,stdout=stream,stderr=subprocess.STDOUT)
    commands.append(dict(argv=argv,cwd=str(REPO),log=label+".log",returncode=result.returncode,duration_seconds=time.monotonic()-beginning))
    (OUT/"execution-commands.json").write_text(json.dumps(commands,indent=2)+"\n")
    print(json.dumps(dict(step=label,returncode=result.returncode,seconds=commands[-1]["duration_seconds"])),flush=True)
    return result.returncode

meta=json.loads((OUT/"baseline-01/preflight.json").read_text());assert meta["candidate"]==CANDIDATE
files=["core.py","server.py","json_codec.py"]
image_proof=[]
for name in meta["containers"]:
    argv=["docker","exec",name,"python","-c","import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in "+repr(files)+"}))"]
    label="packaged-"+("source" if name==meta["containers"][0] else "peer")
    assert run(argv,label)==0
    observed=json.loads((OUT/(label+".log")).read_text());expected={f:intake["stage_files_sha256"][f] for f in files}
    assert observed==expected
    image_proof.append(dict(container=name,expected=expected,observed=observed))
(OUT/"packaged-image-proof.json").write_text(json.dumps(dict(candidate=CANDIDATE,proof=image_proof),indent=2)+"\n")
run(meta["probe_command"],"baseline-probes-execution")
run([sys.executable,"-B",str(HERE/"very_deep_run_c7.py"),"--runtime",str(OUT/"baseline-01"),"--out",str(OUT/"very-deep-01")],"very-deep-driver")
# This runner always removes the previously started own baseline services/network.
run([sys.executable,"-B",str(HERE/"candidate7_extra.py"),str(OUT/"baseline-01"),str(REPO)],"inherited-extra-driver")
common=["--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate",CANDIDATE,"--handoff",str(OUT/"intake.json")]
for family in ["semantic","opaque-ids","nesting","snapshot"]:
    run([sys.executable,"-B",str(HERE/"semantic_runtime.py"),*common,"--probe-family",family,"--out",str(OUT/(family+"-01"))],family+"-driver")
run([sys.executable,"-B",str(HERE/"decoder_runtime.py"),*common,"--out",str(OUT/"decoder-01")],"decoder-driver")
for family,script in [("numeric","numeric_forms_current_run.py"),("fractional","fractional_party_run.py")]:
    run([sys.executable,"-B",str(HERE/script),"--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate",CANDIDATE,"--out",str(OUT/(family+"-01"))],family+"-driver")
summary=dict(candidate=CANDIDATE,started_at=began_at,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),wall_seconds=time.monotonic()-started,
    step_returncodes={c["log"]:c["returncode"] for c in commands},driver_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    note="Recorded return codes are orchestration results; probe assertions/runner errors remain separately preserved and decide coverage.")
(OUT/"execution-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
raise SystemExit(1 if any(c["returncode"] for c in commands) else 0)
