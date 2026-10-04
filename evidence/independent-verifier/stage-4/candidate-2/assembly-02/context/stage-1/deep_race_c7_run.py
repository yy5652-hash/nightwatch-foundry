"""Run separately sealed own races using the proven retained exact image."""
import datetime as dt
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];OUT=HERE/'candidate-7/deep-race-01'
CANDIDATE='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
PROBE='27aaf9a931893995b62c060dc77a1237dc0f9fd4'
intake=json.loads((HERE/'candidate-7/intake.json').read_text())
assert intake['candidate']==CANDIDATE and intake['execution_authorized'] and intake['complete_task']
baseline=json.loads((HERE/'candidate-7/baseline-01/preflight.json').read_text())
OUT.mkdir(parents=True,exist_ok=False);commands=[];containers=[];network_created=False
prefix='independent-verifier-dr-'+dt.datetime.now(dt.timezone.utc).strftime('%m%d%H%M%S%f')
network=prefix+'-net';started=time.monotonic();result=1
proof=dict(candidate=CANDIDATE,probe_revision=PROBE,started_at=dt.datetime.now(dt.timezone.utc).isoformat(),startup={},status='running',build_claim='Retained complete image from fresh named baseline build; no new build claim')
def save():
    (OUT/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    (OUT/'runtime.json').write_text(json.dumps(proof,indent=2)+'\n')
def run(argv,label,input_bytes=None,required=True):
    began=time.monotonic()
    with (OUT/(label+'.log')).open('wb') as stream:
        p=subprocess.run(argv,cwd=REPO,input=input_bytes,stdout=stream,stderr=subprocess.STDOUT)
    commands.append(dict(argv=argv,cwd=str(REPO),log=label+'.log',returncode=p.returncode,duration_seconds=time.monotonic()-began,stdin_sha256=hashlib.sha256(input_bytes).hexdigest() if input_bytes else None))
    save()
    if required and p.returncode:raise RuntimeError('Recorded command failed: '+label)
    return p.returncode
try:
    source=subprocess.check_output(['git','show',PROBE+':evidence/independent-verifier/stage-1/deep_race_c7.py'],cwd=REPO)
    (OUT/'executed-client.py').write_bytes(source);proof['client_sha256']=hashlib.sha256(source).hexdigest()
    run(['docker','image','inspect',baseline['image']],'image')
    proof['image_id']=json.loads((OUT/'image.log').read_text())[0]['Id']
    run(['docker','network','create','--internal',network],'network-create');network_created=True
    run(['docker','network','inspect',network],'network-inspect')
    assert json.loads((OUT/'network-inspect.log').read_text())[0]['Internal'] is True
    urls=[]
    for role,port in [('source',18360),('peer',18361)]:
        name=prefix+'-'+role;began=time.monotonic()
        run(['docker','run','-d','--name',name,'--network',network,'--cpus','2','--memory','2g','-p',f'127.0.0.1:{port}:8080',baseline['image']],role+'-start');containers.append(name)
        url='http://'+name+':8080';urls.append(url)
        health="import json,time,urllib.request;deadline=time.monotonic()+4.5\nwhile True:\n try:\n  r=urllib.request.urlopen("+repr(url+'/health')+",timeout=.5);assert r.status==200 and json.load(r)=={'status':'ok'};break\n except Exception:\n  if time.monotonic()>deadline:raise\n  time.sleep(.02)\n"
        run(['docker','run','--rm','--name',prefix+'-health','--network',network,'--cpus','2','--memory','2g','--entrypoint','python',baseline['runner_image'],'-c',health],role+'-health')
        proof['startup'][role]=dict(readiness_seconds=time.monotonic()-began,cross_container_health=True,internal_port=8080)
        assert proof['startup'][role]['readiness_seconds']<5
        run(['docker','inspect',name],role+'-inspect');info=json.loads((OUT/(role+'-inspect.log')).read_text())[0]
        assert info['HostConfig']['NanoCpus']==2000000000 and info['HostConfig']['Memory']==2147483648 and info['HostConfig']['NetworkMode']==network and not info['Mounts'] and info['Image']==proof['image_id']
        code="import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['core.py','server.py','json_codec.py']}))"
        run(['docker','exec',name,'python','-c',code],role+'-hashes')
        hashes=json.loads((OUT/(role+'-hashes.log')).read_text());assert hashes=={f:intake['stage_files_sha256'][f] for f in hashes}
        proof['startup'][role]['packaged_hashes']=hashes
    argv=['docker','run','--rm','-i','--name',prefix+'-client','--network',network,'--cpus','2','--memory','2g','--entrypoint','python',baseline['runner_image'],'-B','-',*urls,CANDIDATE]
    result=run(argv,'client',source,False)
    data=json.loads((OUT/'client.log').read_text());assert data['candidate']==CANDIDATE
    (OUT/'probes.json').write_text(json.dumps(data,indent=2)+'\n');proof['status']='completed';proof['client_returncode']=result
except Exception as error:
    proof['status']='runner_error';proof['runner_error']=dict(type=type(error).__name__,message=str(error));raise
finally:
    cleanup=[]
    for name in containers:
        cleanup.append(dict(resource=name,returncode=run(['docker','rm','-f',name],name+'-cleanup',required=False)))
    if network_created:cleanup.append(dict(resource=network,returncode=run(['docker','network','rm',network],'network-cleanup',required=False)))
    proof.update(cleanup=cleanup,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),wall_seconds=time.monotonic()-started)
    save()
print(json.dumps(dict(candidate=CANDIDATE,client_returncode=result,output=str(OUT))))
raise SystemExit(result)
