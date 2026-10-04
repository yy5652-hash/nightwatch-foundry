"""Fresh named Stage2 and genuine earlier-origin images; only own evidence mutates."""
import argparse, datetime as dt, hashlib, json, re, subprocess, time
from pathlib import Path

HERE=Path(__file__).resolve().parent; R=HERE.parents[2]; W=R.parents[1]
ORIGINS={'legacy-s1':('49287b4a5a1481f995c470ccae31776f03d4b863',1),'exact-s1':('75005d57fe0904753eac4eab5bf4e4c9a78b6d1b',1),'legacy-s2':('4b92041057beb669d2e6c528e8268f4d0d1e6421',2)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--probe-revision',required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
    intake=json.loads((HERE/'candidate-2/intake.json').read_text()); C=intake['candidate']
    assert intake['complete_package'] and intake['end_received'] and intake['execution_authorized'] and len(intake['all_parts'])==13
    assert re.fullmatch('[0-9a-f]{40}',a.probe_revision)
    out=Path(a.out).resolve();assert out.is_relative_to(W);out.mkdir(parents=True,exist_ok=False)
    prefix='independent-verifier-c2-'+dt.datetime.now(dt.timezone.utc).strftime('%m%d%H%M%S')
    commands=[]; containers=[]; network=prefix+'-net'; created_network=False
    facts=dict(candidate=C,probe_revision=a.probe_revision,prefix=prefix,started_at=dt.datetime.now(dt.timezone.utc).isoformat(),status='preflight',source={},containers=[],intake=intake)
    def save():
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');(out/'preflight.json').write_text(json.dumps(facts,indent=2)+'\n')
    def run(argv,label,cwd=R,required=True):
        began=time.monotonic();log=label+'.log'
        with (out/log).open('w') as f:proc=subprocess.run(argv,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
        commands.append(dict(argv=argv,cwd=str(cwd),log=log,returncode=proc.returncode,seconds=time.monotonic()-began));save()
        if required and proc.returncode:raise RuntimeError('Failed own command; retained '+str(out/log))
        return (out/log).read_text()
    try:
        for role,(rev,stage_num) in {'current':(C,2),**ORIGINS}.items():
            clone=W/'band-work'/(prefix+'-'+role)
            run(['git','clone','--no-hardlinks','--no-checkout',str(R),str(clone)],role+'-clone')
            run(['git','checkout','--detach',rev],role+'-checkout',clone)
            assert run(['git','rev-parse','HEAD'],role+'-head',clone).strip()==rev
            assert not run(['git','status','--porcelain=v1'],role+'-status',clone).strip()
            tree=run(['git','ls-tree','-r',rev],role+'-tree',clone)
            assert '160000 ' not in tree
            stage=clone/('stage-'+str(stage_num));issues=[str(x) for x in stage.rglob('*') if x.is_symlink() or x.name in ['.git','.gitmodules']]
            assert not issues,issues
            hashes={str(x.relative_to(stage)):hashlib.sha256(x.read_bytes()).hexdigest() for x in stage.rglob('*') if x.is_file()}
            facts['source'][role]=dict(revision=rev,stage=stage_num,clone=str(clone),source_sha256=hashes,tree_issues=issues,clean=True,image_tag=prefix+':'+role)
            (out/(role+'-RUN.md')).write_bytes((stage/'RUN.md').read_bytes())
            if role=='current':
                assert run(['git','rev-parse',rev+':stage-2'],role+'-stage2-tree',clone).strip()==intake['stage_2_tree']
                assert not run(['git','diff',intake['accepted_stage1'],rev,'--','stage-1'],'frozen-stage1-diff',clone).strip()
                facts['clone']=str(clone);facts['frozen_stage1_unchanged']=True
            if a.execute:
                run(['docker','build','-t',prefix+':'+role,'.'],role+'-build',stage)
                image=json.loads(run(['docker','image','inspect',prefix+':'+role],role+'-image'))[0]
                facts['source'][role]['image_id']=image['Id']
        if not a.execute: save();print(json.dumps({'status':'preflight','output':str(out)}));return
        # Copy only own top-level protocol files from a sealed revision. No peer test is read.
        context=out/'own-client-context';context.mkdir()
        client_manifest=[]
        for folder in ['stage-1','stage-2']:
            (context/folder).mkdir()
            listing=run(['git','ls-tree','--name-only',a.probe_revision+':evidence/independent-verifier/'+folder],folder+'-client-list').splitlines()
            for name in listing:
                if not (name.endswith('.py') or name=='Browser.Dockerfile'):continue
                argv=['git','show',a.probe_revision+':evidence/independent-verifier/'+folder+'/'+name]
                data=subprocess.check_output(argv,cwd=R);(context/folder/name).write_bytes(data)
                client_manifest.append(dict(path=folder+'/'+name,sha256=hashlib.sha256(data).hexdigest(),argv=argv))
        facts['client_manifest']=client_manifest;facts['runner_image']=prefix+':client'
        run(['docker','build','-f','stage-2/Browser.Dockerfile','-t',facts['runner_image'],'.'],'client-build',context)
        run(['docker','network','create','--internal',network],'network-create');created_network=True
        info=json.loads(run(['docker','network','inspect',network],'network-inspect'))[0];assert info['Internal']
        facts['network']=network;urls={}
        roles=[('target','current',18309,18300,True),('peer','current',8080,18301,False),('third','current',18311,18303,True),('legacy-s1','legacy-s1',18312,18304,True),('exact-s1','exact-s1',18313,18305,True),('legacy-s2','legacy-s2',18314,18306,True)]
        for role,source,port,host,override in roles:
            name=prefix+'-'+role;assert len(name)<=63
            argv=['docker','run','-d','--name',name,'--network',network,'--cpus','2','--memory','2g','-p',f'127.0.0.1:{host}:{port}']
            if override:argv+=['-e','PORT='+str(port)]
            argv+=[facts['source'][source]['image_tag']]
            launch_at=dt.datetime.now(dt.timezone.utc).isoformat();began=time.monotonic()
            run(argv,role+'-start');containers.append(name);urls[role]=f'http://{name}:{port}'
            run(['docker','run','--rm','--name',prefix+'-health','--network',network,'--cpus','2','--memory','2g','--entrypoint','python',facts['runner_image'],'/verifier/stage-1/health.py','--url',urls[role]+'/health','--timeout','57'],role+'-health')
            elapsed=time.monotonic()-began;healthy_at=dt.datetime.now(dt.timezone.utc).isoformat()
            assert elapsed<60
            inspected=json.loads(run(['docker','inspect',name],role+'-inspect'))[0]
            assert inspected['HostConfig']['NanoCpus']==2000000000 and inspected['HostConfig']['Memory']==2147483648 and not inspected['Mounts'] and inspected['HostConfig']['NetworkMode']==network
            names=list(facts['source'][source]['source_sha256']);code='import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in '+repr([n for n in names if n.endswith('.py') or n.startswith('web/')])+ ' if Path(f).is_file()}))'
            packaged=json.loads(run(['docker','exec',name,'python','-c',code],role+'-packaged-hashes'))
            expected={n:v for n,v in facts['source'][source]['source_sha256'].items() if n in packaged};assert packaged==expected
            facts['containers'].append(dict(name=name,role=role,source=source,url=urls[role],default_port=not override,internal_port=port,host_port=host,startup_to_health_seconds=elapsed,launch_at=launch_at,healthy_at=healthy_at,health_before_source_inspection=True,cross_container_access=True,cpu=2,memory_bytes=2147483648,mounts=[],actual_image_id=inspected['Image'],packaged_sha256=packaged))
            assert inspected['Image']==facts['source'][source]['image_id'];save()
        release={**intake,'urls':urls,'source_revisions':{k:v[0] for k,v in ORIGINS.items()},'frozen_stage1_verified':True,'offline_2cpu_2g_no_mounts_verified':True,'runtime':str(out),'execution_authorized':True}
        (out/'release.json').write_text(json.dumps(release,indent=2)+'\n')
        facts.update(status='running_for_independent_checks',urls=urls,retained_services=True);save()
        print(json.dumps({'candidate':C,'runtime':str(out),'clone':facts['clone'],'readiness':{x['role']:x['startup_to_health_seconds'] for x in facts['containers']}}))
    except Exception as e:
        facts['status']='runner_error';facts['runner_error']=dict(type=type(e).__name__,message=str(e));save()
        for name in containers:run(['docker','rm','-f',name],name+'-cleanup',required=False)
        if created_network:run(['docker','network','rm',network],'network-cleanup',required=False)
        raise
if __name__=='__main__':main()
