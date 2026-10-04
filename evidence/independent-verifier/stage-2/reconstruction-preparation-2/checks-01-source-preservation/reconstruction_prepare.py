"""Local preparation audit only: no HTTP, Docker, browser or service imports."""
import argparse
import ast
import collections
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent.parent
WORKSPACE=REPO.parent.parent
sys.path.insert(0,str(ROOT.parent/'stage-1'))
from coverage_metadata import responsible_owner,validate
from semantic_oracle import Number,parse,encode,same,self_check as numeric_self_check
from decoder_oracle import LEAF,LEAF_ALIAS,LEAF_DIFFERENT,LEAF_TYPED,wrap
from reconstruction_requirements import ROWS,ACCEPTED,PENDING,ORIGINS,SHAPES,DEPTHS,ID_CASES
from reconstruction_oracle import members,available,step,serial_witness,seeded_trace
from reconstruction_probe import body,deep_create,deep_moves,validate_release,fixture
from reconstruction_browser_protocol import opaque_ids,numeric_cases,token_spelling

PACKAGE='TK-20261004-S2-independent-verifier-RECONSTRUCT-2'
PREP=ROOT/'reconstruction-preparation-2'
NEW_FILES=['reconstruction_requirements.py','reconstruction_oracle.py','reconstruction_probe.py','reconstruction_browser_protocol.py','reconstruction_prepare.py']

def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n')

def controls():
    checks=[]
    def check(label,condition):
        checks.append(dict(label=label,passed=bool(condition)))
        if not condition:raise AssertionError(label)
    tables={'a':2,'b':4,'c':6};pairs=[['b','a'],['c','b']]
    check('declared-reverse-order',members(['a','b'],tables,pairs)==(['b','a'],None))
    check('not-transitive',members(['a','c'],tables,pairs)==(None,'combination_not_allowed'))
    check('duplicate-member',members(['a','a'],tables,pairs)==(None,'validation_failed'))
    check('three-members',members(['a','b','c'],tables,pairs)==(None,'combination_not_allowed'))
    check('wrong-member-type',members([1,'a'],tables,pairs)==(None,'malformed_request'))
    check('ordered-options',available(tables,pairs,[],0,90,5)==[dict(table_ids=['c'],capacity=6),dict(table_ids=['b','a'],capacity=6),dict(table_ids=['c','b'],capacity=10)])
    base=dict(reference='A',owner='U',table_ids=['b','a'],party_size=2,start=0,end=90,status='confirmed',created_at='original')
    check('half-open',available(tables,pairs,[base],90,180,5)==available(tables,pairs,[],90,180,5))
    check('one-minute-overlap',available(tables,pairs,[base],89,179,5)==[dict(table_ids=['c'],capacity=6)])
    state,result=step([base],dict(kind='patch',owner='U',reference='A',table_ids=['a','b']),tables,pairs)
    check('reverse-pair-is-noop',state==[base] and result=={'status':200})
    state,result=step([base],dict(kind='patch',owner='OTHER',reference='A',table_ids=['c']),tables,pairs)
    check('private-not-found',state==[base] and result==dict(status=404,code='not_found'))
    state,result=step([base],dict(kind='patch',owner='U',reference='A',table_ids=['missing'],cutoff_passed=True),tables,pairs)
    check('cutoff-before-change-validation',state==[base] and result==dict(status=409,code='cutoff_passed'))
    second=dict(base,reference='B',table_ids=['c'])
    swap=dict(kind='moves',owner='U',moves=[dict(reference='A',table_ids=['c']),dict(reference='B',table_ids=['b','a'])])
    state,result=step([base,second],swap,tables,pairs)
    check('atomic-occupied-swap',result=={'status':201} and state[0]['table_ids']==['c'] and state[1]['table_ids']==['b','a'])
    check('swap-identities-retained',state[0]['created_at']=='original' and state[0]['reference']=='A')
    bad=dict(kind='moves',owner='U',moves=[dict(reference='A',table_ids=['c']),dict(reference='B',table_ids=['c'])])
    state,result=step([base,second],bad,tables,pairs)
    check('failed-overlap-rollback',state==[base,second] and result==dict(status=409,code='table_unavailable'))
    early=dict(kind='moves',owner='U',moves=[dict(reference='A',table_ids=['a','c']),dict(reference='B',cutoff_passed=True)])
    state,result=step([base,second],early,tables,pairs)
    check('input-order-before-later-cutoff',state==[base,second] and result==dict(status=422,code='combination_not_allowed'))
    new_record=dict(base,reference='C',table_ids=['a'])
    operations=[dict(kind='cancel',owner='U',reference='A',started=1,finished=3,observed=dict(status=200)),
                dict(kind='create',record=new_record,started=2,finished=4,observed=dict(status=201))]
    check('serial-cancel-then-create',serial_witness([base],operations,tables,pairs)==[[0,1]])
    operations[1]['started']=0;operations[1]['finished']=0.5
    check('real-time-refutes-impossible-success',serial_witness([base],operations,tables,pairs)==[])
    for origin,(_,stage,profile) in ORIGINS.items():
        raw=body(stage,['b','a'] if stage==2 else ['a'],extra={'n':Number('9007199254740993.0')})
        value=parse(raw)
        check(origin+'-source-shape',('table_id' in value)==(stage==1) and ('table_ids' in value)==(stage==2))
        check(origin+'-numeric-projection',same(value['n'],Number('9007199254740992.0'),legacy=profile=='python-json-v1')==(profile=='python-json-v1'))
    for label in ID_CASES:
        ids=opaque_ids(label)
        check('opaque-'+label+'-limit',all(1<=len(x)<=64 for x in ids))
        check('opaque-'+label+'-distinct',len(set(ids))==4)
    check('opaque-exact64',all(len(x)==64 for x in opaque_ids('max64')))
    constructions=[]
    for shape in SHAPES:
        for depth in DEPTHS:
            leaf_value=parse(LEAF)
            check(f'{shape}-{depth}-leaf-alias',same(leaf_value,parse(LEAF_ALIAS)))
            check(f'{shape}-{depth}-leaf-difference',not same(leaf_value,parse(LEAF_DIFFERENT)))
            for category,raw in [('create',deep_create(shape,depth)),('moves',deep_moves(shape,depth,['REAL01','REAL02']))]:
                nested=wrap(shape,depth)
                check(f'{shape}-{depth}-{category}-envelope',raw.startswith(b'{') and raw.endswith(b'}') and nested in raw)
                constructions.append(dict(shape=shape,depth=depth,operation=category,bytes=len(raw),sha256=sha(raw),
                    grammar_basis='valid shallow leaf plus exact balanced array/object production; shallow envelope assembled before injection',deep_decoded=False))
    for spelling,seating,digits in numeric_cases():
        check(f'{spelling}-{seating}-{len(digits)}-token',same(parse(token_spelling(digits,spelling)),Number(digits)))
    invalid_release=dict(candidate='0'*40,accepted_stage1=ACCEPTED)
    refused=False
    try:validate_release(invalid_release)
    except ValueError:refused=True
    check('partial-release-execution-refused',refused)
    return checks,constructions

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out).resolve()
    if PREP.resolve() not in out.parents:p.error('new unique preparation output must stay in declared owned folder')
    out.mkdir(parents=True,exist_ok=False);began=time.monotonic();utc_start=dt.datetime.now(dt.timezone.utc).isoformat()
    checks=[];errors=[];historic_before={}
    try:
        historic_paths=[ROOT.parent/'stage-1/candidate-7/coverage.csv',ROOT/'candidate-1/coverage.csv',ROOT.parent/'stage-1/candidate-7/VERDICT.md']
        historic_before={str(x.relative_to(REPO)):sha(x.read_bytes()) for x in historic_paths}
        rows=[responsible_owner(r) for r in ROWS];metadata=validate(rows)
        assert all(r['verdict']=='unverified' and r['candidate_full_revision']==PENDING and r['evidence_path']=='PENDING_FRESH_STAGE2_EVIDENCE' for r in rows)
        fields=list(dict.fromkeys(k for r in rows for k in r))
        with (out/'coverage.csv').open('w',newline='') as h:
            writer=csv.DictWriter(h,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        metadata.update(normative_rows=sum(r['normative']=='True' for r in rows),diagnostic_rows=sum(r['normative']=='False' for r in rows),
            inherited_normative_rows=sum(r['introduced_stage']=='1' and r['normative']=='True' for r in rows),
            earlier_stage2_rows=sum(r['introduced_stage']=='2' and not r['requirement_id'].startswith('TK2R-') for r in rows),
            new_normative_rows=sum(r['requirement_id'].startswith('TK2R-') for r in rows),all_current_rows_unverified=True,
            prospective_candidate=PENDING,no_historical_evidence_as_current=True)
        write(out/'metadata.json',metadata)
        source_files={
            'participant-guide.md':WORKSPACE/'kickoff/docs/participant-guide.md',
            'stage-1.md':WORKSPACE/'kickoff/tablekeeper/spec/stage-1.md',
            'stage-2.md':WORKSPACE/'kickoff/tablekeeper/spec/stage-2.md',
            'PRODUCT_ACCEPTANCE.md':WORKSPACE/'factory/PRODUCT_ACCEPTANCE.md',
            'timestamp-decision.md':REPO/'evidence/coordinator/timestamp-representation-decision.md',
            'receipt-decision.md':REPO/'evidence/coordinator/receipt-shape-decision.md',
            'numeric-control-decision.md':REPO/'evidence/coordinator/numeric-control-decision.md',
            'numeric-value-decision.md':REPO/'evidence/coordinator/json-number-semantics-decision.md',
            'complete-package.md':REPO/f'evidence/coordinator/handoffs/{PACKAGE}.md',
            'delivery.json':REPO/f'evidence/coordinator/handoffs/{PACKAGE}.delivery.json',
            'accepted-freeze.json':REPO/f'evidence/coordinator/accepted/stage-1-{ACCEPTED}.json',
        }
        (out/'source-inputs').mkdir();sources=[]
        for name,path in source_files.items():
            raw=path.read_bytes();(out/'source-inputs'/name).write_bytes(raw)
            sources.append(dict(path=str(path),copy='source-inputs/'+name,bytes=len(raw),sha256=sha(raw)))
        write(out/'source-manifest.json',sources)
        delivery=json.loads((out/'source-inputs/delivery.json').read_text())
        assert sorted(x['part'] for x in delivery)==list(range(1,17))
        assert all(x['result']['status']=='accepted' for x in delivery)
        assert (out/'source-inputs/complete-package.md').read_text().rstrip().endswith('END OF PACKAGE '+PACKAGE)
        write(out/'intake.json',dict(package_id=PACKAGE,parts={str(x['part']):x['result']['message_id'] for x in delivery},end_received=True,
            acknowledgement_message_id='6d602d2e-1eae-435b-a8e1-a9a0b0523b57',complete_ack_before_preparation=True,
            preparation_authorized=True,execution_authorized=False,accepted_stage1=ACCEPTED,shared_assignment=18))
        frozen=json.loads((out/'source-inputs/accepted-freeze.json').read_text());assert frozen['candidate_full_revision']==ACCEPTED
        verdict=ROOT.parent/'stage-1/candidate-7/VERDICT.md';assert sha(verdict.read_bytes())==frozen['independent_verdict_sha256']
        frozen_files={}
        for entry in frozen['tree']:
            path=entry['path'];raw=subprocess.run(['git','show',ACCEPTED+':stage-1/'+path],cwd=REPO,capture_output=True,check=True).stdout
            actual=(REPO/'stage-1'/path).read_bytes();assert raw==actual
            frozen_files[path]=dict(accepted_blob=entry['object_id'],sha256=sha(actual),matches_accepted=True)
        freeze_revision=subprocess.run(['git','rev-parse','0f351f9'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip()
        write(out/'frozen-stage1-proof.json',dict(candidate=ACCEPTED,freeze_revision=freeze_revision,verdict_revision='a22de6b769c1454c35650377da1251edc99de744',files=frozen_files,production_imported=False))
        syntax=[]
        for name in NEW_FILES:
            tree=ast.parse((ROOT/name).read_text(),filename=name)
            imports=[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
            assert not any(x in ('core','server','json_codec') for x in imports)
            syntax.append(dict(path=name,sha256=sha((ROOT/name).read_bytes()),parsed=True,no_production_import=True))
        write(out/'syntax.json',syntax)
        checks,constructions=controls();checks+=numeric_self_check()
        write(out/'controls.json',checks);write(out/'deep-constructions.json',constructions)
        trace=seeded_trace();write(out/'reference-trace.json',trace)
        assert trace==seeded_trace();assert len(trace['operations'])==160
        write(out/'historical-preservation.json',dict(before=historic_before,after={str(x.relative_to(REPO)):sha(x.read_bytes()) for x in historic_paths},unchanged=all(sha(x.read_bytes())==historic_before[str(x.relative_to(REPO))] for x in historic_paths)))
        assert all(sha(x.read_bytes())==historic_before[str(x.relative_to(REPO))] for x in historic_paths)
    except Exception as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
        write(out/'controls-partial.json',checks)
    finally:
        summary=dict(mode='preparation only',package_id=PACKAGE,started_at=utc_start,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            seconds=time.monotonic()-began,controls=len(checks),failed_controls=sum(not x.get('passed',False) for x in checks),runner_errors=errors,
            candidate_http_requests=0,browser_interactions=0,images_built=0,official_checks=0,all_current_behavior_unverified=True,
            highest_consecutive_accepted_stage=1,harness='Codex',configured_model='gpt-6.1-sol',actual_model_effort_usage_catalog_estimate_billed_spend='unknown')
        write(out/'summary.json',summary)
        manifest=[dict(path=str(x.relative_to(out)),bytes=x.stat().st_size,sha256=sha(x.read_bytes())) for x in sorted(out.rglob('*')) if x.is_file()]
        write(out/'artifact-manifest.json',manifest);print(json.dumps(summary))
    return bool(errors or summary['failed_controls'])

if __name__=='__main__':raise SystemExit(main())
