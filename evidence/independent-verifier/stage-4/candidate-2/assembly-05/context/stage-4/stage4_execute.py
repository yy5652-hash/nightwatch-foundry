"""Sequential independently named current protocols; outputs are never reused."""
import argparse, datetime as dt, json, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--families',default='closure-errors,preview,apply,oracle,amend,numeric,concurrency');a=parser.parse_args()
 out=Path(a.out).resolve();assert out.is_relative_to(HERE);out.mkdir(parents=True,exist_ok=False)
 runtime=HERE/'candidate-1/runtime-01';facts=json.loads((runtime/'preflight.json').read_text());assert facts['status']=='running_for_independent_checks'
 release=runtime/'release.json';commands=[];began=time.monotonic();started=dt.datetime.now(dt.timezone.utc).isoformat()
 (out/'executed-orchestrator.py').write_bytes(Path(__file__).read_bytes())
 (out/'client-source-binding.json').write_text(json.dumps(dict(candidate=facts['candidate'],probe_revision=facts['probe_revision'],image=facts['runner_image'],image_id=facts['runner_image_id'],manifest=facts['client_manifest']),indent=2)+'\n')
 for family in a.families.split(','):
  assert family in ('closure-errors','preview','apply','oracle','amend','numeric','concurrency')
  argv=['docker','run','--rm','--name',facts['prefix']+'-check','--network',facts['network'],'--cpus','2','--memory','2g','-v',str(out)+':/evidence','-v',str(runtime)+':'+str(runtime)+':ro','-v',str(HERE/'candidate-1/intake.json')+':'+str(HERE/'candidate-1/intake.json')+':ro','--entrypoint','python',facts['runner_image'],'/verifier/stage-4/'+('stage4_closure_errors.py' if family=='closure-errors' else 'stage4_probe.py'),'--release',str(release),'--out','/evidence/'+family]
  if family!='closure-errors':argv+=['--family',family,'--execute']
  start=time.monotonic()
  with (out/(family+'.log')).open('w') as log:rc=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  commands.append(dict(family=family,argv=argv,cwd=str(R),returncode=rc,seconds=time.monotonic()-start,log=family+'.log'))
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(json.dumps(commands[-1]),flush=True)
 summary=dict(candidate=facts['candidate'],started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),seconds=time.monotonic()-began,commands=len(commands),nonzero_commands=sum(c['returncode']!=0 for c in commands))
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');raise SystemExit(bool(summary['nonzero_commands']))
if __name__=='__main__':main()
