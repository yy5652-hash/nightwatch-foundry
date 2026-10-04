"""Independent complete closure error/precision classification from cumulative specs.

The interval rule governs correct-type invalid intervals; Stage1 section5 retains
400 for wrong JSON types. No builder/official protocol or production helper used.
Private credentials/exports remain in process memory, never saved.
"""
import argparse, datetime as dt, hashlib, http.client, json, time
from pathlib import Path
from urllib.parse import urlsplit
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--release',required=True);parser.add_argument('--out',required=True);a=parser.parse_args()
 release=json.loads(Path(a.release).read_text());out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
 assert release['stage']==4 and release['complete_candidate_package'] and release['acknowledged_before_execution']
 for prefix in ['source_proof','resource_proof','package_intake']:
  p=Path(release[prefix+'_path']);assert sha(p.read_bytes())==release[prefix+'_sha256']
 u=urlsplit(release['urls']['target']);assert u.hostname.startswith('independent-verifier-')
 started=dt.datetime.now(dt.timezone.utc).isoformat();calls=[];checks=[];tokens={}
 def call(method,path,body=None,key=None,token=None,raw=False):
  payload=body if raw else (None if body is None else json.dumps(body,separators=(',',':')).encode())
  headers={'Content-Type':'application/json; charset=utf-8'}
  if key is not None:headers['Idempotency-Key']=key
  if token is not None:headers['Authorization']='Bearer '+token
  conn=http.client.HTTPConnection(u.hostname,u.port,timeout=10 if path.startswith('/_test/') else 5)
  begin=time.monotonic();conn.request(method,path,payload,headers);response=conn.getresponse();data=response.read();elapsed=time.monotonic()-begin;conn.close()
  value=None if path=='/_test/export' or not data else json.loads(data)
  code=value.get('error',{}).get('code') if isinstance(value,dict) else None
  row=dict(index=len(calls)+1,method=method,path=path,request_bytes=len(payload or b''),request_sha256=sha(payload or b''),key=key,authenticated=token is not None,status=response.status,error_code=code,response_bytes=len(data),response_sha256=sha(data),seconds=elapsed,content_type=response.getheader('Content-Type'))
  if path.endswith('/replans'):row['body']=body.decode() if raw else body
  calls.append(row);return response.status,value,data
 def check(case,condition,expected=None,actual=None,source='Stage1 section5; Stage4 Seating changes after a table closure'):
  checks.append(dict(requirement=case,passed=bool(condition),expected=expected,actual=actual,source=source,request_index=len(calls),candidate=release['candidate']))
 def expect(case,result,status,code=None):
  got,value,_=result;actual=[got,value.get('error',{}).get('code') if isinstance(value,dict) else None]
  check(case,got==status and (code is None or actual[1]==code),[status,code],actual)
 fixture=dict(users=[dict(id='m',email='manager@independent.test',password='independent fixture',display_name='Manager'),dict(id='u',email='diner@independent.test',password='independent fixture',display_name='Diner')],restaurants=[dict(id='r',name='Verifier Restaurant',timezone='UTC',slot_minutes=30,reservation_duration_minutes=30,cancellation_cutoff_minutes=0,opening_hours=[dict(weekday=w,opens='17:00',closes='23:00') for w in ['mon','tue','wed','thu','fri','sat','sun']],tables=[dict(id='a',label='Window',capacity=2),dict(id='b',label='Garden',capacity=4)],combinable=[['a','b']],manager_user_ids=['m'])],reservations=[])
 expect('setup-reset',call('POST','/_test/reset',fixture),204)
 for who,email in [('m','manager@independent.test'),('u','diner@independent.test')]:
  got=call('POST','/auth/login',dict(email=email,password='independent fixture'));expect('setup-login-'+who,got,200);tokens[who]=got[1]['token']
 base={'table_id':'a','from':'2035-06-04T18:00:00+00:00','to':'2035-06-04T19:00:00+00:00'}
 cases=[]
 for field in ['from','to']:
  for name,value in [('null',None),('true',True),('false',False),('number',7),('array',[]),('object',{})]:cases.append((field+'-wrong-type-'+name,{**base,field:value},400,'malformed_request'))
  missing={k:v for k,v in base.items() if k!=field};cases.append((field+'-missing',missing,422,'validation_failed'))
  for name,value in [('empty',''),('text','invalid'),('no-offset','2035-06-04T18:00:00'),('bad-date','2035-02-30T18:00:00+00:00'),('bad-clock','2035-06-04T25:00:00+00:00'),('bad-offset','2035-06-04T18:00:00+25:00')]:cases.append((field+'-bad-format-'+name,{**base,field:value},422,'validation_failed'))
 cases.extend([('interval-equal',{**base,'to':base['from']},422,'validation_failed'),('interval-reversed',{**base,'from':base['to'],'to':base['from']},422,'validation_failed'),('table-wrong-type',{**base,'table_id':{}},400,'malformed_request'),('table-missing',{k:v for k,v in base.items() if k!='table_id'},422,'validation_failed'),('table-unknown',{**base,'table_id':'missing'},404,'not_found')])
 try:
  for i,(case,body,status,code) in enumerate(cases):
   before=call('GET','/_test/export')[2]
   expect('closure-'+case,call('POST','/restaurants/r/replans',body,key='error-'+str(i),token=tokens['m']),status,code)
   after=call('GET','/_test/export')[2];check('closure-'+case+'-atomic',before==after,sha(before),sha(after))
   repaired=call('POST','/restaurants/r/replans',base,key='error-'+str(i),token=tokens['m']);expect('closure-'+case+'-failed-key-reusable',repaired,201)
  for i,payload in enumerate([b'null',b'[]',b'1',b'true',b'{',b'{"from":NaN}']):
   before=call('GET','/_test/export')[2]
   expect('whole-body-malformed-'+str(i),call('POST','/restaurants/r/replans',payload,key='whole-'+str(i),token=tokens['m'],raw=True),400,'malformed_request')
   after=call('GET','/_test/export')[2];check('whole-body-atomic-'+str(i),before==after)
  original=call('POST','/restaurants/r/replans',base,key='used',token=tokens['m']);expect('valid-preview',original,201)
  expect('used-key-difference-before-type',call('POST','/restaurants/r/replans',{**base,'from':None},key='used',token=tokens['m']),409,'idempotency_key_reuse')
  replay=call('POST','/restaurants/r/replans',dict(reversed(list(base.items()))),key='used',token=tokens['m']);expect('preview-replay',replay,200);check('preview-receipt-original',original[1]==replay[1])
  expect('booking-for-boundaries',call('POST','/reservations',dict(restaurant_id='r',table_id='a',starts_at_local='2035-06-04T18:00',party_size=1),key='boundary-booking',token=tokens['u']),201)
  boundaries=[('before-equal','2035-06-04T17:59:00+00:00','2035-06-04T18:00:00+00:00',0),('before-tiny-overlap','2035-06-04T17:59:00+00:00','2035-06-04T18:00:00.000000000000000001+00:00',1),('after-equal','2035-06-04T18:30:00+00:00','2035-06-04T19:00:00+00:00',0),('after-tiny-overlap','2035-06-04T18:29:59.999999999999999999+00:00','2035-06-04T19:00:00+00:00',1)]
  for case,start,end,count in boundaries:
   got=call('POST','/restaurants/r/replans',dict(table_id='a',**{'from':start},to=end),key=case,token=tokens['m']);expect('closure-'+case,got,201);check('closure-'+case+'-considered',len(got[1]['assignments'])==count,count,len(got[1]['assignments']))
 finally:
  (out/'executed-source.py').write_bytes(Path(__file__).read_bytes())
  (out/'requests.json').write_text(json.dumps(calls,indent=2)+'\n');(out/'assertions.json').write_text(json.dumps(checks,indent=2)+'\n')
  summary=dict(candidate=release['candidate'],started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),requests=len(calls),assertions=len(checks),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),errors=0,maximum_request_seconds=max(c['seconds'] for c in calls),private_exports_saved=False,source_interpretation='Wrong endpoint JSON types use inherited400; correct-type invalid/missing intervals use422; no new coordinator decision inferred.')
  (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
 raise SystemExit(any(not c['passed'] for c in checks))
if __name__=='__main__':main()
