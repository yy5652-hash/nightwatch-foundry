"""Additional independently derived current Stage4 boundaries; private bytes stay in memory."""
import argparse,copy,json,sys,threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,date,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from stage4_probe import Client,fixture,closure,DAY,raw,same,integer
from stage3_oracle import resolve
from stage3_probe import parse

def refuse(c,rid,operation,status=409,code='table_unavailable'):
    before=c.export();c.response(rid,operation(),status,code);c.check(rid+'-atomic',before==c.export())

def calendar(c,release):
    # Actual future HTTP operations; no clock substitution. Original scheduled dates
    # straddle each zone's spring/fall transition and independently resolve first fold.
    for zone,gap,fold,clock in [('Europe/Berlin','2035-03-25','2035-10-28','02:30'),('America/New_York','2035-03-11','2035-11-04','01:30')]:
        for kind,day,newclock in [('gap',gap,'02:30'),('fold',fold,clock)]:
            f=fixture();f['restaurants'][0]['timezone']=zone;c.setup(f)
            start=(date.fromisoformat(day)-timedelta(days=7)).isoformat();s=c.adopt(c.make(local=start+'T00:30'),count=2)
            if kind=='gap':
                refuse(c,'amend-dst-gap',lambda:c.amend(s,time=newclock),422,'invalid_local_time')
                c.response('amend-dst-gap-failed-reusable',c.amend(s,time='04:00'),201)
            else:
                got=c.response('amend-dst-fold',c.amend(s,time=newclock),201)
                for o in got['occurrences']:
                    r=o['reservation'];expected=resolve(r['starts_at_local'],zone)
                    c.check('amend-dst-fold',datetime.fromisoformat(r['starts_at'])==expected)
                    c.check('amend-absolute-duration',datetime.fromisoformat(r['ends_at'])-datetime.fromisoformat(r['starts_at'])==timedelta(minutes=30))
    # Different per-date policies require retained tables/party validation and end recomputation.
    for start in ['2035-12-25','2036-02-22','2036-12-29']:
        f=fixture();c.setup(f);anchor=c.make(local=start+'T18:00',party=2);s=c.adopt(anchor,count=3);r=f['restaurants'][0]
        policies=[]
        for index,duration in [(0,60),(1,90),(2,120)]:
            day=(date.fromisoformat(start)+timedelta(days=7*index)).isoformat()
            body={k:r[k] for k in ['slot_minutes','cancellation_cutoff_minutes','opening_hours']};body.update(effective_from=day,reservation_duration_minutes=duration,capacities={t['id']:t['capacity'] for t in r['tables']})
            p=c.response('calendar-policy',c.call('POST','/restaurants/r/policies',body,token=c.tokens['m'],key='p'+str(index)),201);policies.append(p)
        before=c.current_series(s);got=c.response('amend-real-policy',c.amend(before,time='19:00'),201)
        for i,(a,b) in enumerate(zip(before['occurrences'],got['occurrences'])):
            old=a['reservation'];new=b['reservation'];expected=(date.fromisoformat(start)+timedelta(days=7*i)).isoformat()+'T19:00'
            c.check('amend-calendar-boundary',new['starts_at_local']==expected)
            c.check('amend-retain-owner',new['reservation_id']==old['reservation_id'] and new['reference']==old['reference'])
            c.check('amend-retain-party',same(new['party_size'],old['party_size']) and same(new['table_ids'],old['table_ids']))
            c.check('amend-real-policy',integer(new['accepted_terms']['policy_version'])==i+1 and integer(new['accepted_terms']['reservation_duration_minutes'])==[60,90,120][i])
            c.check('amend-absolute-duration',datetime.fromisoformat(new['ends_at'])-datetime.fromisoformat(new['starts_at'])==timedelta(minutes=[60,90,120][i]))
        body={k:r[k] for k in ['slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','opening_hours']};body.update(effective_from=start,capacities={t['id']:1 for t in r['tables']})
        c.response('calendar-capacity-reduction',c.call('POST','/restaurants/r/policies',body,token=c.tokens['m'],key='reduce'),201)
        refuse(c,'amend-real-all-fields',lambda:c.amend(got,time='20:00',key='retained-fields'),422,'party_exceeds_capacity')
    c.seed();s=c.adopt(c.make(),count=2);ref=s['occurrences'][1]['reference']
    c.response('exception',c.call('PATCH','/reservations/'+ref,dict(party_size=2),token=c.tokens['u']),200);c.response('cancel-exception',c.call('POST','/reservations/'+ref+'/cancel',{},token=c.tokens['u']),200)
    now=c.current_series(s);got=c.response('amend-skip-both',c.amend(now,time='19:00'),201);c.check('amend-skip-both',same(now['occurrences'][1],got['occurrences'][1]))

def closures(c,release):
    c.seed();p=c.preview(closure(start=DAY+'T19:00:00+00:00',end=DAY+'T19:30:00+00:00'));c.response('closure-empty-apply',c.apply(p),201)
    for party in [1,10]:
        response=c.response('closure-availability',c.call('GET','/availability?'+urlencode(dict(restaurant_id='r',date=DAY,party_size=party,explain='true'))),200)
        slot=next(x for x in response['slots'] if x['starts_at_local']==DAY+'T19:00');a=next(x for x in slot['explain'] if x['table_id']=='a')
        c.check('closure-single-availability','a' not in slot['available_table_ids'])
        c.check('closure-pair-availability',all('a' not in o['table_ids'] for o in slot['available_options']))
        c.check('closure-explain-capacity',a['rules'][0]['holds'] is (party<=2) and a['rules'][1]['holds'] is False)
        if party==10:c.check('closure-explain-both',a['available'] is False and all(x['holds'] is False for x in a['rules']))
        if party==1:
            for clock in ['18:30','19:30']:
                adjacent=next(x for x in response['slots'] if x['starts_at_local']==DAY+'T'+clock);c.check('closure-unaffected-availability','a' in adjacent['available_table_ids'] and any(o['table_ids']==['b','a'] for o in adjacent['available_options']))
            c.check('closure-unaffected-availability','b' in slot['available_table_ids'])
    response=c.response('closure-without-explain',c.call('GET','/availability?'+urlencode(dict(restaurant_id='r',date=DAY,party_size=1))),200);c.check('closure-without-explain',all('explain' not in s for s in response['slots']))
    refuse(c,'closure-pair-create',lambda:c.call('POST','/reservations',dict(restaurant_id='r',table_ids=['b','a'],starts_at_local=DAY+'T19:00',party_size=4),token=c.tokens['u'],key='closed-pair'))
    a=c.make(local=DAY+'T18:00');b=c.make(seats=('c',),local=DAY+'T18:00',key='b')
    refuse(c,'closure-patch',lambda:c.call('PATCH','/reservations/'+a['reference'],dict(starts_at_local=DAY+'T19:00'),token=c.tokens['u']))
    refuse(c,'closure-batch',lambda:c.call('POST','/reservation-moves',dict(moves=[dict(reference=a['reference'],starts_at_local=DAY+'T19:00'),dict(reference=b['reference'],starts_at_local=DAY+'T20:00')]),token=c.tokens['u'],key='closed-move'))
    s=c.adopt(a,count=2);refuse(c,'closure-series-amend',lambda:c.amend(s,time='19:00'))
    c.seed();a=c.make();p=c.preview(closure(start='2035-06-11T18:00:00+00:00',end='2035-06-11T18:30:00+00:00'));c.response('closure-future-apply',c.apply(p),201)
    refuse(c,'closure-adoption',lambda:c.call('POST','/series',dict(anchor_reference=a['reference'],count=2,interval_weeks=1),token=c.tokens['u'],key='future-series'))
    c.seed();a=c.make();p=c.preview();c.response('closure-receipt-apply',c.apply(p),201)
    replay=c.response('closure-source-immutable',c.call('POST','/reservations',dict(restaurant_id='r',table_ids=['a'],starts_at_local=DAY+'T18:00',party_size=1),token=c.tokens['u'],key='create'),200);c.check('closure-source-immutable',same(a,replay) and c.lookup(a['reference'])['table_ids']!=a['table_ids'])

def scopes(c,release):
    f=fixture();f['restaurants'][0]['manager_user_ids']=['m','v'];c.setup(f);s=c.adopt(c.make());p=c.preview();paths={'preview':'/restaurants/r/replans','apply':'/restaurants/r/replans/'+p['plan_id']+'/apply','amend':'/series/'+s['series_id']+'/amend'}
    for family,path in paths.items():
        token=c.tokens['u'] if family=='amend' else c.tokens['m'];body=dict(expected_revision=s['revision'],from_index=0,local_time='18:00') if family=='amend' else closure() if family=='preview' else {}
        for key,name,code,status in [(None,'missing-key','missing_idempotency_key',400),('','empty-key','missing_idempotency_key',400),('x'*256,'256-char','validation_failed',422)]:refuse(c,'retry-'+family+'-'+name,lambda:pathcall(c,path,body,token,key),status,code)
    for name,restaurant,table in [('unknown-restaurant','missing','a'),('table-other-restaurant','r','x')]:refuse(c,'preview-'+name,lambda:c.call('POST','/restaurants/'+restaurant+'/replans',closure(table=table),token=c.tokens['m'],key=name),404,'not_found')
    for name,path,token,status,code in [('unknown-plan','/restaurants/r/replans/missing/apply',c.tokens['m'],404,'not_found'),('anonymous',paths['apply'],None,401,'unauthenticated'),('nonmanager',paths['apply'],c.tokens['u'],403,'forbidden')]:refuse(c,'apply-'+name,lambda:c.call('POST',path,{},token=token,key=name),status,code)
    refuse(c,'amend-unknown',lambda:c.call('POST','/series/missing/amend',dict(expected_revision=1,from_index=0,local_time='19:00'),token=c.tokens['u'],key='unknown'),404,'not_found')
    # Same literal key independent on two restaurant paths and two owned series paths.
    for restaurant,table in [('r','a'),('r2','x')]:c.response('retry-preview-path-scope',c.call('POST','/restaurants/'+restaurant+'/replans',closure(table=table),token=c.tokens['m'],key='shared-path'),201)
    owned=c.adopt(c.make(seats=('f',),local=DAY+'T21:00',key='second'),count=2,key='second-series')
    for series in [s,owned]:c.response('retry-amend-path-scope',c.amend(series,time='18:00' if series is s else '21:00',key='shared-path'),201)
    for token in [c.tokens['m'],c.tokens['v']]:c.response('retry-preview-user-scope',c.call('POST','/restaurants/r/replans',closure(table='b'),token=token,key='shared-user'),201)
    # Independent two diner agreements, genuinely owned by different users.
    got=c.response('other-create',c.call('POST','/reservations',dict(restaurant_id='r',table_id='e',starts_at_local=DAY+'T22:00',party_size=1),token=c.tokens['v'],key='other'),201)
    other=c.response('other-adopt',c.call('POST','/series',dict(anchor_reference=got['reference'],count=2,interval_weeks=1),token=c.tokens['v'],key='other'),201)
    for series,token,clock in [(s,c.tokens['u'],'18:00'),(other,c.tokens['v'],'22:00')]:c.response('retry-amend-user-scope',c.call('POST','/series/'+series['series_id']+'/amend',dict(expected_revision=series['revision'],from_index=0,local_time=clock),token=token,key='shared-user'),201)
    # Separate empty plans have the same application body and path-scoped key.
    for i,token in enumerate([c.tokens['m'],c.tokens['v']]):
        plan=c.preview(closure(table='d',start=DAY+'T23:00:00+00:00',end=DAY+'T23:30:00+00:00'),key='empty'+str(i));path='/restaurants/r/replans/'+plan['plan_id']+'/apply'
        c.response('retry-apply-path-scope',c.call('POST',path,{},token=token,key='shared-path'),201)
    # Same plan: second manager's identical key is a fresh attempt, hence applied error,
    # not the first manager's successful replay.
    plan=c.preview(closure(table='c',start=DAY+'T23:00:00+00:00',end=DAY+'T23:30:00+00:00'),key='sameplan');c.response('apply-manager',c.apply(plan,key='shared-user'),201)
    refuse(c,'retry-apply-user-scope',lambda:c.call('POST','/restaurants/r/replans/'+plan['plan_id']+'/apply',{},token=c.tokens['v'],key='shared-user'),409,'plan_already_applied')
    # Applied/stale current-resource failures must lose to stored different-body identity.
    refuse(c,'retry-apply-different-before-resource',lambda:c.apply(plan,key='shared-user',body={'ignored':1}),409,'idempotency_key_reuse')
    original=c.preview(closure(table='c'),key='priority');refuse(c,'retry-preview-different-before-resource',lambda:c.call('POST','/restaurants/r/replans',closure(table='missing'),token=c.tokens['m'],key='priority'),409,'idempotency_key_reuse')
    now=c.current_series(s);body=dict(expected_revision=now['revision'],from_index=0,local_time='19:00');c.response('amend-priority',pathcall(c,paths['amend'],body,c.tokens['u'],'priority'),201)
    refuse(c,'retry-amend-different-before-resource',lambda:pathcall(c,paths['amend'],{**body,'local_time':'invalid'},c.tokens['u'],'priority'),409,'idempotency_key_reuse')
    # There is no public permission revocation API. A source-derived diagnostic
    # establishes that a declaration contradicting existing manager receipts is
    # invalid state; it cannot manufacture a reachable permission-loss scenario.
    snapshot=parse(c.export());snapshot['state']['restaurants'][0]['manager_user_ids']=[]
    refuse(c,'manager-declaration-import-diagnostic',lambda:c.call('POST','/_test/import',body=raw(snapshot)),422,'validation_failed')

def pathcall(c,path,body,token,key):return c.call('POST',path,body,token=token,key=key)

def selection(c,release):
    f=fixture();f['restaurants'][1]['manager_user_ids']=[];c.setup(f)
    pair=c.make(seats=('a','b'),party=4);before=c.make(local=DAY+'T17:30',key='before');after=c.make(seats=('d',),local=DAY+'T18:30',key='after');cancelled=c.make(seats=('f',),key='cancelled')
    c.response('selection-cancel',c.call('POST','/reservations/'+cancelled['reference']+'/cancel',{},token=c.tokens['u']),200)
    other=c.response('selection-other-owner',c.call('POST','/reservations',dict(restaurant_id='r',table_id='c',starts_at_local=DAY+'T18:00',party_size=1),token=c.tokens['v'],key='other-owner'),201)
    c.response('selection-other-restaurant',c.call('POST','/reservations',dict(restaurant_id='r2',table_id='x',starts_at_local=DAY+'T18:00',party_size=1),token=c.tokens['u'],key='other-restaurant'),201)
    unmoved=c.adopt(c.make(seats=('f',),local=DAY+'T21:00',key='unmoved-series-anchor'),count=2,key='unmoved-series')
    refuse(c,'preview-restaurant-manager',lambda:c.call('POST','/restaurants/r2/replans',closure(table='x'),token=c.tokens['m'],key='restaurant-permission'),403,'forbidden')
    old=parse(c.export());body=closure(table='f',end=DAY+'T18:30:00+00:00');p=c.preview(body);now=parse(c.export())
    for field in old['state']:
        if field not in ['plans','receipts']:c.check('preview-readonly-'+field,same(old['state'][field],now['state'][field]))
    c.check('preview-selection',sorted(a['reference'] for a in p['assignments'])==sorted([pair['reference'],other['reference']]))
    c.check('preview-set-equality',all(a['changed'] is False for a in p['assignments']) and next(a for a in p['assignments'] if a['reference']==pair['reference'])['table_ids']==['b','a'])
    c.check('preview-plan-id',isinstance(p['plan_id'],str) and 1<=len(p['plan_id'])<=64)
    c.check('preview-response-closure',same(p['closure'],body))
    c.response('selection-unrelated-write',c.call('POST','/reservations',dict(restaurant_id='r2',table_id='x',starts_at_local=DAY+'T20:00',party_size=1),token=c.tokens['u'],key='unrelated'),201)
    histories={r:c.history(r) for r in [pair['reference'],before['reference'],after['reference'],cancelled['reference']]};applied=c.response('apply-other-restaurant',c.apply(p),201);new=parse(c.export())
    c.check('apply-response-id',applied['plan_id']==p['plan_id']);c.check('apply-response-all',[r['reference'] for r in applied['reservations']]==sorted([pair['reference'],other['reference']]))
    for prior in old['state']['reservations']:
        current=next(r for r in new['state']['reservations'] if r['reference']==prior['reference']);c.check('selection-identity-owner-status',all(same(prior[k],current[k]) for k in ['reservation_id','reference','user_id','created_at','starts_at','ends_at','starts_at_local','party_size','status','accepted_terms','table_ids','revision']))
    for ref,h in histories.items():c.check('apply-unmoved-history',same(h,c.history(ref)))
    c.check('series-repair-unmoved-series',same(unmoved,c.current_series(unmoved)))
    c.check('revision-apply-once',integer(applied['restaurant_revision'])==integer(p['restaurant_revision'])+1)
    refuse(c,'apply-already-before-stale',lambda:c.apply(p,key='fresh-applied'),409,'plan_already_applied')

def competing(c,release):
    c.seed();s=c.adopt(c.make(),count=3);plans=[c.preview(key='p'+str(i)) for i in range(50)];barrier=threading.Barrier(50)
    def op(i):barrier.wait();return c.apply(plans[i],key='different'+str(i))
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(op,range(50)))
    c.check('concurrency-apply-distinct',sorted(r[0] for r in results)==[201]+[409]*49 and all(r[1]['error']['code']=='stale_plan' for r in results if r[0]==409))
    winner=next(i for i,r in enumerate(results) if r[0]==201);got=c.current_series(s)
    c.check('concurrency-apply-distinct',integer(got['revision'])==2 and [o['reservation']['table_ids'] for o in got['occurrences']]==[['b'],['a'],['a']])
    # Failure keys remain reusable on the failed path after genuine replacement with
    # the captured before-apply state is independently verified in raw prefix families.
    for i,r in enumerate(results):
        if r[0]==409:c.response('concurrency-failure-keys',c.call('POST','/restaurants/r/replans/'+plans[i]['plan_id']+'/apply',{'ignored':1},token=c.tokens['m'],key='different'+str(i)),409,'stale_plan')
    c.seed();s=c.adopt(c.make(),count=2)
    for o in s['occurrences']:c.response('empty-cancel',c.call('POST','/reservations/'+o['reference']+'/cancel',{},token=c.tokens['u']),200)
    now=c.current_series(s);p=c.preview();before=c.public_state();c.response('amend-empty-success',c.amend(now),201);c.check('amend-empty-success',same(before,c.public_state()));c.response('staleness-empty-series',c.apply(p),201)
    c.seed();first=c.preview(key='first');second=c.preview(key='second');c.response('empty-apply',c.apply(first),201);refuse(c,'staleness-apply',lambda:c.apply(second,key='second'),409,'stale_plan')

def private(c,release):
    c.seed();p=c.preview();c.response('private-apply',c.apply(p),201);template=parse(c.export())
    for name in ['closure-table','plan-restaurant','receipt-original']:
        before=c.export();state=copy.deepcopy(template)
        if name=='closure-table':state['state']['closures'][0]['table_id']='missing'
        elif name=='plan-restaurant':state['state']['plans'][p['plan_id']]['restaurant_id']='missing'
        else:next(r for r in state['state']['receipts'] if r['path']=='/restaurants/r/replans')['response']['plan_id']='missing'
        c.response('private-state-invalid-'+name,c.call('POST','/_test/import',body=raw(state)),422,'validation_failed');c.check('private-state-invalid-'+name,before==c.export())
    c.seed();f=fixture();f['restaurants'][0]['tables']=[dict(id='a',label='A',capacity=4),dict(id='b',label='B',capacity=4),dict(id='c',label='C',capacity=4)];f['restaurants'][0]['combinable']=[['b','a'],['c','b']];c.setup(f)
    c.make(seats=('b','a'),party=7);p=c.preview();template=parse(c.export());template['state']['plans'][p['plan_id']]['assignments'][0]['table_ids'].reverse()
    before=c.export();c.response('private-state-invalid-plan-rank',c.call('POST','/_test/import',body=raw(template)),422,'validation_failed');c.check('private-state-invalid-plan-rank',before==c.export())

FAMILIES=dict(calendar=calendar,closures=closures,scopes=scopes,selection=selection,competing=competing,private=private)
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);p.add_argument('--family',choices=FAMILIES,required=True);a=p.parse_args();r=validate(json.loads(Path(a.release).read_text()));c=Client(r['urls']['target'],a.out,r['candidate']);error=None
    try:FAMILIES[a.family](c,r)
    except BaseException as e:error=repr(e);raise
    finally:c.save(error)
if __name__=='__main__':main()
