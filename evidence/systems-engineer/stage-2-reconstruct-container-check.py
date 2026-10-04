"""Own exact-commit complete-context Stage 2/genuine origins orchestration."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

p=argparse.ArgumentParser()
p.add_argument('--revision',required=True)
p.add_argument('--probe-revision',required=True)
p.add_argument('--out',required=True)
a=p.parse_args()
repo=Path.cwd().resolve();workspace=repo.parents[1]
out=Path(a.out).resolve();out.relative_to(repo/'evidence/systems-engineer')
out.mkdir(parents=True,exist_ok=False)
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f').lower()
prefix='systems-engineer-s2-reconstruct-'+stamp
clone=workspace/'band-work'/prefix
network=prefix+'-net';image=prefix+':current';client_image=prefix+':client'
created=[];contexts=[];network_created=False
began=time.monotonic()
record={'started_utc':datetime.now(timezone.utc).isoformat(),'commands':[], 'services':[],
        'clients':[],'cleanup':[],'clone':str(clone),'highest_accepted':1,
        'stage2_accepted':False,'configured_model':'gpt-6.1-sol','actual_usage_spend':'unknown',
        'scope':'own constrained complete-context API/helper probes; browser review separate'}
def run(argv,*,timeout=120,required=True):
    start=time.monotonic()
    r=subprocess.run(argv,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    log=out/('command-%03d.log'%len(record['commands']));log.write_bytes(r.stdout)
    record['commands'].append({'argv':argv,'returncode':r.returncode,'seconds':time.monotonic()-start,'log':str(log)})
    if required and r.returncode:raise RuntimeError('Command failed: '+str(log))
    return r.stdout
def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def tree(revision,folder,target):
    paths=run(['git','ls-tree','-r','--name-only',revision,'--',folder]).decode().splitlines()
    manifest={}
    for path in paths:
        relative=Path(path).relative_to(folder)
        destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(run(['git','show',revision+':'+path]))
        manifest[str(relative)]=hashfile(destination)
    return manifest
def inspect(name):
    d=json.loads(run(['docker','inspect',name]))[0];h=d['HostConfig']
    assert h['NanoCpus']==2000000000 and h['Memory']==2147483648 and d['Mounts']==[]
    assert h['NetworkMode']==network
    return {'name':name,'image_id':d['Image'],'cpu':2,'memory_bytes':h['Memory'],
            'mounts':[],'network':network,'port_bindings':h['PortBindings']}
def health(name,port):
    code=("import time,urllib.request\nfor i in range(120):\n try:\n"
          "  assert urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=.5).status==200\n"
          "  break\n except Exception: time.sleep(.05)\nelse: raise RuntimeError('health deadline')"%port)
    run(['docker','exec',name,'python','-c',code],timeout=60)
def client(label,args,artifacts):
    name=prefix+'-'+label
    run(['docker','create','--name',name,'--network',network,'--cpus','2','--memory','2g',
         client_image,'python','-B',*args]);created.append(name)
    resource=inspect(name)
    run(['docker','start',name]);code=int(run(['docker','wait',name],timeout=180).decode().strip())
    (out/(label+'.log')).write_bytes(run(['docker','logs',name]))
    item={'label':label,'exit_code':code,'resource':resource,'artifacts':[]}
    for source,target in artifacts:
        run(['docker','cp',name+':'+source,str(out/target)],required=False)
        item['artifacts'].append(target)
    record['clients'].append(item)

try:
    candidate=run(['git','rev-parse',a.revision+'^{commit}']).decode().strip()
    probe_revision=run(['git','rev-parse',a.probe_revision+'^{commit}']).decode().strip()
    record.update(candidate=candidate,probe_revision=probe_revision)
    run(['git','clone','--no-hardlinks','--no-checkout',str(repo),str(clone)])
    run(['git','-C',str(clone),'checkout','--detach',candidate])
    assert run(['git','-C',str(clone),'status','--porcelain'])==b''
    record['clean_clone_before']=True
    stage=clone/'stage-2'
    record['current_context_sha256']={str(f.relative_to(stage)):hashfile(f) for f in stage.rglob('*') if f.is_file()}
    run(['docker','build','-t',image,str(stage)],timeout=300)
    specs=[('current-a',8080,18170,image,candidate,'stage-2'),
           ('current-b',18171,18171,image,candidate,'stage-2')]
    historical=[('accepted','75005d57fe0904753eac4eab5bf4e4c9a78b6d1b','stage-1',18172),
                ('legacy','49287b4a5a1481f995c470ccae31776f03d4b863','stage-1',18173),
                ('old','16aee9f0ea10de5b8fa81a84429cc337c3c4490f','stage-2',18174)]
    record['historical_context_sha256']={}
    for label,revision,folder,port in historical:
        context=Path(tempfile.mkdtemp(prefix=prefix+'-'+label+'-',dir=workspace/'band-work'));contexts.append(context)
        record['historical_context_sha256'][label]=tree(revision,folder,context)
        tag=prefix+':'+label
        run(['docker','build','-t',tag,str(context)],timeout=300)
        specs.append((label,port,port,tag,revision,folder))
    context=Path(tempfile.mkdtemp(prefix=prefix+'-client-',dir=workspace/'band-work'));contexts.append(context)
    probes=('stage-2-reconstruct-http-client.py','stage-2-builder-probes.py','stage-1-builder-probes.py',
            'stage-1-json-http-probes.py','stage-1-2-decimal-probes.py','stage-2-reconstruct-arithmetic-probes.py')
    record['probe_sha256']={}
    for filename in probes:
        (context/filename).write_bytes(run(['git','show',probe_revision+':evidence/systems-engineer/'+filename]))
        record['probe_sha256'][filename]=hashfile(context/filename)
    (context/'Dockerfile').write_text('FROM '+image+'\nWORKDIR /probe\nCOPY *.py ./\n')
    run(['docker','build','-t',client_image,str(context)],timeout=180)
    run(['docker','network','create','--internal',network]);network_created=True
    assert json.loads(run(['docker','network','inspect',network]))[0]['Internal'] is True
    urls=[]
    for label,port,host_port,tag,revision,folder in specs:
        name=prefix+'-'+label
        launch=time.monotonic();launch_utc=datetime.now(timezone.utc).isoformat()
        cmd=['docker','run','-d','--name',name,'--network',network,'--cpus','2','--memory','2g',
             '-p',str(host_port)+':'+str(port)]
        if port!=8080:cmd+=['-e','PORT='+str(port)]
        run(cmd+[tag]);created.append(name)
        health(name,port)
        healthy=time.monotonic();healthy_utc=datetime.now(timezone.utc).isoformat()
        assert healthy-launch<60
        info=inspect(name)
        info.update(source_revision=revision,source_folder=folder,start_to_healthy_seconds=healthy-launch,
                    launch_utc=launch_utc,healthy_utc=healthy_utc,source_sha256={})
        for filename in ('core.py','server.py','json_codec.py'):
            expected=run(['git','show',revision+':'+folder+'/'+filename],required=filename!='json_codec.py')
            if record['commands'][-1]['returncode']:continue
            actual=run(['docker','exec',name,'python','-c',
                 "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())"%filename]).decode().strip()
            assert actual==hashlib.sha256(expected).hexdigest()
            info['source_sha256'][filename]=actual
        record['services'].append(info);urls.append('http://'+name+':'+str(port))
    base,peer,accepted,legacy,old=urls
    client('reconstruction',['stage-2-reconstruct-http-client.py','--base',base,'--peer',peer,
       '--accepted',accepted,'--legacy',legacy,'--old',old,'--out','/tmp/systems-reconstruction'],
       [('/tmp/systems-reconstruction','reconstruction')])
    client('members',['stage-2-builder-probes.py','--url',base,'--destination-url',peer,'--source-url',accepted,
       '--trace','/tmp/systems-members.json'],[('/tmp/systems-members.json','member-oracle.json')])
    client('inherited',['stage-1-builder-probes.py','--stage','2','--url',base,'--destination-url',peer,'--legacy-url',legacy],[])
    client('numbers',['stage-1-json-http-probes.py','--base',base,'--peer',peer,'--legacy',legacy,'--old',old,
       '--out','/tmp/systems-numbers'],[('/tmp/systems-numbers','numbers')])
    client('digits',['stage-1-2-decimal-probes.py','--stage','2','--url',base,'--destination-url',peer,
       '--trace','/tmp/systems-digits.json'],[('/tmp/systems-digits.json','digits.json')])
    client('arithmetic',['stage-2-reconstruct-arithmetic-probes.py','--module','/app/json_codec.py',
       '--out','/tmp/systems-arithmetic.json'],[('/tmp/systems-arithmetic.json','arithmetic.json')])
    for label,path in (('reconstruction','reconstruction/trace.json'),('numbers','numbers/trace.json'),('digits','digits.json')):
        file=out/path
        record[label+'_summary']=json.loads(file.read_text()).get('summary') if file.exists() else None
    assert run(['git','-C',str(clone),'status','--porcelain'])==b''
    record['clean_clone_after']=True
    frozen=run(['git','diff',candidate,'75005d57fe0904753eac4eab5bf4e4c9a78b6d1b','--','stage-1'])
    assert frozen==b'';record['frozen_stage1_diff_empty']=True
    record['result']='passed' if all(c['exit_code']==0 for c in record['clients']) else 'failed'
except Exception as error:
    record['result']='failed';record['driver_exception']={'type':type(error).__name__,'message':str(error)}
finally:
    for name in reversed(created):
        run(['docker','logs',name],required=False)
        run(['docker','rm','-f',name],required=False)
        record['cleanup'].append({'resource':name,'returncode':record['commands'][-1]['returncode']})
    if network_created:
        run(['docker','network','rm',network],required=False)
        record['cleanup'].append({'resource':network,'returncode':record['commands'][-1]['returncode']})
    for context in contexts:shutil.rmtree(context)
    record['contexts_removed']=all(not c.exists() for c in contexts)
    record['wall_seconds']=time.monotonic()-began
    record['finished_utc']=datetime.now(timezone.utc).isoformat()
    (out/'runtime.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record.get(k) for k in ('candidate','result','reconstruction_summary','numbers_summary','digits_summary','wall_seconds','driver_exception')}))
    raise SystemExit(record.get('result')!='passed')
