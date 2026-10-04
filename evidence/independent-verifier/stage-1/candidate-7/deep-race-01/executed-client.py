"""Independent raw deep-body 50-client races and unchanged receipt replacement."""
import concurrent.futures as futures
import hashlib
import http.client
import json
import sys
import threading
import time
from urllib.parse import urlsplit

BASE,PEER,CANDIDATE=sys.argv[1:4]
operations=[];checks=[];started=time.monotonic();gate_lock=threading.Lock()

def sha(raw):return hashlib.sha256(raw).hexdigest()
def call(method,path,body=None,token=None,key=None,base=BASE):
    url=urlsplit(base);headers={"Content-Type":"application/json; charset=utf-8"}
    if token:headers["Authorization"]="Bearer "+token
    if key:headers["Idempotency-Key"]=key
    connection=http.client.HTTPConnection(url.hostname,url.port,timeout=10 if path.startswith("/_test/") else 5)
    began=time.monotonic()
    try:
        connection.request(method,path,body,headers);r=connection.getresponse();raw=r.read()
        value=None if path=="/_test/export" or not raw else json.loads(raw)
        public={"private_snapshot_sha256":sha(raw)} if path=="/_test/export" else {k:v for k,v in value.items() if k!="token"} if path.startswith("/auth/") and isinstance(value,dict) else value
        with gate_lock:operations.append(dict(method=method,path=path,peer=base,key=key,status=r.status,request_bytes=len(body or b""),request_sha256=sha(body or b""),response=public,response_bytes=len(raw),response_sha256=sha(raw),duration_seconds=time.monotonic()-began))
        return r.status,value,raw
    finally:connection.close()

def check(shape,key,condition,expected,observed):
    checks.append(dict(requirement_id=f"TK1-deep-race-{shape}-{key}",passed=bool(condition),expected=expected,observed=observed))
def shallow(value):return json.dumps(value,separators=(",",":")).encode()
fixture=shallow(dict(users=[],restaurants=[dict(id="r",name="Race Kitchen",timezone="UTC",slot_minutes=30,reservation_duration_minutes=60,cancellation_cutoff_minutes=0,opening_hours=[dict(weekday=d,opens="00:00",closes="23:59") for d in ["mon","tue","wed","thu","fri","sat","sun"]],tables=[dict(id="t",label="Window",capacity=4)])],reservations=[]))
ordinary=b'{"restaurant_id":"r","table_id":"t","starts_at_local":"2035-06-04T18:00","party_size":2}'
errors=[]
try:
    for shape,prefix,suffix in [("array",b"[",b"]"),("object",b'{"v":',b"}")]:
        def body(leaf=b"1",start=ordinary):return start[:-1]+b',"ignored":'+prefix*20000+leaf+suffix*20000+b"}"
        check(shape,"reset",call("POST","/_test/reset",fixture)[0]==204,204,"reset")
        auth=call("POST","/auth/signup",shallow(dict(email="race@probe.invalid",password="race-probe-pass",display_name="Race Diner")))
        token=auth[1]["token"]
        for mode in ["identical","competing"]:
            check(shape,mode+"-clean-state",call("POST","/_test/reset",fixture)[0]==204,204,"reset")
            token=call("POST","/auth/signup",shallow(dict(email="race@probe.invalid",password="race-probe-pass",display_name="Race Diner")))[1]["token"]
            barrier=threading.Barrier(50)
            def submit(index):
                key="one-key" if mode=="identical" else "competing-"+str(index)
                barrier.wait(timeout=15)
                return index,key,call("POST","/reservations",body(),token,key)
            with futures.ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(submit,range(50)))
            statuses=[item[2][0] for item in results];winner=next(item for item in results if item[2][0]==201)
            original=winner[2][1];counts={str(status):statuses.count(status) for status in set(statuses)}
            check(shape,mode+"-one-create",statuses.count(201)==1,"one 201",counts)
            check(shape,mode+"-other-statuses",statuses.count(200 if mode=="identical" else 409)==49,"49 replay200 or overlap409",counts)
            check(shape,mode+"-other-bodies",all(item[2][1]==original for item in results) if mode=="identical" else all(item[2][1].get("error",{}).get("code")=="table_unavailable" for item in results if item[2][0]!=201),"same original receipts or specified overlap errors","checked")
            listing=call("GET","/reservations",token=token)
            check(shape,mode+"-state-once",listing[1]=={"reservations":[original]},"one original record",len(listing[1]["reservations"]))
            captured=call("GET","/_test/export")[2]
            cancelled=call("POST","/reservations/"+original["reference"]+"/cancel",b"{}",token)
            replay=call("POST","/reservations",body(b"1.0"),token,winner[1])
            check(shape,mode+"-immutable-alias",cancelled[0]==200 and replay[:2]==(200,original),"original deep numeric-alias receipt after cancel",replay[0])
            imported=call("POST","/_test/import",captured,base=PEER)
            peer_replay=call("POST","/reservations",body(),token,winner[1],base=PEER)
            peer_current=call("GET","/reservations",token=token,base=PEER)
            check(shape,mode+"-raw-transfer",imported[0]==204 and peer_replay[:2]==(200,original) and peer_current[1]=={"reservations":[original]},"unchanged capture restores original token/record/receipt",dict(import_status=imported[0],replay_status=peer_replay[0],snapshot_bytes=len(captured),snapshot_sha256=sha(captured),deep_export_decoded=False))
            conflict=call("POST","/reservations",body(b"2"),token,winner[1],base=PEER)
            check(shape,mode+"-changed-body",conflict[0]==409 and conflict[1].get("error",{}).get("code")=="idempotency_key_reuse",409,conflict[0])
            if mode=="competing":
                failed_key=next(item[1] for item in results if item[2][0]==409)
                recovered=call("POST","/reservations",body(start=ordinary.replace(b"18:00",b"19:30")),token,failed_key,base=PEER)
                check(shape,"competing-failed-key-reusable",recovered[0]==201,201,recovered[0])
    check("all","timing",all(o["duration_seconds"]<(10 if o["path"].startswith("/_test/") else 5) for o in operations),"ordinary<5/control<10",max(o["duration_seconds"] for o in operations))
    check("all","no-5xx",all(200<=o["status"]<500 for o in operations),"no5xx","checked")
except Exception as error:
    errors.append(dict(type=type(error).__name__,message=str(error),scope="Client/runner exception; no invented HTTP response"))
print(json.dumps(dict(candidate=CANDIDATE,wrapper_depth=20000,shapes=["array","object"],wave_size=50,requests=len(operations),assertions=len(checks),failed_assertions=sum(not c["passed"] for c in checks),checks=checks,operations=operations,runner_errors=errors,duration_seconds=time.monotonic()-started,max_request_seconds=max((o["duration_seconds"] for o in operations),default=0),max_request_bytes=max((o["request_bytes"] for o in operations),default=0)),indent=2))
raise SystemExit(1 if errors or any(not c["passed"] for c in checks) else 0)
