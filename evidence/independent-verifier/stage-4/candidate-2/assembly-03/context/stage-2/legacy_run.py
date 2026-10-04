"""Independently build this run's actual pre-serializer commit and transfer genuine receipts."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
OLD='49287b4a5a1481f995c470ccae31776f03d4b863'
def main():
    p=argparse.ArgumentParser()
    for field in ['runtime','repo','workspace','out']: p.add_argument('--'+field,required=True)
    p.add_argument('--current-view',action='store_true')
    a=p.parse_args(); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=False)
    f=json.loads((Path(a.runtime)/'preflight.json').read_text()); prefix='independent-verifier-s2-old-'+f['candidate'][:8]+'-'+out.name
    commands=[]
    def run(argv,cwd=None,required=True):
        log=out/('command-%02d.log'%len(commands)); t=time.monotonic()
        with log.open('w') as h: v=subprocess.run(argv,cwd=cwd,stdout=h,stderr=subprocess.STDOUT)
        commands.append(dict(argv=argv,cwd=str(cwd) if cwd else None,returncode=v.returncode,seconds=time.monotonic()-t,log=str(log)))
        (out/'commands.json').write_text(json.dumps(commands,indent=2))
        if required and v.returncode: raise RuntimeError(str(log))
        return log.read_text()
    clone=Path(a.workspace)/'band-work'/prefix
    run(['git','clone','--no-hardlinks','--no-checkout',a.repo,str(clone)])
    run(['git','checkout','--detach',OLD],clone)
    head=run(['git','rev-parse','HEAD'],clone).strip(); clean=not run(['git','status','--porcelain=v1'],clone).strip()
    if head!=OLD or not clean: raise RuntimeError('Legacy clone is not exact and clean')
    image=prefix+':source'; container=prefix+'-service'
    run(['docker','build','-t',image,'.'],clone/'stage-1')
    hashes={q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in (clone/'stage-1').glob('*.py')}
    run(['docker','run','-d','--name',container,'--network',f['network'],'--cpus','2','--memory','2g','-e','PORT=18311',image])
    try:
        run(['docker','run','--rm','--name',prefix+'-health','--network',f['network'],'--entrypoint','python',f['runner_image'],'/verifier/stage-1/health.py','--url','http://'+container+':18311/health','--timeout','57'])
        inspect=json.loads(run(['docker','inspect',container]))[0]
        observed=json.loads(run(['docker','exec',container,'python','-c','import hashlib,json,pathlib;print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path("/app").glob("*.py")}))']))
        proof=dict(source_revision=OLD,clone=str(clone),clean=clean,source_hashes=hashes,image_hashes=observed,hashes_match=hashes==observed,
            nano_cpus=inspect['HostConfig']['NanoCpus'],memory=inspect['HostConfig']['Memory'],mounts=inspect['Mounts'],network=inspect['HostConfig']['NetworkMode'])
        (out/'source-proof.json').write_text(json.dumps(proof,indent=2))
        runner='independent-verifier-s2:review-runner-05' if a.current_view else f['runner_image']
        script='/verifier/stage-2/legacy_receipts_current.py' if a.current_view else '/verifier/stage-1/legacy_receipts.py'
        run(['docker','run','--rm','--name',prefix+'-probe','--network',f['network'],'--cpus','2','--memory','2g','-v',str(out)+':/out','--entrypoint','python',runner,
             script,'--base',f['containers'][0]['url'],'--peer',f['containers'][1]['url'],
             '--legacy','http://'+container+':18311','--candidate',f['candidate'],'--out','/out/probes'],required=False)
    finally: run(['docker','rm','-f',container],required=False)
    print(json.dumps(dict(candidate=f['candidate'],source_revision=OLD,commands=len(commands),nonzero=sum(bool(c['returncode']) for c in commands),seconds=sum(c['seconds'] for c in commands))))
    raise SystemExit(any(c['returncode'] for c in commands))
if __name__=='__main__': main()
