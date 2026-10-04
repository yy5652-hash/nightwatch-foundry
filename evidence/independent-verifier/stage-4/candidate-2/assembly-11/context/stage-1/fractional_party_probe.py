"""Finite giant fractional party values and endpoint/receipt error precedence."""
import copy
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal

sys.set_int_max_str_digits(0)  # Separate HTTP client process only.
BASE,CANDIDATE=sys.argv[1:3]
N_TEXT="1"+"0"*4299+"1"
FRACTION=N_TEXT+".5"
N=int(N_TEXT)
decoded=json.loads('{"party_size":'+FRACTION+'}',parse_float=Decimal)
assert decoded["party_size"].is_finite() and decoded["party_size"] != decoded["party_size"].to_integral_value()
assert len(N_TEXT)==4301
ops=[]
checks=[]
began=time.monotonic()
SECRET={"token","tokens","sessions","password","password_hash","password_salt","salt","hash","state"}
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def safe(v):
    if isinstance(v,dict): return {k: {"private_value_sha256":digest(x)} if k in SECRET else safe(x) for k,x in v.items()}
    if isinstance(v,list): return [safe(x) for x in v]
    return v
def call(method,path,body=None,raw=None,token=None,key=None):
    headers={"Content-Type":"application/json; charset=utf-8"}
    if token: headers["Authorization"]="Bearer "+token
    if key is not None: headers["Idempotency-Key"]=key
    wire=raw if raw is not None else json.dumps(body) if body is not None else None
    request=urllib.request.Request(BASE+path,data=None if wire is None else wire.encode(),headers=headers,method=method)
    start=time.monotonic()
    try:
        try: response=urllib.request.urlopen(request,timeout=10 if path.startswith("/_test/") else 5)
        except urllib.error.HTTPError as e: response=e
        with response: status,text=response.status,response.read().decode()
        value=json.loads(text) if text else None
    except Exception as e: status,value=0,{"transport_error":str(e)}
    ops.append(dict(operation=len(ops)+1,method=method,path=path,body=safe(body),raw_body=raw,
        has_token=bool(token),key=key,status=status,response=safe(value),duration_seconds=time.monotonic()-start))
    return status,value
def check(key,condition,expected=None,observed=None):
    checks.append(dict(requirement_id="TK1-finite-party-"+key,passed=bool(condition),expected=safe(expected),observed=safe(observed)))
def expect(rid,method,path,body=None,raw=None,status=200,code=None,**kwargs):
    s,v=call(method,path,body=body,raw=raw,**kwargs)
    check(rid,s==status and (code is None or v.get("error",{}).get("code")==code),dict(status=status,code=code),dict(status=s,response=v))
    return v
def state():
    s,v=call("GET","/_test/export")
    assert s==200
    return v
f={"users":[],"restaurants":[{"id":"r","name":"Fraction Kitchen","timezone":"UTC","slot_minutes":30,
    "reservation_duration_minutes":90,"cancellation_cutoff_minutes":0,"opening_hours":[{"weekday":"mon","opens":"18:00","closes":"23:00"}],
    "tables":[{"id":"t0","label":"Window","capacity":N+1},{"id":"t1","label":"Garden","capacity":N+1}]}],"reservations":[]}
expect("reset-control","POST","/_test/reset",f,status=204)
login=expect("signup-control","POST","/auth/signup",dict(email="fraction@probe.invalid",password="fraction-probe-pass",display_name="Fraction Diner"),status=201)
token=login["token"]
normal=dict(restaurant_id="r",table_id="t0",starts_at_local="2035-06-04T18:00",party_size=2)
receipt=expect("create-control","POST","/reservations",normal,token=token,key="successful",status=201)
raw='{"restaurant_id":"r","table_id":"t1","starts_at_local":"2035-06-04T18:00","party_size":'+FRACTION+'}'
before=state()
expect("create-value","POST","/reservations",raw=raw,token=token,key="fraction-failed",status=422,code="validation_failed")
check("create-atomic",state()==before)
expect("missing-key","POST","/reservations",raw=raw,token=token,status=400,code="missing_idempotency_key")
expect("reuse-before-value","POST","/reservations",raw=raw,token=token,key="successful",status=409,code="idempotency_key_reuse")
check("key-errors-atomic",state()==before)
expect("authentication","POST","/reservations",raw=raw,key="not-authenticated",status=401,code="unauthenticated")
valid=dict(normal,table_id="t1")
expect("failed-key-reusable","POST","/reservations",valid,token=token,key="fraction-failed",status=201)
patch_raw='{"party_size":'+FRACTION+'}'
before=state()
expect("patch-value","PATCH","/reservations/"+receipt["reference"],raw=patch_raw,token=token,status=422,code="validation_failed")
check("patch-atomic",state()==before)
move_raw='{"moves":[{"reference":"'+receipt["reference"]+'","party_size":'+FRACTION+'}]}'
expect("moves-value","POST","/reservation-moves",raw=move_raw,token=token,key="fraction-move",status=422,code="validation_failed")
check("moves-atomic",state()==before)
expect("moves-missing-key","POST","/reservation-moves",raw=move_raw,token=token,status=400,code="missing_idempotency_key")
valid_move={"moves":[{"reference":receipt["reference"],"party_size":1}]}
expect("moves-failed-key-reusable","POST","/reservation-moves",valid_move,token=token,key="fraction-move",status=201)
expect("moves-reuse-before-value","POST","/reservation-moves",raw=move_raw,token=token,key="fraction-move",status=409,code="idempotency_key_reuse")
expect("huge-integer-control","POST","/reservations",dict(normal,starts_at_local="2035-06-04T20:00",party_size=N),token=token,key="huge-integer",status=201)

for literal in ["NaN","Infinity","-Infinity"]:
    for method,path,wire in [("POST","/reservations",raw.replace(FRACTION,literal)),("PATCH","/reservations/"+receipt["reference"],patch_raw.replace(FRACTION,literal)),("POST","/reservation-moves",move_raw.replace(FRACTION,literal))]:
        expect("literal-"+literal+"-"+method+"-"+path.split("/")[1],method,path,raw=wire,token=token,key="literal-control",status=400,code="malformed_request")
expect("literal-before-auth","POST","/reservations",raw=raw.replace(FRACTION,"NaN"),status=400,code="malformed_request")

# A genuine past confirmed record exercises amendment cutoff before value
# checks. It was created over the API, not fabricated in exported state.
past=expect("past-create-control","POST","/reservations",dict(normal,starts_at_local="2001-01-01T18:00"),token=token,key="past",status=201)
before=state()
expect("patch-cutoff-before-value","PATCH","/reservations/"+past["reference"],raw=patch_raw,token=token,status=409,code="cutoff_passed")
past_move='{"moves":[{"reference":"'+past["reference"]+'","party_size":'+FRACTION+'}]}'
expect("moves-cutoff-before-value","POST","/reservation-moves",raw=past_move,token=token,key="past-fraction",status=409,code="cutoff_passed")
check("cutoff-atomic",state()==before)
expect("cancel-control","POST","/reservations/"+receipt["reference"]+"/cancel",{},token=token)
expect("patch-cancelled-before-value","PATCH","/reservations/"+receipt["reference"],raw=patch_raw,token=token,status=409,code="reservation_cancelled")
cancelled_move='{"moves":[{"reference":"'+receipt["reference"]+'","party_size":'+FRACTION+'}]}'
expect("moves-cancelled-before-value","POST","/reservation-moves",raw=cancelled_move,token=token,key="cancelled-fraction",status=409,code="reservation_cancelled")
summary=dict(candidate_full_revision=CANDIDATE,http_operations=len(ops),assertions=len(checks),failed_assertions=sum(not x["passed"] for x in checks),
    duration_seconds=time.monotonic()-began,lexical_proof=dict(integer_part_digits=len(N_TEXT),fractional_digits=1,valid_json_number=True,mathematically_finite=True,nonintegral=True,client_validation="stdlib Decimal used only to independently classify wire token"),operations=ops,results=checks)
print(json.dumps(summary,indent=2))
raise SystemExit(1 if summary["failed_assertions"] else 0)
