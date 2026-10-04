"""Collect only complete fresh observations; historical/failing attempts excluded."""
import argparse,csv,json,shlex,sys
from collections import defaultdict,Counter
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-1';C='91e2c471acded1b861b3fec725f202297b1c6740'
GROUPS={'new-http-01':'policies,explain,numeric,terms,series,rollback,moves,concurrency,calendar,trace,first_error,upgrade,deep','new-http-02':'retry',
 'inherited-http-01':'original-minimal,calendar-minimal,race50,decimal,semantic,opaque-ids,nesting,snapshot,decoder,pairs,large-minutes,numeric,fractional,very-deep,deep-race','inherited-http-02':'baseline,retained-amend',
 'supplement-01':'policies,explain,terms,series','read-races-01':'races','reconstruction-http-02':'origins,deep,opaque,numeric','old-supplement-01':'oracle,coverage','migrations-02':'migrations',
 'inherited-browser-01':'boundaries,historical,visual,calendar','inherited-browser-02':'general','reconstruction-browser-01':'upgrade,numeric,opaque','inherited-upgrade-01':'four-upgrades','old-supplement-02':'overflow','old-supplement-03':'browser',
 'browser-03':'product,accepted-s1,accepted-s2,accepted-s1-desktop,accepted-s2-desktop','extra-browser-01':'extra-browser'}
def load(p):return json.loads(p.read_text())
def walk(value,pointer=''):
 if isinstance(value,dict):
  if 'requirement_id' in value and 'passed' in value:yield value,pointer
  for k,v in value.items():yield from walk(v,pointer+'/'+str(k))
 elif isinstance(value,list):
  for i,v in enumerate(value):yield from walk(v,pointer+'/'+str(i))
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False);evidence=defaultdict(list);runs=[]
 for group,labels in GROUPS.items():
  commands=load(H/group/'commands.json')
  for label in labels.split(','):
   cmd=next(x for x in commands if x['label']==label);assert cmd['returncode']==0,(group,label)
   folder=H/group/label
   payload_path=next((p for p in [folder/'summary.json',folder/'probes.json',folder/'browser-report.json',folder/'upgrade-report.json',H/group/(label+'.json')] if p.is_file()),None);assert payload_path,(group,label)
   data=load(payload_path);assert data.get('candidate',data.get('candidate_full_revision'))==C
   for key in ['failures','failed','failed_assertions','runner_errors','errors','error','stopped_after_expectation','blocked_paths','flow_errors']:assert not data.get(key),(payload_path,key)
   assert data.get('complete',True) is True
   browser='browser' in group or 'upgrade' in group or group=='old-supplement-02' or (group=='old-supplement-03')
   files=[folder/'assertions.json'] if (folder/'assertions.json').is_file() else [payload_path]
   if (folder/'api/assertions.json').is_file():files.append(folder/'api/assertions.json')
   count=0
   for file in files:
    for item,pointer in walk(load(file)):
     assert item['passed'] is True,(file,pointer)
     evidence[item['requirement_id']].append(dict(passed=True,evidence_path=str(file.relative_to(R))+'#'+pointer,command=shlex.join(cmd['argv']),run=group+'/'+label,method='real browser / actual API operations' if browser else 'black-box HTTP'))
     count+=1
   api=load(folder/'api/summary.json') if (folder/'api/summary.json').is_file() else {}
   counts=data.get('counts') or {}
   requests=data.get('requests',data.get('http_operations',counts.get('requests',counts.get('direct',counts.get('http',api.get('requests',0))))))
   browser_requests=data.get('browser_requests',counts.get('browser',len(data.get('request_trace',[])))) if browser else 0
   assertions=data.get('assertions');assertions=len(assertions) if isinstance(assertions,list) else assertions
   runs.append(dict(name=group+'/'+label,kind='browser' if browser else 'http',requests=requests,browser_requests=browser_requests,assertions=count,declared_assertions=assertions,seconds=cmd['seconds'],forwardings=len(data.get('transport',[])),screenshots=len(list(folder.rglob('*.png'))),command=shlex.join(cmd['argv']),summary=str(payload_path.relative_to(R))))
 # Explicit packaged Engine diagnostic has its own scope and actual command.
 direct=load(H/'direct-01/summary.json');dcmd=next(x for x in load(H/'direct-01/commands.json') if x['log']=='execute.log')
 for item,pointer in walk(direct):
  assert item['passed'];evidence[item['requirement_id']].append(dict(passed=True,evidence_path=str((H/'direct-01/summary.json').relative_to(R))+'#'+pointer,command=shlex.join(dcmd['argv']),run='direct-01',method='labelled packaged Engine diagnostic; diagnostic clock substitution; not HTTP'))
 if (H/'review-checks.json').is_file():
  for item in load(H/'review-checks.json'):evidence[item['requirement_id']].append(item)
 rows=list(csv.DictReader((HERE/'initial-1/checks-02/coverage.csv').open()));existing={r['requirement_id'] for r in rows}
 # Independently numbered extra legacy bootstrap/private-state constraints.
 for rid in sorted(evidence):
  if not rid.startswith(('TK3-upgrade-bootstrap-','TK3-upgrade-invalid-')) or rid in existing:continue
  row={k:'' for k in rows[0]};row.update(requirement_id=rid,source_section='Stage1 §10; Stage3 Recurring reservations, Policies and accepted terms, Reservation history',source_line='216',introduced_stage='3',applicable_stages='3,4',owner='systems-engineer',implementation_owner='systems-engineer',verification_owner='independent-verifier',requirement_text='Independent genuine import / invalid-state obligation: '+rid[4:],case='current-legacy-bootstrap',normative='True',source_file='stage-3.md',preparation_origin='Independently authored current source-faithful compatibility probe; private state remains in memory.');rows.append(row)
 bindings={}
 for row in rows:
  links=evidence.get(row['requirement_id'],[]);bindings[row['requirement_id']]=links;row['candidate_full_revision']=C
  row['verdict']='verified' if links and all(x['passed'] for x in links) else 'unverified'
  row['evidence_path']='; '.join(sorted({x['evidence_path'] for x in links})) if links else 'UNVERIFIED_CURRENT_EVIDENCE'
  row['executable_command_or_interaction']='\n'.join(sorted({x['command'] for x in links})) if links else 'Missing current evidence; no acceptance.'
  row['verification_method']='; '.join(sorted({x.get('method','current review') for x in links})) if links else 'Current candidate evidence not yet bound'
  row['interpretation_note']='Fresh named Stage3 evidence only. Original-response, historical timestamp, exact-number/legacy-profile and semantic numeric-control interpretations retained. Empty old history/revision1/policy0/counter0 are source-faithful bootstrap choices; no prior event invented. Labelled Engine diagnostics are separate from black-box HTTP.'
 fields=list(dict.fromkeys(k for row in rows for k in row))
 with (out/'coverage.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
 for name,value in [('coverage-bindings',bindings),('all-observations',evidence),('completed-runs',runs),('gaps',[r for r in rows if r['verdict']!='verified'])]:(out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
 print(json.dumps(dict(candidate=C,normative_rows=sum(r['normative']=='True' for r in rows),verdicts=dict(Counter(r['verdict'] for r in rows)),gaps_by_case=dict(Counter(r['case'] for r in rows if r['verdict']!='verified')))))
if __name__=='__main__':main()
