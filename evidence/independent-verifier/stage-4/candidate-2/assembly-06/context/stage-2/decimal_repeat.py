"""Fresh independent current/frozen processes for the inherited decimal boundary."""
import argparse,json,subprocess,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser()
    for k in ['runtime','out']:p.add_argument('--'+k,required=True)
    a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    f=json.loads((Path(a.runtime)/'preflight.json').read_text());commands=[];containers=[]
    def run(argv,required=True):
        log=out/('command-%02d.log'%len(commands));t=time.monotonic()
        with log.open('w')as h:v=subprocess.run(argv,stdout=h,stderr=subprocess.STDOUT)
        commands.append(dict(argv=argv,returncode=v.returncode,seconds=time.monotonic()-t,log=str(log)));(out/'commands.json').write_text(json.dumps(commands,indent=2))
        if required and v.returncode:raise RuntimeError(str(log))
        return log.read_text()
    try:
        proofs=[];urls=[]
        for index,stage in [(0,'stage-2'),(2,'stage-1')]:
            name='independent-verifier-decimal-'+stage+'-'+out.name;port=18313+index
            run(['docker','run','-d','--name',name,'--network',f['network'],'--cpus','2','--memory','2g','-e','PORT='+str(port),f['containers'][index]['image']]);containers.append(name)
            url='http://'+name+':'+str(port);urls.append(url)
            run(['docker','run','--rm','--name',name+'-health','--network',f['network'],'--entrypoint','python','independent-verifier-s2:review-runner-08','/verifier/stage-1/health.py','--url',url+'/health','--timeout','57'])
            inspect=json.loads(run(['docker','inspect',name]))[0]
            observed=json.loads(run(['docker','exec',name,'python','-c','import hashlib,json,pathlib;print(json.dumps({str(p.relative_to("/app")):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path("/app").rglob("*") if p.is_file()}))']))
            expected={k.removeprefix(stage+'/'):v for k,v in f['source_hashes'].items() if k.startswith(stage+'/') and (k.endswith('.py')or '/web/'in k)}
            proofs.append(dict(stage=stage,name=name,expected=expected,image_files=observed,match=expected==observed,cpu=inspect['HostConfig']['NanoCpus'],memory=inspect['HostConfig']['Memory'],mounts=inspect['Mounts'],network=inspect['HostConfig']['NetworkMode']))
            if expected!=observed:raise RuntimeError('Source hash mismatch')
        (out/'source-proof.json').write_text(json.dumps(proofs,indent=2))
        run(['docker','run','--rm','--name','independent-verifier-decimal-probe-'+out.name,'--network',f['network'],'--cpus','2','--memory','2g','-v',str(out)+':/out','--entrypoint','python','independent-verifier-s2:review-runner-08','/verifier/stage-2/decimal_limit.py','--base',urls[0],'--legacy',urls[1],'--candidate',f['candidate'],'--out','/out/probes'],required=False)
    finally:
        for name in containers:run(['docker','rm','-f',name],required=False)
    print(json.dumps(dict(candidate=f['candidate'],commands=len(commands),nonzero=sum(bool(c['returncode'])for c in commands),seconds=sum(c['seconds']for c in commands))))
    raise SystemExit(any(c['returncode']for c in commands))
if __name__=='__main__':main()
