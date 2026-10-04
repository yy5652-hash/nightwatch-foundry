"""Unreleased independent black-box Stage4 protocol. No candidate defaults.

Private export bytes and tokens stay in memory; trace persists digests only.
Inherited HTTP/browser families need fresh Stage4 execution separately.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote, urlsplit, urlencode
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'stage-3'))
from stage3_probe import Client as EarlierClient, fixture as earlier_fixture, raw, integer
from semantic_oracle import same, parse, encode
from decoder_oracle import wrap, LEAF, LEAF_ALIAS
from stage4_requirements import S1,S2,S3,TOKENS
from stage4_oracle import instant, seating_plan, booking

DAY='2035-06-04'
def sha(data):return hashlib.sha256(data).hexdigest()
def fixture():
    f=earlier_fixture();r=f['restaurants'][0]
    r.update(slot_minutes=30,reservation_duration_minutes=30)
    r['tables']=[dict(id=t,label='Hospitality '+t,capacity=i+2) for i,t in enumerate('abcdef')]
    r['combinable']=[['b','a'],['c','b'],['d','e'],['f','e']]
    f['restaurants'][1]['manager_user_ids']=['m']
    return f
def closure(table='a',start=DAY+'T18:00:00+00:00',end=DAY+'T20:00:00+00:00'):
    return dict(table_id=table,**{'from':start},to=end)
def validate_release(r):
    if r.get('stage')!=4:raise ValueError('Stage4 named execution package required')
    for key in ['candidate','systems_revision','interface_revision']:
        if not re.fullmatch('[0-9a-f]{40}',r.get(key,'')):raise ValueError('full committed '+key+' required')
    flags=['execution_authorized','complete_candidate_package','end_received','acknowledged_before_execution','systems_full_handoff','interface_full_handoff',
           'fresh_clone_verified','current_packaged_hashes_verified','offline_2cpu_2g_no_service_mounts_verified','frozen_stage1_verified','frozen_stage2_verified','frozen_stage3_verified','complete_nine_file_copy_verified']
    if any(r.get(k) is not True for k in flags):raise ValueError('independent release/source/runtime proof incomplete')
    if [r.get('accepted_stage'+str(n)) for n in (1,2,3)]!=[S1,S2,S3]:raise ValueError('genuine frozen origins differ')
    if not re.fullmatch('sha256:[0-9a-f]{64}',r.get('image_id','')):raise ValueError('current image missing')
    for key in ['source_proof','resource_proof','package_intake']:
        p=Path(r.get(key+'_path',''))
        if not p.is_file() or sha(p.read_bytes())!=r.get(key+'_sha256'):raise ValueError('concrete independent proof not bound: '+key)
    for name in ['target','peer','accepted-s1','accepted-s2','accepted-s3']:
        u=urlsplit(r.get('urls',{}).get(name,''))
        if u.scheme!='http' or not (u.hostname or '').startswith('independent-verifier-') or u.username or u.password:raise ValueError('own internal constrained URL required: '+name)
    for name,rev in [('accepted-s1',S1),('accepted-s2',S2),('accepted-s3',S3)]:
        if r.get('source_revisions',{}).get(name)!=rev:raise ValueError('genuine origin required: '+name)
    return r

class Client(EarlierClient):
    def check(self,case,condition,detail=None):
        self.assertions.append(dict(requirement_id='TK4-'+case,passed=bool(condition),detail=detail,candidate=self.candidate))
        if not condition:raise AssertionError(case)
    def seed(self):return self.setup(fixture())
    def make(self,seats=('a',),local=DAY+'T18:00',party=1,key='create'):
        return self.response('setup-create',self.call('POST','/reservations',dict(restaurant_id='r',table_ids=list(seats),starts_at_local=local,party_size=party),token=self.tokens['u'],key=key),201)
    def preview(self,body=None,key='preview',restaurant='r'):
        return self.response('preview-status',self.call('POST','/restaurants/'+restaurant+'/replans',body or closure(),token=self.tokens['m'],key=key),201)
    def apply(self,plan,key='apply',restaurant='r',body=None):
        return self.call('POST','/restaurants/'+restaurant+'/replans/'+quote(plan['plan_id'],safe='')+'/apply',{} if body is None else body,token=self.tokens['m'],key=key)
    def adopt(self,anchor,count=4,key='adopt'):
        got=self.response('setup-adopt',self.call('POST','/series',dict(anchor_reference=anchor['reference'],count=count,interval_weeks=1),token=self.tokens['u'],key=key),201)
        self.series_ids.append(got['series_id']);return got
    def current_series(self,s):return self.response('setup-series',self.call('GET','/series/'+quote(s['series_id'],safe=''),token=self.tokens['u']),200)
    def amend(self,s,time='19:00',index=0,key='amend',revision=None,**extra):
        return self.call('POST','/series/'+quote(s['series_id'],safe='')+'/amend',dict(expected_revision=s['revision'] if revision is None else revision,from_index=index,local_time=time,**extra),token=self.tokens['u'],key=key)

def preview_family(c):
    c.seed();a=c.make();before=c.public_state()
    body=closure();p=c.preview(body)
    c.check('preview-no-booking-write',same(before,c.public_state()))
    c.check('preview-response-revision',integer(p['restaurant_revision'])==1)
    c.check('preview-response-all',[x['reference'] for x in p['assignments']]==[a['reference']])
    c.check('preview-response-changed',p['assignments'][0]['changed'] is True)
    c.check('preview-response-moved',integer(p['moved_count'])==1)
    c.response('retry-preview-same-json',c.call('POST','/restaurants/r/replans',dict(reversed(list(body.items()))),token=c.tokens['m'],key='preview'),200)
    for token,status,code in [(None,401,'unauthenticated'),(c.tokens['u'],403,'forbidden')]:
        c.response('preview-anonymous' if token is None else 'preview-nonmanager',c.call('POST','/restaurants/r/replans',body,token=token,key='permission'),status,code)
    for i,b in enumerate([closure(table='missing'),closure(end=body['from']),closure(start=body['to']),closure(start=DAY+'T18:00:00'),closure(start='invalid')]):
        old=c.export();c.response('preview-invalid-'+str(i),c.call('POST','/restaurants/r/replans',b,token=c.tokens['m'],key='invalid'+str(i)),404 if i==0 else 422,'not_found' if i==0 else 'validation_failed')
        c.check('preview-infeasible-state',old==c.export())
    # Exact comparison around the booked end: tiny positive overlap vs zero.
    for side,end in [('equal',DAY+'T18:00:00+00:00'),('after',DAY+'T18:00:00.000000000000000001+00:00')]:
        p=c.preview(closure(start=DAY+'T17:59:00+00:00',end=end),key='edge'+side)
        c.check('instants-to-'+side+'-18',len(p['assignments'])==(0 if side=='equal' else 1))

def apply_family(c):
    c.seed();a=c.make();h=c.history(a['reference']);p=c.preview();got=c.response('apply-status',c.apply(p),201)
    now=c.lookup(a['reference']);hist=c.history(a['reference'])
    c.check('apply-restaurant-once',integer(got['restaurant_revision'])==integer(p['restaurant_revision'])+1)
    c.check('apply-moved-revision',integer(now['revision'])==integer(a['revision'])+1)
    c.check('apply-identity',all(same(a[k],now[k]) for k in ['reservation_id','reference','party_size','starts_at','ends_at','starts_at_local','created_at','accepted_terms']))
    entry=hist['entries'][-1]
    c.check('apply-moved-event',len(hist['entries'])==len(h['entries'])+1 and entry['event']=='reassigned')
    c.check('apply-event-field',same(entry['changes'],[dict(field='table_ids',**{'from':a['table_ids']},to=now['table_ids'])]))
    c.check('apply-event-plan',entry['plan_id']==p['plan_id'])
    c.response('apply-applied-different-key',c.apply(p,key='another'),409,'plan_already_applied')
    replay=c.response('apply-repeat-original',c.apply(p),200);c.check('apply-repeat-original',same(got,replay))
    c.response('apply-wrong-restaurant',c.apply(p,key='wrong',restaurant='r2'),404,'not_found')
    c.response('closure-create',c.call('POST','/reservations',dict(restaurant_id='r',table_id='a',starts_at_local=DAY+'T18:00',party_size=1),token=c.tokens['u'],key='closed'),409,'table_unavailable')
    result=c.response('closure-explain-no-overlap',c.call('GET','/availability?'+urlencode(dict(restaurant_id='r',date=DAY,party_size=1,explain='true'))),200)
    row=next(s for s in result['slots'] if s['starts_at_local']==DAY+'T18:00');why=next(t for t in row['explain'] if t['table_id']=='a')
    c.check('closure-explain-no-overlap',why['rules'][1]['holds'] is False and 'a' not in row['available_table_ids'])
    stale=c.preview(closure(table='b'),key='stale');c.make(seats=('f',),local=DAY+'T21:00',key='intervening')
    before=c.export();c.response('apply-stale',c.apply(stale,key='stale-apply'),409,'stale_plan');c.check('apply-stale-atomic',before==c.export())
    c.check('apply-repeat-original',same(got,c.response('apply-repeat-original',c.apply(p),200)))

def oracle_family(c):
    c.seed();records=[]
    for i,(seats,clock) in enumerate([(('a',),'18:00'),(('b',),'18:00'),(('a',),'19:00'),(('c',),'19:00'),(('d',),'20:00'),(('f',),'20:00')]):
        r=c.make(seats,DAY+'T'+clock,key='oracle'+str(i));records.append(r)
    body=closure(end=DAY+'T20:30:00+00:00');p=c.preview(body)
    model=[booking(r['reference'],r['table_ids'],instant(r['starts_at']),instant(r['ends_at']),{k:integer(v) for k,v in r['accepted_terms']['capacities'].items()},integer(r['party_size'])) for r in records]
    expected=seating_plan(tuple('abcdef'),fixture()['restaurants'][0]['combinable'],model,[],dict(table_id='a',start=instant(body['from']),end=instant(body['to'])))
    for field in ['assignments','moved_count','unused_seats']:c.check('preview-objective-'+field,same(p[field],expected[field]))
    c.check('preview-bound-all',len(p['assignments'])==6)
    before=c.public_state();c.response('apply-status',c.apply(p),201)
    for assignment in p['assignments']:
        prior=next(r for r in before['reservations']['reservations'] if r['reference']==assignment['reference']);now=c.lookup(assignment['reference'])
        c.check('apply-identity',all(same(now[k],prior[k]) for k in ['reference','reservation_id','accepted_terms','starts_at','ends_at','party_size','created_at']))

def amend_family(c):
    c.seed();a=c.make();s=c.adopt(a);before=c.current_series(s)
    refs=[o['reference'] for o in before['occurrences']]
    c.response('setup-exception',c.call('PATCH','/reservations/'+refs[1],dict(party_size=2),token=c.tokens['u']),200)
    c.response('setup-cancel',c.call('POST','/reservations/'+refs[2]+'/cancel',{},token=c.tokens['u']),200)
    current=c.current_series(s);old=c.public_state();got=c.response('amend-status',c.amend(current),201)
    c.check('amend-series-once',integer(got['revision'])==integer(current['revision'])+1)
    for i,(before_o,after_o) in enumerate(zip(current['occurrences'],got['occurrences'])):
        b=before_o['reservation'];n=after_o['reservation']
        c.check('amend-retain-reference',after_o['reference']==before_o['reference'])
        if i in (1,2):c.check('amend-skip-exception' if i==1 else 'amend-skip-cancelled',same(before_o,after_o))
        else:
            c.check('amend-member-revision',integer(n['revision'])==integer(b['revision'])+1)
            c.check('amend-no-exceptions',after_o['exception'] is False)
            c.check('amend-schedule-original',n['starts_at_local']==b['starts_at_local'][:10]+'T19:00')
            c.check('amend-retain-seating',same(n['table_ids'],b['table_ids']))
    replay=c.response('amend-replay-original',c.amend(current),200);c.check('amend-replay-original',same(got,replay))
    c.response('amend-stale-first',c.amend(current,time='23:59',key='stale'),409,'stale_revision')
    now=c.current_series(s);public_before=c.public_state();noop=c.response('amend-noop-success',c.amend(now,time='19:00',key='noop'),201)
    c.check('amend-noop-success',same(noop,now))
    # Export differs only by a legitimately stored successful no-op receipt.
    c.check('amend-noop-terms',same(public_before,c.public_state()))
    for token,status in [(None,401),(c.tokens['v'],404),(c.tokens['m'],404)]:
        c.response('amend-anonymous' if token is None else 'amend-other-owner',c.call('POST','/series/'+s['series_id']+'/amend',dict(expected_revision=now['revision'],from_index=0,local_time='20:00'),token=token,key='private'),status,'unauthenticated' if token is None else 'not_found')

def numeric_family(c):
    c.seed();s=c.adopt(c.make())
    base=dict(expected_revision=s['revision'],from_index=0,local_time='19:00')
    for field in ['expected_revision','from_index']:
        for name,literal in TOKENS:
            # Only invalid values, integral controls need independently fresh keys/state.
            if name in ['integral-decimal','integral-exponent'] or (field=='from_index' and name=='zero'):continue
            body=raw({k:v for k,v in base.items() if k!=field})[:-1]+b',"'+field.encode()+b'":'+literal.encode()+b'}'
            status,code=(409,'stale_revision') if field=='expected_revision' and name=='large' else (422,'validation_failed')
            old=c.export();c.response('numeric-'+field+'-'+name,c.call('POST','/series/'+s['series_id']+'/amend',body=body,token=c.tokens['u'],key='n-'+field+'-'+name),status,code)
            c.check('amend-failed-counters',old==c.export())

def concurrency_family(c):
    c.seed();s=c.adopt(c.make());p=c.preview()
    def apply_one(_):return c.apply(p,key='wave')
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(apply_one,range(50)))
    c.check('concurrency-apply-identical50',sorted(r[0] for r in results)==[200]*49+[201] and all(same(results[0][1],r[1]) for r in results))
    now=c.current_series(s)
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(lambda _:c.amend(now,time='20:00',key='amend-wave'),range(50)))
    c.check('concurrency-amend-identical50',sorted(r[0] for r in results)==[200]*49+[201] and all(same(results[0][1],r[1]) for r in results))

FAMILIES=dict(preview=preview_family,apply=apply_family,oracle=oracle_family,amend=amend_family,numeric=numeric_family,concurrency=concurrency_family)
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--family',choices=FAMILIES,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:raise SystemExit('Candidate execution held; complete acknowledged release required')
    release=validate_release(json.loads(a.release.read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
    try:FAMILIES[a.family](c)
    except Exception as e:error=repr(e);raise
    finally:c.save(error)
if __name__=='__main__':main()
