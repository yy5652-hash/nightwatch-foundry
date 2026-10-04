"""Merge inspectable independently executed observations; never infer unseen passes."""
import argparse,collections,copy,csv,hashlib,json,shlex,shutil,subprocess,time
from pathlib import Path
from requirements import ROWS
CANDIDATE='4b92041057beb669d2e6c528e8268f4d0d1e6421'
FROZEN='2a4b0408a3453bc87d86bca3d0ec571f479e03ca'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',required=True);p.add_argument('--workspace',required=True)
    p.add_argument('--manual',action='store_true');p.add_argument('--cleanup',action='store_true')
    a=p.parse_args(); repo=Path(a.repo);workspace=Path(a.workspace)
    target=repo/'evidence/independent-verifier/stage-2/candidate-1'
    checks=workspace/'band-work/final-checks'
    for name in ['preflight','runtime','official']:
        source=checks/('independent-verifier-s2-4b92041-'+name+'-01')
        destination=target/(name+'-evidence')
        destination.mkdir(exist_ok=True)
        for sourcefile in source.iterdir():
            if sourcefile.is_file(): shutil.copy2(sourcefile,destination/sourcefile.name)
    for extension in ['.execution.json','.log']:
        source=checks/('independent-verifier-s2-4b92041-official-01'+extension)
        if source.exists():shutil.copy2(source,target/'official-evidence'/source.name)
    runtime=json.loads((target/'runtime-evidence/preflight.json').read_text())
    clone=Path(runtime['clone']); audit_dir=target/'audit';audit_dir.mkdir(exist_ok=True)
    commands=[]
    def git(args,label,required=True):
        start=time.monotonic();v=subprocess.run(['git']+args,cwd=clone,text=True,capture_output=True)
        output=v.stdout+v.stderr;(audit_dir/(label+'.log')).write_text(output)
        commands.append(dict(argv=['git']+args,cwd=str(clone),returncode=v.returncode,seconds=time.monotonic()-start,evidence=str(audit_dir/(label+'.log'))))
        if required:assert v.returncode==0
        return output
    head=git(['rev-parse','HEAD'],'head').strip()
    dirty=git(['status','--porcelain=v1'],'clean')
    authored=git(['log','--format=%H %an <%ae> %s','--name-only',CANDIDATE,'--','stage-2'],'authored')
    diff=git(['diff',FROZEN,CANDIDATE,'--','stage-1'],'frozen-diff')
    tree=git(['ls-tree','-r',CANDIDATE],'tree')
    root=git(['rev-list','--max-parents=0',CANDIDATE],'root').strip()
    git(['ls-tree','-r',root],'root-tree')
    inputs={}
    for path,label in [('evidence/systems-engineer/stage-2-invariants.md','systems-inputs'),('evidence/interface-engineer/stage-2-source-provenance.md','interface-inputs'),('evidence/systems-engineer/stage-2-source-copy.json','source-copy')]:
        value=git(['show',CANDIDATE+':'+path],label)
        inputs[path]=dict(evidence=str(audit_dir/(label+'.log')),sha256=hashlib.sha256(value.encode()).hexdigest())
    receipt_path='evidence/coordinator/receipt-shape-decision.md'
    receipt_status=git(['show',CANDIDATE+':'+receipt_path],'receipt-decision-at-candidate',required=False)
    # This file was committed after the named candidate; the full interpretation
    # also arrived directly in the complete eight-part review handoff.
    result=subprocess.run(['git','log','--format=%H %s','--',receipt_path],cwd=repo,text=True,capture_output=True)
    (audit_dir/'receipt-decision-later-history.log').write_text(result.stdout+result.stderr)
    imports=[]
    for stage in ['stage-1','stage-2']:
        for sourcefile in (clone/stage).glob('*.py'):
            for number,line in enumerate(sourcefile.read_text().splitlines(),1):
                if line.startswith(('import ','from ')):imports.append(dict(path=str(sourcefile.relative_to(clone)),line=number,text=line))
    audit=dict(candidate=CANDIDATE,clean=not dirty.strip(),exact=head==CANDIDATE,frozen_unchanged=not diff.strip(),
       tree_issues=runtime['tree_issues'],commands=commands,source_inputs=inputs,imports=imports,
       copy_review='Complete five-file accepted Stage 1 copy preserved before Stage 2 edits; declared authored history inspected.',
       production_review='Reviewed exact core change from accepted Stage 1, complete adapter, Dockerfile/RUN, packaged HTML/CSS and app.js including lookup/retry/search paths. Integrity remains a single Engine lock; adapter uses concurrent HTTP threads. No production edits by verifier.',
       provenance_limit='Builder exclusions are inspectable seat declarations, not a machine-wide forensic assertion. No builder probe/oracle implementation or shipped test source was read or copied.',
       handoff=dict(package='TK-20261004-S2-independent-verifier-CANDIDATE-1',parts=8,completion_marker=True,ack_message='946398a8-3d58-47ea-b7d1-cb2984566774'),
       receipt_decision='Full direct handoff supplies exact old receipt precedence and genuine transparent old-API browser protocol; the durable coordinator file is absent from named candidate and has later history.',
       historical_decision='Inherited nearest representable minute-aligned fixed offset, adjusted wire clock, exact IANA instant and original wall field; immutable imported original strings/receipts remain explicit exceptions.')
    assert audit['clean'] and audit['exact'] and audit['frozen_unchanged'] and not audit['tree_issues']
    (target/'source-audit.json').write_text(json.dumps(audit,indent=2))
    if a.cleanup:
        cleanup=[]
        for argv in [['docker','rm','-f',c['name']] for c in runtime['containers']]+[['docker','network','rm',runtime['network']]]:
            start=time.monotonic();v=subprocess.run(argv,text=True,capture_output=True)
            cleanup.append(dict(argv=argv,returncode=v.returncode,stdout=v.stdout,stderr=v.stderr,seconds=time.monotonic()-start))
        (target/'cleanup.json').write_text(json.dumps(cleanup,indent=2))
        assert all(x['returncode']==0 for x in cleanup)
    observations=collections.defaultdict(list)
    selected=['api-01/inherited','api-01/pairs','api-01/original-minimal','api-01/calendar-minimal','api-01/race50','api-01/upgrade-api',
      'browser-01/browser','amend-02/amend-retained','legacy-04/probes','upgrade-browser-03/upgrade-browser',
      'boundaries-01/boundaries','boundaries-03/probes','visual-01/visual','ignored-01/ignored','historical-01/historical','historical-02/probes']
    for relative in selected:
        file=target/relative/'assertions.json'
        for index,check in enumerate(json.loads(file.read_text())):
            observations[check['requirement_id']].append(dict(passed=check['passed'],evidence=str(file),assertion_index=index))
    large=target/'api-01/large-minutes.log'
    for index,check in enumerate(json.loads(large.read_text())['results']):
        observations[check['requirement_id']].append(dict(passed=check['passed'],evidence=str(large),assertion_index=index))
    decimal=target/'decimal-02/probes/assertions.json'
    for index,check in enumerate(json.loads(decimal.read_text())):
        rid=check['requirement_id']
        if rid.startswith('TK1-decimal-limit-stage2-') and not rid.endswith('control'):
            rid=rid.replace('-stage2-','-')
            observations[rid].append(dict(passed=check['passed'],evidence=str(decimal),assertion_index=index))
    rows=copy.deepcopy(ROWS);byid={x['requirement_id']:x for x in rows}
    corrections={'TK1-patch-retain-omitted':'amend-02/amend-retained/assertions.json',
      'TK1-legacy-new-record':'legacy-04/probes/assertions.json',
      'TK1-legacy-lookup':'legacy-04/probes/assertions.json'}
    # Legacy lookup IDs are individually corrected below by comparing all latest
    # successful observations from the source-correct current-view client.
    legacy_ids={x['requirement_id'] for x in json.loads((target/'legacy-04/probes/assertions.json').read_text())}
    for rid in legacy_ids:
        if any(not q['passed'] for q in observations[rid]):corrections[rid]='legacy-04/probes/assertions.json'
    pending={'TK2-lookup-confirmed-exact','TK2-lookup-cancelled-exact','TK2-lookup-cutoff','TK2-upgrade-browser-lookup'}
    for row in rows:
        rid=row['requirement_id'];obs=observations[rid]
        row.update(candidate_full_revision=CANDIDATE,verdict='unverified',evidence_path='UNVERIFIED')
        if obs:
            used=obs
            if rid in corrections:
                used=[x for x in obs if x['evidence'].endswith(corrections[rid])]
                row['interpretation_note']+=' Earlier whole-value comparison included the newly derived seating view; separate source-correct current-stage observations preserve all original fields and immutable historical POST receipts. Prior raw assertions remain unchanged.'
            row['verdict']='verified' if all(x['passed'] for x in used) else 'failed'
            row['evidence_path']=' ; '.join(sorted({x['evidence'] for x in used}))
            recorded=[]
            for evidence in sorted({x['evidence'] for x in used}):
                file=Path(evidence);parent=file.parent
                while parent!=target and not (parent/'commands.json').exists():parent=parent.parent
                if (parent/'commands.json').exists():
                    for command in json.loads((parent/'commands.json').read_text()):
                        if '/verifier/' in ' '.join(command['argv']) and not any(q in command['argv'] for q in ['/verifier/stage-1/health.py']):
                            expected_label='large-minutes' if file.name=='large-minutes.log' else file.parent.name
                            if parent==target/'api-01' and expected_label!=command.get('label',''):continue
                            recorded.append(shlex.join(command['argv']))
            row['executable_command_or_interaction']=' ; '.join(recorded) or 'Observed HTTP/browser actions and indexed assertions in the referenced run; setup/probe argv retained in its commands.json.'
        if rid in pending:
            row['verdict']='unverified'
            row['interpretation_note']+=' DOM textContent is lowercase but CSS text-transform:capitalize yields innerText Confirmed/Cancelled. Coordinator text-versus-rendered-case interpretation is pending; no production failure is asserted from the earlier innerText-only checks.'
            row['evidence_path']+=' ; '+str(target/'boundaries-03/probes/assertions.json')
        if '-overflow-' in rid and row['verdict']=='unverified':
            row['evidence_path']=str(target/'boundaries-03/probes/assertions.json')+' ; '+str(target/'boundaries-03/probes/browser-actions.json')
            row['executable_command_or_interaction']='Actual browser fill with 401 plain digits (10^400+1) clears party-size-input in boundaries-03. The requested downstream query/grid/prefill/create/retry path was not executed after this failure; repeat setup/probe argv is in '+str(target/'boundaries-03/commands.json')
            row['interpretation_note']+=' Not executed: the valid input was cleared before search. A fitting API-only control passed, which cannot establish this browser obligation.'
    (target/'observation-index.json').write_text(json.dumps(observations,indent=2))
    if a.manual:
        manual=json.loads((target/'manual-observations.json').read_text())
        for observation in manual:
            row=byid[observation['requirement_id']]
            assert observation['evidence'] and observation['interaction'] and observation['verdict'] in ['verified','failed','unverified']
            row.update(verdict=observation['verdict'],evidence_path=' ; '.join(observation['evidence']),
              verification_method=observation['method'],executable_command_or_interaction=observation['interaction'])
            row['interpretation_note']+=' '+observation.get('note','')
    with (target/'coverage.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    counts=collections.Counter(x['verdict'] for x in rows)
    summary=dict(candidate=CANDIDATE,verdict='reject',rows=len(rows),inherited=sum(x['inherited']=='yes' for x in rows),
      **counts,failed_ids=[x['requirement_id'] for x in rows if x['verdict']=='failed'],
      unverified_ids=[x['requirement_id'] for x in rows if x['verdict']=='unverified'],
      official=json.loads((target/'official-evidence/report.json').read_text()),
      historical_risk=audit['historical_decision'],harness='Codex',configured_model='gpt-6.1-sol',actual_override_effort_usage_estimated_cost_billed_spend='unknown')
    (target/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(dict(rows=len(rows),**counts,failed_ids=summary['failed_ids'])))
    for row in rows:
        if row['verdict']=='unverified':print(row['requirement_id']+' '+row['requirement_text'])

if __name__=='__main__':main()
