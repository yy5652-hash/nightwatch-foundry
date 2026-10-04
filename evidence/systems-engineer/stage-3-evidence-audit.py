"""Systems saved-evidence/source/resource audit; not independent acceptance."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--runs',nargs='+',required=True);p.add_argument('--out',required=True);a=p.parse_args()
repo=Path.cwd().resolve();destination=Path(a.out);assert not destination.exists()
candidate=subprocess.check_output(['git','rev-parse',a.candidate+'^{commit}']).decode().strip()
manifest=[];objects=0;fingerprints=0;private=[];runs=[]
def sha(raw):return hashlib.sha256(raw).hexdigest()
for directory in a.runs:
    folder=Path(directory);folder.resolve().relative_to(repo/'evidence/systems-engineer')
    for file in sorted(folder.rglob('*')):
        if not file.is_file():continue
        raw=file.read_bytes();manifest.append({'path':str(file),'bytes':len(raw),'sha256':sha(raw)})
        if file.suffix!='.json':continue
        stack=[json.loads(raw)]
        while stack:
            value=stack.pop()
            if isinstance(value,dict):
                objects+=1
                for key,item in value.items():
                    if key.lower() in ('password','password_hash','token','tokens','state','authorization'):
                        if isinstance(item,dict) and set(item) in ({'fingerprint'},{'private_state_sha256'}):fingerprints+=1
                        else:private.append({'path':str(file),'key':key})
                    stack.append(item)
            elif isinstance(value,list):stack.extend(value)
    runtime=folder/'runtime.json'
    if not runtime.exists():continue
    data=json.loads(runtime.read_text())
    if data['result']!='passed':
        assert folder.name=='systems-engineer-s3-service-01'
        assert [(c['label'],c['exit_code']) for c in data['clients'] if c['exit_code']] == [('inherited',1)]
        log=(folder/'inherited.log').read_text();assert "KeyError: 'numeric_profile'" in log and 'errors=1' in log
    else:assert all(c['exit_code']==0 for c in data['clients'])
    assert data['clean_clone_before'] and data['clean_clone_after'] and data['contexts_removed']
    assert data['frozen_stage1_diff_empty'] and data['frozen_stage2_diff_empty']
    assert len(data['services'])==6 and len(data['clients'])==6 and len(data['cleanup'])==13
    assert all(c['returncode']==0 for c in data['cleanup'])
    for service in data['services']:
        assert service['cpu']==2 and service['memory_bytes']==2147483648 and service['mounts']==[] and service['start_to_healthy_seconds']<60
    for client in data['clients']:
        resource=client['resource'];assert resource['cpu']==2 and resource['memory_bytes']==2147483648 and resource['mounts']==[]
    assert subprocess.check_output(['git','diff',candidate,data['candidate'],'--','stage-3/core.py','stage-3/json_codec.py'])==b''
    assert subprocess.check_output(['git','-C',data['clone'],'status','--porcelain'])==b''
    deep=json.loads((folder/'deep/trace.json').read_text());assert deep['summary']['failed']==0
    exports=[e for e in deep['operations'] if e['path']=='/_test/export']
    assert exports and all(e['decoded'] is False for e in exports)
    forwards=[e for e in deep['operations'] if e['path']=='/_test/import' and e['status']==204]
    assert len(forwards)==7 and all(e['request_sha256'] in {s['response_sha256'] for s in exports} for e in forwards)
    assert all(t['decoded'] is False and t['export_sha256']==t['import_sha256'] and t['export_bytes']==t['import_bytes'] for t in deep['raw_transfers'])
    transitions=json.loads((folder/'transitions/trace.json').read_text());assert transitions['summary']['failed']==0 and transitions['summary']['errors']==0
    assert transitions['summary']['scenarios']==14
    runs.append({'candidate':data['candidate'],'protocol':data['probe_revision'],'runtime':str(runtime),'original_result':data['result'],
      'wall_seconds':data['wall_seconds'],'cleanup_count':len(data['cleanup']),'services':data['services'],
      'summaries':{k:data.get(k) for k in ('transitions_summary','numbers_summary','digits_summary','deep_summary')},'raw_successful_forwardings':len(forwards)})
assert not private,private
assert any(run['original_result']=='passed' for run in runs)
frozen={}
for stage,revision in ((1,'75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'),(2,'4dba10246b07b2dda19de260d529f9d94ba0a1ed')):
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'--','stage-'+str(stage)]).decode().splitlines()
    frozen[str(stage)]={}
    for path in paths:
        data=subprocess.check_output(['git','show',revision+':'+path]);assert Path(path).read_bytes()==data
        frozen[str(stage)][path]=sha(data)
    assert subprocess.check_output(['git','diff',revision,candidate,'--','stage-'+str(stage)])==b''
production={path:sha(subprocess.check_output(['git','show',candidate+':'+path])) for path in ('stage-3/core.py','stage-3/json_codec.py','stage-3/server.py')}
result={'kind':'own evidence/source/resource audit; no independent acceptance','candidate':candidate,'checked_utc':datetime.now(timezone.utc).isoformat(),
        'highest_accepted':2,'files':len(manifest),'json_object_records':objects,'private_fingerprints':fingerprints,'raw_private_json_findings':private,
        'scope':'owned saved JSON values only; source/log strings, peer evidence and genuine room export excluded','manifest':manifest,'runs':runs,
        'frozen_stage_sources':frozen,'candidate_production_sha256':production}
destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('candidate','files','json_object_records','private_fingerprints','raw_private_json_findings')}))
