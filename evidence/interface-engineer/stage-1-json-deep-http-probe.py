"""Own moderate-depth real HTTP receipt/migration probe, independent of codec.

Body wrappers are valid by composition. Only shallow public responses are parsed.
Private exports stay raw in memory and are forwarded unchanged; no recursive
client traversal or raised recursion limit is used for those deep snapshots.
"""
import concurrent.futures
import hashlib
import http.client
import json
import re
import sys
import threading
import time
from urllib.parse import urlsplit

URLS = [urlsplit(url) for url in sys.argv[1:]]
assert len(URLS) == 2
DEPTH = 1050
RESULTS, TRACE = [], []
START = time.monotonic()


def check(name, condition):
    RESULTS.append({"name": name, "passed": bool(condition)})


def call(index, method, path, value=None, *, raw=None, token=None, key=None):
    body = raw if raw is not None else (json.dumps(value, separators=(",", ":")).encode() if value is not None else None)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = "Bearer "+token
    if key:
        headers["Idempotency-Key"] = key
    c = http.client.HTTPConnection(URLS[index].hostname, URLS[index].port, timeout=10 if path.startswith('/_test/') else 5)
    begin = time.monotonic()
    try:
        c.request(method, path, body, headers)
        r = c.getresponse()
        wire = r.read()
        seconds = time.monotonic()-begin
        # Successful deep exports are transported, not parsed by the client.
        parsed = None if not wire or (path == '/_test/export' and r.status == 200) else json.loads(wire)
        check("JSON UTF-8 response", r.getheader('Content-Type') == 'application/json; charset=utf-8')
        check("Exact byte length", r.getheader('Content-Length') == str(len(wire)))
        check("Request meets applicable timeout", seconds < (10 if path.startswith('/_test/') else 5))
        safe_path = re.sub(r'/reservations/[^/]+', '/reservations/<reference>', path)
        TRACE.append({"process":index,"method":method,"path":safe_path,"status":r.status,
                      "code":parsed.get('error',{}).get('code') if isinstance(parsed,dict) else None,
                      "seconds":seconds,"request_bytes":len(body or b''),"response_bytes":len(wire),
                      "request_sha256":hashlib.sha256(body or b'').hexdigest(),"response_sha256":hashlib.sha256(wire).hexdigest()})
        return r.status, parsed, wire
    finally:
        c.close()


def expect(name, response, status, code=None):
    check(name, response[0] == status and (code is None or response[1].get('error',{}).get('code') == code))
    if status == 204:
        check("204 has zero response bytes", response[2] == b'')
    return response


def deep(kind):
    value = b'{"exact":0.100000000000000005,"alias":1.0,"truth":true,"text":"1"}'
    for i in range(DEPTH):
        object_layer = kind == 'object' or (kind == 'alternating' and i%2 == 0)
        value = (b'{"v":'+value+b'}') if object_layer else b'['+value+b']'
    return value


def body(value, nested):
    ordinary = json.dumps(value, separators=(',',':')).encode()
    return ordinary[:-1]+b',"ignored":'+nested+b'}'


def public_fingerprint(index, token):
    response = expect("Current own reservations remain available", call(index,'GET','/reservations',token=token),200)
    return hashlib.sha256(json.dumps(response[1],sort_keys=True,separators=(',',':')).encode()).hexdigest()


def run():
    fixture = {"users":[{"id":"deep-diner","email":"deep@example.test","password":"correct horse","display_name":"Deep"}],
               "restaurants":[{"id":"deep-room","name":"Quiet Room","timezone":"UTC","slot_minutes":30,
                 "reservation_duration_minutes":60,"cancellation_cutoff_minutes":0,
                 "opening_hours":[{"weekday":day,"opens":"18:00","closes":"23:30"} for day in ('mon','tue','wed','thu','fri','sat','sun')],
                 "tables":[{"id":"t"+str(i),"label":"Table "+str(i),"capacity":4} for i in range(1,4)]}],"reservations":[]}
    for i in range(2):
        expect("Normal fixture reset",call(i,'POST','/_test/reset',fixture),204)
    token = expect("Real diner login",call(0,'POST','/auth/login',{"email":"deep@example.test","password":"correct horse"}),200)[1]['token']
    old_destination_token = expect("Destination session before replacement",call(1,'POST','/auth/login',{"email":"deep@example.test","password":"correct horse"}),200)[1]['token']
    originals, raw_bodies = [], []
    for i, kind in enumerate(('array','object','alternating')):
        fields = {"restaurant_id":"deep-room","table_id":'t1' if i != 1 else 't2',
                  "starts_at_local":'2099-06-01T20:00' if i == 2 else '2099-06-01T18:00',"party_size":2}
        raw = body(fields,deep(kind))
        raw_bodies.append(raw)
        headers = {"token":token,"key":"deep-create-"+str(i)}
        first = expect("Real deep "+kind+" create",call(0,'POST','/reservations',raw=raw,**headers),201)
        originals.append(first[1])
        replay = expect("Original deep create replay",call(0,'POST','/reservations',raw=raw,**headers),200)
        check("Original create JSON value preserved",replay[1] == first[1])
        alias = raw.replace(b'"party_size":2',b'"party_size":2e0').replace(b'"alias":1.0',b'"alias":1e0')
        check("Equal numeric aliases inside deep bodies replay",expect("Deep alias replay",call(0,'POST','/reservations',raw=alias,**headers),200)[1] == first[1])
        changed = raw.replace(b'0.100000000000000005',b'0.100000000000000006')
        expect("Deep exact fractional difference conflicts",call(0,'POST','/reservations',raw=changed,**headers),409,'idempotency_key_reuse')
        typed = raw.replace(b'"truth":true',b'"truth":1')
        expect("Deep boolean versus number stays distinct",call(0,'POST','/reservations',raw=typed,**headers),409,'idempotency_key_reuse')
    moves = {"moves":[{"reference":originals[0]['reference'],"table_id":"t2"},{"reference":originals[1]['reference'],"table_id":"t1"}]}
    move_raw = body(moves,deep('alternating'))
    moved = expect("Real atomic move with deep ignored field",call(0,'POST','/reservation-moves',raw=move_raw,token=token,key='deep-move'),201)[1]
    check("Deep batch original replay",expect("Deep batch retry",call(0,'POST','/reservation-moves',raw=move_raw,token=token,key='deep-move'),200)[1] == moved)
    expect("Current amendment after original receipt",call(0,'PATCH','/reservations/'+originals[2]['reference'],{"party_size":1},token=token),200)
    expect("Current cancellation after original receipt",call(0,'POST','/reservations/'+originals[0]['reference']+'/cancel',token=token),200)
    original_current = public_fingerprint(0,token)
    captured = expect("Deep private export succeeds",call(0,'GET','/_test/export'),200)[2]
    check("Private current profiles persisted",len(re.findall(rb'"numeric_profile"\s*:\s*"exact-v1"',captured)) >= 4)
    expect("Unchanged raw deep snapshot forward",call(1,'POST','/_test/import',raw=captured),204)
    expect("Prior destination token replaced",call(1,'GET','/reservations',token=old_destination_token),401,'unauthenticated')
    check("Imported deep state retains current public records",public_fingerprint(1,token) == original_current)
    second = expect("Imported deep snapshot exports again",call(1,'GET','/_test/export'),200)[2]
    expect("Second raw snapshot replacement",call(0,'POST','/_test/import',raw=second),204)
    for index in range(2):
        for i, raw in enumerate(raw_bodies):
            replay = expect("Deep original create after independent replacement",call(index,'POST','/reservations',raw=raw,token=token,key='deep-create-'+str(i)),200)
            check("Immutable original create after mutation/import",replay[1] == originals[i])
            expect("Deep unequal fraction still conflicts after import",call(index,'POST','/reservations',raw=raw.replace(b'0.100000000000000005',b'0.100000000000000006'),token=token,key='deep-create-'+str(i)),409,'idempotency_key_reuse')
        check("Immutable original move after mutation/import",expect("Deep move after independent replacement",call(index,'POST','/reservation-moves',raw=move_raw,token=token,key='deep-move'),200)[1] == moved)
        check("Replays do not mutate imported current view",public_fingerprint(index,token) == original_current)
    invalid = re.sub(rb'"numeric_profile"\s*:\s*"exact-v1"',b'"numeric_profile":"unknown-profile"',second,count=1)
    check("Invalid profile probe actually changes deep snapshot",invalid != second)
    expect("Invalid deep profile import rejected",call(1,'POST','/_test/import',raw=invalid),422,'validation_failed')
    expect("Malformed deep snapshot import rejected",call(1,'POST','/_test/import',raw=second[:-1]),400,'malformed_request')
    check("Both invalid imports preserve current records/token",public_fingerprint(1,token) == original_current)
    fifty_raw = body({"restaurant_id":"deep-room","table_id":"t3","starts_at_local":"2099-06-01T18:00","party_size":2},deep('object'))
    barrier = threading.Barrier(50)
    def deep_compete(_):
        barrier.wait(timeout=5)
        return call(0,'POST','/reservations',raw=fifty_raw,token=token,key='deep-fifty')
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
        responses = list(pool.map(deep_compete,range(50)))
    statuses = [r[0] for r in responses]
    check("50 deep identical requests: one201 and49replays",statuses.count(201)==1 and statuses.count(200)==49)
    first = next(r[1] for r in responses if r[0] == 201)
    check("All deep concurrent original receipts identical",all(r[1] == first for r in responses))
    latest = expect("Concurrent deep receipt export",call(0,'GET','/_test/export'),200)[2]
    expect("Concurrent deep receipt forwarded unchanged",call(1,'POST','/_test/import',raw=latest),204)
    check("Concurrent original receipt replays after import",expect("Imported concurrent deep retry",call(1,'POST','/reservations',raw=fifty_raw,token=token,key='deep-fifty'),200)[1] == first)
    public = expect("No deep duplicate reservations",call(1,'GET','/reservations',token=token),200)[1]['reservations']
    check("Exactly four real reservation identities",len(public)==4 and len({r['reservation_id'] for r in public})==4)


try:
    run()
except Exception as exc:
    check("Deep probe completes without client/flow exception",False)
    TRACE.append({"client_exception":type(exc).__name__})
summary = {"scope":"Real moderate deep HTTP receipts and raw unchanged snapshots; own independently authored builder evidence",
           "depth":DEPTH,"client_recursion_limit":sys.getrecursionlimit(),"operations":sum('method' in r for r in TRACE),
           "assertions":len(RESULTS),"passed":sum(r['passed'] for r in RESULTS),"failed":sum(not r['passed'] for r in RESULTS),
           "seconds":time.monotonic()-START,"max_request_seconds":max((r.get('seconds',0) for r in TRACE),default=0),
           "max_body_bytes":max((r.get('request_bytes',0) for r in TRACE),default=0),"checks":RESULTS,"trace":TRACE}
print(json.dumps(summary,indent=2))
sys.exit(1 if summary['failed'] else 0)
