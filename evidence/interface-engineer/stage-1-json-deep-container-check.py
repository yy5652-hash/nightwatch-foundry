"""Supplement actual deep HTTP against the previously clean-built named image.

No rebuild or fresh build claim: binds the retained complete-image proof, creates
two independent services and a separate stdlib client, removes only own resources.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--revision',required=True)
p.add_argument('--probe-revision',required=True)
p.add_argument('--source-run',required=True)
args=p.parse_args()
source_run=(ROOT/args.source_run).resolve()
assert source_run.is_relative_to(ROOT/'evidence/interface-engineer')
prior=json.loads((source_run/'run.json').read_text())
proof=json.loads((source_run/'source-proof.json').read_text())
assert prior['candidate']==args.revision and proof['candidate']==args.revision and not prior['errors']
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ').lower()
slug='interface-engineer-json-deep-'+stamp
resource='interface-engineer-jd-'+stamp
out=ROOT/'evidence/interface-engineer'/slug
out.mkdir()
network=slug
image=prior['images_retained'][0]
commands,checks,resources,errors,created=[],[],[],[],[]
network_created=False
begin=time.monotonic()


def execute(argv,stdin=None,log=None,required=True):
    t=time.monotonic()
    r=subprocess.run(argv,cwd=ROOT,input=stdin,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    row={'argv':argv,'cwd':str(ROOT),'seconds':time.monotonic()-t,'returncode':r.returncode}
    if stdin is not None:row['stdin_sha256']=hashlib.sha256(stdin).hexdigest()
    if log:(out/log).write_bytes(r.stdout);row['output']=log
    commands.append(row)
    if required and r.returncode:raise RuntimeError('Own command failed: '+' '.join(argv[:3]))
    return r.stdout


def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition:errors.append(name)


HEALTH="""import json,time,urllib.request,sys
t=time.monotonic()
while True:
 try:
  with urllib.request.urlopen('http://127.0.0.1:'+sys.argv[1]+'/health',timeout=2) as r:
   if r.status==200 and json.loads(r.read())=={'status':'ok'}:break
 except Exception:
  if time.monotonic()-t>50:raise
  time.sleep(.05)
print(json.dumps({'status':200,'seconds':time.monotonic()-t}))
"""
try:
    image_info=json.loads(execute(['docker','image','inspect',image]))[0]
    check('Retained complete image identity matches clean-build proof',image_info['Id']==prior['resources'][0]['image'])
    probe=execute(['git','show',args.probe_revision+':evidence/interface-engineer/stage-1-json-deep-http-probe.py'])
    clone=Path(proof['clone'])
    check('Prior exact clean clone retained',subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone).decode().strip()==args.revision and subprocess.check_output(['git','status','--porcelain'],cwd=clone)==b'')
    execute(['docker','network','create','--internal',network],log='network.log')
    network_created=True
    urls=[]
    for i,port in enumerate((8080,9090)):
        name=resource+'-'+str(i)
        assert len(name)<=63
        argv=['docker','run','-d','--name',name,'--network',network,'--cpus','2','--memory','2g','-p',str(18236+i)+':'+str(port)]
        if i:argv+=['-e','PORT=9090']
        launch=time.monotonic()
        execute(argv+[image],log='run-'+str(i)+'.log')
        created.append(name)
        ready=json.loads(execute(['docker','exec',name,'python','-c',HEALTH,str(port)],log='health-'+str(i)+'.json'))
        elapsed=time.monotonic()-launch
        check('Actual service healthy within60s '+str(i),ready['status']==200 and elapsed<60)
        info=json.loads(execute(['docker','inspect',name]))[0]
        check('Offline constrained no-mount service '+str(i),info['HostConfig']['NanoCpus']==2000000000 and info['HostConfig']['Memory']==2147483648 and not info['Mounts'])
        hashes=json.loads(execute(['docker','exec',name,'python','-c',"import pathlib,hashlib,json;print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').glob('*.py')}))"],log='hash-'+str(i)+'.json'))
        check('Actual core/server/module match named coherent source '+str(i),all(hashes[n]==proof['source_hashes'][n] for n in ('core.py','server.py','json_codec.py')))
        listen=execute(['docker','exec',name,'python','-c',"import pathlib;print(pathlib.Path('/proc/net/tcp').read_text())"],log='listen-'+str(i)+'.txt')
        check('All-interface actual selected PORT '+str(i),('00000000:'+f'{port:04X}').encode() in listen)
        resources.append({'name':name,'image':info['Image'],'source_revision':args.revision,'source_hashes':hashes,
                          'nano_cpus':info['HostConfig']['NanoCpus'],'memory':info['HostConfig']['Memory'],'mounts':info['Mounts'],
                          'network':info['HostConfig']['NetworkMode'],'port':port,'host_port':18236+i,'health_from_launch_seconds':elapsed})
        urls.append('http://'+name+':'+str(port))
    check('Network has no outbound routing',json.loads(execute(['docker','network','inspect',network]))[0]['Internal'] is True)
    result=json.loads(execute(['docker','run','--rm','-i','--name',resource+'-client','--network',network,'--cpus','2','--memory','2g','--entrypoint','python',image,'-',*urls],stdin=probe,log='deep-http.json',required=False))
    check('Own real deep HTTP suite passes',result['failed']==0)
    (out/'summary.json').write_text(json.dumps({'candidate':args.revision,'probe_revision':args.probe_revision,'source_run':str(source_run),
         'retained_image':image_info['Id'],'rebuild':False,'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'probe_sha256':hashlib.sha256(probe).hexdigest(),'deep_http':{k:result[k] for k in ('depth','client_recursion_limit','operations','assertions','passed','failed','seconds','max_request_seconds','max_body_bytes')},'runtime_checks':checks},indent=2)+'\n')
except Exception as exc:
    errors.append(type(exc).__name__+': '+str(exc))
finally:
    cleanup=[]
    for name in reversed(created):
        execute(['docker','logs',name],log='logs-'+name[-1]+'.txt',required=False)
        execute(['docker','rm','-f',name],log='cleanup-'+name[-1]+'.log',required=False)
        cleanup.append(commands[-1])
    if network_created:
        execute(['docker','network','rm',network],log='cleanup-network.log',required=False)
        cleanup.append(commands[-1])
    if any(r['returncode'] for r in cleanup):errors.append('Own cleanup failed')
    seconds=time.monotonic()-begin
    (out/'run.json').write_text(json.dumps({'candidate':args.revision,'probe_revision':args.probe_revision,'source_run':str(source_run),'image':image,
        'rebuild':False,'commands':commands,'checks':checks,'resources':resources,'errors':errors,'cleanup':cleanup,'seconds':seconds,
        'model':'configured gpt-6.1-sol','actual_override_effort_usage_spend':'unknown'},indent=2)+'\n')
    print(json.dumps({'candidate':args.revision,'out':str(out),'seconds':seconds,'errors':errors}))
sys.exit(1 if errors else 0)
