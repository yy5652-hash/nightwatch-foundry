"""Own saved-evidence invariants and scoped JSON privacy audit; not a verifier."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--candidate',required=True)
p.add_argument('--runs',nargs='+',required=True)
p.add_argument('--out',default='evidence/systems-engineer/stage-2-reconstruct-evidence-audit.json')
a=p.parse_args()
repo=Path.cwd().resolve();destination=Path(a.out)
if destination.exists():raise RuntimeError('Evidence audit output must be unique')
candidate=subprocess.check_output(['git','rev-parse',a.candidate+'^{commit}'],text=True).strip()
accepted='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
folders=[Path(f) for f in a.runs]
manifest=[];objects=0;fingerprints=0;private=[];runs=[]
def sha(raw):return hashlib.sha256(raw).hexdigest()
for folder in folders:
    folder.resolve().relative_to(repo/'evidence/systems-engineer')
    for file in sorted(folder.rglob('*')):
        if not file.is_file():continue
        raw=file.read_bytes();manifest.append({'path':str(file),'bytes':len(raw),'sha256':sha(raw)})
        if file.suffix!='.json':continue
        parsed=json.loads(raw);stack=[parsed]
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
        # Preserve the first full observation as failed. The obsolete Stage 2
        # fractional expectation is independently inspected, never relabelled.
        assert folder.name=='systems-engineer-s2-reconstruct-service-01'
        assert [(c['label'],c['exit_code']) for c in data['clients'] if c['exit_code']] == [('digits',1)]
        digits=json.loads((folder/'digits.json').read_text())
        failed=[r['label'] for r in digits['assertions'] if not r['passed']]
        assert failed==['invalid base field HTTP 400','invalid base field error malformed_request']
    assert data['clean_clone_before'] and data['clean_clone_after'] and data['contexts_removed']
    assert len(data['services'])==5 and len(data['clients'])==6
    assert all(c['returncode']==0 for c in data['cleanup'])
    if data['result']=='passed':assert all(c['exit_code']==0 for c in data['clients'])
    for s in data['services']:
        assert s['cpu']==2 and s['memory_bytes']==2147483648 and s['mounts']==[] and s['start_to_healthy_seconds']<60
    assert subprocess.check_output(['git','diff',candidate,data['candidate'],'--','stage-2/core.py','stage-2/json_codec.py'])==b''
    assert subprocess.check_output(['git','-C',data['clone'],'status','--porcelain'])==b''
    own=json.loads((folder/'reconstruction/trace.json').read_text())
    assert own['summary']['failed']==0 and own['summary']['scenarios']==3
    exports=[e for e in own['events'] if e['path']=='/_test/export']
    assert exports and all(not e['decoded'] for e in exports)
    source_digests={e['response_sha256'] for e in exports}
    forwards=[e for e in own['events'] if e['path']=='/_test/import' and e['status']==204]
    assert forwards and all(e['request_sha256'] in source_digests for e in forwards)
    runs.append({'candidate':data['candidate'],'runtime':str(runtime),'original_result':data['result'],'wall_seconds':data['wall_seconds'],
      'summaries':{k:data.get(k) for k in ('reconstruction_summary','numbers_summary','digits_summary')},
      'raw_export_count':len(exports),'unchanged_successful_forwardings':len(forwards),
      'cleanup_count':len(data['cleanup']),'source_identity':data['services'],
      'maximum_request_seconds':own['summary']['maximum_request_seconds']})
assert private==[],private
assert any(r['original_result']=='passed' for r in runs)
frozen={}
for file in (repo/'stage-1').iterdir():
    if not file.is_file():continue
    committed=subprocess.check_output(['git','show',accepted+':stage-1/'+file.name])
    assert file.read_bytes()==committed
    frozen[file.name]=sha(committed)
assert len(frozen)==6
assert subprocess.check_output(['git','diff',accepted,candidate,'--','stage-1'])==b''
production={f:sha(subprocess.check_output(['git','show',candidate+':'+f]))
            for f in ('stage-2/core.py','stage-2/json_codec.py','stage-2/server.py')}
result={'kind':'own evidence audit; no independent acceptance','candidate':candidate,
  'checked_utc':datetime.now(timezone.utc).isoformat(),'highest_accepted':1,
  'files':len(manifest),'json_object_records':objects,'private_fingerprints':fingerprints,
  'raw_private_json_findings':private,'scope':'saved JSON values; source/log strings and full room export excluded',
  'manifest':manifest,'runs':runs,'frozen_stage1_sha256':frozen,'candidate_production_sha256':production}
destination.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('candidate','files','json_object_records','private_fingerprints','raw_private_json_findings')}))
