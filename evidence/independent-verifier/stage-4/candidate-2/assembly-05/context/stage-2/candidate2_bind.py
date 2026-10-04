"""Current evidence binding only; incomplete/obsolete families stay preserved and excluded."""
import copy,csv,json,shlex,sys
from collections import defaultdict,Counter
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-2';C='4dba10246b07b2dda19de260d529f9d94ba0a1ed'
def load(p):return json.loads(p.read_text())
def relative(p):return str(p.relative_to(R))
def main():
    evidence=defaultdict(list);runs=[]
    groups={'http-01':['original-minimal','calendar-minimal','race50','decimal','semantic','opaque-ids','nesting','pairs','retained-amend','large-minutes','numeric','fractional','very-deep','deep-race'],
        'inherited-02':['baseline','snapshot','decoder','legacy'],'origins-02':['origins'],
        'reconstruction-http-01':['deep','opaque','numeric'],'browser-01':['general','boundaries','historical','visual'],
        'reconstruction-browser-01':['upgrade','numeric','opaque'],'upgrade-browser-01':['four-upgrades'],
        'supplement-01':['browser'],'supplement-oracle-02':['oracle'],'coverage-closures-01':['coverage','overflow'],'calendar-browser-01':['calendar']}
    def walk(value,pointer=''):
        if isinstance(value,dict):
            if 'requirement_id' in value and 'passed' in value:yield value,pointer
            for k,v in value.items():yield from walk(v,pointer+'/'+str(k))
        elif isinstance(value,list):
            for i,v in enumerate(value):yield from walk(v,pointer+'/'+str(i))
    for group,labels in groups.items():
        commands=load(H/group/'commands.json')
        for label in labels:
            cmd=next(x for x in commands if x.get('log')==label+'.log');assert cmd['returncode']==0,(group,label,cmd)
            folder=H/group/label;payload=load(folder/'summary.json') if (folder/'summary.json').exists() else load(folder/'probes.json') if (folder/'probes.json').exists() else load(H/group/(label+'.json'))
            assert payload.get('candidate',payload.get('candidate_full_revision'))==C
            assert not any(payload.get(k) for k in ['failures','failed_assertions','runner_errors','errors','stopped_after_expectation','blocked_paths','flow_errors'])
            files=[folder/'assertions.json'] if (folder/'assertions.json').exists() else [folder/'probes.json'] if (folder/'probes.json').exists() else [H/group/(label+'.json')]
            count=0
            for file in files:
                for item,pointer in walk(load(file)):
                    assert item['passed'] is True,(file,pointer,item)
                    evidence[item['requirement_id']].append(dict(passed=True,evidence_path=relative(file)+'#'+pointer,command=shlex.join(cmd['argv']),run=group+'/'+label,method='real browser and direct HTTP' if 'browser' in group or group=='supplement-01' else 'black-box HTTP'))
                    count+=1
            runs.append(dict(name=group+'/'+label,counts=payload.get('counts'),requests=payload.get('requests',payload.get('http_operations',payload.get('counts',{}).get('requests'))),browser_requests=payload.get('browser_requests'),assertions=payload['assertions'],counted_assertion_records=count,seconds=payload.get('duration_seconds',payload.get('seconds')),failures=0,command=shlex.join(cmd['argv'])))
    if (H/'review-checks.json').exists():
        for item in load(H/'review-checks.json'):
            evidence[item['requirement_id']].append(item)
    rows=list(csv.DictReader((H/'coverage-prepared.csv').open()));existing={r['requirement_id'] for r in rows}
    for group in ['supplement-01/browser','supplement-oracle-02/oracle','upgrade-browser-01/four-upgrades','coverage-closures-01/coverage','calendar-browser-01/calendar']:
        checks=load(H/group/'assertions.json')
        for item in checks:
            rid=item['requirement_id']
            if rid in existing:continue
            existing.add(rid);row={k:'' for k in rows[0]}
            owner='systems-engineer'
            if 'browser' in group:
                core_words=['fixture','actual-token','source-auth','retained-create','retained-moves','raw-import','original-shape','one-booking','retained-originals','new-write','mixed-peer','mixed-originals','exact-instant','actual-create']
                combined_words=['original-receipt','body-key-user','retry','pair-capacity']
                owner='systems-engineer' if any(rid.endswith(x) for x in core_words) else 'systems-engineer / interface-engineer' if any(rid.endswith(x) for x in combined_words) else 'interface-engineer'
            row.update(requirement_id=rid,source_section='Stage1 §§3.4,5,7,8,10,11; Stage2 API, Concurrent bookings and amendments, Existing clients after an upgrade, Product and visual direction',source_line='1',introduced_stage='2',applicable_stages='2,3,4',owner=owner,implementation_owner=owner,verification_owner='independent-verifier',requirement_text='Independently executed conditional current-candidate obligation: '+rid.removeprefix('TK2R-'),case='current-wire-upgrade-oracle',normative='True',source_file='stage-2.md',interpretation_note='Actual real source/server outcomes; exact wire tokens remain numeric. Parameterized observations are requirement decomposition, not a shipped/hidden test score.',preparation_origin='Independently authored current supplement; no builder protocol read.')
            rows.append(row)
    bindings={}
    for row in rows:
        found=evidence.get(row['requirement_id'],[]);bindings[row['requirement_id']]=found
        row['candidate_full_revision']=C
        row['verdict']='verified' if found and all(x['passed'] for x in found) else 'failed' if found else 'unverified'
        row['evidence_path']='; '.join(sorted({x['evidence_path'] for x in found})) if found else 'UNVERIFIED_CURRENT_EVIDENCE'
        row['executable_command_or_interaction']='\n'.join(sorted({x['command'] for x in found})) if found else 'Current evidence missing; promotion prohibited.'
        row['verification_method']='; '.join(sorted({x.get('method','current observed review') for x in found})) if found else row['verification_method']
        if row.get('interpretation_note'):
            row['historical_interpretation_note']=row['interpretation_note'] if row.get('historical_candidate') else ''
        row['interpretation_note']='Fresh current-candidate evidence only. Adopted exact numeric/legacy profile, immutable original receipt shape, semantic numeric control and historical exact-instant/nearest-minute-offset decisions apply. Original historic columns/results remain unchanged.'
        if row['requirement_id']=='TK1-own-stage':row['interpretation_note']+=' Current Stage2 independently claims2 with separate Stage3 overshoot; genuine frozen Stage1 is built unchanged at its accepted Stage1 revision. Stage2 is not required to fail its own Stage2 suite.'
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (H/'coverage-draft.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    gaps=[r for r in rows if r['verdict']!='verified'];norm=[r for r in rows if r['normative']=='True']
    (H/'current-binding-gaps.json').write_text(json.dumps(gaps,indent=2)+'\n')
    (H/'coverage-bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
    (H/'completed-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
    summary=dict(candidate=C,normative_rows=len(norm),verdicts=dict(Counter(r['verdict'] for r in norm)),diagnostic_rows=len(rows)-len(norm),gaps_by_case=dict(Counter(r['case'] for r in gaps)))
    (H/'binding-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
