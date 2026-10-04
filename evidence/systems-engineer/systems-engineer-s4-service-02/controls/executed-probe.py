"""Source-bound packaged Engine clock/counter diagnostic, explicitly not HTTP."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,'/app')
import core
from json_codec import same_value, dumps
sys.set_int_max_str_digits(0)
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
clock=datetime(2026,1,1,tzinfo=timezone.utc)
class DiagnosticClock(datetime):
    @classmethod
    def now(cls,tz=None):
        return clock.astimezone(tz) if tz else clock.replace(tzinfo=None)
core.datetime=DiagnosticClock
e=core.Engine();assertions=0;calls=0;observations=[]
def check(condition,label):
    global assertions
    assertions+=1;observations.append({'label':label,'passed':bool(condition)})
    if not condition:raise AssertionError(label)
def request(method,path,body=None,headers=None,status=200,code=None):
    global calls
    calls+=1;s,v=e.request(method,path,headers or {},body)
    check(s==status,'status '+method+' '+path)
    if code:check(v.get('error',{}).get('code')==code,'error '+code)
    return v
f={'users':[{'id':u,'email':u+'@example.test','password':'fixture password','display_name':u} for u in ('u','m')],
   'restaurants':[{'id':'r','name':'Clock Garden','timezone':'Europe/Berlin','slot_minutes':30,'reservation_duration_minutes':90,
       'cancellation_cutoff_minutes':120,'manager_user_ids':['m'],
       'opening_hours':[{'weekday':d,'opens':'00:00','closes':'06:00'} for d in ('mon','tue','wed','thu','fri','sat','sun')],
       'tables':[{'id':x,'label':x,'capacity':2} for x in ('a','b','c')],'combinable':[['b','c']]}], 'reservations':[]}
began=time.monotonic()
try:
    request('POST','/_test/reset',f,status=204)
    login=request('POST','/auth/login',{'email':'u@example.test','password':'fixture password'});auth={'Authorization':'Bearer '+login['token']}
    manager=request('POST','/auth/login',{'email':'m@example.test','password':'fixture password'});mh={'Authorization':'Bearer '+manager['token']}
    body={'restaurant_id':'r','table_id':'a','party_size':1,'starts_at_local':'2026-03-15T01:00'}
    original=request('POST','/reservations',body,{**auth,'Idempotency-Key':'anchor'},201)
    series=request('POST','/series',{'anchor_reference':original['reference'],'count':3,'interval_weeks':1},{**auth,'Idempotency-Key':'adopt'},201)
    amend={'expected_revision':1,'from_index':0,'local_time':'02:30'};path='/series/'+series['series_id']+'/amend'
    before=request('GET','/_test/export')
    request('POST',path,amend,{**auth,'Idempotency-Key':'gap'},422,'invalid_local_time')
    check(same_value(before,request('GET','/_test/export')),'gap rolls all state back')
    clock=datetime(2026,4,1,tzinfo=timezone.utc)
    noop=request('POST',path,{'expected_revision':1,'from_index':0,'local_time':'01:00'},{**auth,'Idempotency-Key':'noop'},201)
    check(same_value(noop,series),'past eligible noop preserves series and all members')
    state=request('GET','/_test/export')['state'];check(state['restaurant_revisions']['r']==2,'noop does not bump restaurant')
    request('POST',path,amend,{**auth,'Idempotency-Key':'cutoff'},409,'cutoff_passed')
    request('POST',path,{**amend,'expected_revision':99},{**auth,'Idempotency-Key':'stale'},409,'stale_revision')
    closure={'table_id':'a','from':'2026-03-14T00:00:00Z','to':'2026-03-31T00:00:00Z'}
    plan=request('POST','/restaurants/r/replans',closure,{**mh,'Idempotency-Key':'preview'},201)
    applied=request('POST','/restaurants/r/replans/'+plan['plan_id']+'/apply',{}, {**mh,'Idempotency-Key':'apply'},201)
    check(len(applied['reservations'])==3 and all(r['revision']==2 for r in applied['reservations']),'past whole-series operator repair moves all members once')
    current=request('GET','/series/'+series['series_id'],headers=auth)
    check(current['revision']==2 and all(not o['exception'] for o in current['occurrences']),'repair increments series once without exceptions')
    check(all(o['reservation']['accepted_terms']==series['occurrences'][i]['reservation']['accepted_terms'] for i,o in enumerate(current['occurrences'])),'repair preserves terms')
    check(request('GET','/_test/export')['state']['restaurant_revisions']['r']==3,'repair increments restaurant once')
    check(request('POST','/reservations',body,{**auth,'Idempotency-Key':'anchor'})==original,'old create receipt survives repair')
    captured=request('GET','/_test/export');peer=core.Engine();check(peer.request('POST','/_test/import',{},captured)[0]==204,'populated diagnostic replacement accepted')
    result='passed'
except Exception as error:
    result='failed';observations.append({'error_type':type(error).__name__,'message':str(error)})
finally:
    summary={'result':result,'calls':calls,'assertions':assertions,'seconds':time.monotonic()-began,
        'scope':'packaged actual Engine with diagnostic-only substituted clock; not HTTP',
        'sha256':{p:hashlib.sha256(Path('/app',p).read_bytes()).hexdigest() for p in ('core.py','json_codec.py')}}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    (out/'executed-probe.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(summary));sys.exit(result!='passed')
