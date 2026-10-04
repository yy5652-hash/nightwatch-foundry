"""Independent Stage 3 raw HTTP protocol, prepared but not released.

Default execution is impossible. A later acknowledged complete candidate release,
independent image/source/resource proof and both full builder handoffs are required.
Private exports and tokens remain in memory. Public JSON is parsed losslessly by
the verifier's previously authored semantic oracle, never a production module.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import http.client
import json
from pathlib import Path
import re
import sys
import threading
import time
from urllib.parse import quote,urlsplit,urlencode

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'stage-1'))
from semantic_oracle import Number,parse,encode,same
from stage3_requirements import S1,S2,cases
from stage3_oracle import selected,terms,weekly,resolve,changes,Model,Refusal
from decoder_oracle import wrap,LEAF,LEAF_ALIAS,LEAF_DIFFERENT,LEAF_TYPED

DAY='2035-06-04'
def raw(value):return encode(value).encode('utf-8')
def sha(value):return hashlib.sha256(value).hexdigest()
def integer(value):
    # Only bounded public revision/version/count values use this helper.
    if isinstance(value,bool):raise ValueError('boolean is not integer')
    return int(encode(value))

def fixture(zone='UTC'):
    users=[dict(id=k,email=k+'@stage3.invalid',password='independent-pass',display_name=n) for k,n in [('u','Diner'),('v','Other Diner'),('m','Manager')]]
    restaurant=dict(id='r',name='Juniper Kitchen',timezone=zone,slot_minutes=30,reservation_duration_minutes=90,
        cancellation_cutoff_minutes=0,manager_user_ids=['m'],
        opening_hours=[dict(weekday=d,opens='00:00',closes='23:59') for d in ('mon','tue','wed','thu','fri','sat','sun')],
        tables=[dict(id=t,label=n,capacity=8) for t,n in [('a','Window Alcove'),('b','Garden Bench'),('c','Cedar Booth')]],combinable=[['b','a'],['b','c']])
    other=deepcopy(restaurant);other.update(id='r2',name='Cedar Kitchen',manager_user_ids=[])
    other['tables']=[dict(id='x',label='Cedar Table',capacity=8)];other['combinable']=[]
    return dict(users=users,restaurants=[restaurant,other],reservations=[])

def policy(day='2035-06-01',**kw):
    value=dict(effective_from=day,slot_minutes=30,reservation_duration_minutes=60,cancellation_cutoff_minutes=0,
        opening_hours=fixture()['restaurants'][0]['opening_hours'],capacities=dict(a=2,b=4,c=6))
    value.update(kw);return value

def create_body(seats=('a',),local=DAY+'T18:00',party=2,stage=3,**kw):
    value=dict(restaurant_id='r',starts_at_local=local,party_size=party)
    if stage==1:value['table_id']=seats[0]
    else:value['table_ids']=list(seats)
    value.update(kw);return value

def validate_release(release):
    for key in ('candidate','systems_revision','interface_revision'):
        if not re.fullmatch('[0-9a-f]{40}',release.get(key,'')):raise ValueError('full revision required: '+key)
    for key in ('complete_candidate_package','end_received','acknowledged_before_execution','execution_authorized',
        'systems_full_handoff','interface_full_handoff','fresh_clone_verified','current_packaged_hashes_verified',
        'offline_2cpu_2g_no_service_mounts_verified','frozen_stage1_verified','frozen_stage2_verified'):
        if release.get(key) is not True:raise ValueError('later independent release proof required: '+key)
    if release.get('accepted_stage1')!=S1 or release.get('accepted_stage2')!=S2:raise ValueError('accepted origin differs')
    if release.get('stage')!=3:raise ValueError('Stage 3 execution only')
    if not re.fullmatch('sha256:[0-9a-f]{64}',release.get('image_id','')):raise ValueError('current image required')
    for key in ('source_proof_path','resource_proof_path','package_intake_path'):
        p=Path(release.get(key,''))
        if not p.is_file():raise ValueError('concrete independent proof missing: '+key)
        if sha(p.read_bytes())!=release.get(key.replace('_path','_sha256')):raise ValueError('proof hash mismatch: '+key)
    for name in ('target','peer','accepted-s1','accepted-s2'):
        parsed=urlsplit(release.get('urls',{}).get(name,''))
        if parsed.scheme!='http' or not (parsed.hostname or '').startswith('independent-verifier-') or parsed.username or parsed.password:
            raise ValueError('own constrained internal service required: '+name)
    if release.get('source_revisions',{}).get('accepted-s1')!=S1 or release.get('source_revisions',{}).get('accepted-s2')!=S2:
        raise ValueError('real accepted origins required')
    return release

class Client:
    def __init__(self,base,out,candidate):
        self.base=base;self.out=Path(out);self.candidate=candidate;self.trace=[];self.assertions=[];self.count=0
        self.tokens={};self.series_ids=[];self.start=time.monotonic()
    def call(self,method,path,value=None,token=None,key=None,url=None,body=None,decode=True):
        body=raw(value) if value is not None and body is None else body
        parsed=urlsplit(url or self.base);headers={'Content-Type':'application/json; charset=utf-8'}
        if token:headers['Authorization']='Bearer '+token
        if key is not None:headers['Idempotency-Key']=key
        start=time.monotonic();conn=http.client.HTTPConnection(parsed.hostname,parsed.port,timeout=10 if path.startswith('/_test/') else 5)
        try:
            conn.request(method,path,body=body,headers=headers);response=conn.getresponse();data=response.read();status=response.status
        finally:conn.close()
        self.count+=1
        self.trace.append(dict(index=self.count,method=method,path=path,url=url or self.base,status=status,seconds=time.monotonic()-start,
            request_bytes=len(body or b''),request_sha256=sha(body or b''),response_bytes=len(data),response_sha256=sha(data),
            token_present=bool(token),key_fingerprint=sha(key.encode()) if key is not None else None,private_export_decoded=False if not decode else None))
        return status,parse(data) if data and decode else None,data
    def check(self,case,condition,detail=None):
        self.assertions.append(dict(requirement_id='TK3-'+case,passed=bool(condition),detail=detail,candidate=self.candidate))
        if not condition:raise AssertionError(case)
    def response(self,case,result,status,code=None):
        actual,value,_=result;self.check(case,actual==status and (code is None or value.get('error',{}).get('code')==code),{'status':actual,'expected':status,'code':code})
        return value
    def setup(self,f=None,url=None):
        self.series_ids=[];self.response('setup-reset',self.call('POST','/_test/reset',f or fixture(),url=url),204)
        tokens={}
        for user in ('u','v','m'):
            tokens[user]=self.response('setup-login-'+user,self.call('POST','/auth/login',dict(email=user+'@stage3.invalid',password='independent-pass'),url=url),200)['token']
        self.tokens=tokens;return tokens
    def create(self,seats=('a',),local=DAY+'T18:00',party=2,key='create',url=None,stage=3):
        return self.response('setup-create',self.call('POST','/reservations',create_body(seats,local,party,stage),token=self.tokens['u'],key=key,url=url),201)
    def lookup(self,ref):return self.response('setup-lookup',self.call('GET','/reservations/'+quote(ref,safe=''),token=self.tokens['u']),200)
    def history(self,ref):return self.response('setup-history',self.call('GET','/reservations/'+quote(ref,safe='')+'/history',token=self.tokens['u']),200)
    def public_state(self):
        reservations=self.response('setup-list',self.call('GET','/reservations',token=self.tokens['u']),200)
        refs=[r['reference'] for r in reservations['reservations']]
        return dict(reservations=reservations,policies=self.response('setup-policies',self.call('GET','/restaurants/r/policies'),200),
            histories={r:self.history(r) for r in refs},series={sid:self.response('setup-series-get',self.call('GET','/series/'+quote(sid,safe=''),token=self.tokens['u']),200) for sid in self.series_ids})
    def export(self,url=None):return self.response_bytes('GET','/_test/export',url=url)
    def response_bytes(self,method,path,url=None,body=None):
        status,_,data=self.call(method,path,url=url,body=body,decode=False)
        if status!=200:raise RuntimeError('raw export refused')
        return data
    def transfer(self,source,dest,body):
        result=self.call('POST','/_test/import',url=dest,body=body,decode=False)
        self.trace.append(dict(event='raw-unchanged-transfer',source=source,destination=dest,bytes=len(body),sha256=sha(body),decoded=False,status=result[0]))
        return result
    def save(self,error=None):
        self.out.mkdir(parents=True,exist_ok=False)
        payload=dict(candidate=self.candidate,requests=self.count,assertions=len(self.assertions),failed=sum(not a['passed'] for a in self.assertions),
            seconds=time.monotonic()-self.start,error=error,complete=error is None,private_exports_saved=0)
        for name,value in [('summary.json',payload),('trace.json',self.trace),('assertions.json',self.assertions)]:
            (self.out/name).write_text(json.dumps(value,indent=2)+'\n')

def policy_family(c):
    c.setup();original=c.response('policies-original-detail',c.call('GET','/restaurants/r'),200)
    old=c.create();oldhist=c.history(old['reference']);policies=[]
    for i,(day,duration) in enumerate([('2035-06-20',120),('2035-06-01',60),('2035-06-01',90),('2000-01-01',30)],1):
        p=policy(day,reservation_duration_minutes=duration)
        got=c.response('policies-first-version' if i==1 else 'policies-contiguous-version',c.call('POST','/restaurants/r/policies',p,token=c.tokens['m'],key='policy-'+str(i)),201)
        c.check('policies-contiguous-version',integer(got['policy_version'])==i);policies.append({**p,'policy_version':i})
    c.check('policies-original-detail',same(original,c.response('policies-original-detail',c.call('GET','/restaurants/r'),200)))
    c.check('policies-existing-record',same(old,c.lookup(old['reference'])))
    c.check('policies-existing-history',same(oldhist,c.history(old['reference'])))
    got=c.response('policies-public-list',c.call('GET','/restaurants/r/policies'),200)['policies']
    c.check('policies-list-order',same(got,policies))
    base={**fixture()['restaurants'][0],'policy_version':0,'capacities':dict(a=8,b=8,c=8)}
    for day in ['1999-12-31','2035-06-01','2035-06-04','2035-06-19','2035-06-20']:
        result=c.response('policies-out-of-order',c.call('GET','/availability?'+urlencode(dict(restaurant_id='r',date=day,party_size=1,explain='true'))),200)
        chosen=selected(base,policies,day)
        c.check('explain-policy-version',all(integer(t['policy_version'])==chosen['policy_version'] for s in result['slots'] for t in s['explain']))
    for token,expected in [(None,401),(c.tokens['u'],403),(c.tokens['v'],403)]:
        c.response('policies-no-token' if token is None else 'policies-non-manager',c.call('POST','/restaurants/r/policies',policy(),token=token,key='refused'),expected,'unauthenticated' if token is None else 'forbidden')
    c.response('policies-restaurant-scoped',c.call('POST','/restaurants/r2/policies',policy(),token=c.tokens['m'],key='other'),403,'forbidden')
    c.response('policies-unknown-restaurant',c.call('POST','/restaurants/missing/policies',policy(),token=c.tokens['m'],key='unknown'),404,'not_found')

def explanation_family(c):
    c.setup();c.create(seats=('b','a'),party=9)
    f=fixture()['restaurants'][0];capacities={t['id']:t['capacity'] for t in f['tables']}
    for party in [2,9]:
        result=c.response('explain-true',c.call('GET','/availability?'+urlencode(dict(restaurant_id='r',date=DAY,party_size=party,explain='true'))),200)
        for slot in result['slots']:
            ids=[]
            c.check('explain-table-order',[t['table_id'] for t in slot['explain']]==['a','b','c'])
            a_start=resolve(slot['starts_at_local'],'UTC');b_start=resolve(DAY+'T18:00','UTC')
            from datetime import timedelta
            overlaps=a_start<b_start+timedelta(minutes=90) and b_start<a_start+timedelta(minutes=90)
            for t in slot['explain']:
                cap=party<=capacities[t['table_id']];free=not(overlaps and t['table_id'] in ('a','b'))
                c.check('explain-rule-order',[r['rule'] for r in t['rules']]==['capacity','no_overlap'])
                c.check('explain-conjunction',t['rules'][0]['holds'] is cap and t['rules'][1]['holds'] is free and t['available'] is (cap and free))
                if cap and free:ids.append(t['table_id'])
            c.check('explain-ids-order',ids==slot['available_table_ids'])
        no=c.response('explain-omitted',c.call('GET','/availability?'+urlencode(dict(restaurant_id='r',date=DAY,party_size=party))),200)
        c.check('explain-omitted',all('explain' not in s for s in no['slots']))
    for case in cases():
        if case['family']=='explain' and 'explain' in case['parameters']:
            c.response('explain-'+case['name'],c.call('GET','/availability?'+urlencode(dict(restaurant_id='r',date=DAY,party_size=1,explain=case['parameters']['explain']))),422,'validation_failed')

def numeric_family(c):
    for case in cases():
        params=case['parameters'];field=params.get('field')
        if field is None or 'token' not in params:continue
        c.setup();candidate=parse(params['token']);good=params['value_valid']
        if case['family']=='policies':
            value=policy();value['capacities']['a']=candidate if field=='capacity' else value['capacities']['a']
            if field!='capacity':value[field]=candidate
            before=c.public_state();result=c.call('POST','/restaurants/r/policies',value,token=c.tokens['m'],key='numeric')
            c.response('policies-'+case['name'],result,201 if good else 422,None if good else 'validation_failed')
            if not good:c.check('policies-failed-state',same(before,c.public_state()))
        elif case['family']=='series':
            anchor=c.create();value=dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1);value[field]=candidate
            before=c.public_state();result=c.call('POST','/series',value,token=c.tokens['u'],key='numeric')
            c.response('series-'+case['name'],result,201 if good else 422,None if good else 'validation_failed')
            if not good:c.check('series-rollback-reservations',same(before,c.public_state()))
        else:
            anchor=c.create();value={'expected_revision':candidate}
            path='/reservation-moves' if case['family']=='moves' else '/reservations/'+anchor['reference']
            body={'moves':[{'reference':anchor['reference'],**value}]} if case['family']=='moves' else value
            before=c.public_state();result=c.call('POST' if case['family']=='moves' else 'PATCH',path,body,token=c.tokens['u'],key='numeric' if case['family']=='moves' else None)
            c.response(case['family']+'-'+case['name'],result,201 if good and case['family']=='moves' else 200 if good else 422,None if good else 'validation_failed')
            if not good:c.check('terms-amend-atomic',same(before,c.public_state()))
    for case in cases():
        if case['family']!='policies' or not any(k in case['parameters'] for k in ('missing','date','capacities_mode','opening_mode')):continue
        c.setup();p=policy();x=case['parameters']
        if 'missing' in x:p.pop(x['missing'])
        if 'date' in x:p['effective_from']=x['date']
        cm=x.get('capacities_mode')
        if cm=='missing':p['capacities'].pop('a')
        if cm=='extra':p['capacities']['outside']=3
        if cm=='replace':p['capacities']['outside']=p['capacities'].pop('a')
        if cm=='array':p['capacities']=[]
        om=x.get('opening_mode')
        if om=='duplicate':p['opening_hours'].append(deepcopy(p['opening_hours'][0]))
        if om=='unknown':p['opening_hours'][0]['weekday']='holiday'
        if om=='overnight':p['opening_hours'][0].update(opens='23:00',closes='01:00')
        if om=='equal':p['opening_hours'][0].update(opens='18:00',closes='18:00')
        if om=='format':p['opening_hours'][0]['opens']='6:00'
        if om=='object':p['opening_hours']={}
        before=c.public_state();c.response('policies-'+case['name'],c.call('POST','/restaurants/r/policies',p,token=c.tokens['m'],key='shape'),422,'validation_failed')
        c.check('policies-failed-state',same(before,c.public_state()))

def terms_family(c):
    c.setup();created=c.create();ref=created['reference'];path='/reservations/'+ref
    c.check('terms-create-revision',integer(created['revision'])==1)
    c.response('policies-manager-allowed',c.call('POST','/restaurants/r/policies',policy(),token=c.tokens['m'],key='new-policy'),201)
    c.response('terms-noop-revision',c.call('PATCH',path,dict(table_ids=['a'],expected_revision=1),token=c.tokens['u']),200)
    c.check('terms-noop-terms',same(created,c.lookup(ref)))
    for i,patch in enumerate([dict(table_ids=['a','b'],party_size=5),dict(table_ids=['c']),dict(table_ids=['b','c'],starts_at_local=DAY+'T19:00',party_size=6)],2):
        old=c.lookup(ref);hist=c.history(ref)
        result=c.response('terms-amend-new-terms',c.call('PATCH',path,patch,token=c.tokens['u']),200)
        c.check('terms-amend-revision-once',integer(result['revision'])==i)
        c.check('terms-amend-new-terms',integer(result['accepted_terms']['policy_version'])==1)
        after=c.history(ref);c.check('history-historic-terms',same(after['entries'][:-1],hist['entries']))
        seatsold=old['table_ids'];seatsnew=result['table_ids'];expected=[]
        if seatsold!=seatsnew:
            field='table_ids' if len(seatsold)>1 or len(seatsnew)>1 else 'table_id'
            expected.append({'field':field,'from':seatsold if field=='table_ids' else seatsold[0],'to':seatsnew if field=='table_ids' else seatsnew[0]})
        for field in ('starts_at_local','party_size'):
            if not same(old[field],result[field]):expected.append({'field':field,'from':old[field],'to':result[field]})
        c.check('history-changed-order',same(after['entries'][-1]['changes'],expected))
    before=c.public_state()
    c.response('terms-stale-before-fields',c.call('PATCH',path,dict(expected_revision=1,party_size=False),token=c.tokens['u']),409,'stale_revision')
    c.check('terms-amend-atomic',same(before,c.public_state()))
    c.response('history-reversed-noop',c.call('PATCH',path,dict(table_ids=['c','b']),token=c.tokens['u']),200)
    c.check('history-reversed-noop',same(before,c.public_state()))
    cancelled=c.response('terms-cancel-once',c.call('POST',path+'/cancel',{},token=c.tokens['u']),200)
    c.check('terms-cancel-once',integer(cancelled['revision'])==5)
    c.check('terms-cancel-repeat-revision',same(cancelled,c.response('terms-cancel-repeat-revision',c.call('POST',path+'/cancel',{},token=c.tokens['u']),200)))
    hist=c.history(ref)['entries'];c.check('history-seq-contiguous',[integer(e['seq']) for e in hist]==list(range(1,len(hist)+1)))
    c.check('history-cancel-empty',hist[-1]['event']=='cancelled' and hist[-1]['changes']==[])
    c.check('history-at-order',[datetime.fromisoformat(e['at']) for e in hist]==sorted(datetime.fromisoformat(e['at']) for e in hist))
    c.check('terms-decision-cancelled',same(c.response('terms-decision-current',c.call('GET',path+'/decision',token=c.tokens['u']),200)['accepted_terms'],cancelled['accepted_terms']))
    replay=c.response('upgrade-original-create',c.call('POST','/reservations',create_body(),token=c.tokens['u'],key='create'),200)
    c.check('upgrade-original-create',same(replay,created))

def series_family(c):
    c.setup();anchor=c.create(seats=('b','a'),party=5);ref=anchor['reference'];hist=c.history(ref)
    c.response('policies-manager-allowed',c.call('POST','/restaurants/r/policies',policy('2035-06-11'),token=c.tokens['m'],key='policy'),201)
    body=dict(anchor_reference=ref,count=4,interval_weeks=1)
    receipt=c.response('series-response-status',c.call('POST','/series',body,token=c.tokens['u'],key='series'),201)
    sid=receipt['series_id'];c.series_ids.append(sid)
    c.check('series-anchor-history',same(c.history(ref),hist));current=c.lookup(ref)
    for name in ('reference','reservation_id','revision','accepted_terms','starts_at_local','starts_at','ends_at','created_at'):
        c.check('series-anchor-'+('id' if name=='reservation_id' else 'ref' if name=='reference' else 'terms' if name=='accepted_terms' else 'times' if name.endswith('_at') or name=='starts_at_local' else name),same(current[name],anchor[name]))
    occ=receipt['occurrences'];c.check('series-response-count',len(occ)==4)
    c.check('series-response-order',[integer(x['index']) for x in occ]==list(range(4)))
    c.check('series-calendar-dates',[x['reservation']['starts_at_local'] for x in occ]==weekly(anchor['starts_at_local'],4,1))
    c.check('series-own-policy',[integer(x['reservation']['accepted_terms']['policy_version']) for x in occ]==[0,1,1,1])
    c.check('series-initial-exceptions',all(x['exception'] is False for x in occ))
    references=[x['reference'] for x in occ]
    c.check('series-distinct-reference',len(set(references))==4)
    patch=dict(party_size=6);member=references[1]
    c.response('series-patch-exception',c.call('PATCH','/reservations/'+member,patch,token=c.tokens['u']),200)
    c.response('series-permanent-exception',c.call('PATCH','/reservations/'+member,dict(party_size=5),token=c.tokens['u']),200)
    got=c.response('series-get-current',c.call('GET','/series/'+sid,token=c.tokens['u']),200)
    c.check('series-permanent-exception',got['occurrences'][1]['exception'] is True and integer(got['revision'])==3)
    c.response('series-cancel-no-exception',c.call('POST','/reservations/'+references[2]+'/cancel',{},token=c.tokens['u']),200)
    c.response('series-anchor-cancel-siblings',c.call('POST','/reservations/'+ref+'/cancel',{},token=c.tokens['u']),200)
    got=c.response('series-get-current',c.call('GET','/series/'+sid,token=c.tokens['u']),200)
    c.check('series-anchor-cancel-siblings',[x['reservation']['status'] for x in got['occurrences']]==['cancelled','confirmed','cancelled','confirmed'])
    c.check('series-cancel-no-exception',got['occurrences'][2]['exception'] is False)
    before=c.public_state();c.response('series-repeat-cancel-series',c.call('POST','/reservations/'+ref+'/cancel',{},token=c.tokens['u']),200)
    c.check('series-repeat-cancel-series',same(before,c.public_state()))
    replay=c.response('series-series-retry-replay-after-mutation',c.call('POST','/series',body,token=c.tokens['u'],key='series'),200)
    c.check('series-series-retry-replay-after-mutation',same(replay,receipt))
    for endpoint,path in [('history','/reservations/'+ref+'/history'),('decision','/reservations/'+ref+'/decision'),('series','/series/'+sid)]:
        for caller,token in [('owner',c.tokens['u']),('other-diner',c.tokens['v']),('manager',c.tokens['m']),('no-token',None),('malformed-token','bad token'),('unknown-token','unknown')]:
            fam='history' if endpoint=='history' else 'terms' if endpoint=='decision' else 'series'
            c.response(fam+'-privacy-'+endpoint+'-'+caller,c.call('GET',path,token=token),200 if caller=='owner' else 404,None if caller=='owner' else 'not_found')

def rollback_family(c):
    for scenario in ['capacity','grid','closed','outside','occupied-single','occupied-pair']:
        c.setup();anchor=c.create(seats=('b','a'),party=5)
        p=policy('2035-06-11')
        if scenario=='capacity':p['capacities']=dict(a=1,b=1,c=6)
        if scenario=='grid':p['slot_minutes']=75;p['opening_hours']=[dict(weekday=d,opens='17:00',closes='23:59') for d in ('mon','tue','wed','thu','fri','sat','sun')]
        if scenario=='closed':p['opening_hours']=[]
        if scenario=='outside':p['opening_hours']=[dict(weekday=d,opens='19:00',closes='23:59') for d in ('mon','tue','wed','thu','fri','sat','sun')]
        blocker=None
        if scenario.startswith('occupied'):blocker=c.create(seats=('a',) if scenario.endswith('single') else ('b','a'),local='2035-06-11T18:00',party=2,key='occupied')
        else:c.response('policies-manager-allowed',c.call('POST','/restaurants/r/policies',p,token=c.tokens['m'],key='fail-policy'),201)
        before=c.public_state();body=dict(anchor_reference=anchor['reference'],count=4,interval_weeks=1)
        status,value,_=c.call('POST','/series',body,token=c.tokens['u'],key='failed-series')
        code={'capacity':'party_exceeds_capacity','grid':'not_on_slot_grid','closed':'outside_opening_hours','outside':'outside_opening_hours','occupied-single':'table_unavailable','occupied-pair':'table_unavailable'}[scenario]
        c.check('series-first-failure',status==(409 if code=='table_unavailable' else 422) and value['error']['code']==code)
        c.check('series-reject-'+scenario+'-records',same(before,c.public_state()))
        # A different valid body with the failed key must not give reuse; later
        # families independently repair the obstruction and prove real success.
        status,value,_=c.call('POST','/series',dict(anchor_reference='missing',count=2,interval_weeks=1),token=c.tokens['u'],key='failed-series')
        c.check('series-rollback-key',status==404 and value['error']['code']=='not_found')
        if blocker:c.response('series-rollback-key',c.call('POST','/reservations/'+blocker['reference']+'/cancel',{},token=c.tokens['u']),200)
        else:c.response('policies-manager-allowed',c.call('POST','/restaurants/r/policies',policy('2035-06-11'),token=c.tokens['m'],key='repair-policy'),201)
        c.response('series-rollback-key',c.call('POST','/series',body,token=c.tokens['u'],key='failed-series'),201)

def retry_family(c):
    for kind in ['policies','series']:
        c.setup();anchor=c.create()
        path='/restaurants/r/policies' if kind=='policies' else '/series'
        token=c.tokens['m' if kind=='policies' else 'u']
        value=policy() if kind=='policies' else dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1)
        value['ignored']=Number('9007199254740993.0')
        for key,name,status,code in [(None,'missing-key',400,'missing_idempotency_key'),('','empty-key',400,'missing_idempotency_key'),('k'*256,'key-256',422,'validation_failed')]:
            c.response(kind+'-'+kind+'-retry-'+name,c.call('POST',path,value,token=token,key=key),status,code)
        original=c.response(kind+'-retry-first',c.call('POST',path,value,token=token,key='receipt'),201)
        reversed_value={k:value[k] for k in reversed(value)}
        got=c.response(kind+'-'+kind+'-retry-same-body-order',c.call('POST',path,reversed_value,token=token,key='receipt'),200)
        c.check(kind+'-'+kind+'-retry-same-body-order',same(got,original))
        alias=deepcopy(value);alias['ignored']=Number('90071992547409930e-1')
        got=c.response(kind+'-'+kind+'-retry-same-body-numeric-alias',c.call('POST',path,alias,token=token,key='receipt'),200)
        c.check(kind+'-'+kind+'-retry-same-body-numeric-alias',same(got,original))
        invalid={'count':False} if kind=='series' else {'slot_minutes':False}
        c.response(kind+'-'+kind+'-retry-different-body-priority',c.call('POST',path,invalid,token=token,key='receipt'),409,'idempotency_key_reuse')
        failed=deepcopy(value);failed['count' if kind=='series' else 'slot_minutes']=False
        c.response(kind+'-failed-key',c.call('POST',path,failed,token=token,key='failed'),422,'validation_failed')
        # Repair to a genuinely available second anchor for series (the first is
        # already adopted); failure did not claim the key.
        repaired=deepcopy(value)
        if kind=='series':repaired['anchor_reference']=c.create(seats=('c',),key='companion')['reference']
        c.response(kind+'-'+kind+'-retry-failure-key-reuse',c.call('POST',path,repaired,token=token,key='failed'),201)
        if kind=='series':
            c.response('series-patch-exception',c.call('PATCH','/reservations/'+anchor['reference'],dict(party_size=3),token=c.tokens['u']),200)
            c.response('series-cancel-no-exception',c.call('POST','/reservations/'+anchor['reference']+'/cancel',{},token=c.tokens['u']),200)
        else:c.response('policies-manager-allowed',c.call('POST',path,policy('2035-06-20'),token=token,key='later'),201)
        got=c.response(kind+'-'+kind+'-retry-replay-after-mutation',c.call('POST',path,value,token=token,key='receipt'),200)
        c.check(kind+'-'+kind+'-retry-replay-after-mutation',same(got,original))

def deep_family(c,release):
    target=release['urls']['target'];peer=release['urls']['peer']
    for kind in ['policies','series']:
        for shape in ['array','object','alternating']:
            for depth in [1100,5000,10000,20000]:
                c.setup();anchor=c.create()
                path='/restaurants/r/policies' if kind=='policies' else '/series'
                token=c.tokens['m' if kind=='policies' else 'u']
                base=raw(policy() if kind=='policies' else dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1))
                make=lambda leaf:base[:-1]+b',"ignored":'+wrap(shape,depth,leaf)+b'}'
                key='deep-'+kind+'-'+shape+'-'+str(depth)
                status,receipt,_=c.call('POST',path,body=make(LEAF),token=token,key=key)
                name=kind+'-deep-'+shape+'-'+str(depth)+'-'
                c.check(name+'strict-grammar',status==201)
                status,replayed,_=c.call('POST',path,body=make(LEAF_ALIAS),token=token,key=key)
                c.check(name+'numeric-alias',status==200 and same(replayed,receipt))
                for leaf in [LEAF_DIFFERENT,LEAF_TYPED]:
                    c.response(name+'typed-difference',c.call('POST',path,body=make(leaf),token=token,key=key),409,'idempotency_key_reuse')
                export=c.export();c.response(name+'raw-import',c.transfer(target,peer,export),204)
                status,replayed,_=c.call('POST',path,body=make(LEAF),token=token,key=key,url=peer)
                c.check(name+'original-replay',status==200 and same(replayed,receipt))
                export2=c.export(peer);c.response(name+'raw-import',c.transfer(peer,target,export2),204)
                status,replayed,_=c.call('POST',path,body=make(LEAF_ALIAS),token=token,key=key)
                c.check(name+'original-replay',status==200 and same(replayed,receipt))

def calendar_family(c):
    # Future dates permit adoption under a real, unmodified clock. Pure model
    # checks separately retain the specification's 2026 transition dates.
    from datetime import date,timedelta
    def sunday(year,month,last=False,minimum=1):
        start=date(year,month,minimum)
        while start.weekday()!=6:start+=timedelta(days=1)
        if last:
            while (start+timedelta(days=7)).month==month:start+=timedelta(days=7)
        return start
    for zone,transition,clock,gap in [('Europe/Berlin',sunday(2035,3,True),'02:30',True),
        ('Europe/Berlin',sunday(2035,10,True),'02:30',False),('America/New_York',sunday(2035,3,minimum=8),'02:30',True),
        ('America/New_York',sunday(2035,11),'01:30',False)]:
        c.setup(fixture(zone));local=(transition-timedelta(days=7)).isoformat()+'T'+clock
        anchor=c.create(local=local);before=c.public_state();body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
        status,value,_=c.call('POST','/series',body,token=c.tokens['u'],key='calendar')
        if gap:
            c.check('series-dst-gap',status==422 and value['error']['code']=='invalid_local_time')
            c.check('series-rollback-reservations',same(before,c.public_state()))
        else:
            c.check('series-dst-fold',status==201)
            member=value['occurrences'][1]['reservation']
            c.check('series-dst-fold',datetime.fromisoformat(member['starts_at']).astimezone(timezone.utc)==resolve(transition.isoformat()+'T'+clock,zone))
            c.check('series-absolute-duration',(datetime.fromisoformat(member['ends_at']).astimezone(timezone.utc)-datetime.fromisoformat(member['starts_at']).astimezone(timezone.utc)).total_seconds()==90*60)

def first_error_family(c):
    # Two failing dates with different errors establish indexed occurrence order.
    from datetime import date,timedelta
    transition=date(2035,3,25) # Independently confirmed below as Berlin's last March Sunday.
    while (transition+timedelta(days=7)).month==3:transition+=timedelta(days=7)
    if transition.weekday()!=6:raise RuntimeError('reference transition construction invalid')
    c.setup(fixture('Europe/Berlin'));anchor_day=transition-timedelta(days=14)
    anchor=c.create(local=anchor_day.isoformat()+'T02:30',party=2)
    middle=(anchor_day+timedelta(days=7)).isoformat()
    p=policy(middle,capacities=dict(a=1,b=4,c=6))
    c.response('policies-manager-allowed',c.call('POST','/restaurants/r/policies',p,token=c.tokens['m'],key='earlier-capacity'),201)
    before=c.public_state();body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
    c.response('series-first-failure',c.call('POST','/series',body,token=c.tokens['u'],key='first-failure'),422,'party_exceeds_capacity')
    c.check('series-rollback-reservations',same(before,c.public_state()))
    c.setup(fixture('Europe/Berlin'));anchor=c.create(local=(transition-timedelta(days=7)).isoformat()+'T02:30',party=2)
    c.create(local=(transition+timedelta(days=7)).isoformat()+'T02:30',party=2,key='later-occupied')
    before=c.public_state();body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
    c.response('series-first-failure',c.call('POST','/series',body,token=c.tokens['u'],key='first-failure'),422,'invalid_local_time')
    c.check('series-rollback-reservations',same(before,c.public_state()))

def moves_family(c):
    c.setup();a=c.create(seats=('b','a'),party=5);b=c.create(seats=('c',),key='second')
    sa=c.response('series-response-status',c.call('POST','/series',dict(anchor_reference=a['reference'],count=3,interval_weeks=1),token=c.tokens['u'],key='sa'),201)
    sb=c.response('series-response-status',c.call('POST','/series',dict(anchor_reference=b['reference'],count=3,interval_weeks=1),token=c.tokens['u'],key='sb'),201)
    c.series_ids=[sa['series_id'],sb['series_id']]
    aa=[x['reference'] for x in sa['occurrences']];bb=[x['reference'] for x in sb['occurrences']]
    body={'moves':[dict(reference=aa[0],table_ids=['c'],party_size=5,expected_revision=1),dict(reference=bb[0],table_ids=['a','b'],expected_revision=1),
        dict(reference=aa[1],party_size=6,expected_revision=1),dict(reference=bb[1])]}
    result=c.response('moves-swap-atomic',c.call('POST','/reservation-moves',body,token=c.tokens['u'],key='batch'),201)
    c.check('moves-changed-revision',[integer(x['revision']) for x in result['reservations']]==[2,2,2,1])
    for sid in c.series_ids:
        series=c.response('series-get-current',c.call('GET','/series/'+sid,token=c.tokens['u']),200)
        c.check('moves-series-once',integer(series['revision'])==2)
    before=c.public_state()
    bad={'moves':[dict(reference=aa[2],party_size=6),dict(reference=bb[2],expected_revision=999,party_size=False)]}
    c.response('moves-stale-priority',c.call('POST','/reservation-moves',bad,token=c.tokens['u'],key='failed-batch'),409,'stale_revision')
    c.check('moves-failure-records',same(before,c.public_state()))
    replay=c.response('moves-replay-counters',c.call('POST','/reservation-moves',body,token=c.tokens['u'],key='batch'),200)
    c.check('moves-replay-counters',same(replay,result) and same(before,c.public_state()))

def upgrade_family(c,release):
    for origin,stage in [('accepted-s1',1),('accepted-s2',2)]:
        source=release['urls'][origin];target=release['urls']['target'];peer=release['urls']['peer']
        c.setup(url=source);tokens=deepcopy(c.tokens);seats=('a',) if stage==1 else ('b','a')
        body=create_body(seats,party=2,stage=stage,ignored=Number('9007199254740993.0'))
        if stage==1:body['table_ids']={'previously_ignored':True}
        receipt=c.response('upgrade-'+origin+'-real-source',c.call('POST','/reservations',body,token=tokens['u'],key='origin',url=source),201)
        second=c.create(seats=('c',),key='other',url=source,stage=stage)
        moves={'moves':[dict(reference=second['reference'],party_size=3)]}
        moves_receipt=c.response('upgrade-'+origin+'-moves-receipt',c.call('POST','/reservation-moves',moves,token=tokens['u'],key='origin-moves',url=source),201)
        export=c.export(source);c.setup();obsolete=c.tokens['u'];c.tokens=tokens
        c.response('upgrade-raw-transfer',c.transfer(source,target,export),204)
        c.response('upgrade-replacement',c.call('GET','/reservations',token=obsolete),401,'unauthenticated')
        for user in ('u','v','m'):c.response('upgrade-sessions',c.call('GET','/reservations',token=tokens[user]),200)
        current=c.lookup(receipt['reference']);c.check('upgrade-references',current['reservation_id']==receipt['reservation_id'])
        adopted=c.response('upgrade-adoption',c.call('POST','/series',dict(anchor_reference=receipt['reference'],count=3,interval_weeks=1),token=tokens['u'],key='adopt-imported'),201)
        c.series_ids=[adopted['series_id']]
        for path,request,key,original in [('/reservations',body,'origin',receipt),('/reservation-moves',moves,'origin-moves',moves_receipt)]:
            got=c.response('upgrade-original-shape',c.call('POST',path,request,token=tokens['u'],key=key),200)
            c.check('upgrade-original-shape',same(got,original))
        mixed=c.export();c.response('upgrade-second-transfer',c.transfer(target,peer,mixed),204)
        got=c.response('upgrade-second-replay',c.call('POST','/reservations',body,token=tokens['u'],key='origin',url=peer),200)
        c.check('upgrade-second-replay',same(got,receipt))
        c.response('upgrade-series-roundtrip',c.call('GET','/series/'+adopted['series_id'],token=tokens['u'],url=peer),200)

def concurrent_family(c):
    c.setup();barrier=threading.Barrier(50);b=raw(policy());url=c.base;token=c.tokens['m']
    # Independent local clients, one buffered body each. A launch barrier establishes
    # client overlap; later staged final-byte workloads add stronger saved gates.
    def worker(i):
        barrier.wait();client=Client(url,c.out,'concurrent-'+str(i));result=client.call('POST','/restaurants/r/policies',token=token,key='same-policy',body=b)
        return result,client.trace
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(worker,range(50)))
    statuses=[x[0][0] for x in results];c.check('policies-policies-retry-concurrent50',statuses.count(201)==1 and statuses.count(200)==49)
    receipts=[x[0][1] for x in results];c.check('policies-policies-retry-concurrent50',all(same(receipts[0],v) for v in receipts))
    c.trace.extend({'event':'concurrent-worker', 'requests':t} for _,t in results);c.count+=50
    # Use a fresh original-capacity fixture for the amendment wave; the policy
    # wave above deliberately published capacity 2 and must not contaminate it.
    c.setup();anchor=c.create();ref=anchor['reference'];barrier=threading.Barrier(2)
    def amendment(party):
        barrier.wait();client=Client(url,c.out,'revision-race');return client.call('PATCH','/reservations/'+ref,dict(expected_revision=1,party_size=party),token=c.tokens['u']),client.trace
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(amendment,[3,4]))
    c.check('terms-concurrent-revision',sorted(x[0][0] for x in results)==[200,409])
    c.trace.extend({'event':'concurrent-amendment', 'requests':t} for _,t in results);c.count+=2
    c.check('history-seq-contiguous',len(c.history(ref)['entries'])==2)
    c.setup();anchor=c.create();barrier=threading.Barrier(50);b=raw(dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1));token=c.tokens['u']
    def adoption(i):
        barrier.wait();client=Client(url,c.out,'series-race');return client.call('POST','/series',body=b,token=token,key='same-series'),client.trace
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(adoption,range(50)))
    statuses=[x[0][0] for x in results];receipts=[x[0][1] for x in results]
    c.check('series-series-retry-concurrent50',statuses.count(201)==1 and statuses.count(200)==49 and all(same(receipts[0],v) for v in receipts))
    c.trace.extend({'event':'concurrent-series', 'requests':t} for _,t in results);c.count+=50

def trace_family(c):
    from stage3_trace import reference_trace,execute_trace
    execute_trace(c,reference_trace())

FAMILIES=dict(policies=policy_family,explain=explanation_family,numeric=numeric_family,terms=terms_family,
    series=series_family,rollback=rollback_family,moves=moves_family,concurrency=concurrent_family,retry=retry_family,calendar=calendar_family,trace=trace_family,first_error=first_error_family)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--family',required=True,choices=list(FAMILIES)+['upgrade','deep']);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if not args.execute:raise SystemExit('Prepared only: explicit later release plus --execute required')
    release=validate_release(json.loads(Path(args.release).read_text()));out=Path(args.out)
    if out.exists():raise SystemExit('New unique output required; preserved results cannot be replaced')
    c=Client(release['urls']['target'],out,release['candidate']);error=None
    try:
        if args.family=='upgrade':upgrade_family(c,release)
        elif args.family=='deep':deep_family(c,release)
        else:FAMILIES[args.family](c)
    except BaseException as exc:
        error=dict(kind='failed-expectation' if isinstance(exc,AssertionError) else 'runner-exception',type=type(exc).__name__,message=str(exc));raise
    finally:c.save(error)

if __name__=='__main__':main()
