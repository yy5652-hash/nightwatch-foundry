"""Source-bound complete Stage 2 builds and own real browser upgrade probes."""
import argparse
import ast
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
WORKSPACE=ROOT.parent.parent
ACCEPTED='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
HISTORIC='49287b4a5a1481f995c470ccae31776f03d4b863'
OLD_S2='16aee9f0ea10de5b8fa81a84429cc337c3c4490f'
PROBE='evidence/interface-engineer/stage-2-browser-probe.py'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--revision',required=True)
    parser.add_argument('--probe-revision',required=True)
    parser.add_argument('--scenario-prefix',help='Own labelled supplement only; full run has no prefix')
    args=parser.parse_args()
    assert len(args.revision)==len(args.probe_revision)==40
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ').lower()
    out=ROOT/'evidence/interface-engineer'/('interface-engineer-s2-reconstructed-'+stamp)
    out.mkdir()
    clone=ROOT.parent/('interface-engineer-s2-reconstructed-'+stamp)
    # Each container name is one DNS label; keep every service label <=63 bytes.
    commands=[]; started=[]; network='interface-engineer-s2r-'+stamp
    created_network=False; contexts=[]; beginning=time.perf_counter()
    report={'candidate':args.revision,'probe_revision':args.probe_revision,'supplemental_scope_prefix':args.scenario_prefix,'accepted_stage1':ACCEPTED,'historic_stage1':HISTORIC,'old_stage2':OLD_S2,'clone':str(clone),'out':str(out),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'harness':'Codex','configured_model':'gpt-6.1-sol','actual_model_override_effort_usage_cost':'unknown','commands':commands,'startup':{},'resources':{}}
    def run(argv,label,check=True,input_bytes=None,binary=False):
        start=time.perf_counter()
        r=subprocess.run(argv,cwd=ROOT,input=input_bytes,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/(label+'.log')).write_bytes(r.stdout)
        row={'argv':argv,'exit':r.returncode,'seconds':time.perf_counter()-start,'log':label+'.log'}
        if input_bytes is not None:row.update(stdin_bytes=len(input_bytes),stdin_sha256=hashlib.sha256(input_bytes).hexdigest())
        commands.append(row)
        if check and r.returncode:raise RuntimeError(label+' failed; preserved log '+str(out/(label+'.log')))
        return r.stdout if binary else r.stdout.decode('utf-8').strip()
    def blob(revision,path):
        argv=['git','show',revision+':'+path]
        b=subprocess.check_output(argv,cwd=ROOT)
        commands.append({'argv':argv,'exit':0,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
        return b
    def image_hashes(name,label):
        code="import pathlib,hashlib,json;print(json.dumps({str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').rglob('*') if p.is_file() and p.suffix in ('.py','.js','.css','.html')}))"
        return json.loads(run(['docker','exec',name,'python','-c',code],label))
    try:
        names=run(['git','ls-tree','-r','--name-only',args.revision,'stage-2'],'source-file-list').splitlines()
        hashes={p:hashlib.sha256(blob(args.revision,p)).hexdigest() for p in names}
        for p in names:assert (ROOT/p).read_bytes()==blob(args.revision,p),'uncommitted source '+p
        frozen_names=run(['git','ls-tree','-r','--name-only',ACCEPTED,'stage-1'],'frozen-file-list').splitlines()
        for p in frozen_names:assert (ROOT/p).read_bytes()==blob(ACCEPTED,p),'frozen Stage1 changed '+p
        report['source_hashes']=hashes
        source=blob(args.probe_revision,PROBE); ast.parse(source)
        (out/'executed-probe.py').write_bytes(source)
        driver=Path(__file__).read_bytes();(out/'executed-driver.py').write_bytes(driver)
        report['driver_sha256']=hashlib.sha256(driver).hexdigest()
        report['probe_sha256']=hashlib.sha256(source).hexdigest()
        ast.parse(blob(args.revision,'stage-2/server.py'))
        run(['git','clone','--no-hardlinks','--no-checkout',str(ROOT),str(clone)],'clean-clone')
        run(['git','-C',str(clone),'checkout','--detach',args.revision],'clean-detach')
        assert not run(['git','-C',str(clone),'status','--porcelain'],'clone-clean-before')
        images={}
        specs=[('current',args.revision,'stage-2',clone/'stage-2'),('accepted',ACCEPTED,'stage-1',clone/'stage-1')]
        for label,revision,stage in [('historic',HISTORIC,'stage-1'),('old-stage2',OLD_S2,'stage-2')]:
            context=out/('interface-engineer-'+label+'-context');context.mkdir();contexts.append(context)
            files=run(['git','ls-tree','-r','--name-only',revision,stage],label+'-file-list').splitlines()
            for p in files:
                target=context/Path(p).relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob(revision,p))
            specs.append((label,revision,stage,context))
        source_by_label={}
        for label,revision,stage,context in specs:
            images[label]='interface-engineer-tablekeeper-'+label+':reconstructed-'+stamp
            run(['docker','build','-t',images[label],str(context)],'build-'+label)
            source_by_label[label]={str(p.relative_to(context)):hashlib.sha256(p.read_bytes()).hexdigest() for p in context.rglob('*') if p.is_file() and p.suffix in ('.py','.js','.css','.html')}
        report['image_ids']={label:run(['docker','image','inspect','--format','{{.Id}}',img],'image-'+label) for label,img in images.items()}
        run(['docker','network','create','--internal',network],'network-create');created_network=True
        assert json.loads(run(['docker','network','inspect',network],'network-inspect'))[0]['Internal']
        services=[('current',images['current'],9090,18250),('destination',images['current'],8080,18251),('accepted',images['accepted'],8080,18252),('historic',images['historic'],8080,18253),('old-stage2',images['old-stage2'],8080,18254)]
        names_by_label={}
        for label,img,port,hostport in services:
            name=network+'-'+label;names_by_label[label]=name;launched=time.perf_counter();launch_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
            assert len(name.encode('ascii'))<=63
            argv=['docker','run','-d','--name',name,'--network',network,'--cpus','2','--memory','2g','-p',str(hostport)+':'+str(port)]
            if port!=8080:argv+=['-e','PORT='+str(port)]
            argv+=[img];run(argv,'start-'+label);started.append(name)
            health="import json,time,urllib.request;\nfor i in range(100):\n try:\n  r=urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=1);assert r.status==200 and json.load(r)=={'status':'ok'};print('healthy');break\n except Exception:\n  time.sleep(.05)\nelse:raise RuntimeError('health failed')"%port
            run(['docker','exec',name,'python','-c',health],'health-'+label)
            report['startup'][label]={'seconds_to_health_command_return':time.perf_counter()-launched,'launch_utc':launch_utc,'healthy_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_inspection_occurs_after_health':True,'port':port}
            assert report['startup'][label]['seconds_to_health_command_return']<60
            obj=json.loads(run(['docker','inspect',name],'inspect-'+label))[0]
            assert obj['HostConfig']['NanoCpus']==2000000000 and obj['HostConfig']['Memory']==2147483648 and not obj['Mounts']
            assert list(obj['NetworkSettings']['Networks'])==[network]
            report['resources'][label]={'cpus':2,'memory_bytes':2147483648,'mounts':[],'internal_network':network}
            actual=image_hashes(name,'packaged-'+label)
            expected=source_by_label['current' if label=='destination' else label]
            for path,digest in expected.items():assert actual[path]==digest,(label,path)
        runner=network+'-probe';started.append(runner)
        assert len(runner.encode('ascii'))<=63
        argv=['docker','run','-i','--name',runner,'--network',network,'--cpus','2','--memory','2g']
        env={'S2_BASE':'http://'+names_by_label['current']+':9090','S2_DEST_BASE':'http://'+names_by_label['destination']+':8080','S1_BASE':'http://'+names_by_label['accepted']+':8080','S1_REVISION':ACCEPTED,'S1_HIST_BASE':'http://'+names_by_label['historic']+':8080','S1_HIST_REVISION':HISTORIC,'S2_OLD_BASE':'http://'+names_by_label['old-stage2']+':8080','S2_OLD_REVISION':OLD_S2,'CANDIDATE':args.revision,'PROBE_OUT':'/tmp/interface-engineer-out'}
        if args.scenario_prefix:env['S2_SCENARIO_PREFIX']=args.scenario_prefix
        for key,value in env.items():argv+=['-e',key+'='+value]
        launcher="import sys;exec(compile(sys.stdin.buffer.read(),'sealed-interface-probe.py','exec'))"
        argv+=['df-harness-runner:latest','python','-B','-c',launcher]
        run(argv,'browser',False,input_bytes=source)
        probe_resource=json.loads(run(['docker','inspect',runner],'inspect-probe'))[0]
        assert probe_resource['HostConfig']['NanoCpus']==2000000000 and probe_resource['HostConfig']['Memory']==2147483648 and not probe_resource['Mounts']
        assert list(probe_resource['NetworkSettings']['Networks'])==[network]
        report['resources']['probe']={'cpus':2,'memory_bytes':2147483648,'mounts':[],'internal_network':network}
        run(['docker','cp',runner+':/tmp/interface-engineer-out/.',str(out)],'copy-browser-evidence')
        result=json.loads((out/'browser-report.json').read_text())
        report['browser_summary']={k:result[k] for k in ['passed','total','assertions','seconds','browser_version']}
        report['verdict']='PASS' if result['passed']==result['total'] else 'FAIL'
        for label,name in names_by_label.items():
            obj=json.loads(run(['docker','inspect',name],'final-state-'+label))[0]
            assert obj['State']['Running'] and not obj['State']['OOMKilled']
        assert not run(['git','-C',str(clone),'status','--porcelain'],'clone-clean-after')
        for p in frozen_names:assert (ROOT/p).read_bytes()==blob(ACCEPTED,p)
        report['frozen_stage1_unchanged']=True
    except Exception as exc:
        report['verdict']='ERROR';report['error']=str(exc)
    finally:
        for name in reversed(started):
            run(['docker','logs',name],'logs-'+name,False)
            run(['docker','rm','-f',name],'cleanup-'+name,False)
        if created_network:run(['docker','network','rm',network],'cleanup-network',False)
        for context in contexts:shutil.rmtree(context)
        report['temporary_contexts_removed']=True
        report['total_seconds']=time.perf_counter()-beginning
        report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        (out/'runtime-report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'out':str(out),'candidate':args.revision,'verdict':report.get('verdict'),'summary':report.get('browser_summary'),'error':report.get('error'),'seconds':report['total_seconds']},indent=2))
    return 0 if report.get('verdict')=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
