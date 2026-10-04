"""Create a fresh append-only preparation observation; never run a service.

Only owned reference/protocol modules are imported. Official sources are copied
as forensic bytes. Git blobs are hashed for immutable provenance, not test oracles.
"""
import argparse
import ast
import csv
from datetime import datetime,timedelta,timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
WORKSPACE=REPO.parents[1]
sys.path.insert(0,str(ROOT.parent/'stage-1'))
from coverage_metadata import validate as metadata_validate
from semantic_oracle import parse,encode,same
from stage3_requirements import S1,S2,FREEZE,PACKAGE,SEED,cases
from stage3_oracle import Model,Refusal,selected,terms,weekly,resolve,interval,canonical,changes,serial_histories
from stage3_probe import validate_release,raw,fixture,policy,create_body
from stage3_trace import reference_trace
from stage3_browser import validate_selectors

PARTS={
 1:'9eb11d43-b397-4334-836b-9c7b2846255b',2:'922bd4ec-e90f-4f7f-9fb9-4cd1a0523de1',
 3:'9ff39574-3268-408a-86e6-a9461659a707',4:'dd525eab-20a9-4c49-9b58-35a1a969a7b7',
 5:'29a3f2b1-f70c-46e7-9314-738a079b91ac',6:'e709cbbb-201c-4cb0-aa75-0701672c61c6',
 7:'fa56ed3f-a241-4b1a-81a7-f42aec6a157d',8:'74b8f5ff-d1ee-4ee6-9136-ce72fcf8407a',
 9:'99e89c3f-6477-4e1a-bcbe-8216e19b59f8',10:'1e9fdad0-beac-454b-b0b2-b6af455f6df8',
 11:'0f8c047a-4dfe-414e-b399-a380a45fc7bf',12:'75eacf39-bc3e-4cf2-b3af-b1cfe75b6138',
 13:'847198b8-82a8-4ecb-8d3b-b02622f15b75'}

def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)

def run(out):
    started=datetime.now(timezone.utc);clock=time.monotonic();controls=[];commands=[]
    if out.exists():raise ValueError('unique preparation output required')
    out.mkdir(parents=True);sources=out/'source-inputs';sources.mkdir()
    def check(name,condition):
        controls.append(dict(name=name,passed=bool(condition),kind='local preparation/construction only'))
        if not condition:raise AssertionError(name)
    def command(argv,cwd=REPO):
        began=time.monotonic();p=subprocess.run(argv,cwd=cwd,capture_output=True)
        record=dict(argv=[str(x) for x in argv],cwd=str(cwd),returncode=p.returncode,seconds=time.monotonic()-began,
            stdout_bytes=len(p.stdout),stdout_sha256=sha(p.stdout),stderr_bytes=len(p.stderr),stderr_sha256=sha(p.stderr))
        commands.append(record)
        if p.returncode:raise RuntimeError('source command failed: '+repr(argv))
        return p.stdout
    error=None
    try:
        manifest=[]
        source_files=[('participant-guide.md',WORKSPACE/'kickoff/docs/participant-guide.md')]+[(f'stage-{n}.md',WORKSPACE/f'kickoff/tablekeeper/spec/stage-{n}.md') for n in (1,2,3)]
        source_files += [('PRODUCT_ACCEPTANCE.md',WORKSPACE/'factory/PRODUCT_ACCEPTANCE.md')]
        source_files += [(name,REPO/'evidence/coordinator'/name) for name in ['timestamp-representation-decision.md','receipt-shape-decision.md','numeric-control-decision.md','json-number-semantics-decision.md']]
        source_files += [('complete-handoff.md',REPO/f'evidence/coordinator/handoffs/{PACKAGE}.md'),
            ('delivery.json',REPO/f'evidence/coordinator/handoffs/{PACKAGE}-delivery.json'),
            ('accepted-stage2.json',REPO/'evidence/coordinator/accepted/stage-2.json')]
        for name,source in source_files:
            data=source.read_bytes();(sources/name).write_bytes(data)
            manifest.append(dict(source=str(source),copy=str(sources/name),bytes=len(data),sha256=sha(data)))
            check('source-copy-'+name,data==(sources/name).read_bytes())
        # Runtime END markers were observed in the delivered part13 and acknowledged.
        # Do not demand transport markers in the unsplit durable body file.
        intake=dict(package=PACKAGE,expected_parts=13,received_parts=[dict(part=i,inbound_message_id=PARTS[i]) for i in range(1,14)],
            end_observed_in_runtime_part=13,end_marker='END OF PACKAGE '+PACKAGE,complete_content_marker='END OF COMPLETE CONTENT '+PACKAGE,
            completeness_acknowledgment_action='jam_reply_to_message',acknowledged_inbound_message_id=PARTS[13],
            acknowledgment_reply_id='unknown',acknowledged_before_preparation=True,shared_card=21,
            accepted_stage1=S1,accepted_stage2=S2,coordinator_freeze_revision=FREEZE,highest_accepted_stage=2,
            scope='independent preparation only; candidate execution awaits complete later handoff',
            initial_package_authorizes_candidate_execution=False)
        save(out/'intake.json',intake)
        check('all-numbered-parts',set(PARTS)==set(range(1,14)))
        complete=(sources/'complete-handoff.md').read_text()
        for n in (1,2,3):check('complete-specification-'+str(n),(sources/f'stage-{n}.md').read_text().strip() in complete)
        freeze_source='evidence/coordinator/accepted/stage-2.json'
        sealed=command(['git','show',FREEZE+':'+freeze_source]);check('freeze-manifest-seal',sealed==(sources/'accepted-stage2.json').read_bytes())
        expected_trees={1:(S1,'75f6ece6952c570eedf8a548f4428a5b2c986128'),2:(S2,'422380c814043021c2df2daad8edbbb34d5b5887')}
        frozen=[]
        for n,(revision,expected) in expected_trees.items():
            tree=command(['git','rev-parse',revision+':stage-'+str(n)]).decode().strip();check('accepted-tree-'+str(n),tree==expected)
            entries=command(['git','ls-tree','-r',revision,'--','stage-'+str(n)]).decode().splitlines()
            for entry in entries:
                head,path=entry.split('\t');mode,kind,blob=head.split();data=command(['git','show',revision+':'+path])
                current=(REPO/path).read_bytes();check('frozen-production-'+path,current==data)
                frozen.append(dict(stage=n,candidate=revision,path=path,mode=mode,blob=blob,sha256=sha(data),current_matches=True))
        kickoff_revision=command(['git','rev-parse','HEAD'],WORKSPACE/'kickoff').decode().strip()
        kickoff_status=command(['git','status','--porcelain'],WORKSPACE/'kickoff').decode()
        check('kickoff-exact-clean',kickoff_revision=='803560d2a678ace1414465c098eb0ab5380ffade' and not kickoff_status)
        save(out/'source-proof.json',dict(source_copies=manifest,frozen_sources=frozen,kickoff_revision=kickoff_revision,kickoff_clean=not kickoff_status,
            production_imports=0,production_execution=0,production_edits=0,inspection_scope='hashes/byte identity only; no service implementation used as oracle'))

        own_sources=sorted(ROOT.glob('stage3_*.py'));source_manifest=[]
        for p in own_sources:
            data=p.read_bytes();tree=ast.parse(data,filename=str(p));source_manifest.append(dict(path=str(p),sha256=sha(data),bytes=len(data)))
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):check('safe-import-'+p.name+'-'+str(node.lineno),not (node.module or '').startswith(('core','server','json_codec','harness','stage-1','stage-2')))
            check('ast-'+p.name,True)
        save(out/'prepared-source-manifest.json',source_manifest)
        executed=out/'executed-source';executed.mkdir()
        for p in own_sources:(executed/p.name).write_bytes(p.read_bytes())
        from decoder_oracle import wrap,LEAF,LEAF_ALIAS
        constructions=[]
        for kind in ['policy','series']:
            body=raw(policy() if kind=='policy' else dict(anchor_reference='ABC12345',count=2,interval_weeks=1))
            parse(body);parse(LEAF);parse(LEAF_ALIAS)
            for shape in ['array','object','alternating']:
                for depth in [1100,5000,10000,20000]:
                    data=body[:-1]+b',"ignored":'+wrap(shape,depth,LEAF)+b'}'
                    constructions.append(dict(kind=kind,shape=shape,depth=depth,bytes=len(data),sha256=sha(data),
                        derivation='valid shallow finite leaf + exactly balanced independently composed wrappers; deep body not decoded'))
                    check('deep-construction-'+kind+'-'+shape+'-'+str(depth),data.startswith(body[:-1]) and data.endswith(b'}'))
        save(out/'deep-constructions.json',constructions)

        base=Model().base
        publications=[{**deepcopy(base),'effective_from':d,'policy_version':i} for i,d in enumerate(['2035-06-20','2035-06-01','2035-06-01','2000-01-01'],1)]
        for day,version in [('1999-12-31',0),('2000-01-01',4),('2035-05-31',4),('2035-06-01',3),('2035-06-19',3),('2035-06-20',1)]:
            check('policy-selection-'+day,selected(base,publications,day)['policy_version']==version)
        result=terms(publications[2]);check('terms-whole-no-date',set(result)==set(base) and 'effective_from' not in result)
        result['capacities']['a']=999;check('terms-detached',publications[2]['capacities']['a']==8)
        for pair in [('b','a'),('a','b')]:check('canonical-'+str(pair),canonical(pair,('a','b','c'),(('b','a'),('b','c')))==('b','a'))
        for pair,code in [(('a','a'),'validation_failed'),(('a','c'),'combination_not_allowed'),(('a','b','c'),'combination_not_allowed'),(('x',),'not_found')]:
            try:canonical(pair,('a','b','c'),(('b','a'),('b','c')))
            except Refusal as refusal:check('canonical-refusal-'+str(pair),refusal.code==code)
            else:check('canonical-refusal-'+str(pair),False)
        calendars=[]
        for zone,day,clock_value,gap in [('Europe/Berlin','2026-03-29','02:30',True),('Europe/Berlin','2026-10-25','02:30',False),
            ('America/New_York','2026-03-08','02:30',True),('America/New_York','2026-11-01','01:30',False)]:
            local=day+'T'+clock_value
            try:
                start,end=interval(local,zone,90);check('calendar-not-gap-'+zone,not gap)
                candidates=[datetime.fromisoformat(local).replace(tzinfo=__import__('zoneinfo').ZoneInfo(zone),fold=f).astimezone(timezone.utc) for f in (0,1)]
                check('first-fold-'+zone,start==min(candidates));check('absolute-duration-'+zone,(end-start).total_seconds()==5400)
                calendars.append(dict(zone=zone,local=local,instant=start.isoformat(),end=end.isoformat(),kind='first-fold'))
            except Refusal as refusal:
                check('calendar-gap-'+zone,gap and refusal.code=='invalid_local_time');calendars.append(dict(zone=zone,local=local,error=refusal.code,kind='model-gap'))
        for count in (2,8,12):
            for weeks in (1,2,4):
                days=weekly('2035-12-28T19:30',count,weeks)
                check('weekly-'+str(count)+'-'+str(weeks),len(days)==count and all(x.endswith('T19:30') for x in days) and all((datetime.fromisoformat(days[i])-datetime.fromisoformat(days[0])).days==i*weeks*7 for i in range(count)))
        save(out/'calendar-model.json',calendars)

        model=Model();a=model.create('A',('a','b'),'2035-06-04T18:00',5);b=model.create('B',('c',),'2035-06-04T18:00',2)
        check('pair-created-representation',a.history[0]['changes'][0]==dict(field='table_ids',**{'from':None},to=['b','a']))
        before=model.snapshot();model.batch([dict(reference='A',table_ids=['a','b'])]);check('reversed-noop-all',model.snapshot()==before)
        model.batch([dict(reference='A',table_ids=['c']),dict(reference='B',table_ids=['a','b'])])
        check('atomic-swap-revisions',model.bookings['A'].revision==model.bookings['B'].revision==2 and model.restaurant_revision==1)
        before=model.snapshot()
        try:model.batch([dict(reference='A',table_ids=['a','b'])])
        except Refusal as refusal:check('failed-overlap',refusal.code=='table_unavailable' and model.snapshot()==before)
        else:check('failed-overlap',False)
        try:model.batch([dict(reference='A',expected_revision=1,party_size=999)],editable=False)
        except Refusal as refusal:check('stale-before-cutoff-model',refusal.code=='stale_revision' and model.snapshot()==before)
        else:check('stale-before-cutoff-model',False)
        s=model.adopt('A',4,1);check('adoption-anchor',model.bookings['A'].revision==2 and model.bookings['A'].history==before[1]['A'].history)
        check('adoption-counter-once',model.restaurant_revision==2 and model.series[s].revision==1)
        model.batch([dict(reference='A',party_size=6),dict(reference='A-1',party_size=6)])
        check('batch-series-once',model.series[s].revision==2 and model.bookings['A'].exception and model.bookings['A-1'].exception)
        model.batch([dict(reference='A',party_size=5)]);check('permanent-exception-model',model.bookings['A'].exception)
        model.cancel('A-2');check('cancel-no-exception-model',not model.bookings['A-2'].exception)
        before=model.snapshot();model.cancel('A-2');check('repeat-cancel-model',model.snapshot()==before)
        model.cancel('A');check('anchor-siblings-model',model.bookings['A-1'].status=='confirmed' and model.bookings['A-3'].status=='confirmed')
        gap=Model(zone='Europe/Berlin');gap.create('G',('a',),'2026-03-22T02:30',2);before=gap.snapshot()
        try:gap.adopt('G',3,1)
        except Refusal as refusal:check('series-gap-rollback-model',refusal.code=='invalid_local_time' and gap.snapshot()==before)
        else:check('series-gap-rollback-model',False)
        initial=Model();initial.create('A',('a',),'2035-06-04T18:00',2)
        operations=[lambda m:(m.batch([dict(reference='A',expected_revision=1,party_size=3)]) or ['A']),lambda m:(m.batch([dict(reference='A',expected_revision=1,party_size=4)]) or ['A'])]
        check('exhaustive-serial-two',serial_histories(initial,operations,{0:['A'],1:'stale_revision'})==[[0,1]])
        trace=reference_trace();check('deterministic-reference-trace',trace==reference_trace())
        check('trace-160',len(trace['operations'])==160)
        for op in trace['operations']:
            state=op['reference_after']
            for ref,record in state['bookings'].items():
                check('trace-history-'+str(op['index'])+'-'+ref,[e['seq'] for e in record['history']]==list(range(1,len(record['history'])+1)))
                check('trace-revision-'+str(op['index'])+'-'+ref,record['revision']==record['history'][-1]['revision'])
        save(out/'reference-trace.json',trace)

        # No saved release authorizes execution. Even fully populated shape-control
        # objects exist only inside this pure function and never open connections.
        incomplete={'stage':3,'accepted_stage1':S1,'accepted_stage2':S2}
        try:validate_release(incomplete)
        except ValueError:check('unreleased-refused',True)
        else:check('unreleased-refused',False)
        proof=out/'source-proof.json';digest=sha(proof.read_bytes())
        release=dict(candidate='1'*40,systems_revision='2'*40,interface_revision='3'*40,stage=3,accepted_stage1=S1,accepted_stage2=S2,image_id='sha256:'+'4'*64,
            urls={name:'http://independent-verifier-model-'+name+':8080' for name in ('target','peer','accepted-s1','accepted-s2')},
            source_revisions={'accepted-s1':S1,'accepted-s2':S2})
        booleans=('complete_candidate_package','end_received','acknowledged_before_execution','execution_authorized','systems_full_handoff','interface_full_handoff',
            'fresh_clone_verified','current_packaged_hashes_verified','offline_2cpu_2g_no_service_mounts_verified','frozen_stage1_verified','frozen_stage2_verified')
        release.update({key:True for key in booleans})
        for key in ('source_proof','resource_proof','package_intake'):release[key+'_path']=str(proof);release[key+'_sha256']=digest
        check('release-shape-control',validate_release(release) is release)
        for key in booleans:
            invalid=deepcopy(release);invalid[key]=False
            try:validate_release(invalid)
            except ValueError:check('release-refusal-'+key,True)
            else:check('release-refusal-'+key,False)
        for key in ('candidate','systems_revision','interface_revision','image_id','accepted_stage1','accepted_stage2'):
            invalid=deepcopy(release);invalid[key]='pending'
            try:validate_release(invalid)
            except ValueError:check('release-refusal-'+key,True)
            else:check('release-refusal-'+key,False)
        for key in ('target','peer','accepted-s1','accepted-s2'):
            invalid=deepcopy(release);invalid['urls'][key]='http://external.invalid'
            try:validate_release(invalid)
            except ValueError:check('release-refusal-url-'+key,True)
            else:check('release-refusal-url-'+key,False)
        try:validate_selectors(release)
        except ValueError:check('no-invented-browser-selectors',True)
        else:check('no-invented-browser-selectors',False)
        save(out/'execution-release-template.json',dict(stage=3,candidate='pending later complete named candidate',accepted_stage1=S1,accepted_stage2=S2,
            execution_authorized=False,complete_candidate_package=False,end_received=False,systems_full_handoff=False,interface_full_handoff=False,
            note='Non-executable template. INITIAL-1 and pure shape controls never authorize candidate requests.'))

        all_cases=cases();check('new-case-identifiers',len({c['id'] for c in all_cases})==len(all_cases))
        save(out/'cases.json',dict(scope='prepared requirements only; every current verdict unverified',by_id={c['id']:c for c in all_cases}))
        inherited_path=REPO/'evidence/independent-verifier/stage-2/candidate-2/metadata-repair-01/coverage.csv'
        inherited_bytes=inherited_path.read_bytes();(sources/'historical-stage2-coverage.csv').write_bytes(inherited_bytes)
        check('historical-matrix-sealed',sha(inherited_bytes)=='71918164490be53bf334065f5aff2281ca536cfe4c06aa741ea78f0eb96060b4')
        inherited=list(csv.DictReader(inherited_path.open()));new_rows=[]
        prefix=out.relative_to(REPO).as_posix()
        extra=['prior_stage2_matrix','prior_stage2_candidate','prior_stage2_verdict','prior_stage2_command','prior_stage2_evidence','preparation_status']
        columns=list(inherited[0])+[k for k in extra if k not in inherited[0]]
        inherited_plan={}
        for old in inherited:
            row=dict(old);identifier=row['requirement_id'];inherited_plan[identifier]=dict(source_section=row['source_section'],introduced_stage=row['introduced_stage'],
                historical_verdict=old['verdict'],historical_candidate=old['candidate_full_revision'],current_verdict='unverified',
                required_execution='Fresh current Stage3 inherited executable/API/browser/source/runtime coverage; historical run not current proof.')
            row.update(prior_stage2_matrix='evidence/independent-verifier/stage-2/candidate-2/metadata-repair-01/coverage.csv',prior_stage2_candidate=old['candidate_full_revision'],
                prior_stage2_verdict=old['verdict'],prior_stage2_command=old['executable_command_or_interaction'],prior_stage2_evidence=old['evidence_path'],
                applicable_stages='3,4',candidate_full_revision='pending complete Stage3 candidate',verdict='unverified',inherited='yes',
                evidence_path=prefix+'/inherited-plan.json#/by_id/'+identifier,
                executable_command_or_interaction='PENDING EXECUTION: fresh Stage3 binding of inherited requirement '+identifier+'; prior Stage2 actual argv is historical only.',
                future_command_binding='Require later complete candidate package, fresh source/image/runtime identity and all applicable earlier independent/official protocols against Stage3. Save actual argv and concrete current file evidence.',
                interpretation_note=old['interpretation_note']+' Stage3: policies/terms/revisions/current representations accumulate; historical successful receipt bodies remain unchanged.',
                preparation_status='prepared only; file is a prospective obligation, not observed behavior')
            new_rows.append(row)
        save(out/'inherited-plan.json',dict(by_id=inherited_plan,prior_matrix_sha256=sha(inherited_bytes)))
        for case in all_cases:
            row={k:'' for k in columns};family=case['family'];method='real browser + direct HTTP + independent visual review' if family=='browser' else 'independent black-box HTTP + finite reference/source supplements where labelled'
            row.update(requirement_id=case['id'],requirement_text=case['text'],source_section='Stage3 '+case['section'],source_line=str(case['line']),source_file='stage-3.md',
                introduced_stage='3',applicable_stages='3,4',owner=case['owner'],implementation_owner=case['owner'],verification_owner='independent-verifier',
                candidate_full_revision='pending complete Stage3 candidate',verification_method=method,case=case['name'],
                interpretation_note='Complete specifications plus four adopted decisions. Preparation/model controls never establish service behavior. Exact restaurant counter observability requires labelled source/export supplement, not an invented public field. Product brief rows are task-specific quality obligations.',
                executable_command_or_interaction=('PENDING: ../../.venv/bin/python -B evidence/independent-verifier/stage-3/stage3_browser.py --release <later-complete-release.json> --out <new-unique-output> --execute; real selector bindings required' if family=='browser' else
                    'PENDING: ../../.venv/bin/python -B evidence/independent-verifier/stage-3/stage3_probe.py --family '+({'history':'terms','upgrade':'upgrade','terms':'terms','moves':'moves'}.get(family,family))+' --release <later-complete-release.json> --out <new-unique-output> --execute; bind exact executed cases and any labelled supplement'),
                evidence_path=prefix+'/cases.json#/by_id/'+case['id'],verdict='unverified',normative='True',preparation_origin='Independently derived INITIAL-1 full source, no builder/test oracle',
                preparation_status='prepared only; no candidate calls',inherited='no')
            new_rows.append(row)
        with (out/'coverage.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n');writer.writeheader();writer.writerows(new_rows)
        proof=metadata_validate(new_rows)
        for row in new_rows:
            check('current-unverified-'+row['requirement_id'],row['verdict']=='unverified' and row['candidate_full_revision']=='pending complete Stage3 candidate')
            path=REPO/row['evidence_path'].split('#',1)[0];check('concrete-link-'+row['requirement_id'],path.is_file())
        normative=sum(row['normative'].lower()=='true' for row in new_rows);diagnostic=len(new_rows)-normative
        check('inherited-counts',len(inherited)==6571 and sum(x['normative'].lower()=='true' for x in inherited)==6549 and diagnostic==22)
        proof.update(normative=normative,diagnostics=diagnostic,new_stage3_rows=len(all_cases),inherited_normative=6549,all_current_unverified=True,
            evidence_files_only=True,current_behavior_verified=0,candidate_revision='pending complete Stage3 candidate')
        save(out/'metadata-self-check.json',proof)
        (out/'PROTOCOL_BINDING.md').write_text('''# Stage 3 prepared protocol binding

This inventory is prospective. Each case requires a fresh exact candidate and actual row-level observations; a family command or model control alone is never coverage.

| Scope | Prepared executable / later binding |
| --- | --- |
| Effective dates, versions, immutability and managers | stage3_probe.py policies |
| Independent explanations and query grammar | stage3_probe.py explain |
| Complete policies, exact value/type/range controls | stage3_probe.py numeric |
| History, accepted terms and optional revisions | stage3_probe.py terms |
| Anchor/occurrences/exceptions/privacy | stage3_probe.py series |
| Failed occurrences and all-state rollback | stage3_probe.py rollback and calendar |
| Collective moves and series counters | stage3_probe.py moves |
| New idempotent paths | stage3_probe.py retry and concurrency |
| Deep ignored values, original receipts and raw transfers | stage3_probe.py deep |
| Genuine accepted Stage1/Stage2 migration | stage3_probe.py upgrade |
| Deterministic reference operations | stage3_probe.py trace; stage3_trace.py independently compares actual observed records |
| Actual diner terms/history/series and upgrades | stage3_browser.py; new selectors bound to real product, not invented IDs |
| Current restaurant counter observability | Later independently labelled source/opaque-state supplement; no invented public API field |
| Inherited 6,549 requirements / 22 separate admissions | Fresh Stage3 cumulative execution; prior CSV/argv is only history |

Remaining execution bindings include first-failure multi-error variants, legacy-origin additional profile chains, full staged final-byte concurrency/read histories, inherited runtime/protocol assembly and exact official suite counts. Their rows remain unverified. Candidate delivery may require further independently authored driver or selector/source supplements before every case can execute. This preparation does not assert that every prospective row has already run or that one command automatically covers its entire family.

Real-clock series adoption cannot succeed from past 2026 spring anchors because accepted cutoffs apply. The calendar model retains the specified 2026 transitions; real future 2035 series tests independently exercise gap/fold/duration. Earlier ordinary booking probes still exercise the published 2026 dates. Do not relabel a model result as a past-clock series HTTP observation.

No bulk series cancellation, manager private access, signup role or Stage4 endpoint is invented. Initial package authorizes preparation only. Actual execution waits the complete committed candidate and both full committed builder handoffs.
''')
        save(out/'artifact-manifest.json',[dict(path=str(p.relative_to(REPO)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(out.rglob('*')) if p.is_file()])
        summary=dict(package=PACKAGE,status='prepared; execution held',normative_rows=normative,unverified=normative,verified=0,failed=0,diagnostics=diagnostic,
            total_rows=len(new_rows),introduced_stage3_rows=len(all_cases),local_controls=len(controls),local_controls_passed=sum(c['passed'] for c in controls),
            reference_operations=160,seed=SEED,deep_constructions=len(constructions),own_python_files=len(own_sources),
            candidate_http_requests=0,browser_interactions=0,service_images_built=0,official_checks=0,production_edits=0,
            highest_consecutive_accepted_stage=2,accepted_stage1=S1,accepted_stage2=S2,
            started_utc=started.isoformat(),ended_utc=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-clock,
            harness='Codex',configured_model='gpt-6.1-sol',actual_model_override='unknown',effort='unknown',tokens='unknown',catalog_estimated_cost='unknown',billed_spend='unknown')
        save(out/'summary.json',summary)
        return summary
    except BaseException as exc:
        error=dict(kind='preparation-error',type=type(exc).__name__,message=str(exc));raise
    finally:
        save(out/'controls.json',controls);save(out/'commands.json',commands)
        save(out/'execution.json',dict(argv=sys.argv,cwd=str(Path.cwd()),started_utc=started.isoformat(),ended_utc=datetime.now(timezone.utc).isoformat(),
            seconds=time.monotonic()-clock,error=error,service_calls=0,browser_calls=0,production_execution=0,all_control_scope='preparation only'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args();out=Path(args.out).resolve()
    if not out.is_relative_to(ROOT):raise SystemExit('Only owned Stage3 evidence outputs permitted')
    print(json.dumps(run(out),indent=2))

if __name__=='__main__':main()
