"""Fresh current observation binding; partial attempts never establish downstream rows."""
import argparse,csv,json,shlex,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.set_int_max_str_digits(0);csv.field_size_limit(sys.maxsize)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-2';C='58270860cb6a762c8a4c2a551672701fb00bd613'
SELECTED={'current-http-01':None,'errors-02':None,'full-bound-02':None,'transitions-01':None,'extra-01':['retry','deep'],'extra-02':None,'atomic-02':['prefix'],'atomic-03':None,'model-01':None,'races-02':None,'inherited-http-01':None,'inherited-browser-01':None,'boundaries-01':None,'recovery-02':None,'product-01':None}
def load(p):return json.loads(p.read_text())
def walk(v,pointer=''):
    if isinstance(v,dict):
        if 'passed' in v and ('requirement_id' in v or 'requirement' in v):yield v,pointer
        for k,x in v.items():yield from walk(x,pointer+'/'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v):yield from walk(x,pointer+'/'+str(i))
def collect():
    evidence=defaultdict(list);runs=[]
    for group,labels in SELECTED.items():
        path=H/group/'commands.json'
        if not path.is_file():continue
        for cmd in load(path):
            label=cmd['family']
            if labels is not None and label not in labels or cmd['returncode']!=0:continue
            folder=H/group/label;payload=next((p for p in [folder,folder/'summary.json',folder/'report.json',folder/'probes.json',folder/'browser-report.json',folder/'upgrade-report.json',H/group/(label+'.json')] if p.is_file()),None)
            if payload is None:
                log=H/group/(label+'.log');data=json.loads(log.read_text());payload=H/group/(label+'-derived.json')
                if not payload.exists():payload.write_text(json.dumps(data,indent=2)+'\n')
            assert payload,(group,label);data=load(payload);assert data.get('candidate',data.get('candidate_full_revision'))==C,(payload,'candidate')
            for k in ['failures','failed','failed_assertions','runner_errors','errors','error','stopped_after_expectation','blocked_paths','flow_errors']:assert not data.get(k),(payload,k)
            assert data.get('complete',True) is True
            kind='browser' if group in ['inherited-browser-01','recovery-02','product-01'] else 'http';files=[folder/'assertions.json'] if (folder/'assertions.json').is_file() else [payload]
            if (folder/'api/assertions.json').is_file():files.append(folder/'api/assertions.json')
            count=0
            for file in files:
                for item,pointer in walk(load(file)):
                    assert item['passed'];rid=item.get('requirement_id',item.get('requirement'));evidence[rid].append(dict(passed=True,evidence_path=str(file.relative_to(R))+'#'+pointer,command=shlex.join(cmd['argv']),run=group+'/'+label,method='actual browser/API' if kind=='browser' else 'black-box HTTP'));count+=1
            api=load(folder/'api/summary.json') if (folder/'api/summary.json').is_file() else {};counts=data.get('counts') or {};requests=data.get('requests',data.get('actual_http_requests',data.get('direct_api_requests',data.get('http_operations',counts.get('requests',counts.get('direct',counts.get('http',api.get('requests',0))))))));browser_requests=data.get('browser_requests',counts.get('browser',len(data.get('request_trace',[])))) if kind=='browser' else 0
            forward=data.get('forwarding_operations',len(data.get('transport',[])))
            if (folder/'forwarding.json').is_file():forward=len(load(folder/'forwarding.json'))
            runs.append(dict(name=group+'/'+label,kind=kind,requests=requests,browser_requests=browser_requests,assertions=count,seconds=cmd['seconds'],forwardings=forward,screenshots=len(list(folder.rglob('*.png'))),command=shlex.join(cmd['argv']),summary=str(payload.relative_to(R))))
    direct=load(H/'direct-01/summary.json');cmd=next(x for x in load(H/'direct-01/commands.json') if x.get('log')=='execute.log')
    for item,pointer in walk(direct):
        assert item['passed'];evidence[item['requirement_id']].append(dict(passed=True,evidence_path=str((H/'direct-01/summary.json').relative_to(R))+'#'+pointer,command=shlex.join(cmd['argv']),run='direct-01',method='packaged Engine diagnostic with clock substitution; not HTTP'))
    return evidence,runs
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--review-file',action='append',default=[]);a=p.parse_args();out=Path(a.out).resolve();assert out.is_relative_to(H);out.mkdir(parents=True,exist_ok=False);evidence,runs=collect()
    for file in a.review_file:
        for item in load(Path(file)):
            assert item['passed'];evidence[item['requirement_id']].append(item)
    rows=list(csv.DictReader((H/'coverage-initial.csv').open()));bindings={}
    for row in rows:
        rid=row['requirement_id'];links=evidence.get(rid,[])
        # The twelve explicit wrong-type rows retain their exact field/value identity.
        if rid.startswith('TK4-closure-') and 'wrong-type' in rid:links=evidence.get(rid.removeprefix('TK4-'),links)
        bindings[rid]=links;row['verdict']='verified' if links and all(x['passed'] for x in links) else 'unverified';row['candidate_full_revision']=C
        row['evidence_path']='; '.join(sorted({x['evidence_path'] for x in links})) if links else str((H/'intake.json').relative_to(R))
        row['executable_command_or_interaction']='\n'.join(sorted({x['command'] for x in links})) if links else 'Current requirement has no complete matching observation; withheld'
        row['verification_method']='; '.join(sorted({x.get('method','current independent applicability review') for x in links})) if links else 'unverified current scope'
    with (out/'coverage.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
    for name,value in [('coverage-bindings',bindings),('all-observations',evidence),('completed-runs',runs),('gaps',[{k:r[k] for k in ['requirement_id','requirement_text','case','introduced_stage','normative']} for r in rows if r['verdict']!='verified'])]:(out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(records=len(rows),verdicts=dict(Counter(r['verdict'] for r in rows)),gaps_by_stage=dict(Counter(r['introduced_stage'] for r in rows if r['verdict']!='verified')),selected_runs=len(runs))))
if __name__=='__main__':main()
