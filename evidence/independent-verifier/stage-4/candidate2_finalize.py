"""Final concrete metadata, finite timing, source preservation and acceptance facts."""
import csv,hashlib,json,sys,subprocess,stat
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
sys.set_int_max_str_digits(0);csv.field_size_limit(sys.maxsize)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-2';C='58270860cb6a762c8a4c2a551672701fb00bd613'
def load(p):return json.loads(p.read_text())
def write(name,v):
    p=H/name;data=json.dumps(v,indent=2)+'\n'
    if p.exists():assert p.read_text()==data
    else:p.write_text(data)
def preservation(rev,path):
    output=subprocess.check_output(['git','ls-tree','-rz',rev,'--',path],cwd=R);rows=[]
    for line in output.split(b'\0'):
        if not line:continue
        header,name=line.split(b'\t',1);mode,kind,oid=header.decode().split();p=R/name.decode();data=p.read_bytes();digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert digest==oid and kind=='blob';assert stat.S_IMODE(p.stat().st_mode)==(0o755 if mode=='100755' else 0o644)
        rows.append(dict(path=name.decode(),mode=mode,blob=oid,sha256=hashlib.sha256(data).hexdigest(),unchanged=True))
    return dict(revision=rev,files=len(rows),all_unchanged=True,manifest=rows)
def main():
    rows=list(csv.DictReader((H/'binding-10/coverage.csv').open()));required=load(HERE.parent/'stage-3/candidate-1/metadata-self-check.json')['required_fields'];bad=[]
    for row in rows:
        assert all(row.get(k) for k in required);assert row['candidate_full_revision']==C and row['verdict']=='verified' and row['verification_owner']=='independent-verifier'
        assert set(row['implementation_owner'].split(' / '))<={'systems-engineer','interface-engineer'}
        for path in row['evidence_path'].split(';'):
            if not (R/path.strip().split('#')[0]).is_file():bad.append([row['requirement_id'],path])
    assert not bad and len({r['requirement_id'] for r in rows})==len(rows)
    normative=[r for r in rows if r['normative']=='True'];assert len(normative)==7840 and len(rows)==7862
    for name in ['coverage.csv','coverage-bindings.json','completed-runs.json']:
        dest=H/name;data=(H/'binding-10'/name).read_bytes()
        if dest.exists():assert dest.read_bytes()==data
        else:dest.write_bytes(data)
    metadata=dict(candidate=C,records=len(rows),normative=len(normative),verified=len(normative),failed=0,unverified=0,nonnormative_diagnostics=22,required_fields=required,all_fields_populated=True,unique_identifiers=True,concrete_evidence_files=True,missing_files=[],ownership_explicit=True,source_only_unreachable_permission_rows=['TK4-retry-'+x+'-different-before-permission' for x in ['preview','apply','amend']],matrix_sha256=hashlib.sha256((H/'coverage.csv').read_bytes()).hexdigest())
    write('metadata-self-check.json',metadata)
    runs=load(H/'completed-runs.json');totals={kind:dict(runs=sum(x['kind']==kind for x in runs),requests=sum(x['requests'] for x in runs if x['kind']==kind),assertions=sum(x['assertions'] for x in runs if x['kind']==kind),browser_originated_requests=sum(x['browser_requests'] for x in runs if x['kind']==kind),forwardings=sum(x['forwardings'] for x in runs if x['kind']==kind),retained_pngs=sum(x['screenshots'] for x in runs if x['kind']==kind)) for kind in ['http','browser']}
    timed=[]
    def walk(v,file):
        if isinstance(v,dict):
            if isinstance(v.get('method'),str) and isinstance(v.get('path'),str):
                t=v.get('seconds',v.get('duration_seconds'))
                if isinstance(t,(int,float)):timed.append(dict(file=str(file.relative_to(R)),method=v['method'],path=v['path'],seconds=t,limit=10 if v['path'].startswith('/_test/') else 5))
            for x in v.values():walk(x,file)
        elif isinstance(v,list):
            for x in v:walk(x,file)
    for run in runs:
        folder=H/run['name'];file=next((p for p in [folder/'trace.json',folder/'operations.json',folder/'requests.json',R/run['summary']] if p.is_file()),None);assert file;walk(load(file),file)
        if run['kind']=='browser' and (folder/'api/trace.json').is_file():walk(load(folder/'api/trace.json'),folder/'api/trace.json')
    violations=[x for x in timed if x['seconds']>x['limit']];assert timed and not violations
    write('request-timing-audit.json',dict(candidate=C,saved_timed_observations=len(timed),maximum_seconds=max(x['seconds'] for x in timed),violations=[],by_file=dict(Counter(x['file'] for x in timed)),scope='One primary actual trace/operations/requests/payload per selected complete protocol plus separately saved direct API browser traces. These are saved finite timing observations, not unique request or internal serializer counts. Official/health/source/Engine traffic excluded.'))
    preserved=[preservation('16b6955aee3036298aaa81aa3533fe3536d44cff','evidence/independent-verifier/stage-4/candidate-1'),preservation('f4addfc743c6c5ffb7e9d9b1ccf41d89572c57a5','evidence/independent-verifier/stage-4/repair-1')];write('historical-preservation-final.json',dict(candidate=C,preserved=preserved,source='Exact Git blobs and filesystem modes; later append-only correction files remain additional history.'))
    cleanup=load(H/'final-runtime-proof.json');assert cleanup['namespace_empty'] and cleanup['cleanup_exits']==[0]*9 and cleanup['graded_diff_empty'] and len(cleanup['clean_clones'])==6
    audit=load(H/'artifact-audit-02.json');assert not audit['unclassified_private_payload_findings'] and not audit['json_read_errors']
    source=load(H/'source-audit-01/source-proof.json');assert source['candidate']==C and len(source['frozen'])==24 and all(x['working_bytes_equal'] for x in source['frozen']+source['source'])
    direct=load(H/'direct-01/summary.json');assert direct['failed']==0 and direct['calls']==70 and len(direct['assertions'])==71
    facts=load(H/'runtime-01/preflight.json');official=load(H/'official/report.json');assert official['revision']==C and str(official['claimed_stage'])=='4'
    for n,count in [(1,120),(2,25),(3,7),(4,6)]:assert official['checks'][str(n)]['passed']==count
    intake=load(H/'intake.json');assert intake['all_parts_received'] and intake['end_received'] and intake['final_completion_marker_received'] and intake['acknowledged_before_execution']
    now=datetime.now(timezone.utc);started=datetime.fromisoformat(intake['recorded_at']);elapsed=(now-started).total_seconds()
    summary=dict(candidate=C,stage_4_tree='00e208c746a488a9b4cb0761efd04b90c4248dd8',verdict='accept',highest_consecutive_accepted=4,production_edits=0,coverage=metadata,current_protocols=totals,direct_diagnostic=dict(scope=direct['scope'],calls=70,assertions=71,failed=0),official=dict(stage1=120,stage2=25,stage3=7,stage4=6,passed=158,failed=0,errors=0,skips=0,deselections=0,xfails=0,claim=4,external_command_seconds=37.62366225000005),image=facts['source']['current']['image_id'],source_hashes=facts['source']['current']['source_sha256'],cleanup=cleanup,startup_bounds=[dict(role=x['role'],port=x['internal_port'],seconds=x['startup_to_health_seconds'],default=x['default_port']) for x in facts['containers']],timing=dict(recorded_intake_at=started.isoformat(),aggregation_at=now.isoformat(),intake_record_to_aggregation_seconds=elapsed,whole_factory_elapsed='coordinator-owned',seal_timing='separate later evidence'),model=dict(harness='Codex',configured='gpt-6.1-sol',actual_override=None,effort=None,tokens=None,catalog_estimated_cost=None,billed_spend=None),known_interpretations=['Exact historical IANA instant and original wall fields, minute-aligned new wire offset and immutable old seconds-offset strings; incompatible literal grammars not claimed simultaneously.','Immutable original successful receipt schema/value/body meaning.','Exact current numeric values and genuine receipt-scoped legacy comparison only.','Visible exact semantic numeric control; native HTML type judging ambiguity.'],limits=['Finite payload/depth/exponent/workload and supported-bound observations; no arbitrary performance guarantee.','Scoped visual and accessibility assessment, not complete WCAG certification.','Three unreachable public permission-loss rows use exact source ordering/applicability review.','Build cache available; no uncached build or host-published reachability claim.','Older source bootstrap: revision1/fixture-policy0/empty prior history/private counter0/no invented manager.','Public release, real room export, operator README/FACTORY and submission remain operator-controlled.'])
    write('summary.json',summary)
    table=['# Complete current independent protocols','','| Protocol | Kind | Direct requests | Assertions | Browser requests | Forwardings | Seconds |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for x in runs:table.append('| '+x['name']+' | '+x['kind']+' | '+str(x['requests'])+' | '+str(x['assertions'])+' | '+str(x['browser_requests'])+' | '+str(x['forwardings'])+' | '+format(x['seconds'],'.9f')+' |')
    table+=['','Exact commands and individual summary paths are in [completed-runs.json](completed-runs.json). Browser/API assertions, browser-originated requests and forwarding transports remain separate; no summed unique-request total. Selector binding, official, startup and source traffic are excluded. Engine70/71 is separately labelled, not HTTP.']
    (H/'COMPLETED_RUNS.md').write_text('\n'.join(table)+'\n')
    print(json.dumps(dict(candidate=C,verdict='accept',normative=7840,verified=7840,failed=0,unverified=0,totals=totals,timed=len(timed),maximum=max(x['seconds'] for x in timed),elapsed=elapsed,preserved=[x['files'] for x in preserved])))
if __name__=='__main__':main()
