"""Current source-bound clients; concrete output and command per protocol."""
import argparse, datetime, json, shlex, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent; R=HERE.parents[2]; H=HERE/'candidate-2'
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--group',required=True)
    p.add_argument('--assembly');p.add_argument('--release');p.add_argument('--families');a=p.parse_args()
    out=Path(a.out).resolve();assert out.is_relative_to(H);out.mkdir(parents=True,exist_ok=False)
    runtime=H/'runtime-01';f=json.loads((runtime/'preflight.json').read_text());assert f['status']=='running_for_independent_checks'
    release=Path(a.release).resolve() if a.release else runtime/'release.json'
    if a.assembly:
        assembly=Path(a.assembly).resolve();b=json.loads((assembly/'client-proof.json').read_text());f.update(runner_image=b['image'],runner_image_id=b['image_id'],probe_revision=b['probe_revision'],client_manifest=b['manifest'])
    jobs=[]
    if a.group=='basic':
        for name in (a.families or 'closure-errors,preview,apply,oracle,amend,numeric,concurrency').split(','):
            script='stage4_closure_errors.py' if name=='closure-errors' else 'stage4_probe.py'
            args=['--release',str(release),'--out','/evidence/'+name]
            if name!='closure-errors':args+=['--family',name,'--execute']
            jobs.append((name,'/verifier/stage-4/'+script,args))
    elif a.group=='full-bound':jobs=[('full-bound','/verifier/stage-4/candidate2_full_bound.py',['--release',str(release),'--out','/evidence/full-bound','--execute'])]
    elif a.group=='model':jobs=[('model','/verifier/stage-4/candidate2_model.py',['--release',str(release),'--out','/evidence/model'])]
    elif a.group=='inherited-binding':jobs=[('binding','/verifier/stage-3/stage3_browser_binding.py',['--release',str(release),'--out','/evidence/binding'])]
    elif a.group=='atomic':
        for name in (a.families or 'prefix,invalid').split(','):jobs.append((name,'/verifier/stage-4/candidate2_atomic.py',['--release',str(release),'--out','/evidence/'+name,'--family',name]))
    elif a.group in ('errors','transitions','extra'):
        script={'errors':'candidate2_error_matrix.py','transitions':'repair-1/transitions.py','extra':'candidate2_extra.py'}[a.group]
        choices={'errors':'preview,apply,amend','transitions':'two-series,empty,ordering,distinct,atomic-reads','extra':'retry,deep,upgrade,staleness'}
        for name in (a.families or choices[a.group]).split(','):jobs.append((name,'/verifier/stage-4/'+script,['--release',str(release),'--out','/evidence/'+name,'--family',name,'--execute']))
    elif a.group in ('inherited-http','inherited-browser'):
        inventory=json.loads((HERE.parent/'stage-3/candidate-1/completed-runs.json').read_text())
        for record in inventory:
            if record['kind']!=('http' if a.group=='inherited-http' else 'browser'):continue
            if a.families and record['name'] not in a.families.split(','):continue
            old=shlex.split(record['command']);idx=old.index('--entrypoint')+3;script=old[idx];args=old[idx+1:]
            label=record['name'].replace('/','--')
            for i,value in enumerate(args):
                if value=='91e2c471acded1b861b3fec725f202297b1c6740':args[i]=f['candidate']
                elif value.startswith('http://independent-verifier-s3-'):
                    role=value.rsplit('-',1)[-1].split(':')[0]
                    if role not in f['urls']:
                        role=next(k for k in f['urls'] if ('-'+k+':') in value)
                    args[i]=f['urls'][role]
                elif value.endswith('release.json'):args[i]=str(release)
                elif value.startswith('/evidence/'):args[i]='/evidence/'+label
            jobs.append((label,script,args))
    else:
        script={'binding':'candidate2_binding.py','recovery':'candidate2_recovery.py'}.get(a.group)
        if not script:raise ValueError(a.group)
        if a.group=='binding':jobs=[('binding','/verifier/stage-4/'+script,['--release',str(release),'--out','/evidence/binding'])]
        else:
            for family in ['preview','apply','amend']:
                for mode in ['lost','malformed']:jobs.append((family+'-'+mode,'/verifier/stage-4/'+script,['--release',str(release),'--out','/evidence/'+family+'-'+mode,'--family',family,'--mode',mode,'--execute']))
    commands=[]
    (out/'executed-orchestrator.py').write_bytes(Path(__file__).read_bytes())
    (out/'client-source-binding.json').write_text(json.dumps(dict(candidate=f['candidate'],probe_revision=f['probe_revision'],image=f['runner_image'],image_id=f['runner_image_id'],manifest=f['client_manifest']),indent=2)+'\n')
    for label,script,args in jobs:
        argv=['docker','run','--rm','--name',f['prefix']+'-check','--network',f['network'],'--cpus','2','--memory','2g','-v',str(H)+':'+str(H)+':ro','-v',str(out)+':/evidence','--entrypoint','python',f['runner_image'],script,*args]
        began=time.monotonic()
        with (out/(label+'.log')).open('w') as log:rc=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
        commands.append(dict(family=label,argv=argv,cwd=str(R),returncode=rc,seconds=time.monotonic()-began,log=label+'.log'))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(json.dumps({k:commands[-1][k] for k in ['family','returncode','seconds']}),flush=True)
        if rc:break
    (out/'summary.json').write_text(json.dumps(dict(candidate=f['candidate'],group=a.group,requested=len(jobs),executed=len(commands),nonzero=sum(bool(c['returncode']) for c in commands)),indent=2)+'\n')
    raise SystemExit(any(c['returncode'] for c in commands))
if __name__=='__main__':main()
