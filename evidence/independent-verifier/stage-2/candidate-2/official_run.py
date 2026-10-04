"""Unchanged official Stage2 invocation, including all applicable suites/overshoot."""
import datetime as dt, json, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[3];W=R.parents[1]
f=json.loads((HERE/'runtime-01/preflight.json').read_text())
out=W/'band-work/final-checks'/('independent-verifier-s2-c2-4dba1024-official-'+dt.datetime.now(dt.timezone.utc).strftime('%H%M%S'))
argv=[str(W/'.venv/bin/python'),'-m','harness','run','--track','tablekeeper','--repo',f['clone'],'--stage','2','--mode','isolated','--out',str(out)]
started=dt.datetime.now(dt.timezone.utc).isoformat();began=time.monotonic()
with (HERE/'official-command.log').open('w') as log:result=subprocess.run(argv,cwd=W/'kickoff',stdout=log,stderr=subprocess.STDOUT)
record=dict(argv=argv,cwd=str(W/'kickoff'),output=str(out),returncode=result.returncode,started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),wall_seconds=time.monotonic()-began)
(HERE/'official-command.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
raise SystemExit(result.returncode)
