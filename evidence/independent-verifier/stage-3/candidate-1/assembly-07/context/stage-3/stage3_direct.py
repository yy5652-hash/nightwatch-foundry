"""Labelled packaged Engine checks, not black-box HTTP or a clock endpoint.

Only this diagnostic process substitutes its datetime.now provider. Original
packaged source bytes are unmodified. Independent zoneinfo computes expectations.
"""
import copy,datetime as dt,hashlib,json
from pathlib import Path
from zoneinfo import ZoneInfo
import core
import json_codec

checks=[];observations=[];calls=0
def check(name,value):
 checks.append(dict(requirement_id=name,passed=bool(value)))
 if not value:raise AssertionError(name)
class Clock(dt.datetime):
 current=dt.datetime(2000,1,1,tzinfo=dt.timezone.utc)
 @classmethod
 def now(cls,tz=None):return cls.current.astimezone(tz) if tz is not None else cls.current.replace(tzinfo=None)
core.datetime=Clock
def fixture(zone='UTC',cutoff=0):
 return dict(users=[dict(id='u',email='u@direct.invalid',password='independent-pass',display_name='Diner')],restaurants=[dict(id='r',name='Juniper',timezone=zone,slot_minutes=30,reservation_duration_minutes=90,cancellation_cutoff_minutes=cutoff,manager_user_ids=['u'],opening_hours=[dict(weekday=d,opens='00:00',closes='23:59') for d in ('mon','tue','wed','thu','fri','sat','sun')],tables=[dict(id='a',label='Alcove',capacity=8)],combinable=[])],reservations=[])
def request(e,method,path,body=None,token=None,key=None):
 global calls
 headers={}
 if token:headers['authorization']='Bearer '+token
 if key:headers['idempotency-key']=key
 calls+=1;return e.request(method,path,headers,body)
def setup(f):
 e=core.Engine();check('DIRECT-reset',request(e,'POST','/_test/reset',f)[0]==204)
 status,auth=request(e,'POST','/auth/login',dict(email='u@direct.invalid',password='independent-pass'));check('DIRECT-login',status==200);return e,auth['token']
for zone,day,clock,gap in [('Europe/Berlin','2026-03-29','02:30',True),('Europe/Berlin','2026-10-25','02:30',False),('America/New_York','2026-03-08','02:30',True),('America/New_York','2026-11-01','01:30',False)]:
 Clock.current=dt.datetime(2000,1,1,tzinfo=dt.timezone.utc);e,token=setup(fixture(zone));date=dt.date.fromisoformat(day);anchor_local=(date-dt.timedelta(days=7)).isoformat()+'T'+clock
 status,anchor=request(e,'POST','/reservations',dict(restaurant_id='r',table_id='a',starts_at_local=anchor_local,party_size=2),token,'anchor');check('DIRECT-series-anchor-created',status==201)
 # A selected dated policy is real, and only applies from occurrence one.
 policy=dict(effective_from=day,slot_minutes=30,reservation_duration_minutes=60,cancellation_cutoff_minutes=0,opening_hours=fixture()['restaurants'][0]['opening_hours'],capacities=dict(a=6))
 check('DIRECT-series-policy-published',request(e,'POST','/restaurants/r/policies',policy,token,'policy')[0]==201)
 snapshot=json_codec.dumps(request(e,'GET','/_test/export')[1]);status,s=request(e,'POST','/series',dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1),token,'adopt')
 prefix='TK3-series-calendar-'+zone.replace('/','-')+'-'+day+'-'
 if gap:
  check(prefix+'first-fold-or-gap',status==422 and s['error']['code']=='invalid_local_time')
  check(prefix+'rollback-or-commit',snapshot==json_codec.dumps(request(e,'GET','/_test/export')[1]))
  for name in ('local-calendar','policy-date','absolute-end'):check(prefix+name,status==422 and s['error']['code']=='invalid_local_time')
 else:
  check(prefix+'rollback-or-commit',status==201 and len(s['occurrences'])==3)
  member=s['occurrences'][1]['reservation'];wall=dt.datetime.fromisoformat(day+'T'+clock).replace(tzinfo=ZoneInfo(zone),fold=0);start=wall.astimezone(dt.timezone.utc);end=start+dt.timedelta(minutes=60)
  check(prefix+'local-calendar',member['starts_at_local']==day+'T'+clock)
  check(prefix+'policy-date',member['accepted_terms']['policy_version']==1 and s['occurrences'][0]['reservation']==anchor)
  check(prefix+'first-fold-or-gap',dt.datetime.fromisoformat(member['starts_at']).astimezone(dt.timezone.utc)==start)
  check(prefix+'absolute-end',dt.datetime.fromisoformat(member['ends_at']).astimezone(dt.timezone.utc)==end)
 observations.append(dict(zone=zone,date=day,local_clock=clock,gap=gap,status=status,scope='packaged Engine; fixed diagnostic clock 2000-01-01; no HTTP clock-control endpoint'))
# Exact equality against the already accepted cutoff; no wall-clock jitter.
for method,path_suffix,body,key in [('POST','/cancel',{},None),('PATCH','',dict(party_size=3),None),('POST','series',None,'series'),('POST','moves',None,'moves')]:
 e,token=setup(fixture(cutoff=60));Clock.current=dt.datetime(2000,1,1,tzinfo=dt.timezone.utc)
 status,record=request(e,'POST','/reservations',dict(restaurant_id='r',table_id='a',starts_at_local='2026-10-05T18:00',party_size=2),token,'anchor');check('DIRECT-cutoff-anchor',status==201)
 ref=record['reference'];path='/reservations/'+ref+path_suffix
 if path_suffix=='series':path='/series';body=dict(anchor_reference=ref,count=2,interval_weeks=1)
 elif path_suffix=='moves':path='/reservation-moves';body=dict(moves=[dict(reference=ref,party_size=3)])
 Clock.current=dt.datetime(2026,10,5,17,tzinfo=dt.timezone.utc);before=json_codec.dumps(request(e,'GET','/_test/export')[1]);status,value=request(e,method,path,body,token,key)
 check('DIRECT-cutoff-equality-'+path_suffix,status==409 and value['error']['code']=='cutoff_passed' and before==json_codec.dumps(request(e,'GET','/_test/export')[1]))
 Clock.current-=dt.timedelta(microseconds=1);status,value=request(e,method,path,body,token,key);check('DIRECT-cutoff-before-'+path_suffix,status==(201 if path_suffix in ('series','moves') else 200))
# Request, receipt, response and export trees are detached from later caller edits.
Clock.current=dt.datetime(2000,1,1,tzinfo=dt.timezone.utc);f=fixture();e,token=setup(f);f['restaurants'][0]['tables'][0]['capacity']=1
body=dict(restaurant_id='r',table_id='a',starts_at_local='2035-06-04T18:00',party_size=2,ignored={'nested':[1]});original=copy.deepcopy(body)
status,receipt=request(e,'POST','/reservations',body,token,'detached');check('DIRECT-detached-fixture',status==201)
saved=copy.deepcopy(receipt);body['ignored']['nested'][0]=False;receipt['accepted_terms']['capacities']['a']=0
check('DIRECT-detached-receipt',request(e,'POST','/reservations',original,token,'detached')==(200,saved))
snapshot=request(e,'GET','/_test/export')[1];snapshot['state']['reservations'][0]['party_size']=99
check('DIRECT-detached-export',request(e,'GET','/reservations/'+saved['reference'],token=token)[1]==saved)
print(json.dumps(dict(scope='source-bound packaged Engine diagnostic, not HTTP',clock_substitution='only this process; source bytes unchanged',calls=calls,assertions=checks,failed=sum(not x['passed'] for x in checks),observations=observations,packaged_hashes={name:hashlib.sha256(Path('/app/'+name).read_bytes()).hexdigest() for name in ('core.py','json_codec.py','server.py')})))
