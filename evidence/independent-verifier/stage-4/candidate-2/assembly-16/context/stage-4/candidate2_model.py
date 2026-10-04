"""160 real operations compared to own finite transition/history oracle."""
import argparse,copy,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from stage4_probe import Client,fixture,closure,DAY,integer,same,raw
from stage4_oracle import State,booking,instant,Refusal
from semantic_oracle import Number
from candidate2_full_bound import saved,control
SEED=2026100642
def integers(v):
    if isinstance(v,Number):return integer(v)
    if isinstance(v,list):return [integers(x) for x in v]
    if isinstance(v,dict):return {k:integers(x) for k,x in v.items()}
    return v
def stripped(entries):return [{k:v for k,v in e.items() if k!='at'} for e in entries]
def run(c):
    controls=[control(i) for i in range(160)];c.saved_artifacts={'small-unpruned-controls.json':raw(saved(controls))}
    c.seed();anchor=c.make();series=c.adopt(anchor,count=4)
    refs=[o['reference'] for o in series['occurrences']]
    c.response('model-setup-exception',c.call('PATCH','/reservations/'+refs[1],dict(party_size=2),token=c.tokens['u']),200)
    c.response('model-setup-cancelled',c.call('POST','/reservations/'+refs[2]+'/cancel',{},token=c.tokens['u']),200)
    current=c.current_series(series);base=fixture()['restaurants'][0];base={**base,'policy_version':0,'capacities':{t['id']:t['capacity'] for t in base['tables']}}
    initial=[];immutable={}
    for occurrence in current['occurrences']:
        r=occurrence['reservation'];immutable[r['reference']]=copy.deepcopy(r)
        initial.append(booking(r['reference'],r['table_ids'],instant(r['starts_at']),instant(r['ends_at']),integers(r['accepted_terms']['capacities']),integer(r['party_size']),reservation_id=r['reservation_id'],created_at=r['created_at'],starts_at_local=r['starts_at_local'],accepted_terms=integers(r['accepted_terms']),revision=integer(r['revision']),status=r['status'],history=integers(stripped(c.history(r['reference'])['entries'])),series_id=series['series_id'],exception=occurrence['exception']))
    m=State(tuple('abcdef'),base['combinable'],initial);m.restaurant_revision=4
    m.series[series['series_id']]=dict(revision=3,references=refs,scheduled_dates=[o['reservation']['starts_at_local'][:10] for o in series['occurrences']])
    c.check('model-setup-independent-counters',integer(current['revision'])==3 and [integer(o['reservation']['revision']) for o in current['occurrences']]==[1,2,2,1])
    rng=random.Random(SEED);plans=[];receipts=[];traces=[]
    def statecheck(index):
        actual=c.current_series(series);c.check('model-series-revision',integer(actual['revision'])==m.series[series['series_id']]['revision'])
        for i,o in enumerate(actual['occurrences']):
            b=m.bookings[refs[i]];r=o['reservation'];old=immutable[refs[i]]
            c.check('model-identity-owner-index-flags',o['reference']==refs[i] and integer(o['index'])==i and o['exception'] is b['exception'] and all(same(r[k],old[k]) for k in ['reservation_id','reference','created_at','party_size']))
            c.check('model-record-current',same(r['table_ids'],list(b['seating'])) and r['status']==b['status'] and integer(r['revision'])==b['revision'] and r['starts_at_local']==b['starts_at_local'] and instant(r['starts_at'])==b['start'] and instant(r['ends_at'])==b['end'] and same(r['accepted_terms'],b['accepted_terms']))
            h=c.history(refs[i])['entries'];c.check('model-history-exact',same(stripped(h),b['history']))
            c.check('model-history-sequence-time',all(integer(e['seq'])==j+1 for j,e in enumerate(h)) and all(instant(x['at'])<=instant(y['at']) for x,y in zip(h,h[1:])))
        p=c.preview(closure('f',start=DAY+'T22:30:00+00:00',end=DAY+'T23:00:00+00:00'),key='counter-'+str(index));c.check('model-restaurant-revision',integer(p['restaurant_revision'])==m.restaurant_revision)
    for index in range(160):
        kind=rng.choice(['preview','apply','amend','amend','no-op','stale','replay']);key='model-'+str(index);before=c.export();model_before=m.snapshot();expected_error=None;path=None;body=None;result=None
        if kind=='replay' and receipts:
            path,body,who,oldkey,original=copy.deepcopy(rng.choice(receipts));result=c.response('model-original-replay',c.call('POST',path,body,token=c.tokens[who],key=oldkey),200);c.check('model-original-receipt',same(original,result));c.check('model-replay-atomic',before==c.export())
        elif kind=='apply' and plans:
            plan=rng.choice(plans);path='/restaurants/r/replans/'+plan+'/apply';body={};who='m'
            try:expected=m.apply(plan)
            except Refusal as exc:expected_error=exc.code
            response=c.call('POST',path,body,token=c.tokens[who],key=key)
            result=c.response('model-apply-error' if expected_error else 'model-apply',response,404 if expected_error=='not_found' else 409 if expected_error else 201,expected_error)
            if not expected_error:c.check('model-apply-revision-order',integer(result['restaurant_revision'])==m.restaurant_revision and [r['reference'] for r in result['reservations']]==[r['reference'] for r in expected['reservations']])
        elif kind in ['amend','no-op','stale']:
            clock='18:00' if kind=='no-op' else rng.choice(['18:30','19:00','19:30','20:00']);start=rng.choice([0,1,3]);revision=m.series[series['series_id']]['revision']-(1 if kind=='stale' else 0);revision=max(1,revision)
            path='/series/'+series['series_id']+'/amend';body=dict(expected_revision=revision,from_index=start,local_time=clock);who='u'
            try:m.amend(series['series_id'],revision,start,clock,base,[])
            except Refusal as exc:expected_error=exc.code
            result=c.response('model-amend-error' if expected_error else 'model-amend',c.call('POST',path,body,token=c.tokens[who],key=key),409 if expected_error else 201,expected_error)
        else:
            body=closure(rng.choice('abc'),start=DAY+'T18:00:00+00:00',end='2035-06-26T20:30:00+00:00');path='/restaurants/r/replans';who='m';proposal=dict(table_id=body['table_id'],start=instant(body['from']),end=instant(body['to']))
            try:expected=m.preview(proposal)
            except Refusal as exc:expected_error=exc.code
            result=c.response('model-preview-error' if expected_error else 'model-preview',c.call('POST',path,body,token=c.tokens[who],key=key),409 if expected_error else 201,expected_error)
            if not expected_error:
                for field in ['assignments','moved_count','unused_seats']:c.check('model-preview-'+field,same(result[field],expected[field]))
                placeholder=expected['plan_id'];new=m.plans.pop(placeholder);new['plan_id']=result['plan_id'];m.plans[result['plan_id']]=new;plans.append(result['plan_id'])
        if expected_error:
            c.check('model-failure-raw-atomic',before==c.export());c.check('model-failure-reference-atomic',model_before==m.snapshot())
        elif kind!='replay':receipts.append((path,body,who,key,copy.deepcopy(result)))
        statecheck(index);traces.append(dict(index=index,kind=kind,path=path,body=body,expected_error=expected_error,restaurant_revision=m.restaurant_revision,series_revision=m.series[series['series_id']]['revision'],request_count=c.count))
    c.saved_artifacts.update({'actual-model-operation-traces.json':raw(traces),'model-summary.json':(json.dumps(dict(seed=SEED,actual_operations=160,small_unpruned_controls=160,private_state_saved=False),indent=2)+'\n').encode()})
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate(json.loads(Path(a.release).read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
    try:run(c)
    except BaseException as exc:error=repr(exc);raise
    finally:
        c.save(error)
        for name,data in getattr(c,'saved_artifacts',{}).items():(c.out/name).write_bytes(data)
if __name__=='__main__':main()
