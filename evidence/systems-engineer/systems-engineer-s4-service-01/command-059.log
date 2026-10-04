"""Actual deep Stage 3 write receipts and raw unchanged state transfer; exports never decoded."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request,urlopen

p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--peer',required=True);p.add_argument('--out',required=True);a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=False);events=[];checks=[];transfers=[];started=time.monotonic()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def check(label,condition):
    checks.append({'label':label,'passed':bool(condition)})
    if not condition:raise AssertionError(label)
def http(base,method,path,raw=None,token=None,key=None,status=200,decode=True):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    if key:headers['Idempotency-Key']=key
    t=time.monotonic();req=Request(base+path,method=method,data=raw,headers=headers)
    try:r=urlopen(req,timeout=10 if path.startswith('/_test/') else 5)
    except HTTPError as error:r=error
    with r:
        body=r.read();got=r.status
        check('UTF-8 JSON content type',r.headers.get('Content-Type','').lower()=='application/json; charset=utf-8')
        check('exact response Content-Length',int(r.headers['Content-Length'])==len(body))
    elapsed=time.monotonic()-t
    events.append({'method':method,'path':path,'request_bytes':len(raw or b''),'request_sha256':sha(raw or b''),'status':got,'response_bytes':len(body),'response_sha256':sha(body),'seconds':elapsed,'decoded':decode})
    check('applicable request deadline',elapsed<(10 if path.startswith('/_test/') else 5))
    check('expected HTTP status',got in status if isinstance(status,tuple) else got==status)
    return got,json.loads(body) if body and decode else None,body
def body(value):return json.dumps(value,separators=(',',':')).encode()
def envelope(value,deep):
    return body(value)[:-1]+b',"unused":'+deep+b'}'
def login(base,user):return http(base,'POST','/auth/login',body({'email':user+'@test','password':'test password'}))[1]['token']
fixture={'users':[{'id':u,'email':u+'@test','password':'test password','display_name':u} for u in ('u','m')],
 'restaurants':[{'id':'r','name':'R','timezone':'UTC','slot_minutes':30,'reservation_duration_minutes':60,'cancellation_cutoff_minutes':0,
 'opening_hours':[{'weekday':d,'opens':'18:00','closes':'23:00'} for d in ('mon','tue','wed','thu','fri','sat','sun')],
 'tables':[{'id':'a','label':'A','capacity':2},{'id':'b','label':'B','capacity':4}],'combinable':[['b','a']],'manager_user_ids':['m']}],'reservations':[]}
policy={'effective_from':'2099-01-01','slot_minutes':30,'reservation_duration_minutes':60,'cancellation_cutoff_minutes':0,
        'opening_hours':fixture['restaurants'][0]['opening_hours'],'capacities':{'a':2,'b':4}}
try:
    for shape,depth in (('array',10000),('object',10000),('alternating',20000)):
        if shape=='array':prefix=b'['*depth;suffix=b']'*depth
        elif shape=='object':prefix=b'{"x":'*depth;suffix=b'}'*depth
        else:prefix=b'[{"x":'*(depth//2);suffix=b'}]'*(depth//2)
        deep=prefix+b'{"n":1,"huge":1e999999,"tiny":1e-999999}'+suffix
        equal=prefix+b'{"n":1.0,"huge":10e999998,"tiny":10e-1000000}'+suffix
        unequal=prefix+b'{"n":true,"huge":1e999999,"tiny":1e-999999}'+suffix
        http(a.base,'POST','/_test/reset',envelope(fixture,deep),status=204);u=login(a.base,'u');m=login(a.base,'m')
        published=http(a.base,'POST','/restaurants/r/policies',envelope(policy,deep),m,'shared',201)[1]
        check('deep policy exact alias original response',http(a.base,'POST','/restaurants/r/policies',envelope(policy,equal),m,'shared')[1]==published)
        http(a.base,'POST','/restaurants/r/policies',envelope(policy,unequal),m,'shared',409)
        booking={'restaurant_id':'r','table_ids':['a','b'],'starts_at_local':'2099-04-16T18:00','party_size':5}
        raw=envelope(booking,deep);alias=envelope(booking,equal)
        original=http(a.base,'POST','/reservations',raw,u,'shared',201)[1]
        check('deep create canonical pair',original['table_ids']==['b','a'])
        check('deep create exact alias receipt',http(a.base,'POST','/reservations',alias,u,'shared')[1]==original)
        adoption={'anchor_reference':original['reference'],'count':3,'interval_weeks':1}
        series_raw=envelope(adoption,deep);series=http(a.base,'POST','/series',series_raw,u,'shared',201)[1]
        check('same key independent write path',series['occurrences'][0]['reservation']==original)
        check('deep series exact alias',http(a.base,'POST','/series',envelope(adoption,equal),u,'shared')[1]==series)
        moves={'moves':[{'reference':o['reference'],'table_ids':['b'],'party_size':4} for o in series['occurrences']]}
        move_raw=envelope(moves,deep);moved=http(a.base,'POST','/reservation-moves',move_raw,u,'shared',201)[1]
        check('deep batch exact alias',http(a.base,'POST','/reservation-moves',envelope(moves,equal),u,'shared')[1]==moved)
        captured=http(a.base,'GET','/_test/export',decode=False)[2]
        http(a.base,'POST','/reservations/'+original['reference']+'/cancel',token=u)
        http(a.peer,'POST','/_test/import',captured,status=204)
        transfers.append({'shape':shape,'depth':depth,'export_bytes':len(captured),'import_bytes':len(captured),'export_sha256':sha(captured),'import_sha256':sha(captured),'decoded':False})
        for path,request,key,response,token in (('/reservations',raw,'shared',original,u),('/series',series_raw,'shared',series,u),('/reservation-moves',move_raw,'shared',moved,u),('/restaurants/r/policies',envelope(policy,deep),'shared',published,m)):
            check('original deep receipt after raw replacement '+path,http(a.peer,'POST',path,request,token,key)[1]==response)
        current=http(a.peer,'GET','/series/'+series['series_id'],token=u)[1]
        check('batch affects agreement once',current['revision']==2 and all(o['exception'] for o in current['occurrences']))
        check('anchor cancellation after source capture did not enter peer',current['occurrences'][0]['reservation']['status']=='confirmed')
        http(a.peer,'POST','/reservations/'+original['reference']+'/cancel',token=u)
        again=http(a.peer,'GET','/_test/export',decode=False)[2]
        http(a.base,'POST','/_test/import',again,status=204)
        transfers.append({'shape':shape,'depth':depth,'export_bytes':len(again),'import_bytes':len(again),'export_sha256':sha(again),'import_sha256':sha(again),'decoded':False})
        check('deep original series response after mutation/second replacement',http(a.base,'POST','/series',series_raw,u,'shared')[1]==series)
        stable=http(a.base,'GET','/_test/export',decode=False)[2]
        malformed=stable+b',';http(a.base,'POST','/_test/import',malformed,status=400)
        check('malformed deep replacement atomic',http(a.base,'GET','/_test/export',decode=False)[2]==stable)
        altered=stable.replace(b'"numeric_profile":"exact-v1"',b'"numeric_profile":"foreign"',1)
        check('genuine profile mutation present',altered!=stable)
        http(a.base,'POST','/_test/import',altered,status=422)
        check('unsupported profile replacement atomic',http(a.base,'GET','/_test/export',decode=False)[2]==stable)
    # A separate depth-20,000 array creates a genuine fifty-client receipt wave.
    deep=b'['*20000+b'{"n":1}'+b']'*20000
    http(a.base,'POST','/_test/reset',body(fixture),status=204);u=login(a.base,'u')
    booking={'restaurant_id':'r','table_ids':['b','a'],'starts_at_local':'2099-05-01T18:00','party_size':5};raw=envelope(booking,deep);gate=threading.Barrier(50)
    def create(_):gate.wait();return http(a.base,'POST','/reservations',raw,u,'race',(200,201))
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(create,range(50)))
    check('fifty deep creates one first response',sum(r[0]==201 for r in results)==1)
    check('fifty deep creates forty-nine original replays',sum(r[0]==200 for r in results)==49 and all(r[1]==results[0][1] for r in results))
    anchor=results[0][1];adoption=envelope({'anchor_reference':anchor['reference'],'count':2,'interval_weeks':1},deep);gate=threading.Barrier(50)
    def adopt(_):gate.wait();return http(a.base,'POST','/series',adoption,u,'race',(200,201))
    with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(adopt,range(50)))
    check('fifty deep adoptions one first response',sum(r[0]==201 for r in results)==1)
    check('fifty deep adoptions same original response',sum(r[0]==200 for r in results)==49 and all(r[1]==results[0][1] for r in results))
    captured=http(a.base,'GET','/_test/export',decode=False)[2];http(a.peer,'POST','/_test/import',captured,status=204)
    transfers.append({'shape':'race-array','depth':20000,'export_bytes':len(captured),'import_bytes':len(captured),'export_sha256':sha(captured),'import_sha256':sha(captured),'decoded':False})
    check('deep race series original receipt after transfer',http(a.peer,'POST','/series',adoption,u,'race')[1]==results[0][1])
    result='passed'
except Exception as error:
    result='failed';checks.append({'label':'runner exception','passed':False,'type':type(error).__name__,'message':str(error)})
finally:
    summary={'result':result,'requests':len(events),'assertions':len(checks),'failed':sum(not c['passed'] for c in checks),'raw_transfers':len(transfers),'wall_seconds':time.monotonic()-started,
             'maximum_request_seconds':max((e['seconds'] for e in events),default=0),'maximum_request_bytes':max((e['request_bytes'] for e in events),default=0)}
    (out/'trace.json').write_text(json.dumps({'summary':summary,'operations':events,'assertions':checks,'raw_transfers':transfers},indent=2)+'\n')
    (out/'executed-probe.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(summary));raise SystemExit(result!='passed')
