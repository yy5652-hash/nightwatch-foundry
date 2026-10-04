"""Unchanged isolated official suite runner from exact clean named clone."""
import datetime as dt, json, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1];H=HERE/'candidate-2'
def main():
 f=json.loads((H/'runtime-01/preflight.json').read_text());clone=Path(f['clone']);C=f['candidate']
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip()==C
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=clone,text=True)
 kickoff=W/'kickoff';assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=kickoff,text=True).strip()=='803560d2a678ace1414465c098eb0ab5380ffade'
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=kickoff,text=True)
 out=W/'band-work/final-checks'/('independent-verifier-s4-c2-58270860-official-'+dt.datetime.now(dt.timezone.utc).strftime('%H%M%S'))
 assert not out.exists();argv=[str(W/'.venv/bin/python'),'-m','harness','run','--track','tablekeeper','--repo',str(clone),'--stage','4','--mode','isolated','--out',str(out)]
 started=dt.datetime.now(dt.timezone.utc).isoformat();began=time.monotonic()
 with (H/'official-driver.log').open('x') as log:rc=subprocess.run(argv,cwd=kickoff,stdout=log,stderr=subprocess.STDOUT).returncode
 command=dict(argv=argv,cwd=str(kickoff),candidate=C,returncode=rc,started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),seconds=time.monotonic()-began,output=str(out),source='Unchanged official harness, exact clean clone, no suite/selection/source edits')
 (H/'official-command.json').write_text(json.dumps(command,indent=2)+'\n');print(json.dumps(command))
 raise SystemExit(rc)
if __name__=='__main__':main()
