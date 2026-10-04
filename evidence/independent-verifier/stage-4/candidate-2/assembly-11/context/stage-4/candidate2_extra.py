"""Prepared original receipts, genuine transfer, deep and counter protocols."""
import argparse
from copy import deepcopy
from datetime import date,timedelta
import json
from pathlib import Path
from urllib.parse import quote
from stage4_probe import Client,fixture,closure,DAY,validate_release,raw,same,integer,wrap,LEAF,LEAF_ALIAS

def replay_family(c):
    c.seed();anchor=c.make();series=c.adopt(anchor)
    endpoints=[('preview','/restaurants/r/replans',closure()),('apply',None,{}),
               ('amend','/series/'+series['series_id']+'/amend',dict(expected_revision=1,from_index=0,local_time='19:00'))]
    plan=None;receipts=[]
    for name,path,body in endpoints:
        if name=='apply':path='/restaurants/r/replans/'+plan['plan_id']+'/apply'
        if name=='amend':body={**body,'expected_revision':c.current_series(series)['revision']}
        token=c.tokens['u'] if name=='amend' else c.tokens['m']
        body=deepcopy(body);body['ignored']={'number':1,'array':[1,2]}
        key='retry-'+name;got=c.response('retry-'+name+'-same-json',c.call('POST',path,body,token=token,key=key),201)
        if name=='preview':plan=got
        alias=raw(body).replace(b'"number":1',b'"number":1.0')
        again=c.response('retry-'+name+'-numeric-alias',c.call('POST',path,body=alias,token=token,key=key),200)
        c.check('retry-'+name+'-numeric-alias',same(got,again))
        for slug,changed in [('boolean-distinct',{'number':True,'array':[1,2]}),('array-order',{'number':1,'array':[2,1]}),('ignored-equality',{'number':2,'array':[1,2]})]:
            altered={**body,'ignored':changed};before=c.export()
            c.response('retry-'+name+'-'+slug,c.call('POST',path,altered,token=token,key=key),409,'idempotency_key_reuse')
            c.check('retry-'+name+'-'+slug,before==c.export())
        invalid={**body,'local_time':'invalid'} if name=='amend' else {**body,'from':'invalid'}
        c.response('retry-'+name+'-different-before-validation',c.call('POST',path,invalid,token=token,key=key),409,'idempotency_key_reuse')
        receipts.append((path,body,token,key,got))
    # Actual later mutation cannot rewrite these successful originals.
    c.response('setup-later-cancel',c.call('POST','/reservations/'+anchor['reference']+'/cancel',{},token=c.tokens['u']),200)
    for path,body,token,key,got in receipts:c.check('retry-original-after-mutation',same(got,c.response('retry-original-after-mutation',c.call('POST',path,body,token=token,key=key),200)))

def deep_family(c,release):
    for shape in ['array','object','alternating']:
        for depth in [1100,5000,10000,20000]:
            c.seed();anchor=c.make();s=c.adopt(anchor);p=None;receipts=[]
            for name,body in [('preview',closure()),('apply',{}),('amend',dict(expected_revision=1,from_index=0,local_time='19:00'))]:
                if name=='amend':body={**body,'expected_revision':c.current_series(s)['revision']}
                path='/restaurants/r/replans' if name=='preview' else '/restaurants/r/replans/'+p['plan_id']+'/apply' if name=='apply' else '/series/'+s['series_id']+'/amend'
                token=c.tokens['u'] if name=='amend' else c.tokens['m'];key=name+'-'+shape+'-'+str(depth);leaf=raw(body)
                data=leaf[:-1]+(b',' if len(leaf)>2 else b'')+b'"ignored":'+wrap(shape,depth,LEAF)+b'}'
                alias=leaf[:-1]+(b',' if len(leaf)>2 else b'')+b'"ignored":'+wrap(shape,depth,LEAF_ALIAS)+b'}'
                got=c.response('deep-'+name+'-'+shape+'-'+str(depth),c.call('POST',path,body=data,token=token,key=key),201)
                if name=='preview':p=got
                c.check('deep-'+name+'-'+shape+'-'+str(depth),same(got,c.response('deep-replay',c.call('POST',path,body=alias,token=token,key=key),200)))
                receipts.append((path,data,token,key,got))
            exported=c.export();c.response('upgrade-mixed-second',c.transfer(c.base,release['urls']['peer'],exported),204)
            c.response('upgrade-mixed-second',c.transfer(release['urls']['peer'],c.base,c.export(release['urls']['peer'])),204)
            for path,data,token,key,got in receipts:c.check('deep-raw-replay',same(got,c.response('deep-raw-replay',c.call('POST',path,body=data,token=token,key=key),200)))

def migration_family(c,release):
    for origin,stage in [('accepted-s1',1),('accepted-s2',2),('accepted-s3',3)]:
        source=release['urls'][origin];c.setup(fixture(),url=source)
        body=dict(restaurant_id='r',starts_at_local=DAY+'T18:00',party_size=1)
        body['table_id' if stage==1 else 'table_ids']='a' if stage==1 else ['a']
        created=c.response('upgrade-'+origin,c.call('POST','/reservations',body,token=c.tokens['u'],key='original',url=source),201)
        move=dict(moves=[dict(reference=created['reference'],starts_at_local=DAY+'T18:30')])
        moved=c.response('upgrade-move-receipts',c.call('POST','/reservation-moves',move,token=c.tokens['u'],key='old-move',url=source),201)
        tokens=dict(c.tokens);series=None
        if stage==3:
            series=c.response('upgrade-series-receipts',c.call('POST','/series',dict(anchor_reference=created['reference'],count=4,interval_weeks=1),token=tokens['u'],key='old-series',url=source),201)
            r1=series['occurrences'][1]['reference'];r2=series['occurrences'][2]['reference']
            c.response('setup-old-exception',c.call('PATCH','/reservations/'+r1,dict(party_size=2),token=tokens['u'],url=source),200)
            c.response('setup-old-cancel',c.call('POST','/reservations/'+r2+'/cancel',{},token=tokens['u'],url=source),200)
        exported=c.export(source)
        c.seed();destination_token=c.tokens['u']
        c.response('upgrade-'+origin,c.transfer(source,c.base,exported),204);c.tokens=tokens
        c.response('upgrade-replace',c.call('GET','/reservations',token=destination_token),401,'unauthenticated')
        c.check('upgrade-create-receipts',same(created,c.response('upgrade-create-receipts',c.call('POST','/reservations',body,token=tokens['u'],key='original'),200)))
        c.check('upgrade-move-receipts',same(moved,c.response('upgrade-move-receipts',c.call('POST','/reservation-moves',move,token=tokens['u'],key='old-move'),200)))
        if series is None:series=c.adopt(c.lookup(created['reference']))
        else:c.series_ids=[series['series_id']]
        now=c.current_series(series);changed=c.response('upgrade-imported-amend',c.amend(now,time='19:00',key='new-amend'),201)
        applied=None;p=None
        if stage==3:
            p=c.preview(closure(start=DAY+'T17:00:00+00:00',end=DAY+'T21:00:00+00:00'),key='new-preview')
            applied=c.response('upgrade-imported-repair',c.apply(p,key='new-apply'),201)
        else:
            c.response('upgrade-source-faithful-no-invented-manager',c.call('POST','/restaurants/r/replans',closure(),token=tokens['m'],key='no-invented-manager'),403,'forbidden')
        capture=c.export();c.response('upgrade-mixed-second',c.transfer(c.base,release['urls']['peer'],capture),204)
        c.response('upgrade-mixed-second',c.transfer(release['urls']['peer'],c.base,c.export(release['urls']['peer'])),204)
        if p is not None:
            c.check('upgrade-plans-transfer',same(applied,c.response('upgrade-plans-transfer',c.apply(p,key='new-apply'),200)))
        c.check('upgrade-series-receipts',same(changed,c.response('upgrade-series-receipts',c.amend(now,time='19:00',key='new-amend'),200)))

def staleness_family(c):
    # Revision observed by subsequent public previews, no invented counter API.
    events=['create','patch','cancel','policy','batch','adopt','series-amend','noop-patch','noop-batch','repeat-cancel','noop-series','preview','failed-write','replay','other-restaurant']
    for event in events:
        c.seed();a=c.make();s=c.adopt(a);cur=c.current_series(s)
        companion=c.make(seats=('f',),local=DAY+'T21:00',key='new-anchor') if event=='adopt' else None
        if event=='repeat-cancel':c.response('setup-cancel',c.call('POST','/reservations/'+a['reference']+'/cancel',{},token=c.tokens['u']),200)
        p=c.preview(closure(start=DAY+'T22:00:00+00:00',end=DAY+'T23:00:00+00:00'),key='before')
        change=event in ['create','patch','cancel','policy','batch','adopt','series-amend']
        if event=='create':c.make(seats=('f',),local=DAY+'T21:00',key='new')
        elif event in ['patch','noop-patch']:
            c.response('setup-write',c.call('PATCH','/reservations/'+a['reference'],dict(party_size=2 if change else 1),token=c.tokens['u']),200)
        elif event in ['cancel','repeat-cancel']:c.response('setup-write',c.call('POST','/reservations/'+a['reference']+'/cancel',{},token=c.tokens['u']),200)
        elif event=='policy':
            r=fixture()['restaurants'][0];body={k:r[k] for k in ['slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','opening_hours']}
            body.update(effective_from='2000-01-01',capacities={t['id']:t['capacity'] for t in r['tables']})
            c.response('setup-policy',c.call('POST','/restaurants/r/policies',body,token=c.tokens['m'],key='policy'),201)
        elif event in ['batch','noop-batch']:
            c.response('setup-write',c.call('POST','/reservation-moves',dict(moves=[dict(reference=a['reference'],party_size=2 if change else 1)]),token=c.tokens['u'],key='batch'),201)
        elif event=='adopt':c.adopt(companion,key='new-adopt')
        elif event in ['series-amend','noop-series']:c.response('setup-write',c.amend(cur,time='19:00' if change else '18:00'),201)
        elif event=='preview':c.preview(closure(table='b'),key='another-preview')
        elif event=='failed-write':c.response('setup-failed',c.call('PATCH','/reservations/'+a['reference'],dict(party_size=10000),token=c.tokens['u']),422,'party_exceeds_capacity')
        elif event=='replay':c.response('setup-replay',c.call('POST','/series',dict(anchor_reference=a['reference'],count=4,interval_weeks=1),token=c.tokens['u'],key='adopt'),200)
        elif event=='other-restaurant':c.response('setup-other',c.call('POST','/reservations',dict(restaurant_id='r2',table_id='x',starts_at_local=DAY+'T18:00',party_size=1),token=c.tokens['u'],key='other'),201)
        observed=c.preview(closure(table='b',start=DAY+'T22:00:00+00:00',end=DAY+'T23:00:00+00:00'),key='after')
        c.check('revision-'+event,integer(observed['restaurant_revision'])==integer(p['restaurant_revision'])+(1 if change else 0))
        result=c.apply(p,key='probe-apply')
        c.response('staleness-'+event,result,409 if change else 201,'stale_plan' if change else None)

FAMILIES={'retry':replay_family,'deep':deep_family,'upgrade':migration_family,'staleness':staleness_family}
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--family',choices=FAMILIES,required=True)
    p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:raise SystemExit('Candidate execution held')
    release=validate_release(json.loads(a.release.read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
    try:
        if a.family in ['deep','upgrade']:FAMILIES[a.family](c,release)
        else:FAMILIES[a.family](c)
    except Exception as e:error=repr(e);raise
    finally:c.save(error)
if __name__=='__main__':main()
