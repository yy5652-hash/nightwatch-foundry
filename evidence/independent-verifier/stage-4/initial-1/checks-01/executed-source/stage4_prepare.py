"""Append-only local preparation controls; never imports or runs a service."""
import argparse
import ast
from copy import deepcopy
import csv
from datetime import date,datetime,timedelta,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];WORKSPACE=REPO.parents[1]
sys.path.insert(0,str(ROOT.parent/'stage-1'))
from coverage_metadata import validate as validate_metadata
from stage4_requirements import S1,S2,S3,PACKAGE,SEED,cases
from stage4_oracle import instant,overlap,seating_plan,cartesian_control,booking,State,Refusal,objective,options,serial_orders
from stage4_probe import validate_release,raw
from stage4_browser import validate_selectors
from decoder_oracle import wrap,LEAF,LEAF_ALIAS

PARTS={1:'b1c23304-6c7e-46cc-8a14-cb550492549f',2:'f4dd0a22-c5c3-436d-91db-99e099a5d997',3:'04c04a84-b61e-4e9d-b219-93bd8b21197d',
4:'ee499fbf-ec0c-438b-8226-6fc5c78215b1',5:'88d4857c-6317-49cd-91fe-46b427dadc18',6:'68b9feac-696d-43a5-8dac-ebc45ac22969',
7:'b49c3147-0e2a-4eb4-bedf-3253f25a4371',8:'d4b43234-2708-45dc-8967-301d34640bf2',9:'7203ed3b-755f-421b-9190-0ee105162068',
10:'64c49843-8fe4-40c8-a3a5-6332fb8bda2d',11:'bc106d4c-5c49-4d59-b48f-c3eaf71b7920',12:'a8dc2af2-1c23-4870-b81c-75f14fae49cc',
13:'885e9336-a6b6-45e8-84bc-4afa635f11f3',14:'37118efc-49f1-4288-82d8-b7d1a61dfcfd',15:'fd8f46fb-2f02-4fc8-9134-c46617532c62',
16:'67ae5d8e-8856-4d1e-b7c5-1a61946b69f1',17:'47f23042-65b1-4c2f-93e9-45375cc8acf2',18:'47359ae1-c962-4e88-940e-47c3f1ec4856',19:'e81d30db-b3e3-4cd3-9c62-00dbffce53be'}

def sha(data):return hashlib.sha256(data).hexdigest()
def serial(value):
    if isinstance(value,Fraction):return {'reference_fraction':str(value.numerator)+'/'+str(value.denominator)}
    raise TypeError(type(value).__name__)
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,default=serial)+'\n')

def run(out):
    if out.exists():raise ValueError('new unique preparation output required')
    out.mkdir(parents=True);started=datetime.now(timezone.utc);tick=time.monotonic();controls=[];commands=[];error=None
    def check(name,condition):
        controls.append(dict(name=name,passed=bool(condition),scope='local construction/provenance only'))
        if not condition:raise AssertionError(name)
    def command(argv,cwd=REPO):
        start=time.monotonic();p=subprocess.run(argv,cwd=cwd,capture_output=True)
        commands.append(dict(argv=[str(x) for x in argv],cwd=str(cwd),returncode=p.returncode,seconds=time.monotonic()-start,stdout_sha256=sha(p.stdout),stderr_sha256=sha(p.stderr)))
        if p.returncode:raise RuntimeError('source command failed '+repr(argv))
        return p.stdout
    try:
        sources=out/'source-inputs';sources.mkdir();manifest=[]
        inputs=[('participant-guide.md',WORKSPACE/'kickoff/docs/participant-guide.md'),('PRODUCT_ACCEPTANCE.md',WORKSPACE/'factory/PRODUCT_ACCEPTANCE.md')]
        inputs += [(f'stage-{n}.md',WORKSPACE/f'kickoff/tablekeeper/spec/stage-{n}.md') for n in range(1,5)]
        inputs += [(name,REPO/'evidence/coordinator'/name) for name in ['timestamp-representation-decision.md','receipt-shape-decision.md','numeric-control-decision.md','json-number-semantics-decision.md']]
        inputs += [('complete-handoff.txt',REPO/f'evidence/coordinator/handoffs/{PACKAGE}.txt'),('delivery.json',REPO/f'evidence/coordinator/handoffs/{PACKAGE}-delivery.json'),
                   ('accepted-stage3.json',REPO/'evidence/coordinator/accepted/stage-3.json'),('accepted-stage3-coverage.csv',ROOT.parent/'stage-3/candidate-1/coverage.csv')]
        for name,path in inputs:
            data=path.read_bytes();(sources/name).write_bytes(data);manifest.append(dict(source=str(path),copy=str(sources/name),bytes=len(data),sha256=sha(data)))
            check('source-copy-'+name,data==(sources/name).read_bytes())
        complete=(sources/'complete-handoff.txt').read_text()
        for name in ['participant-guide.md','PRODUCT_ACCEPTANCE.md']+[f'stage-{n}.md' for n in range(1,5)]:
            check('complete-direct-source-'+name,(sources/name).read_text().strip() in complete)
        check('every-part-id',set(PARTS)==set(range(1,20)))
        save(out/'intake.json',dict(package=PACKAGE,expected_parts=19,parts=[dict(part=i,inbound_message_id=PARTS[i]) for i in range(1,20)],
            runtime_end_marker='END '+PACKAGE,second_marker='FINAL COMPLETION MARKER: END '+PACKAGE,marker_part=19,
            acknowledged_by='jam_reply_to_message',acknowledged_inbound=PARTS[19],acknowledgment_reply_id='unknown',acknowledged_before_preparation=True,
            shared_card=24,highest_accepted_stage=3,scope='preparation only',candidate_execution_authorized=False,
            handoff_sha256=sha((sources/'complete-handoff.txt').read_bytes())))
        frozen=[]
        for stage,rev in [(1,S1),(2,S2),(3,S3)]:
            entries=command(['git','ls-tree','-r',rev,'--','stage-'+str(stage)]).decode().splitlines()
            for entry in entries:
                head,path=entry.split('\t');mode,kind,blob=head.split();data=command(['git','show',rev+':'+path]);current=(REPO/path).read_bytes()
                check('frozen-'+path,current==data and kind=='blob')
                frozen.append(dict(stage=stage,candidate=rev,path=path,mode=mode,blob=blob,sha256=sha(data),current_matches=True))
        check('frozen-file-count',len(frozen)==24)
        save(out/'source-proof.json',dict(copies=manifest,frozen=frozen,production_imports=0,production_execution=0,production_edits=0))
        csv.field_size_limit(sys.maxsize);sys.set_int_max_str_digits(0)
        previous=list(csv.DictReader((sources/'accepted-stage3-coverage.csv').open(newline='')))
        fields=['requirement_id','requirement_text','source_section','source_line','source_file','introduced_stage','applicable_stages','owner','implementation_owner','verification_owner',
                'candidate_full_revision','verification_method','executable_command_or_interaction','evidence_path','verdict','normative','case','interpretation_note',
                'inherited_from','previous_candidate','previous_verdict','previous_evidence','previous_command','preparation_status']
        current=[]
        for old in previous:
            row={k:old.get(k,'') for k in fields};row.update(applicable_stages='4',source_file=old.get('source_file') or 'stage-'+old['introduced_stage']+'.md',
                candidate_full_revision='pending complete Stage4 candidate',verdict='unverified',verification_method='preparation only; future fresh '+old['verification_method'],
                executable_command_or_interaction='PENDING: rerun the exact inherited independent protocol scope against released Stage4; bind actual argv/interaction afterwards',
                evidence_path=str(ROOT.relative_to(REPO)/'stage4_prepare.py'),inherited_from=str((sources/'accepted-stage3-coverage.csv').relative_to(REPO)),
                previous_candidate=old['candidate_full_revision'],previous_verdict=old['verdict'],previous_evidence=old['evidence_path'],previous_command=old['executable_command_or_interaction'],
                interpretation_note='Fresh Stage4 evidence required. Four adopted interpretations and source-faithful old bootstrap retained; historical CSV unchanged.',preparation_status='prepared; not candidate evidence')
            current.append(row)
        new=cases();check('atomic-new-identifiers',len({r['requirement_id'] for r in new})==len(new))
        for case in new:
            row={k:case.get(k,'') for k in fields};row.update(owner=case['implementation_owner'],candidate_full_revision='pending complete Stage4 candidate',verdict='unverified',
                verification_method='preparation only; future real browser' if case['family']=='product' else 'preparation only; future black-box HTTP and independently labelled source/model supplements',
                executable_command_or_interaction='PENDING: stage4_browser.py --execute --release <fresh current proof> --family <observed flow>' if case['family']=='product' else 'PENDING: stage4_probe.py --execute --release <fresh current proof> --family <bound obligation family>',
                evidence_path=str(ROOT.relative_to(REPO)/('stage4_browser.py' if case['family']=='product' else 'stage4_requirements.py')),
                interpretation_note='Exact written Stage4 scope; no prepared family pass establishes this row. Counter/timestamp grammar questions require exact current review.',preparation_status='prepared; not candidate evidence')
            current.append(row)
        metadata=validate_metadata(current)
        for r in current:check('file-link-'+r['requirement_id'],(REPO/r['evidence_path']).is_file())
        with (out/'coverage.csv').open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fields);writer.writeheader();writer.writerows(current)
        normative=sum(str(r['normative']).lower()=='true' for r in current)
        check('no-inherited-passes',all(r['verdict']=='unverified' for r in current))
        metadata.update(normative_rows=normative,normative_verified=0,normative_failed=0,normative_unverified=normative,diagnostics=len(current)-normative,concrete_file_links=True,new_stage4_rows=len(new),inherited_rows=len(previous))
        save(out/'metadata-self-check.json',metadata);save(out/'cases.json',new)
        own=[];executed=out/'executed-source';executed.mkdir()
        for path in sorted(ROOT.glob('stage4_*.py')):
            data=path.read_bytes();tree=ast.parse(data,filename=str(path));check('ast-'+path.name,True)
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):check('no-production-import-'+path.name+'-'+str(node.lineno),not (node.module or '').startswith(('core','server','json_codec','harness')))
            (executed/path.name).write_bytes(data);own.append(dict(path=str(path),sha256=sha(data),bytes=len(data)))
        save(out/'executed-source-manifest.json',own)

        base=instant('2035-06-04T18:00:00+00:00');check('offset-equality',base==instant('2035-06-04T20:00:00+02:00')==instant('2035-06-04T18:00:00Z'))
        exact=[]
        for digits in [1,6,7,18,64]:
            value=instant('2035-06-04T18:00:00.'+'0'*(digits-1)+'1+00:00')
            check('exact-fraction-'+str(digits),value-base==Fraction(1,10**digits))
            b=dict(start=base,end=base+1)
            check('half-open-'+str(digits),not overlap(b,dict(start=base-1,end=base)) and overlap(b,dict(start=base-1,end=value)))
            exact.append(dict(digits=digits,delta=value-base,scope='reference construction, not service input observation'))
        save(out/'exact-instant-constructions.json',exact)
        rng=random.Random(SEED);trace=[]
        for i in range(160):
            count=rng.randint(1,6);tables=tuple('abcdef'[:count]);all_pairs=[(tables[a],tables[b]) for a in range(count) for b in range(a+1,count)]
            rng.shuffle(all_pairs);pairs=tuple(all_pairs[:min(4,len(all_pairs))]);records=[]
            for j in range(rng.randint(0,6)):
                capacities={t:rng.randint(1,10) for t in tables};seat=tables[j%count];start=Fraction((j//count)*120)
                records.append(booking('R'+str(j).zfill(6),(seat,),start,start+60,capacities,rng.randint(1,capacities[seat])))
            c=dict(table_id=rng.choice(tables),start=Fraction(30),end=Fraction(300));fixed=booking('FIXED',(tables[-1],),300,360,{t:8 for t in tables})
            records.append(fixed);closures=[dict(table_id=tables[-1],start=Fraction(240),end=Fraction(270))] if count>2 else []
            try:
                result=seating_plan(tables,pairs,records,closures,c);check('oracle-small-independent-'+str(i),len(records)>4 or tuple([result['moved_count'],result['unused_seats'],tuple(result['rank_vector'])])==cartesian_control(tables,pairs,records,closures,c))
                verdict='feasible'
            except Refusal as refusal:
                check('oracle-refusal-'+str(i),refusal.code=='no_feasible_plan');result={'error':refusal.code};verdict='infeasible'
                if len(records)<=4:check('cartesian-infeasible-'+str(i),cartesian_control(tables,pairs,records,closures,c) is None)
            trace.append(dict(index=i,seed=SEED,tables=tables,pairs=pairs,bookings=records,closures=closures,proposed=c,result=result,verdict=verdict,scope='independent model construction; candidate operations zero'))
        save(out/'reference-trace.json',dict(seed=SEED,operations=trace))
        tables=tuple('abcdef');pairs=(('b','a'),('c','b'),('d','e'),('f','e'));caps={t:8 for t in tables}
        records=[booking('R'+str(i),(tables[i%2],),i//2*120,i//2*120+60,caps,2) for i in range(6)]
        fixed=booking('FIXED',('c',),300,360,caps);proposed=dict(table_id='a',start=Fraction(30),end=Fraction(300))
        full=seating_plan(tables,pairs,records+[fixed],[dict(table_id='f',start=Fraction(240),end=Fraction(270))],proposed)
        check('supported-six-four-six',len(full['assignments'])==6);save(out/'full-bound-construction.json',dict(tables=tables,pairs=pairs,bookings=records+[fixed],result=full))
        # A deliberately heterogeneous capacity construction distinguishes both lower objectives.
        one=booking('ONLY',('b',),0,60,dict(a=3,b=7,c=3),2)
        answer=seating_plan(('a','b','c'),(),[one],[],dict(table_id='a',start=0,end=60))
        check('changes-before-waste',answer['assignments'][0]['table_ids']==['b'] and answer['unused_seats']==5)
        one['seating']=('a',);answer=seating_plan(('a','b','c'),(),[one],[],dict(table_id='a',start=0,end=60))
        check('waste-before-rank',answer['assignments'][0]['table_ids']==['c'])
        one['accepted_terms']['capacities']['b']=3;answer=seating_plan(('a','b','c'),(),[one],[],dict(table_id='a',start=0,end=60))
        check('rank-final',answer['assignments'][0]['table_ids']==['b'])
        state=State(('a','b','c'),(),[one]);before=state.snapshot();p=state.preview(dict(table_id='a',start=0,end=60))
        check('preview-only-plans',all(state.snapshot()[k]==v for k,v in before.items() if k!='plans'))
        applied=state.apply(p['plan_id']);check('apply-once',state.restaurant_revision==1 and state.bookings['ONLY']['revision']==2)
        before=state.snapshot()
        try:state.apply(p['plan_id'])
        except Refusal as e:check('already-before-stale',e.code=='plan_already_applied' and state.snapshot()==before)
        fresh=state.preview(dict(table_id='c',start=100,end=200));state.restaurant_revision+=1;before=state.snapshot()
        try:state.apply(fresh['plan_id'])
        except Refusal as e:check('stale-rollback-model',e.code=='stale_plan' and state.snapshot()==before)
        # Original local schedules and old-cutoff inputs are explicitly finite model inputs.
        policy=dict(policy_version=0,slot_minutes=30,reservation_duration_minutes=30,cancellation_cutoff_minutes=0,capacities=dict(a=4,b=4),
                    opening_hours=[dict(weekday=d,opens='00:00',closes='23:59') for d in ['mon','tue','wed','thu','fri','sat','sun']])
        dates=[(date(2035,6,4)+timedelta(days=i*7)).isoformat() for i in range(4)]
        items=[booking('S'+str(i),('a',),instant(day+'T18:00:00+00:00'),instant(day+'T18:30:00+00:00'),policy['capacities'],2,
                       starts_at_local=day+'T18:00',accepted_terms=deepcopy(policy),series_id='series') for i,day in enumerate(dates)]
        model=State(('a','b'),(),items);model.series['series']=dict(revision=1,references=[b['reference'] for b in items],scheduled_dates=dates)
        model.bookings['S1']['exception']=True;model.bookings['S2']['status']='cancelled';old=deepcopy(model.bookings)
        changed=model.amend('series',1,0,'19:00',policy,[])
        check('series-skip-and-once',changed==['S0','S3'] and model.series['series']['revision']==2 and model.restaurant_revision==1)
        check('series-skipped-byte-model',model.bookings['S1']==old['S1'] and model.bookings['S2']==old['S2'])
        check('series-no-exceptions',not model.bookings['S0']['exception'] and not model.bookings['S3']['exception'])
        before=model.snapshot();check('series-noop-all',model.amend('series',2,0,'19:00',policy,[])==[] and model.snapshot()==before)
        try:model.amend('series',1,0,'23:59',policy,[],now=Fraction(10**20))
        except Refusal as e:check('series-stale-before-cutoff',e.code=='stale_revision' and model.snapshot()==before)
        for b in model.bookings.values():b['exception']=True
        before=model.snapshot();check('series-empty',model.amend('series',2,0,'20:00',policy,[])==[] and model.snapshot()==before)
        save(out/'series-model.json',dict(original_dates=dates,changed=changed,state=model.snapshot(),scope='finite local reference transitions only'))
        constructions=[]
        for endpoint,leaf in [('preview',dict(table_id='a',**{'from':'2035-06-04T18:00:00+00:00'},to='2035-06-04T19:00:00+00:00')),('apply',{}),('amend',dict(expected_revision=1,from_index=0,local_time='19:00'))]:
            shallow=raw(leaf)
            for shape in ['array','object','alternating']:
                for depth in [1100,5000,10000,20000]:
                    body=shallow[:-1]+(b',' if len(shallow)>2 else b'')+b'"ignored":'+wrap(shape,depth,LEAF)+b'}'
                    constructions.append(dict(endpoint=endpoint,shape=shape,depth=depth,bytes=len(body),sha256=sha(body),scope='balanced construction only; never decoded as deep private export'))
                    check('deep-'+endpoint+'-'+shape+'-'+str(depth),body.endswith(b'}'))
        save(out/'deep-constructions.json',constructions)
        try:validate_release(dict(stage=4,execution_authorized=False))
        except ValueError:check('unreleased-refused',True)
        else:check('unreleased-refused',False)
        try:validate_selectors({})
        except ValueError:check('unbound-browser-refused',True)
        else:check('unbound-browser-refused',False)
        save(out/'execution-release-template.json',dict(stage=4,candidate='pending',accepted_stage1=S1,accepted_stage2=S2,accepted_stage3=S3,execution_authorized=False,
             complete_candidate_package=False,end_received=False,systems_full_handoff=False,interface_full_handoff=False,selectors_observed_on_candidate=False,
             note='Not executable; proof fields and observed UI bindings require complete later source-bound release'))
        save(out/'summary.json',dict(status='prepared',rows=len(current),normative=normative,new_stage4=len(new),inherited=len(previous),diagnostics=len(current)-normative,
             verified=0,failed=0,unverified=normative,model_constructions=160,seed=SEED,candidate_http_requests=0,browser_interactions=0,images_built=0,official_checks=0,production_edits=0,
             controls=len(controls),passed=sum(c['passed'] for c in controls),start=started.isoformat(),end=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-tick,
             harness='Codex',configured_model='gpt-6.1-sol',actual_model_override='unknown',effort='unknown',tokens='unknown',estimated_cost='unknown',billed_spend='unknown'))
    except Exception as e:error=repr(e);raise
    finally:
        save(out/'controls.json',controls);save(out/'commands.json',commands)
        save(out/'execution.json',dict(argv=sys.argv,cwd=str(REPO),start=started.isoformat(),end=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-tick,error=error,complete=error is None,
             preparation_controls=len(controls),passed=sum(c['passed'] for c in controls),candidate_requests=0,production_imports=0,images_built=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out.resolve())
