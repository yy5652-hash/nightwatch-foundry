"""Frozen-source assessment, not a production codec or acceptance suite.

Reuses proven own exact current/legacy images, checks their immutable identities,
and observes genuine rounded-float receipts through independent-process import.
Separate Decimal experiments examine JSON values without service changes.
"""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.set_int_max_str_digits(0)
ROOT = Path(__file__).resolve().parents[2]
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
prefix = "interface-engineer-num-" + stamp
OUT = ROOT / "evidence/interface-engineer" / prefix
OUT.mkdir()
BASE = ROOT / "evidence/interface-engineer/interface-engineer-s1-candidate5-20261004t024832530922z"
baseline = json.loads((BASE / "run.json").read_text())
commands, checks, created = [], [], []
network_created = False
START = time.monotonic()


def execute(argv, *, source=None, log=None, require=True):
    start = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, input=source, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    row = {"argv": argv, "seconds": time.monotonic() - start, "returncode": result.returncode}
    if source is not None:
        row["stdin_sha256"] = hashlib.sha256(source).hexdigest()
    if log:
        (OUT / log).write_bytes(result.stdout)
        row["output"] = log
    commands.append(row)
    if require and result.returncode:
        raise RuntimeError("Own assessment command failed")
    return result.stdout


def exact(token):
    return json.loads(token, parse_float=Decimal)


def integral(value):
    if type(value) is int:
        return True
    if not isinstance(value, Decimal) or not value.is_finite():
        return False
    _, digits, exponent = value.as_tuple()
    if not any(digits) or exponent >= 0:
        return True
    return -exponent <= len(digits) and all(digit == 0 for digit in digits[exponent:])


def legacy_projection(value):
    # Do not project integer-token values through float: that changes old parser
    # semantics. Decimal here represents only decimal/exponent token provenance.
    return float(value) if isinstance(value, Decimal) else value


def equal(left, right):
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right) and left == right
    return left == right


CLIENT = r'''
import hashlib,http.client,json,sys,time
from urllib.parse import urlsplit
urls=[urlsplit(u) for u in sys.argv[1:]]
results=[];trace=[];start=time.monotonic()
def check(name, condition): results.append({'name':name,'passed':bool(condition)})
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def call(i,method,path,body=None,headers=None,raw=None):
 c=http.client.HTTPConnection(urls[i].hostname,urls[i].port,timeout=5)
 wire=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
 try:
  c.request(method,path,wire,{'Content-Type':'application/json; charset=utf-8',**(headers or {})})
  r=c.getresponse(); data=r.read(); value=json.loads(data) if data else None
  trace.append({'process':i,'method':method,'path':path,'status':r.status,
    'code':value.get('error',{}).get('code') if isinstance(value,dict) else None,
    'request_sha256':hashlib.sha256(wire or b'').hexdigest(),'response_sha256':hashlib.sha256(data).hexdigest()})
  check('JSON response framing',r.getheader('Content-Type')=='application/json; charset=utf-8' and r.getheader('Content-Length')==str(len(data)))
  return r.status,value
 finally:c.close()
fixture={'users':[{'id':'u','email':'u@example.test','password':'correct horse','display_name':'Diner'}],
 'restaurants':[{'id':'r','name':'Quiet Dining','timezone':'UTC','slot_minutes':30,
 'reservation_duration_minutes':90,'cancellation_cutoff_minutes':0,
 'opening_hours':[{'weekday':d,'opens':'18:00','closes':'23:00'} for d in ['mon','tue','wed','thu','fri','sat','sun']],
 'tables':[{'id':'t','label':'Window','capacity':4}]}],'reservations':[]}
def raw(token):
 return ('{"restaurant_id":"r","table_id":"t","starts_at_local":"2099-06-04T18:00","party_size":1,"ignored":{"rounded":'+token+',"integer":9007199254740993}}').encode()
stored_public=None
try:
 check('Genuine earlier service reset',call(0,'POST','/_test/reset',fixture)==(204,None))
 auth=call(0,'POST','/auth/login',{'email':'u@example.test','password':'correct horse'})
 check('Genuine earlier service issues session',auth[0]==200)
 headers={'Authorization':'Bearer '+auth[1]['token'],'Idempotency-Key':'legacy-rounded'}
 original=call(0,'POST','/reservations',headers=headers,raw=raw('9007199254740993.0'))
 check('Genuine source issues original receipt',original[0]==201)
 snapshot=call(0,'GET','/_test/export')[1]
 receipt=snapshot['state']['receipts'][0]
 leaves=receipt['body']['ignored']
 stored_public={'float_type':type(leaves['rounded']).__name__,'float_repr':repr(leaves['rounded']),
   'integer_type':type(leaves['integer']).__name__,'integer_decimal':str(leaves['integer']),
   'receipt_has_parser_profile':any('parser' in k or 'codec' in k for k in receipt),
   'state_schema':snapshot['state']['schema'],'state_fingerprint':digest(snapshot)}
 check('Legacy export genuinely contains rounded float',type(leaves['rounded']) is float and leaves['rounded']==9007199254740992.0)
 check('Legacy export integer leaf remains exact',type(leaves['integer']) is int and leaves['integer']==9007199254740993)
 check('Frozen current accepts genuine unmodified old export',call(1,'POST','/_test/import',snapshot)==(204,None))
 check('Independent destination retains exact prior state',digest(call(1,'GET','/_test/export')[1])==digest(snapshot))
 for i in (0,1):
  check('Real source session/reference retained',call(i,'GET','/reservations/'+original[1]['reference'],headers=headers)==(200,original[1]))
  check('Same original decimal token recovers real receipt',call(i,'POST','/reservations',headers=headers,raw=raw('9007199254740993.0'))==(200,original[1]))
  check('Other token with same old float meaning replays',call(i,'POST','/reservations',headers=headers,raw=raw('9007199254740992.0'))==(200,original[1]))
  changed=call(i,'POST','/reservations',headers=headers,raw=raw('9007199254740994.0'))
  check('Different old parsed float value conflicts',changed[0]==409 and changed[1]['error']['code']=='idempotency_key_reuse')
  integer=call(i,'POST','/reservations',headers=headers,raw=raw('9007199254740993'))
  check('Integer token must not be rounded into old float receipt',integer[0]==409 and integer[1]['error']['code']=='idempotency_key_reuse')
  check('Exact integer equal to stored old value replays',call(i,'POST','/reservations',headers=headers,raw=raw('9007199254740992'))==(200,original[1]))
except Exception as exc:results.append({'name':'Own genuine legacy assessment completes','passed':False,'detail':type(exc).__name__})
print(json.dumps({'seconds':time.monotonic()-start,'operations':len(trace),'assertions':len(results),
 'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results),
 'stored_public_number_observation':stored_public,'results':results,'trace':trace},indent=2))
sys.exit(1 if any(not r['passed'] for r in results) else 0)
'''

errors=[]
try:
    semantic=[]
    for token in ('1','1.0','1e0','9007199254740993.0','1.5','1e-4300','1e4300','-0.0','true','"1"'):
        value=exact(token)
        numeric=type(value) is int or isinstance(value,Decimal)
        serialized=str(value) if numeric else json.dumps(value)
        semantic.append({'token':token,'exact_type':type(value).__name__,'integer_valued':integral(value),
                         'finite':value.is_finite() if isinstance(value,Decimal) else numeric,
                         'numeric_token_roundtrip_equal':equal(value,exact(serialized))})
    comparisons=[]
    for a,b in (('1','1.0'),('1e0','1'),('9007199254740993','9007199254740993.0'),
                ('9007199254740993.0','9007199254740992.0'),('9007199254740993','9007199254740993.0'),('true','1')):
        left,right=exact(a),exact(b)
        comparisons.append({'left':a,'right':b,'exact_numeric_equal':equal(left,right),
                            'legacy_projection_equal':equal(legacy_projection(left),legacy_projection(right))})
    (OUT/'semantic-experiments.json').write_text(json.dumps({'purpose':'Stdlib JSON-value/provenance assessment only, not service implementation',
        'values':semantic,'comparisons':comparisons},indent=2)+'\n')
    execute(['docker','network','create','--internal',prefix],log='network.log');network_created=True
    for index,label in enumerate(('legacy','source')):
        old=next(row for row in baseline['resources'] if row['label']==label)
        tag=baseline['image_tags_retained'][1 if label=='legacy' else 0]
        image_id=execute(['docker','image','inspect','--format','{{.Id}}',tag]).decode().strip()
        if image_id!=old['image']:raise RuntimeError('Retained own image identity changed')
        name=prefix+'-'+label
        execute(['docker','run','-d','--name',name,'--network',prefix,'--cpus','2','--memory','2g',
                 '-e','PORT=9090','-p',str(18228+index)+':9090',tag],log='run-'+label+'.log')
        created.append(name)
        code="import hashlib,json,pathlib,time,urllib.request; print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').glob('*.py')})); print(urllib.request.urlopen('http://127.0.0.1:9090/health',timeout=5).read().decode())"
        observed=execute(['docker','exec',name,'python','-c',code],log='identity-'+label+'.jsonl').decode().splitlines()
        if json.loads(observed[0])!=old['runtime_hashes']:raise RuntimeError('Own source hashes changed')
        info=json.loads(execute(['docker','inspect',name]))[0]
        checks.append({'label':label,'image_id':image_id,'runtime_hashes':json.loads(observed[0]),
                       'nano_cpus':info['HostConfig']['NanoCpus'],'memory':info['HostConfig']['Memory'],
                       'mounts':info['Mounts'],'network_mode':info['HostConfig']['NetworkMode']})
        if checks[-1]['nano_cpus']!=2000000000 or checks[-1]['memory']!=2147483648 or checks[-1]['mounts']:
            raise RuntimeError('Own service constraints do not match')
    result=json.loads(execute(['docker','run','--rm','-i','--name',prefix+'-client','--network',prefix,'--cpus','2',
       '--memory','2g','--entrypoint','python',baseline['image_tags_retained'][0],'-',
       *['http://'+n+':9090' for n in created]],source=CLIENT.encode(),log='genuine-legacy.json',require=False))
    if result['failed']:errors.append('Own genuine legacy assessment has failures')
except Exception as exc:errors.append(type(exc).__name__+': '+str(exc))
finally:
    cleanup=[]
    for name in reversed(created):
        execute(['docker','logs',name],log='logs-'+name.rsplit('-',1)[1]+'.txt',require=False)
        execute(['docker','rm','-f',name],log='cleanup-'+name.rsplit('-',1)[1]+'.txt',require=False);cleanup.append(commands[-1])
    if network_created:
        execute(['docker','network','rm',prefix],log='cleanup-network.txt',require=False);cleanup.append(commands[-1])
    if any(row['returncode'] for row in cleanup):errors.append('Own cleanup failed')
    (OUT/'run.json').write_text(json.dumps({'candidate':baseline['candidate'],'legacy_source':baseline['legacy_source'],
        'baseline_image_proof':str(BASE),'commands':commands,'identity_and_resources':checks,
        'cleanup':cleanup,'errors':errors,'seconds':time.monotonic()-START,'production_changes':False,
        'scope':'Source-decision assessment, genuine legacy observations; no new codec implemented'},indent=2)+'\n')
    print(json.dumps({'out':str(OUT),'seconds':time.monotonic()-START,'errors':errors}))
sys.exit(1 if errors else 0)
