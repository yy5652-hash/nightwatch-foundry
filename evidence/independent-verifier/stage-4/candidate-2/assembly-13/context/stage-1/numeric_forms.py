"""JSON number lexical/value boundaries, distinct from decimal query grammar."""
import copy
import json
import sys
import time
import urllib.error
import urllib.request
sys.set_int_max_str_digits(0) # Client only, not the service process.
BASE,CANDIDATE=sys.argv[1:3]
ops=[]
checks=[]
start=time.monotonic()
f={"users":[],"restaurants":[{"id":"r","name":"Numeric Kitchen","timezone":"UTC","slot_minutes":30,"reservation_duration_minutes":90,"cancellation_cutoff_minutes":0,"opening_hours":[{"weekday":"mon","opens":"18:00","closes":"23:00"}],"tables":[{"id":"t","label":"Window","capacity":2}]}],"reservations":[]}
def safe(v):
    if isinstance(v,dict): return {k: "[private client value]" if k in {"token","password","state"} else safe(x) for k,x in v.items()}
    if isinstance(v,list):return [safe(x) for x in v]
    return v
def call(method,path,raw=None,token=None,key=None):
    headers={"Content-Type":"application/json; charset=utf-8"}
    if token: headers["Authorization"]="Bearer "+token
    if key: headers["Idempotency-Key"]=key
    request=urllib.request.Request(BASE+path,data=None if raw is None else raw.encode(),method=method,headers=headers)
    began=time.monotonic()
    try:
        try: response=urllib.request.urlopen(request,timeout=10 if path.startswith("/_test/") else 5)
        except urllib.error.HTTPError as e:response=e
        with response: status,text=response.status,response.read().decode()
        value=json.loads(text) if text else None
    except Exception as e:status,value=0,{"transport_error":str(e)}
    ops.append(dict(method=method,path=path,raw_body=raw if path=="/_test/reset" else "[synthetic credentials redacted]" if path.startswith("/auth") else raw,status=status,response=safe(value),duration_seconds=time.monotonic()-began))
    return status,value
def check(key,condition,expected,observed):
    checks.append(dict(requirement_id="TK1-numeric-"+key,passed=bool(condition),expected=safe(expected),observed=safe(observed)))
def reset():
    s,v=call("POST","/_test/reset",json.dumps(f))
    check("control-reset",s==204,204,dict(status=s,response=v))

for field in ["slot_minutes","reservation_duration_minutes","cancellation_cutoff_minutes","capacity"]:
    for literal in ["1.0","1e0"]:
        reset()
        altered=copy.deepcopy(f)
        target=altered["restaurants"][0]["tables"][0] if field=="capacity" else altered["restaurants"][0]
        target[field]="NUMERIC_SENTINEL"
        raw=json.dumps(altered).replace('"NUMERIC_SENTINEL"',literal)
        s,v=call("POST","/_test/reset",raw)
        check(field+"-"+literal,s==204,"204 for positive integer JSON number value1",dict(status=s,response=v))

for literal in ["1.0","1e0"]:
    reset()
    s,user=call("POST","/auth/signup",json.dumps(dict(email="numeric@probe.invalid",password="numeric-probe-pass",display_name="Numeric Diner")))
    token=user["token"]
    raw='{"restaurant_id":"r","table_id":"t","starts_at_local":"2035-06-04T18:00","party_size":'+literal+'}'
    s,v=call("POST","/reservations",raw,token,"integer-"+literal)
    check("party-"+literal,s==201 and v.get("party_size")==1,"201 for integer party JSON numeric value1",dict(status=s,response=v))

# 1e4300 is finite mathematically and valid JSON number syntax. It occurs only
# in unknown fields, so endpoint capacity/range rules do not apply to it.
reset()
s,user=call("POST","/auth/signup",json.dumps(dict(email="unknown@probe.invalid",password="numeric-probe-pass",display_name="Unknown Diner")))
token=user["token"]
raw='{"restaurant_id":"r","table_id":"t","starts_at_local":"2035-06-04T18:00","party_size":2,"unused":1e4300}'
s,v=call("POST","/reservations",raw,token,"unknown-finite")
check("unknown-exponent-create",s==201,"201; unknown valid finite JSON number ignored",dict(status=s,response=v))
body=raw.replace(',"unused":1e4300','')
s,v=call("POST","/reservations",body,token,"unknown-finite")
check("unknown-failed-key-control",s==201,"201 if preceding request failed and consumed no key",dict(status=s,response=v))
raw='{"email":"unknown-two@probe.invalid","password":"numeric-probe-pass","display_name":"Second","unused":1e4300}'
s,v=call("POST","/auth/signup",raw)
check("unknown-exponent-signup",s==201,"201; unknown valid finite JSON number ignored",dict(status=s,response=v))
raw=json.dumps(f)[:-1]+',"unused":1e4300}'
s,v=call("POST","/_test/reset",raw)
check("unknown-exponent-reset",s==204,"204; unknown valid finite JSON number ignored",dict(status=s,response=v))
summary=dict(candidate_full_revision=CANDIDATE,http_operations=len(ops),assertions=len(checks),failed_assertions=sum(not x["passed"] for x in checks),duration_seconds=time.monotonic()-start,operations=ops,results=checks)
print(json.dumps(summary,indent=2))
raise SystemExit(1 if summary["failed_assertions"] else 0)
