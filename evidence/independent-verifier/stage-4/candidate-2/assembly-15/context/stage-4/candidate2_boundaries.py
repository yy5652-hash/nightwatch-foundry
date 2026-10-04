"""Individually separated supported bounds, exact fractions and amendment inputs."""
import argparse,copy,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from stage4_probe import Client,fixture,closure,DAY,integer,same,raw
from stage4_requirements import TOKENS
from semantic_oracle import parse

def dimensions(c):
    for dimension in ['tables','pairs','bookings']:
        for n in range(8):
            f=fixture();r=f['restaurants'][0];r['combinable']=[]
            if dimension=='tables':r['tables']=[dict(id=str(i),label='Table '+str(i),capacity=8) for i in range(n)]
            elif dimension=='pairs':r['combinable']=[[a,b] for a,b in [('a','b'),('a','c'),('a','d'),('a','e'),('a','f'),('b','c'),('b','d')]][:n]
            c.setup(f)
            if dimension=='bookings':
                for i in range(n):c.make(('a',),'2035-06-'+str(4+i).zfill(2)+'T18:00',key='b'+str(i))
            table='0' if dimension=='tables' else 'a';body=closure(table,start=DAY+'T17:00:00+00:00',end='2035-06-12T20:00:00+00:00');before=c.export();response=c.call('POST','/restaurants/r/replans',body,token=c.tokens['m'],key='bound');status=response[0]
            c.check('bounds-'+dimension+'-'+str(n),status==404 and response[1]['error']['code']=='not_found' if dimension=='tables' and n==0 else status in [201,422] and (status!=422 or response[1]['error']['code']=='planning_limit') if n> (4 if dimension=='pairs' else 6) else status==201)
            if status!=201:c.check('bounds-failure-atomic',before==c.export())
    c.seed();before=c.preview(closure('f',start=DAY+'T22:00:00+00:00',end=DAY+'T23:00:00+00:00'));c.check('revision-reset-zero',integer(before['restaurant_revision'])==0)
    f=fixture();f['reservations']=[dict(id='seed',reference='SEEDED',user_id='u',restaurant_id='r',table_id='a',starts_at_local=DAY+'T18:00',party_size=1)];c.setup(f);p=c.preview(closure());c.check('revision-seed-zero',integer(p['restaurant_revision'])==0)
def fractions(c):
    c.seed();a=c.make()
    for field in ['from','to']:
        boundary='18:30:00' if field=='from' else '18:00:00';previous='18:29:59' if field=='from' else '17:59:59'
        for side in ['before','equal','after']:
            for digits in [1,6,7,18,64]:
                text=DAY+'T'+(previous+'.'+'9'*digits if side=='before' else boundary if side=='equal' else boundary+'.'+'0'*(digits-1)+'1')+'+00:00';body=closure(start=text if field=='from' else DAY+'T17:00:00+00:00',end=text if field=='to' else DAY+'T19:30:00+00:00');p=c.preview(body,key=field+side+str(digits));count=1 if field=='from' and side=='before' or field=='to' and side=='after' else 0;c.check('instants-'+field+'-'+side+'-'+str(digits),len(p['assignments'])==count and p['closure'][field]==text)
    for i,text in enumerate([DAY+'t18:00:00z',DAY+'T19:00:00+01:00',DAY+'T17:00:00-01:00']):
        p=c.preview(closure(start=text),key='offset'+str(i));c.check('interval-explicit-offset-equal-instant',len(p['assignments'])==1 and p['closure']['from']==text)
def numeric(c):
    for field in ['expected_revision','from_index']:
        for name,literal in TOKENS:
            c.seed();s=c.adopt(c.make(),count=12);body=dict(expected_revision=s['revision'],from_index=0,local_time='18:00');body[field]=parse(literal);before=c.export();response=c.call('POST','/series/'+s['series_id']+'/amend',body,token=c.tokens['u'],key='numeric')
            valid=name in ['integral-decimal','integral-exponent'] or field=='from_index' and name=='zero';status=201 if valid else 409 if field=='expected_revision' and name=='large' else 422;code=None if valid else 'stale_revision' if status==409 else 'validation_failed';c.response('numeric-'+field+'-'+name,response,status,code)
            if status!=201:c.check('numeric-error-atomic',before==c.export())
    for field,values in [('expected_revision',['9007199254740993.0','9007199254740993e0']),('from_index',['11','12','11.0','12.0'])]:
        for i,literal in enumerate(values):
            c.seed();s=c.adopt(c.make(),count=12);body=dict(expected_revision=s['revision'],from_index=0,local_time='18:00');body[field]=parse(literal);status=409 if field=='expected_revision' else 201 if literal in ['11','11.0'] else 422;c.response('numeric-'+field+'-boundary-'+str(i),c.call('POST','/series/'+s['series_id']+'/amend',body,token=c.tokens['u'],key='boundary'),status,None if status==201 else 'stale_revision' if status==409 else 'validation_failed')
    clocks=['00:00','23:59','24:00','1:00','01:0','01:00:00','01:00Z','01:00+00:00',' 01:00','01:00 ','02:60','-1:00','abc','']
    for i,clock in enumerate(clocks):
        f=fixture();f['restaurants'][0].update(slot_minutes=1,reservation_duration_minutes=1);c.setup(f);s=c.adopt(c.make());response=c.amend(s,time=clock);c.response('time-clock-'+str(i),response,201 if i==0 else 422,None if i==0 else 'outside_opening_hours' if i==1 else 'validation_failed')
def extra(c):
    f=fixture();f['restaurants'][0]['manager_user_ids']=['m','v'];c.setup(f);c.make();p=c.preview();c.response('apply-different-manager',c.call('POST','/restaurants/r/replans/'+p['plan_id']+'/apply',{},token=c.tokens['v'],key='other-manager'),201)
    c.seed();c.make();before=c.export()
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(lambda _:c.call('POST','/restaurants/r/replans',closure(),token=c.tokens['m'],key='preview-wave'),range(50)))
    c.check('concurrency-preview-identical50',sorted(r[0] for r in results)==[200]*49+[201] and all(same(results[0][1],r[1]) for r in results));c.check('concurrency-preview-readonly',integer(c.lookup(results[0][1]['assignments'][0]['reference'])['revision'])==1)
    # Authentication/permission is reevaluated only after successful-key lookup.
    for family in ['preview','apply','amend']:
        c.seed();s=c.adopt(c.make());p=c.preview(key='p');path='/restaurants/r/replans' if family=='preview' else '/restaurants/r/replans/'+p['plan_id']+'/apply' if family=='apply' else '/series/'+s['series_id']+'/amend';body=closure() if family=='preview' else {} if family=='apply' else dict(expected_revision=s['revision'],from_index=0,local_time='19:00');who='u' if family=='amend' else 'm';original_path=path;original_body=copy.deepcopy(body);good=c.response('retry-'+family+'-one-char',c.call('POST',path,body,token=c.tokens[who],key='x'),201)
        for slug,key in [('255-char','x'*255)]:
            if family=='apply':p=c.preview(key='newp');path='/restaurants/r/replans/'+p['plan_id']+'/apply'
            elif family=='amend':body={**body,'expected_revision':c.current_series(s)['revision']}
            c.response('retry-'+family+'-'+slug,c.call('POST',path,body,token=c.tokens[who],key=key),201)
        if family=='preview':
            c.response('retry-preview-user-scope',c.call('POST',path,body,token=c.tokens['u'],key='x'),403,'forbidden')
        replay=c.response('retry-'+family+'-object-order',c.call('POST',original_path,dict(reversed(list(original_body.items()))),token=c.tokens[who],key='x'),200);c.check('retry-'+family+'-object-order',same(replay,good))

def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);p.add_argument('--family',choices=['dimensions','fractions','numeric','extra'],required=True);a=p.parse_args();r=validate(json.loads(Path(a.release).read_text()));c=Client(r['urls']['target'],a.out,r['candidate']);error=None
    try:globals()[a.family](c)
    except BaseException as exc:error=repr(exc);raise
    finally:c.save(error)
if __name__=='__main__':main()
