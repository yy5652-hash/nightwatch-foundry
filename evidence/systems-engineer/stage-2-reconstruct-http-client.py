"""Own Stage 2 black-box probes. No production imports; raw private transfers.

Grammar of deep values follows balanced wrapper composition around a finite leaf.
Saved traces contain statuses, public seating, timings and digests, never exports
or credential values. The ordinary member/interval oracle is a separate client.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import http.client
import json
from pathlib import Path
import re
import sys
import threading
import time
from urllib.parse import urlsplit

p = argparse.ArgumentParser()
for name in ('base', 'peer', 'accepted', 'legacy', 'old', 'out'):
    p.add_argument('--'+name, required=True)
a = p.parse_args()
sys.set_int_max_str_digits(0)  # Independent client only.
out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
events, checks, cases = [], [], []
lock = threading.Lock()
began = time.monotonic()

@dataclass(frozen=True)
class RawNumber:
    token: str
class NumberToken(str):
    pass
def digest(raw):
    return hashlib.sha256(raw).hexdigest()
def encode(value):
    literals = []
    def handle(item):
        if isinstance(item, RawNumber):
            marker = '__systems_raw_%d__' % len(literals)
            literals.append((json.dumps(marker), item.token))
            return marker
        raise TypeError(type(item).__name__)
    raw = json.dumps(value, default=handle, separators=(',', ':'), allow_nan=False)
    for marker, literal in literals:
        raw = raw.replace(marker, literal)
    return raw.encode()
def number(value):
    # Independent decimal normalization; no floating point or production helper.
    if type(value) not in (int, NumberToken):
        raise ValueError('Not a numeric response token')
    text = str(value)
    m = re.fullmatch(r'(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?', text)
    digits = (m[2]+(m[3] or '')).lstrip('0')
    exponent = int(m[4] or 0)-len(m[3] or '')
    if not digits:
        return False, '0', 0
    coefficient = digits.rstrip('0')
    return bool(m[1]), coefficient, exponent+len(digits)-len(coefficient)
def eqnumber(value, token):
    return number(value) == number(NumberToken(token))
def check(label, condition, **detail):
    with lock:
        checks.append({'label':label, 'passed':bool(condition), **detail})
def call(base, method, path, body=None, *, raw=None, token=None, key=None,
         expected=None, code=None, decode=True):
    if path == '/_test/export' and decode:
        raise AssertionError('Private export must be transferred raw')
    wire = raw if raw is not None else (None if body is None else encode(body))
    address = urlsplit(base)
    headers = {'Content-Type':'application/json; charset=utf-8'}
    if token is not None: headers['Authorization']='Bearer '+token
    if key is not None: headers['Idempotency-Key']=key
    start = time.monotonic()
    conn = http.client.HTTPConnection(address.hostname, address.port, timeout=10)
    conn.request(method,path,body=wire,headers=headers)
    response = conn.getresponse(); payload=response.read();conn.close()
    elapsed = time.monotonic()-start
    result = json.loads(payload, parse_float=NumberToken) if payload and decode else None
    observed_code = result.get('error',{}).get('code') if isinstance(result,dict) else None
    label = method+' '+path
    with lock:
        events.append({'service':base, 'method':method,'path':path,'status':response.status,
          'code':observed_code,'request_bytes':len(wire or b''),'request_sha256':digest(wire or b''),
          'response_bytes':len(payload),'response_sha256':digest(payload),'seconds':elapsed,
          'decoded':bool(payload and decode),'start_monotonic':start,'end_monotonic':start+elapsed})
    check(label+' no 5xx',response.status<500)
    check(label+' framing',response.getheader('Content-Length')==str(len(payload)) and
          'application/json' in response.getheader('Content-Type','') and
          'charset=utf-8' in response.getheader('Content-Type',''))
    check(label+' timeout',elapsed<(10 if path.startswith('/_test/') else 5))
    if expected is not None:check(label+' status',response.status==expected,expected=expected,observed=response.status)
    if code is not None:check(label+' code',observed_code==code,expected=code,observed=observed_code)
    if response.status==204:check(label+' empty',payload==b'')
    return response.status,result,payload
def fixture(owner='diner', capacities=None):
    values=capacities or [4,4,4,4]
    return {'users':[{'id':owner,'email':owner+'@example.test','password':'reconstruction password','display_name':owner}],
      'restaurants':[{'id':'r','name':'Garden Room','timezone':'UTC','slot_minutes':30,
        'reservation_duration_minutes':90,'cancellation_cutoff_minutes':0,
        'opening_hours':[{'weekday':d,'opens':'18:00','closes':'23:00'} for d in
                         ('mon','tue','wed','thu','fri','sat','sun')],
        'tables':[{'id':t,'label':t.upper(),'capacity':c} for t,c in zip('abcd',values)],
        'combinable':[['b','a'],['d','c'],['b','c']]}],'reservations':[]}
def login(base,owner='diner'):
    return call(base,'POST','/auth/login',{'email':owner+'@example.test','password':'reconstruction password'},expected=200)[1]['token']
def reset(base,owner='diner',capacities=None,ignored=None):
    wire=encode(fixture(owner,capacities))
    if ignored is not None:wire=wire[:-1]+b',"ignored":'+ignored+b'}'
    call(base,'POST','/_test/reset',raw=wire,expected=204)
    return login(base,owner)
def booking(members=('b','a'),party=6,day='2099-06-01',time='18:00'):
    return {'restaurant_id':'r','table_ids':list(members),'party_size':party,'starts_at_local':day+'T'+time}
def create(base,token,body,key,expected=201,code=None,raw=None):
    return call(base,'POST','/reservations',body,raw=raw,token=token,key=key,expected=expected,code=code)
def export(base):return call(base,'GET','/_test/export',expected=200,decode=False)[2]
def transfer(source,destination,raw):
    call(destination,'POST','/_test/import',raw=raw,expected=204)
    check('unchanged raw transfer fingerprint',events[-1]['request_sha256']==digest(raw))
def cancel(base,token,reference):
    return call(base,'POST','/reservations/'+reference+'/cancel',token=token,expected=200)
def scenario(label,operation):
    start=len(checks); t=time.monotonic()
    try: operation()
    except Exception as error:
        check(label+' completed',False,exception=type(error).__name__,message=str(error))
    cases.append({'label':label,'assertions':len(checks)-start,
                  'failed':sum(not c['passed'] for c in checks[start:]),'seconds':time.monotonic()-t})

def numeric_pairs():
    token=reset(a.base,capacities=[RawNumber('9007199254740993.0'),RawNumber('2e0'),4,4])
    options=call(a.base,'GET','/availability?restaurant_id=r&date=2099-06-01&party_size=9007199254740995',expected=200)[1]['slots'][0]
    check('exact pair capacity and singleton filtering',options['available_table_ids']==[] and
          options['available_options'][0]['table_ids']==['b','a'] and
          eqnumber(options['available_options'][0]['capacity'],'9007199254740995'))
    body=booking(party=RawNumber('9007199254740995e0'))
    original=create(a.base,token,body,'numeric')
    alias={**body,'party_size':RawNumber('9007199254740995.0')}
    check('pair numeric aliases original response',create(a.base,token,alias,'numeric',200)[2]==original[2])
    create(a.base,token,{**alias,'table_ids':False},'numeric',409,'idempotency_key_reuse')
    call(a.base,'PATCH','/reservations/'+original[1]['reference'],{'party_size':RawNumber('1.5')},token=token,expected=422,code='validation_failed')
    check('failed fractional amendment unchanged',call(a.base,'GET','/reservations/'+original[1]['reference'],token=token,expected=200)[2]==original[2])
    for value in (True,'2',None,RawNumber('0.5')):
        create(a.base,token,booking(party=value,time='21:00'),'reusable',422,'validation_failed')
    create(a.base,token,booking(party=RawNumber('9007199254740996'),time='21:00'),'reusable',422,'party_exceeds_capacity')
    create(a.base,token,booking(party=2,time='21:00'),'reusable')
    for spelling in ('1e0','2.0','%2B2','-2'):
        call(a.base,'GET','/availability?restaurant_id=r&date=2099-06-01&party_size='+spelling,expected=422,code='validation_failed')
    for exponent in ('4300','9'*80):
        token=reset(a.base,capacities=[RawNumber('4e'+exponent),RawNumber('6e'+exponent),
                                     RawNumber('4e'+exponent),RawNumber('6e'+exponent)])
        options=call(a.base,'GET','/availability?restaurant_id=r&date=2099-06-01&party_size=2',expected=200)[1]['slots'][0]['available_options']
        pair=next(o for o in options if o['table_ids']==['b','a'])
        check('compact exact eligible pair sum '+exponent[:8],eqnumber(pair['capacity'],'10e'+exponent))
        original=create(a.base,token,booking(party=RawNumber('10e'+exponent)),'compact')
        check('compact alias retry',create(a.base,token,booking(party=RawNumber('1e'+str(int(exponent)+1))),'compact',200)[2]==original[2])
        create(a.base,token,booking(party=RawNumber('11e'+exponent),time='21:00'),'excess',422,'party_exceeds_capacity')
        saved=export(a.base);transfer(a.base,a.peer,saved)
        check('compact original receipt replacement',create(a.peer,token,booking(party=RawNumber('10e'+exponent)),'compact',200)[2]==original[2])
    for malformed in (b'{"ignored":NaN}',b'{"ignored":Infinity}',b'{"ignored":1e}',b'{"ignored":[1,]}',b'{"ignored":"\xff"}'):
        before=export(a.peer)
        call(a.peer,'POST','/_test/import',raw=malformed,expected=400,code='malformed_request')
        check('malformed import rollback',export(a.peer)==before)

def genuine_origins():
    for origin,base,pair in (('accepted-exact-stage1',a.accepted,False),
                             ('old-stage1',a.legacy,False),('old-stage2',a.old,True)):
        token=reset(base,owner=origin)
        second_token=login(base,origin)
        precise={'rounded':RawNumber('9007199254740993.0'),'fraction':RawNumber('0.100000000000000005'),'tiny':RawNumber('1e-4300')}
        if pair:
            first=booking();second=booking(('d','c'))
        else:
            first={'restaurant_id':'r','table_id':'a','party_size':2,'starts_at_local':'2099-06-01T18:00',
                   'table_ids':{'formerly_ignored':precise}}
            second={**first,'table_id':'b','table_ids':False}
        first['ignored']=precise;second['ignored']=precise
        original=create(base,token,first,'origin-a'); other=create(base,token,second,'origin-b')
        if pair:
            items=[{'reference':original[1]['reference'],'table_ids':['c','d']},
                   {'reference':other[1]['reference'],'table_ids':['a','b']}]
        else:
            items=[{'reference':original[1]['reference'],'table_id':'b','table_ids':{'ignored':precise}},
                   {'reference':other[1]['reference'],'table_id':'a','table_ids':None}]
        move={'moves':items,'ignored':precise}
        moved=call(base,'POST','/reservation-moves',move,token=token,key='origin-move',expected=201)
        cancel(base,token,original[1]['reference'])
        captured=export(base)
        previous=reset(a.base,owner='replacement-only')
        transfer(base,a.base,captured)
        call(a.base,'GET','/reservations',token=previous,expected=401,code='unauthenticated')
        current=call(a.base,'GET','/reservations/'+original[1]['reference'],token=second_token,expected=200)[1]
        check(origin+' current cancelled representation',current['status']=='cancelled' and 'table_ids' in current)
        check(origin+' original shape retained',('table_ids' in original[1])==pair)
        for destination in (a.base,a.peer):
            if destination==a.peer:transfer(base,destination,captured)
            check(origin+' real create original',create(destination,token,first,'origin-a',200)[2]==original[2])
            check(origin+' real second original',create(destination,token,second,'origin-b',200)[2]==other[2])
            check(origin+' real moves original',call(destination,'POST','/reservation-moves',move,token=token,key='origin-move',expected=200)[2]==moved[2])
        if origin=='accepted-exact-stage1':
            different={**first,'table_ids':False,'party_size':False}
            create(a.base,token,different,'origin-a',409,'idempotency_key_reuse')
            create(a.base,token,first,'new-rule',422,'validation_failed')
        else:
            equal={**first,'ignored':{'rounded':9007199254740992,'fraction':RawNumber('0.1'),'tiny':0}}
            if not pair:equal['table_ids']={'formerly_ignored':equal['ignored']}
            check(origin+' historical numeric alias',create(a.base,token,equal,'origin-a',200)[2]==original[2])
            create(a.base,token,{**first,'ignored':{**precise,'rounded':9007199254740993}},'origin-a',409,'idempotency_key_reuse')
        login(a.base,origin)
        newbody={**booking(('d','c') if pair else ('c',),party=2,time='21:00'),
                 'ignored':RawNumber('9007199254740993.0')}
        new=create(a.base,token,newbody,'new-exact')
        mixed=export(a.base);transfer(a.base,a.peer,mixed)
        check(origin+' mixed exact origin survives',create(a.peer,token,newbody,'new-exact',200)[2]==new[2])
        create(a.peer,token,{**newbody,'ignored':9007199254740992},'new-exact',409,'idempotency_key_reuse')
        cancel(a.peer,token,new[1]['reference'])
        transfer(a.base,a.peer,mixed)
        check(origin+' replacement restores current state',call(a.peer,'GET','/reservations/'+new[1]['reference'],token=token,expected=200)[1]['status']=='confirmed')
        check(origin+' old receipt through mixed replacement',create(a.peer,token,first,'origin-a',200)[2]==original[2])
        bad=mixed.replace(b'"numeric_profile":"exact-v1"',b'"numeric_profile":"invalid"',1)
        check('invalid profile wire changed',bad!=mixed)
        before=export(a.peer);call(a.peer,'POST','/_test/import',raw=bad,expected=422,code='validation_failed')
        check(origin+' invalid mixed replacement atomic',export(a.peer)==before)
        reset(a.peer,owner='reset-clears')
        call(a.peer,'GET','/reservations',token=token,expected=401,code='unauthenticated')

def wrapper(shape,depth,leaf):
    if shape=='array':return b'['*depth+leaf+b']'*depth
    if shape=='object':return b'{"x":'*depth+leaf+b'}'*depth
    return b'{"x":['*(depth//2)+leaf+b']}'*(depth//2)
def attach(body,nested):return encode(body)[:-1]+b',"ignored":'+nested+b'}'
def deep_pairs():
    for depth,shape in ((10000,'array'),(10000,'object'),(20000,'array'),(20000,'object'),(20000,'alternating')):
        label=f'{shape}-{depth}'
        nested=wrapper(shape,depth,b'{"precise":0.100000000000000005,"large":1e4300}')
        alias=wrapper(shape,depth,b'{"large":10e4299,"precise":100000000000000005e-18}')
        wrong=wrapper(shape,depth,b'{"precise":true,"large":1e4300}')
        token=reset(a.base,ignored=nested)
        call(a.base,'POST','/auth/signup',raw=attach({'email':'deep@example.test','password':'reconstruction password','display_name':'Deep'},nested),expected=201)
        body=booking();wire=attach(body,nested)
        original=create(a.base,token,None,'deep-a',raw=wire)
        other=create(a.base,token,None,'deep-b',raw=attach(booking(('d','c')),nested))
        check(label+' alias original',create(a.base,token,None,'deep-a',200,raw=attach(body,alias))[2]==original[2])
        create(a.base,token,None,'deep-a',409,'idempotency_key_reuse',attach({**body,'party_size':False},wrong))
        move={'moves':[{'reference':original[1]['reference'],'table_ids':['c','d']},
                       {'reference':other[1]['reference'],'table_ids':['a','b']}]}
        movewire=attach(move,nested)
        moved=call(a.base,'POST','/reservation-moves',raw=movewire,token=token,key='deep-move',expected=201)
        before=export(a.base)
        badmove={'moves':[{'reference':original[1]['reference'],'table_ids':['b','a']},
                          {'reference':other[1]['reference'],'party_size':True}]}
        call(a.base,'POST','/reservation-moves',raw=attach(badmove,nested),token=token,key='failed',expected=422,code='validation_failed')
        check(label+' nonoccupancy errors before overlap and rollback',export(a.base)==before)
        call(a.base,'POST','/reservation-moves',raw=attach({'moves':[{'reference':original[1]['reference'],'table_ids':['b','a']},
                   {'reference':other[1]['reference'],'table_ids':['b','a']}]},nested),token=token,key='failed',expected=409,code='table_unavailable')
        check(label+' overlap failed key reusable and atomic',export(a.base)==before)
        call(a.base,'POST','/reservation-moves',raw=attach({'moves':[{'reference':original[1]['reference']}]},nested),token=token,key='failed',expected=201)
        saved=export(a.base);cancel(a.base,token,original[1]['reference'])
        transfer(a.base,a.peer,saved)
        for base in (a.base,a.peer):
            check(label+' original create after edits/raw replacement',create(base,token,None,'deep-a',200,raw=wire)[2]==original[2])
            check(label+' original moves after edits/raw replacement',call(base,'POST','/reservation-moves',raw=attach(move,alias),token=token,key='deep-move',expected=200)[2]==moved[2])
        roundtrip=export(a.peer);transfer(a.peer,a.base,roundtrip)
        check(label+' second raw replacement original',create(a.base,token,None,'deep-a',200,raw=wire)[2]==original[2])
        before=export(a.base)
        call(a.base,'POST','/_test/import',raw=before[:-1],expected=400,code='malformed_request')
        check(label+' malformed deep import atomic',export(a.base)==before)
        check(label+' deep export not decoded',all(not e['decoded'] for e in events if e['path']=='/_test/export'))
    nested=wrapper('object',20000,b'{"precise":0.100000000000000005}')
    for competing in (False,True):
        token=reset(a.base)
        gate=threading.Barrier(50)
        def writer(i):
            body=booking(('b','c') if competing and i%2 else ('b','a'))
            gate.wait()
            return create(a.base,token,None,f'competing-{i}' if competing else 'identical',expected=None,raw=attach(body,nested))
        with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(writer,range(50)))
        counts=Counter(r[0] for r in results)
        check('deep pair race counts',counts==({201:1,409:49} if competing else {201:1,200:49}),counts=dict(counts))
        if competing:
            check('all member competitors refused precisely',all(r[0]==201 or r[1]['error']['code']=='table_unavailable' for r in results))
            loser=next(i for i,r in enumerate(results) if r[0]==409)
            create(a.base,token,booking(time='21:00'),f'competing-{loser}')
        else:
            check('all concurrent original pair receipts identical',len({r[2] for r in results})==1)
            check('one current pair booking',len(call(a.base,'GET','/reservations',token=token,expected=200)[1]['reservations'])==1)
            original=results[0];saved=export(a.base);transfer(a.base,a.peer,saved)
            cancel(a.peer,token,original[1]['reference'])
            check('deep race original receipt replacement/cancel',create(a.peer,token,None,'identical',200,raw=attach(booking(),nested))[2]==original[2])

for label,operation in (('exact combined capacities and values',numeric_pairs),
                        ('three genuine origins and mixed replacement',genuine_origins),
                        ('deep combined receipts/raw transfer/races',deep_pairs)):
    scenario(label,operation)
summary={'requests':len(events),'assertions':len(checks),'failed':sum(not c['passed'] for c in checks),
         'scenarios':len(cases),'seconds':time.monotonic()-began,
         'maximum_request_seconds':max(e['seconds'] for e in events),
         'maximum_request_bytes':max(e['request_bytes'] for e in events)}
(out/'trace.json').write_text(json.dumps({'summary':summary,'scenarios':cases,'events':events,'assertions':checks},indent=2)+'\n')
print(json.dumps(summary))
raise SystemExit(bool(summary['failed']))
