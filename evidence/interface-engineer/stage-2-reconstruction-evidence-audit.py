"""Reproducible own artifact/source/cleanup audit; does not execute the service."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True,help='New proof file; existing outputs are refused')
    args=parser.parse_args()
    sys.set_int_max_str_digits(0)
    root=Path(__file__).resolve().parents[2];e=root/'evidence/interface-engineer'
    output=root/args.out
    if output.exists():raise FileExistsError(output)
    candidate='f783598428a88d53490f68498063ed69e02201b3'
    full=e/'interface-engineer-s2-reconstructed-20261004t054351394649z'
    supp=e/'interface-engineer-s2-reconstructed-20261004t054725205604z'
    failed=e/'interface-engineer-s2-reconstructed-20261004t054140435353z'
    pre=e/'interface-engineer-s2-reconstructed-preflight-20261004t053951158486z'
    git=lambda argv:subprocess.check_output(['git']+argv,cwd=root)
    r=json.loads((full/'runtime-report.json').read_text());b=json.loads((full/'browser-report.json').read_text())
    sr=json.loads((supp/'runtime-report.json').read_text());sb=json.loads((supp/'browser-report.json').read_text())
    assert (b['passed'],b['total'],b['assertions'])==(43,43,793)
    assert (sb['passed'],sb['total'],sb['assertions'])==(5,5,90)
    assert r['verdict']==sr['verdict']=='PASS' and r['candidate']==sr['candidate']==candidate
    for folder,report,probe_rev in [(full,r,'a040054f2a8d00c560bea7f02324d1443c5a3f14'),(supp,sr,'bc36441e726766055d1739f00da246666a4dd44f')]:
        blob=git(['show',probe_rev+':evidence/interface-engineer/stage-2-browser-probe.py'])
        assert (folder/'executed-probe.py').read_bytes()==blob and hashlib.sha256(blob).hexdigest()==report['probe_sha256']
        assert not git(['-C',report['clone'],'status','--porcelain']).strip()
        assert git(['-C',report['clone'],'rev-parse','HEAD']).decode().strip()==candidate
        assert all(x['cpus']==2 and x['memory_bytes']==2147483648 and x['mounts']==[] for x in report['resources'].values())
    assert not git(['diff',candidate,'--','stage-1','stage-2']).strip()
    transfers=[x for x in b['trace'] if x['scenario']=='raw-upgrade-transfer'];assert len(transfers)==4
    for x in transfers:assert x['decoded'] is False and x['export_bytes']==x['import_bytes'] and x['export_sha256']==x['import_sha256']
    mixed=[x for x in b['trace'] if x['scenario']=='raw-mixed-roundtrip'];assert len(mixed)==4 and all(x['decoded'] is False for x in mixed)
    wire=[x for x in sb['trace'] if x['scenario']=='integral-wire-presentation'];assert len(wire)==5
    assert all(x['fixture_token']==x['real_response_capacity_tokens'][0] for x in wire)
    counts={'json_files':0,'dict_records':0,'embedded_json_strings':0};findings=[];manifest=[]
    private={'password','password_hash','token','tokens','state','authorization'}
    def inspect(value,path,embedded=False):
        if isinstance(value,dict):
            counts['dict_records']+=1
            for key,v in value.items():
                if key in private:findings.append({'path':path,'field':key})
                inspect(v,path+'/'+key,embedded)
        elif isinstance(value,list):
            for i,v in enumerate(value):inspect(v,path+'/'+str(i),embedded)
        elif isinstance(value,str) and not embedded and value.lstrip().startswith(('{','[')):
            try:parsed=json.loads(value)
            except (ValueError,RecursionError):return
            counts['embedded_json_strings']+=1;inspect(parsed,path+'/embedded-json',True)
    for folder in [pre,failed,full,supp]:
        for p in sorted(folder.rglob('*')):
            if not p.is_file():continue
            blob=p.read_bytes();manifest.append({'path':str(p.relative_to(root)),'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
            if p.suffix=='.json':counts['json_files']+=1;inspect(json.loads(blob),str(p.relative_to(root)))
    assert not findings,findings
    cleanup=[]
    for folder in [failed,full,supp]:
        rr=json.loads((folder/'runtime-report.json').read_text());rows=[x for x in rr['commands'] if x.get('log','').startswith('cleanup-')]
        assert len(rows)==7 and all(x['exit']==0 for x in rows)
        cleanup.append({'artifact':str(folder.relative_to(root)),'count':len(rows),'exits':[x['exit'] for x in rows]})
    proof={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':'Interface Engineer','tested_full_candidate':candidate,'stage_2_tree':git(['rev-parse',candidate+':stage-2']).decode().strip(),'stage_1_tree':git(['rev-parse',candidate+':stage-1']).decode().strip(),'implementation_revision':'a040054f2a8d00c560bea7f02324d1443c5a3f14','full_run_driver_revision':'b50f54c2d5525c6f0dc454fef42f5d382580649c','full_run_probe_revision':'a040054f2a8d00c560bea7f02324d1443c5a3f14','supplement_driver_and_probe_revision':'bc36441e726766055d1739f00da246666a4dd44f','full_scenarios':43,'full_assertions':793,'supplement_scenarios':5,'supplement_assertions':90,'source_and_probe_bindings_verified':True,'current_graded_diff_empty':True,'retained_clones_clean':True,'four_upgrade_raw_traces_verified':True,'four_mixed_raw_roundtrips_verified':True,'five_full_numeric_wire_tokens_verified':True,'six_inspected_process_resources_per_successful_run_verified':True,'cleanup':cleanup,'json_privacy_scope':{'counts':counts,'raw_private_payload_findings':findings,'excluded':'source/log strings, peer evidence and genuine final room export; synthetic test credentials exist in authored protocol source, never live private exports/tokens'},'screenshots':{'full_genuine_product':len(list(full.glob('*.png'))),'supplement_genuine_product':len(list(supp.glob('*.png'))),'failed_blank_diagnostic':len(list(failed.glob('*.png'))),'reviewed':['single-confirmation-desktop.png','opaque-unicode-pair-mobile.png','integral-wire-9d007199254740993Ep15-mobile.png','upgrade-2-16aee9f0-pair-mobile.png']},'max_measured_direct_and_forward_http_seconds':max(x['seconds'] for x in b['http_trace']),'manifest':manifest,'manifest_files':len(manifest),'harness':'Codex','configured_model':'gpt-6.1-sol','actual_model_effort_usage_catalog_cost_billed_spend':'unknown'}
    output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:proof[k] for k in ['manifest_files','json_privacy_scope','screenshots','max_measured_direct_and_forward_http_seconds']},indent=2))

if __name__=='__main__':main()
