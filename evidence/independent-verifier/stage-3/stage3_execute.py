"""Run independently sealed protocols against the source-bound Stage 3 runtime."""
import argparse, hashlib, json, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--out',required=True)
 p.add_argument('--group',choices=['stage3','browser','inherited-http','inherited-browser','inherited-upgrade','reconstruction'],required=True)
 p.add_argument('--families');a=p.parse_args();runtime=Path(a.runtime).resolve();out=Path(a.out).resolve()
 assert runtime.is_relative_to(W) and out.is_relative_to(W);out.mkdir(parents=True,exist_ok=False)
 f=json.loads((runtime/'preflight.json').read_text());assert f['status']=='running_for_independent_checks'
 u=f['urls'];commands=[];release=runtime/'release.json'
 (out/'executed-client-manifest.json').write_text(json.dumps(dict(probe_revision=f['probe_revision'],image=f['runner_image'],image_id=f['runner_image_id'],manifest=f['client_manifest']),indent=2)+'\n')
 def probe(folder,script,label,extra=(),positional=None):
  name=f['prefix']+'-check';argv=['docker','run','--rm','--name',name,'--network',f['network'],'--cpus','2','--memory','2g',
   '-v',str(out)+':/evidence','-v',str(runtime)+':'+str(runtime)+':ro','-v',str(HERE/'candidate-1')+':'+str(HERE/'candidate-1')+':ro',
   '--entrypoint','python',f['runner_image'],'/verifier/'+folder+'/'+script]
  if positional is None:argv+=['--base',u['target'],'--candidate',f['candidate'],'--out','/evidence/'+label]+list(extra)
  else:argv+=positional
  began=time.monotonic()
  with (out/(label+'.log')).open('w') as log:rc=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  commands.append(dict(label=label,argv=argv,cwd=str(R),returncode=rc,seconds=time.monotonic()-began,log=label+'.log'))
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(json.dumps({k:commands[-1][k] for k in ('label','returncode','seconds')}),flush=True)
 if a.group=='stage3':
  families=(a.families or 'policies,explain,numeric,terms,series,rollback,moves,concurrency,retry,calendar,trace,first_error,upgrade,deep').split(',')
  for family in families:probe('stage-3','stage3_probe.py',family,positional=['--family',family,'--release',str(release),'--out','/evidence/'+family,'--execute'])
 elif a.group=='browser':
  for mode in (a.families or 'product,accepted-s1,accepted-s2').split(','):
   probe('stage-3','stage3_browser.py',mode,positional=['--mode',mode,'--release',str(release),'--out','/evidence/'+mode,'--execute'])
 elif a.group=='inherited-http':
  for folder,script,label,extra in [('stage-1','probe.py','baseline',['--peer',u['peer']]),
   ('stage-1','reproduce.py','original-minimal',[]),('stage-1','reproduce_calendar.py','calendar-minimal',[]),('stage-1','race50.py','race50',[]),
   ('stage-1','decimal_probe.py','decimal',['--peer',u['peer']]),('stage-1','semantic_probe.py','semantic',['--peer',u['peer'],'--third',u['third'],'--legacy',u['legacy-s1']]),
   ('stage-1','opaque_id_probe.py','opaque-ids',['--peer',u['peer']]),('stage-1','nesting_probe.py','nesting',['--peer',u['peer']]),
   ('stage-1','snapshot_probe.py','snapshot',['--peer',u['peer'],'--third',u['third']]),('stage-1','decoder_probe.py','decoder',['--peer',u['peer'],'--third',u['third']]),
   ('stage-2','api.py','pairs',['--peer',u['peer']]),('stage-2','amend_retained.py','retained-amend',['--peer',u['peer']])]:
   if not a.families or label in a.families.split(','):
    if label in ('baseline','snapshot','decoder'):
     probe('stage-3','stage3_inherited.py',label,positional=['--family',label,'--base',u['target'],'--candidate',f['candidate'],'--out','/evidence/'+label]+extra)
    else:probe(folder,script,label,extra)
  for script,label,args in [('large_minutes.py','large-minutes',[u['target'],f['candidate'],u['peer']]),('numeric_forms_current.py','numeric',[u['target'],f['candidate']]),
   ('fractional_party_probe.py','fractional',[u['target'],f['candidate']]),('very_deep_probe_c7.py','very-deep',[u['target'],u['peer'],f['candidate']]),('deep_race_c7.py','deep-race',[u['target'],u['peer'],f['candidate']])]:
   if not a.families or label in a.families.split(','):probe('stage-1',script,label,positional=args)
 elif a.group=='inherited-browser':
  for script,label in [('candidate2_browser.py','general'),('browser_boundaries.py','boundaries'),('browser_historical.py','historical'),('visual_detail.py','visual'),('browser_calendar.py','calendar')]:
   if not a.families or label in a.families.split(','):probe('stage-2',script,label)
 elif a.group=='inherited-upgrade':probe('stage-2','candidate2_upgrade.py','four-upgrades',positional=['--release',str(release),'--out','/evidence/four-upgrades'])
 else:
  for case in (a.families or 'origins,deep,opaque,numeric').split(','):
   probe('stage-2','reconstruction_probe.py',case,positional=['--release',str(release),'--out','/evidence/'+case,'--case',case,'--execute'])
 (out/'run-summary.json').write_text(json.dumps(dict(candidate=f['candidate'],group=a.group,commands=commands,nonzero_commands=sum(bool(c['returncode']) for c in commands)),indent=2)+'\n')
 raise SystemExit(any(c['returncode'] for c in commands))
if __name__=='__main__':main()
