"""Own scoped source, artifact, raw-transfer and cleanup audit; no service execution."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',required=True)
    p.add_argument('--run-dir',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--preserve-dir',action='append',default=[])
    args=p.parse_args();sys.set_int_max_str_digits(0)
    root=Path(__file__).resolve().parents[2];output=root/args.out
    assert not output.exists(),'Preserve prior proof outputs'
    run=root/args.run_dir
    runtime=json.loads((run/'runtime-report.json').read_bytes())
    browser=json.loads((run/'browser-report.json').read_bytes())
    git=lambda *argv:subprocess.check_output(['git',*argv],cwd=root)
    assert runtime['candidate']==browser['candidate']==args.candidate
    assert browser['passed']==browser['total'] and browser['total']>=84
    assert runtime['verdict']=='PASS'
    probe=git('show',runtime['probe_revision']+':evidence/interface-engineer/stage-4-browser-probe.py')
    assert (run/'executed-probe.py').read_bytes()==probe
    assert hashlib.sha256(probe).hexdigest()==runtime['probe_sha256']
    assert not git('-C',runtime['clone'],'status','--porcelain').strip()
    assert git('-C',runtime['clone'],'rev-parse','HEAD').decode().strip()==args.candidate
    assert not git('diff',args.candidate,'--','stage-1','stage-2','stage-3','stage-4').strip()
    for stage,revision in [('stage-1','75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'),('stage-2','4dba10246b07b2dda19de260d529f9d94ba0a1ed'),('stage-3','91e2c471acded1b861b3fec725f202297b1c6740')]:
        for path in git('ls-tree','-r','--name-only',revision,stage).decode().splitlines():
            assert (root/path).read_bytes()==git('show',revision+':'+path)
    assert len(runtime['resources'])==8
    assert all(v['cpus']==2 and v['memory_bytes']==2147483648 and not v['mounts'] for v in runtime['resources'].values())
    for v in runtime['startup'].values():assert v['source_inspection_occurs_after_health'] and v['seconds_to_health_command_return']<60
    migrations=[x for x in browser['trace'] if x['scenario']=='raw-upgrade-transfer']
    assert len(migrations)>=10
    for x in migrations:assert x['decoded'] is False and x['export_bytes']==x['import_bytes'] and x['export_sha256']==x['import_sha256']
    mixed=[x for x in browser['trace'] if x['scenario']=='raw-mixed-roundtrip'];assert len(mixed)==len(migrations)
    assert all(x['decoded'] is False for x in mixed)
    series=[x for x in browser['trace'] if x['scenario']=='stage3-series'];assert len(series)==3
    for x in series:assert x['decoded'] is False and x['export_bytes']==x['import_bytes'] and x['export_sha256']==x['import_sha256']
    current=[x for x in browser['trace'] if x['scenario']=='stage4-raw-transfer'];assert len(current)>=9
    for x in current:assert x['decoded'] is False and x['export_bytes']==x['import_bytes'] and x['export_sha256']==x['import_sha256']
    counts={'json_files':0,'dict_records':0,'embedded_json_strings':0};findings=[];manifest=[]
    private={'password','password_hash','token','tokens','state','authorization'}
    def inspect(v,path,embedded=False):
        if isinstance(v,dict):
            counts['dict_records']+=1
            for k,value in v.items():
                if k in private:findings.append({'path':path,'field':k})
                inspect(value,path+'/'+k,embedded)
        elif isinstance(v,list):
            for i,value in enumerate(v):inspect(value,path+'/'+str(i),embedded)
        elif isinstance(v,str) and not embedded and v.lstrip().startswith(('{','[')):
            try:value=json.loads(v)
            except (ValueError,RecursionError):return
            counts['embedded_json_strings']+=1;inspect(value,path+'/embedded-json',True)
    directories=[run,*[root/x for x in args.preserve_dir]]
    cleanup=[]
    for folder in directories:
        for file in sorted(folder.rglob('*')):
            if not file.is_file():continue
            raw=file.read_bytes();manifest.append({'path':str(file.relative_to(root)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            if file.suffix=='.json':counts['json_files']+=1;inspect(json.loads(raw),str(file.relative_to(root)))
        if (folder/'runtime-report.json').is_file():
            rr=json.loads((folder/'runtime-report.json').read_bytes())
            rows=[x for x in rr['commands'] if x.get('log','').startswith('cleanup-')]
            assert len(rows)==9 and all(x['exit']==0 for x in rows)
            cleanup.append({'path':str(folder.relative_to(root)),'count':9,'exits':[x['exit'] for x in rows]})
    assert not findings,findings
    proof={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'owner':'Interface Engineer','candidate':args.candidate,
           'stage4_tree':git('rev-parse',args.candidate+':stage-4').decode().strip(),
           'source_probe_resource_clone_bindings_passed':True,'accepted_stage1_stage2_stage3_unchanged':True,
           'complete_scenarios':browser['total'],'assertions':browser['assertions'],
           'raw_upgrade_transfers':len(migrations),'raw_mixed_roundtrips':len(mixed),'raw_series_transfers':len(series),'raw_stage4_transfers':len(current),
           'startup':runtime['startup'],'cleanup':cleanup,'manifest':manifest,'manifest_files':len(manifest),
           'genuine_screenshots':len(list(run.glob('*.png'))),
           'privacy':{'counts':counts,'raw_private_payload_findings':findings,
                      'excluded':'source/log strings, peer evidence and genuine final room export; synthetic credentials remain in authored test source'},
           'direct_API_operations':browser['direct_http_operations'],'browser_originated_requests':browser['browser_originated_requests'],
           'route_forwarding_operations':browser['forwarded_fetch_operations'],
           'max_measured_direct_forward_request_seconds':max(x['seconds'] for x in browser['http_trace']),
           'harness':'Codex','configured_model':'gpt-6.1-sol','actual_model_effort_usage_spend':'unknown'}
    output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:proof[k] for k in ['candidate','manifest_files','genuine_screenshots','complete_scenarios','assertions','privacy']}))


if __name__=='__main__':main()
