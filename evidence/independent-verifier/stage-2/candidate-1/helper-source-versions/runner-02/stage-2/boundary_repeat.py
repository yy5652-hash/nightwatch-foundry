"""Fresh exact-image process repeat; no previous fixture/state reused."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser()
    for k in ['runtime','out']:p.add_argument('--'+k,required=True)
    a=p.parse_args(); out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    f=json.loads((Path(a.runtime)/'preflight.json').read_text()); c=f['containers'][0];name='independent-verifier-s2-boundary-'+f['candidate'][:8]+'-'+out.name
    commands=[]
    def run(argv,required=True):
        log=out/('command-%02d.log'%len(commands));t=time.monotonic()
        with log.open('w')as h:v=subprocess.run(argv,stdout=h,stderr=subprocess.STDOUT)
        commands.append(dict(argv=argv,returncode=v.returncode,seconds=time.monotonic()-t,log=str(log)));(out/'commands.json').write_text(json.dumps(commands,indent=2))
        if required and v.returncode:raise RuntimeError(str(log))
        return log.read_text()
    run(['docker','run','-d','--name',name,'--network',f['network'],'--cpus','2','--memory','2g','-e','PORT=18312',c['image']])
    try:
        run(['docker','run','--rm','--name',name+'-health','--network',f['network'],'--entrypoint','python','independent-verifier-s2:review-runner-04','/verifier/stage-1/health.py','--url','http://'+name+':18312/health','--timeout','57'])
        inspect=json.loads(run(['docker','inspect',name]))[0]
        observed=json.loads(run(['docker','exec',name,'python','-c','import hashlib,json,pathlib;print(json.dumps({str(p.relative_to("/app")):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path("/app").rglob("*") if p.is_file()}))']))
        expected={k.removeprefix('stage-2/'):v for k,v in f['source_hashes'].items() if k in ['stage-2/core.py','stage-2/server.py','stage-2/web/app.js','stage-2/web/app.css','stage-2/web/index.html']}
        proof=dict(candidate=f['candidate'],hashes_match=observed==expected,expected=expected,observed=observed,
            nano_cpus=inspect['HostConfig']['NanoCpus'],memory=inspect['HostConfig']['Memory'],mounts=inspect['Mounts'],network=inspect['HostConfig']['NetworkMode'])
        (out/'source-proof.json').write_text(json.dumps(proof,indent=2))
        if observed!=expected:raise RuntimeError('Image source mismatch')
        run(['docker','run','--rm','--name',name+'-probe','--network',f['network'],'--cpus','2','--memory','2g','-v',str(out)+':/out','--entrypoint','python','independent-verifier-s2:review-runner-04',
             '/verifier/stage-2/browser_boundaries.py','--base','http://'+name+':18312','--candidate',f['candidate'],'--out','/out/probes'],required=False)
    finally:run(['docker','rm','-f',name],required=False)
    print(json.dumps(dict(candidate=f['candidate'],commands=len(commands),nonzero=sum(bool(c['returncode']) for c in commands),seconds=sum(c['seconds'] for c in commands))))
    raise SystemExit(any(c['returncode'] for c in commands))
if __name__=='__main__':main()
