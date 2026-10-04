"""Packaged Engine controls for two affected agreements and concurrent policy versions; not HTTP."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,threading,time
from core import Engine

started=time.monotonic();checks=0;e=Engine()
def check(value):
    global checks;checks+=1
    if not value:raise AssertionError('counter/control assertion '+str(checks))
def call(method,path,body=None,key=None):
    headers={'Authorization':'Bearer '+token} if 'token' in globals() else {}
    if key:headers['Idempotency-Key']=key
    return e.request(method,path,headers,body)
fixture={'users':[{'id':'u','email':'u@test','password':'test password','display_name':'U'}],
 'restaurants':[{'id':'r','name':'R','timezone':'UTC','slot_minutes':30,'reservation_duration_minutes':60,'cancellation_cutoff_minutes':0,
 'opening_hours':[{'weekday':d,'opens':'18:00','closes':'23:00'} for d in ('mon','tue','wed','thu','fri','sat','sun')],
 'tables':[{'id':'a','label':'A','capacity':2},{'id':'b','label':'B','capacity':4}],'manager_user_ids':['u']}],'reservations':[]}
check(call('POST','/_test/reset',fixture)[0]==204)
status,result=call('POST','/auth/login',{'email':'u@test','password':'test password'});check(status==200);token=result['token']
agreements=[]
for table in ('a','b'):
    status,anchor=call('POST','/reservations',{'restaurant_id':'r','table_id':table,'starts_at_local':'2099-01-01T18:00','party_size':1},table);check(status==201)
    status,agreement=call('POST','/series',{'anchor_reference':anchor['reference'],'count':2,'interval_weeks':1},table);check(status==201);agreements.append(agreement)
before=call('GET','/_test/export')[1]['state']['restaurant_revisions']['r']
moves=[{'reference':o['reference'],'table_id':'b' if index==0 else 'a','expected_revision':1} for index,s in enumerate(agreements) for o in s['occurrences']]
status,response=call('POST','/reservation-moves',{'moves':moves},'swap');check(status==201)
check(call('GET','/_test/export')[1]['state']['restaurant_revisions']['r']==before+1)
for series in agreements:
    current=call('GET','/series/'+series['series_id'])[1]
    check(current['revision']==2);check(all(o['exception'] and o['reservation']['revision']==2 for o in current['occurrences']))
    for occurrence in current['occurrences']:check(len(call('GET','/reservations/'+occurrence['reference']+'/history')[1]['entries'])==2)
check(call('POST','/reservation-moves',{'moves':moves},'swap')==(200,response))
for series in agreements:check(call('GET','/series/'+series['series_id'])[1]['revision']==2)
policy={'effective_from':'2099-01-01','slot_minutes':30,'reservation_duration_minutes':60,'cancellation_cutoff_minutes':0,'opening_hours':fixture['restaurants'][0]['opening_hours'],'capacities':{'a':2,'b':4}}
gate=threading.Barrier(50)
def publish(index):gate.wait();return call('POST','/restaurants/r/policies',policy,'pub-'+str(index))
with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(publish,range(50)))
check(all(r[0]==201 for r in results));check(sorted(r[1]['policy_version'] for r in results)==list(range(1,51)))
gate=threading.Barrier(50)
def replay(index):gate.wait();return call('POST','/restaurants/r/policies',policy,'identical')
with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(replay,range(50)))
check(sum(r[0]==201 for r in results)==1);check(sum(r[0]==200 for r in results)==49);check(all(r[1]==results[0][1] for r in results))
check(len(call('GET','/restaurants/r/policies')[1]['policies'])==51)
check(call('GET','/_test/export')[1]['state']['restaurant_revisions']['r']==before+52)
print(json.dumps({'kind':'packaged direct Engine, not HTTP','assertions':checks,'failed':0,'wall_seconds':time.monotonic()-started,
 'checked_utc':datetime.now(timezone.utc).isoformat(),'core_sha256':hashlib.sha256(open('/app/core.py','rb').read()).hexdigest(),
 'codec_sha256':hashlib.sha256(open('/app/json_codec.py','rb').read()).hexdigest()}))
