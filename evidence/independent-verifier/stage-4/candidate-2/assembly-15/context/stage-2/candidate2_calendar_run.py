"""New unique constrained current-image calendar supplement; own resources only."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;H=HERE/'candidate-2';R=HERE.parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('--probe-revision',required=True);a=p.parse_args();out=H/'calendar-browser-01';out.mkdir(exist_ok=False);f=json.loads((H/'runtime-01/preflight.json').read_text());C=f['candidate'];prefix='independent-verifier-c2-calendar';network=prefix+'-net';service=prefix+'-service';client=prefix+'-client';commands=[];cleanup=[]
    def run(argv,label):
        start=time.monotonic();r=subprocess.run(argv,cwd=R,capture_output=True,text=True);(out/(label+'.log')).write_text(r.stdout+r.stderr);commands.append(dict(argv=argv,cwd=str(R),log=label+'.log',returncode=r.returncode,seconds=time.monotonic()-start));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert r.returncode==0,(label,r.returncode);return r.stdout
    path='evidence/independent-verifier/stage-2/candidate2_calendar_browser.py';data=run(['git','show',a.probe_revision+':'+path],'sealed-source').encode();source=out/'executed-source.py';source.write_bytes(data)
    try:
        run(['docker','network','create','--internal',network],'network-create')
        start=time.monotonic();run(['docker','run','-d','--name',service,'--network',network,'--cpus','2','--memory','2g','-e','PORT=18321','-p','18320:18321',f['source']['current']['image_tag']],'service-start')
        run(['docker','exec',service,'python','-c','import time,urllib.request;deadline=time.monotonic()+4\nwhile True:\n try:\n  print(urllib.request.urlopen("http://127.0.0.1:18321/health",timeout=.2).read().decode());break\n except Exception:\n  if time.monotonic()>deadline:raise\n  time.sleep(.02)'],'health');readiness=time.monotonic()-start
        actual=json.loads(run(['docker','inspect',service],'service-inspect'))[0];assert actual['Image']==f['source']['current']['image_id'] and actual['Mounts']==[] and actual['HostConfig']['NanoCpus']==2000000000 and actual['HostConfig']['Memory']==2147483648
        network_facts=json.loads(run(['docker','network','inspect',network],'network-inspect'))[0];assert network_facts['Internal']
        packaged=json.loads(run(['docker','exec',service,'python','-c','import pathlib,hashlib,json;print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path(".").rglob("*") if p.is_file() and (p.suffix in [".py",".html",".js",".css"])}))'],'packaged-hashes'))
        for name,sha in packaged.items():assert sha==f['source']['current']['source_sha256'][name]
        image=json.loads((H/'assembly-03/client-proof.json').read_text())['image'];base='http://'+service+':18321'
        argv=['docker','run','--rm','--name',client,'--network',network,'--cpus','2','--memory','2g','-v',str(out)+':/evidence','-v',str(source)+':/verifier/stage-2/candidate2_calendar_browser.py:ro','--entrypoint','python',image,'/verifier/stage-2/candidate2_calendar_browser.py','--base',base,'--candidate',C,'--out','/evidence/calendar']
        run(argv,'calendar')
        proof=dict(candidate=C,image_id=actual['Image'],packaged_sha256=packaged,readiness_upper_bound_seconds=readiness,source_sha256=hashlib.sha256(data).hexdigest(),probe_revision=a.probe_revision,cpu=2,memory_bytes=2147483648,mounts=[],internal_offline=True,scope='Additional exact retained-image supplement; original clean build/source identity remain separately saved. No new build or host reachability claim.')
        (out/'source-runtime-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    finally:
        for argv,label in [(['docker','rm','-f',service],'cleanup-service'),(['docker','network','rm',network],'cleanup-network')]:run(argv,label);cleanup.append(commands[-1])
        (out/'cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n')
    print(json.dumps(dict(completed=True,cleanup_commands=len(cleanup))))
if __name__=='__main__':main()
