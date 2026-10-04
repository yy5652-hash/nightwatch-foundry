"""Sealed own client assembly and actual cumulative commands against current Stage2."""
import argparse, hashlib, json, shutil, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--out',required=True);p.add_argument('--probe-revision',required=True);p.add_argument('--assembly');p.add_argument('--group',choices=['assemble','http','inherited','origins','browser','reconstruction-http','reconstruction-browser'],required=True);a=p.parse_args()
    runtime=Path(a.runtime).resolve();out=Path(a.out).resolve();assert runtime.is_relative_to(W) and out.is_relative_to(W);out.mkdir(parents=True,exist_ok=False)
    facts=json.loads((runtime/'preflight.json').read_text());C=facts['candidate'];prefix=facts['prefix'];u=facts['urls'];commands=[]
    def run(argv,label,cwd=R):
        began=time.monotonic()
        with (out/(label+'.log')).open('w') as f:result=subprocess.run(argv,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
        commands.append(dict(argv=argv,cwd=str(cwd),log=label+'.log',returncode=result.returncode,seconds=time.monotonic()-began));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        print(json.dumps({'label':label,'returncode':result.returncode,'seconds':commands[-1]['seconds']}),flush=True)
        return result.returncode
    if a.group=='assemble':
        context=out/'context';context.mkdir();manifest=[]
        for folder in ['stage-1','stage-2']:
            (context/folder).mkdir()
            names=subprocess.check_output(['git','ls-tree','--name-only',a.probe_revision+':evidence/independent-verifier/'+folder],cwd=R,text=True).splitlines()
            for name in names:
                if not (name.endswith('.py') or name=='Browser.Dockerfile'):continue
                path='evidence/independent-verifier/'+folder+'/'+name;argv=['git','show',a.probe_revision+':'+path];data=subprocess.check_output(argv,cwd=R)
                (context/folder/name).write_bytes(data);manifest.append(dict(path=path,sha256=hashlib.sha256(data).hexdigest(),argv=argv))
        for folder,name in [('stage-1','candidate-7/coverage.csv'),('stage-2','candidate-1/coverage.csv')]:
            path='evidence/independent-verifier/'+folder+'/'+name;argv=['git','show',a.probe_revision+':'+path];data=subprocess.check_output(argv,cwd=R)
            target=context/folder/name;target.parent.mkdir(parents=True);target.write_bytes(data);manifest.append(dict(path=path,sha256=hashlib.sha256(data).hexdigest(),argv=argv))
        # These are own requirement inputs, not a previous outcome used as proof.
        dockerfile=context/'Dockerfile'
        dockerfile.write_text('FROM '+facts['runner_image']+'\nCOPY stage-1 /verifier/stage-1\nCOPY stage-2 /verifier/stage-2\n')
        image=prefix+':complete-client-'+a.probe_revision[:8]
        assert run(['docker','build','-t',image,'.'],'client-build',context)==0
        (out/'client-proof.json').write_text(json.dumps(dict(image=image,probe_revision=a.probe_revision,manifest=manifest,dockerfile_sha256=hashlib.sha256(dockerfile.read_bytes()).hexdigest(),runtime=str(runtime),note='No service source changed; complete own protocol dependency/input assembly before first behavioural client invocation.'),indent=2)+'\n')
        release=json.loads((runtime/'release.json').read_text());release.update(systems_revision=release['systems_implementation'],interface_revision=release['interface_implementation'])
        (out/'release.json').write_text(json.dumps(release,indent=2)+'\n');return
    assembly_path=Path(a.assembly).resolve() if a.assembly else runtime.parent/'assembly-01'
    assembly=json.loads((assembly_path/'client-proof.json').read_text());runner=assembly['image'];release=assembly_path/'release.json'
    source_copy=out/'executed-client-manifest.json';source_copy.write_text(json.dumps(assembly,indent=2)+'\n')
    def probe(folder,script,label,extra=(),positional=None,json_stdout=False):
        name=prefix+'-'+str(len(commands));assert len(name)<=63
        argv=['docker','run','--rm','--name',name,'--network',facts['network'],'--cpus','2','--memory','2g','-v',str(out)+':/evidence','-v',str(release)+':/release.json:ro','--entrypoint','python',runner,'/verifier/'+folder+'/'+script]
        if positional is not None:argv+=positional
        else:argv+=['--base',u['target'],'--candidate',C,'--out','/evidence/'+label]+list(extra)
        code=run(argv,label)
        if json_stdout:
            try:data=json.loads((out/(label+'.log')).read_text());(out/(label+'.json')).write_text(json.dumps(data,indent=2)+'\n')
            except Exception as e:(out/(label+'-reader-error.json')).write_text(json.dumps(dict(type=type(e).__name__,message=str(e))))
        return code
    if a.group=='http':
        for script,label,extra in [('probe.py','baseline',['--peer',u['peer']]),('reproduce.py','original-minimal',[]),('reproduce_calendar.py','calendar-minimal',[]),('race50.py','race50',[]),('decimal_probe.py','decimal',['--peer',u['peer']]),('semantic_probe.py','semantic',['--peer',u['peer'],'--third',u['third'],'--legacy',u['legacy-s1']]),('opaque_id_probe.py','opaque-ids',['--peer',u['peer']]),('nesting_probe.py','nesting',['--peer',u['peer']]),('snapshot_probe.py','snapshot',['--peer',u['peer'],'--third',u['third']]),('decoder_probe.py','decoder',['--peer',u['peer'],'--third',u['third']])]:probe('stage-1',script,label,extra)
        for script,label,args in [('large_minutes.py','large-minutes',[u['target'],C,u['peer']]),('numeric_forms_current.py','numeric',[u['target'],C]),('fractional_party_probe.py','fractional',[u['target'],C]),('very_deep_probe_c7.py','very-deep',[u['target'],u['peer'],C]),('deep_race_c7.py','deep-race',[u['target'],u['peer'],C])]:probe('stage-1',script,label,positional=args,json_stdout=True)
        probe('stage-2','api.py','pairs',['--peer',u['peer']]);probe('stage-2','amend_retained.py','retained-amend',['--peer',u['peer']])
    elif a.group=='inherited':
        for family in ['baseline','snapshot','decoder','legacy']:
            extra=['--family',family,'--base',u['target'],'--peer',u['peer'],'--candidate',C,'--out','/evidence/'+family]
            if family in ['snapshot','decoder']:extra+=['--third',u['third']]
            if family=='legacy':extra+=['--legacy',u['legacy-s1']]
            probe('stage-2','candidate2_inherited.py',family,positional=extra)
    elif a.group=='origins':
        probe('stage-2','reconstruction_probe.py','origins',positional=['--release','/release.json','--out','/evidence/origins','--case','origins','--execute'])
    elif a.group=='browser':
        for script,label in [('browser.py','general'),('browser_boundaries.py','boundaries'),('browser_historical.py','historical'),('visual_detail.py','visual')]:probe('stage-2',script,label)
    else:
        browser=a.group=='reconstruction-browser';script='reconstruction_browser_protocol.py' if browser else 'reconstruction_probe.py'
        for case in ['upgrade','numeric','opaque'] if browser else ['origins','deep','opaque','numeric']:
            probe('stage-2',script,case,positional=['--release','/release.json','--out','/evidence/'+case,'--case',case,'--execute'])
    (out/'run-summary.json').write_text(json.dumps(dict(candidate=C,group=a.group,commands=commands,nonzero_commands=sum(bool(c['returncode']) for c in commands),wall_seconds=sum(c['seconds'] for c in commands)),indent=2)+'\n')
    raise SystemExit(any(c['returncode'] for c in commands))
if __name__=='__main__':main()
