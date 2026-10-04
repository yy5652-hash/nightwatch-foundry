"""Build/run exact committed sources and own browser probes without host installs."""
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import time
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[2]
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ').lower()
OUT=ROOT/'evidence/interface-engineer'/('interface-engineer-s2-'+STAMP)
OUT.mkdir()
COMMANDS=[]
def run(args,name,check=True):
    started=time.perf_counter()
    result=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (OUT/(name+'.log')).write_text(result.stdout)
    COMMANDS.append({'argv':args,'exit':result.returncode,'seconds':round(time.perf_counter()-started,3),'log':name+'.log'})
    if check and result.returncode: raise RuntimeError(name+' failed; '+str(OUT/(name+'.log')))
    return result.stdout.strip()
candidate=run(['git','rev-parse','HEAD'],'revision')
paths=['stage-2/server.py','stage-2/core.py','stage-2/Dockerfile','stage-2/.dockerignore','stage-2/RUN.md','stage-2/web/index.html','stage-2/web/app.css','stage-2/web/app.js']
hashes={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in paths}
for path in paths:
    expected=subprocess.run(['git','show',candidate+':'+path],cwd=ROOT,stdout=subprocess.PIPE,check=True).stdout
    if expected!=(ROOT/path).read_bytes(): raise RuntimeError('uncommitted candidate source '+path)
for path in ['server.py','core.py','Dockerfile','.dockerignore','RUN.md']:
    expected=subprocess.run(['git','show','2a4b0408a3453bc87d86bca3d0ec571f479e03ca:stage-1/'+path],cwd=ROOT,stdout=subprocess.PIPE,check=True).stdout
    if expected!=(ROOT/'stage-1'/path).read_bytes(): raise RuntimeError('frozen Stage1 differs: '+path)
image='interface-engineer-tablekeeper-s2:'+STAMP
legacy_image='interface-engineer-tablekeeper-s1:upgrade-'+STAMP
historic_revision='49287b4a5a1481f995c470ccae31776f03d4b863'
historic_image='interface-engineer-tablekeeper-s1:historic-'+STAMP
historic_context=OUT/'interface-engineer-historic-source'
network='interface-engineer-s2-'+STAMP
service=network+'-service';legacy=network+'-legacy';default=network+'-default';runner=network+'-probe'
historic=network+'-historic'
started=[];created_network=False
report={'candidate':candidate,'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_hashes':hashes,'model_configured':'gpt-6.1-sol','harness':'Codex','runtime_model_effort_usage_spend':'unknown','out':str(OUT)}
report['probe_hashes']={p:hashlib.sha256((ROOT/'evidence/interface-engineer'/p).read_bytes()).hexdigest() for p in ['stage-2-browser-probe.py','stage-2-container-check.py']}
try:
    historic_context.mkdir()
    historic_hashes={}
    for filename in ['server.py','core.py','Dockerfile','.dockerignore','RUN.md']:
        argv=['git','show',historic_revision+':stage-1/'+filename]
        source=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,check=True).stdout
        (historic_context/filename).write_bytes(source)
        historic_hashes[filename]=hashlib.sha256(source).hexdigest()
        COMMANDS.append({'argv':argv,'exit':0,'source_sha256':historic_hashes[filename]})
    report['historic_source_revision']=historic_revision
    report['historic_source_hashes']=historic_hashes
    run(['docker','build','-t',image,'stage-2'],'build-stage2')
    run(['docker','build','-t',legacy_image,'stage-1'],'build-accepted-stage1')
    run(['docker','build','-t',historic_image,str(historic_context)],'build-genuine-historic-stage1')
    run(['docker','network','create','--internal',network],'network-create');created_network=True
    before=time.perf_counter()
    for name,img,port,host in [(service,image,'9090','18210'),(legacy,legacy_image,'8080','18211'),(default,image,None,None),(historic,historic_image,None,None)]:
        args=['docker','run','-d','--name',name,'--network',network,'--cpus','2','--memory','2g']
        if port:args+=['-e','PORT='+port,'-p',host+':'+port]
        args+=[img]
        run(args,'start-'+name);started.append(name)
    health_code="import urllib.request,json; r=urllib.request.urlopen('http://127.0.0.1:9090/health',timeout=2); assert r.status==200 and json.load(r)=={'status':'ok'}; print('override PORT PASS')"
    for attempt in range(30):
        result=subprocess.run(['docker','exec',service,'python','-c',health_code],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if result.returncode==0:
            (OUT/'override-health.log').write_text(result.stdout);break
        (OUT/('override-health-attempt-'+str(attempt)+'.log')).write_text(result.stdout)
        time.sleep(.2)
    else:raise RuntimeError('service not healthy in startup window')
    report['override_healthy_seconds']=round(time.perf_counter()-before,3)
    run(['docker','exec',default,'python','-c',"import urllib.request,json; r=urllib.request.urlopen('http://127.0.0.1:8080/health'); assert r.status==200 and json.load(r)=={'status':'ok'}; print('default PORT PASS')"],'default-health')
    for name in started:
        raw=run(['docker','inspect',name],'inspect-'+name)
        obj=json.loads(raw)[0]
        assert obj['HostConfig']['NanoCpus']==2000000000 and obj['HostConfig']['Memory']==2147483648
        assert list(obj['NetworkSettings']['Networks'])==[network]
    raw=run(['docker','network','inspect',network],'network-inspect');assert json.loads(raw)[0]['Internal']
    code="import hashlib,pathlib,json; print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').rglob('*') if p.is_file() and p.suffix in ('.py','.js','.css','.html')}))"
    image_hashes=json.loads(run(['docker','exec',service,'python','-c',code],'image-hashes'))
    for path,digest in hashes.items():
        if path.endswith(('Dockerfile','.dockerignore','RUN.md')):continue
        assert image_hashes['/app/'+path[len('stage-2/'):]]==digest
    report['image_hashes_match']=True
    old_hashes=json.loads(run(['docker','exec',historic,'python','-c',code],'historic-image-hashes'))
    for filename in ['server.py','core.py']:
        assert old_hashes['/app/'+filename]==historic_hashes[filename]
    report['historic_image_hashes_match']=True
    args=['docker','run','--rm','--name',runner,'--network',network,'--cpus','2','--memory','2g',
        '-v',str(ROOT/'evidence/interface-engineer/stage-2-browser-probe.py')+':/work/probe.py:ro',
        '-v',str(OUT)+':/out','-e','S2_BASE=http://'+service+':9090','-e','S1_BASE=http://'+legacy+':8080',
        '-e','S1_HIST_BASE=http://'+historic+':8080','-e','S1_HIST_REVISION='+historic_revision,
        '-e','CANDIDATE='+candidate,'-e','PROBE_OUT=/out','df-harness-runner:latest','python','-B','/work/probe.py']
    output=run(args,'browser',check=False)
    result=json.loads((OUT/'browser-report.json').read_text())
    report['browser_summary']={k:result[k] for k in ['passed','total','assertions','seconds','browser_version']}
    report['verdict']='PASS' if result['passed']==result['total'] else 'FAIL'
    print(output)
except Exception as exc:
    report['verdict']='ERROR';report['error']=str(exc)
    raise
finally:
    for name in reversed(started):
        run(['docker','logs',name],'logs-'+name,check=False)
        run(['docker','rm','-f',name],'cleanup-'+name,check=False)
    if created_network:run(['docker','network','rm',network],'cleanup-network',check=False)
    if historic_context.exists():shutil.rmtree(historic_context)
    report['historic_context_removed']=not historic_context.exists()
    report['commands']=COMMANDS
    report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUT/'runtime-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(str(OUT))
raise SystemExit(0 if report['verdict']=='PASS' else 1)
