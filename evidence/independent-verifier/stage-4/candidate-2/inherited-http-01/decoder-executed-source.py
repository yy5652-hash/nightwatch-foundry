"""Prepared raw HTTP protocol; run only with a complete named release.

Deep inputs/exports are never decoded by the client. Authentication secrets and
private snapshots remain in memory; traces preserve fingerprints and events.
"""
import argparse
import hashlib
import http.client
import json
import time
from pathlib import Path
from urllib.parse import urlsplit
from decoder_oracle import DEPTHS, SHAPES, LEAF, LEAF_ALIAS, LEAF_DIFFERENT, LEAF_TYPED, inject, wrap, grammar_cases, randomized_values
from decoder_requirements import CASES, DEEP
from semantic_oracle import encode

def shallow(value):return json.dumps(value,ensure_ascii=True,separators=(",",":")).encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def fixture():
    return shallow(dict(users=[],restaurants=[dict(id="r",name="Grammar Kitchen",timezone="UTC",slot_minutes=30,
        reservation_duration_minutes=60,cancellation_cutoff_minutes=0,
        opening_hours=[dict(weekday=d,opens="18:00",closes="23:00") for d in ["mon","tue","wed","thu","fri","sat","sun"]],
        tables=[dict(id=t,label="Table "+t,capacity=4) for t in ["a","b","c","d"]])],reservations=[]))
def booking(table="a",party=2):
    return dict(restaurant_id="r",table_id=table,starts_at_local="2035-06-04T18:00",party_size=party)

class DecoderProbe:
    def __init__(self,args):
        self.args=args;self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=False)
        self.began=time.monotonic();self.trace=[];self.results=[];self.errors=[];self.blocked=[]
        self.media=[];self.lengths=[];self.valid_json=[];self.empty=[]
    def check(self,key,condition,expected=None,observed=None):
        assert key in CASES,key
        self.results.append(dict(requirement_id=CASES[key]["requirement_id"],passed=bool(condition),
            expected=expected,observed=observed,operation=len(self.trace)))
    def call(self,method,path,raw=None,token=None,key=None,base=None):
        base=base or self.args.base;url=urlsplit(base);headers={"Content-Type":"application/json; charset=utf-8"}
        if token is not None:headers["Authorization"]="Bearer "+token
        if key is not None:headers["Idempotency-Key"]=key
        began=time.monotonic();conn=http.client.HTTPConnection(url.hostname,url.port,timeout=10 if path.startswith("/_test/") else 5)
        try:
            conn.request(method,path,body=raw,headers=headers);response=conn.getresponse();payload=response.read()
            status=response.status;ctype=response.getheader("Content-Type","");length=response.getheader("Content-Length","")
            if path=="/_test/export":value=None;valid=None
            else:
                try:
                    def invalid_constant(s):raise ValueError(s)
                    value=json.loads(payload.decode("utf-8"),parse_constant=invalid_constant) if payload else None;valid=True
                except (ValueError,UnicodeError):value=None;valid=False
            if payload:self.media.append(ctype.lower().replace(" ","")=="application/json;charset=utf-8")
            if valid is not None and payload:self.valid_json.append(valid)
            self.lengths.append(length.isdigit() and int(length)==len(payload))
            if status==204:self.empty.append(not payload)
            public=value
            if path.startswith("/auth/") and isinstance(public,dict):public={k:v for k,v in public.items() if k!="token"}
            if path=="/_test/export":public={"private_snapshot_sha256":digest(payload),"bytes":len(payload),"decoded":False}
            self.trace.append(dict(operation=len(self.trace)+1,method=method,path=path,base=base,key=key,has_token=token is not None,
                request_sha256=digest(raw) if raw is not None else None,request_bytes=len(raw) if raw is not None else 0,
                response_sha256=digest(payload),response_bytes=len(payload),status=status,response=public,
                content_type=ctype,content_length=length,duration_seconds=time.monotonic()-began))
            return status,value,payload
        finally:conn.close()
    def expect(self,rid,method,path,raw=None,status=200,code=None,original=None,**kw):
        result=self.call(method,path,raw,**kw);observed_code=result[1].get("error",{}).get("code") if isinstance(result[1],dict) else None
        self.check(rid,result[0]==status and (code is None or observed_code==code) and (original is None or result[1]==original),
            dict(status=status,code=code,original_equal=original is not None),dict(status=result[0],code=observed_code,original_equal=None if original is None else result[1]==original))
        return result
    def signup(self,base=None,label="source",nested=None):
        raw=shallow(dict(email=label+"@probe.invalid",password="decoder-probe-pass",display_name="Grammar Diner"))
        return self.call("POST","/auth/signup",inject(raw,nested) if nested is not None else raw,base=base)
    def view(self,token,base=None):
        listed=self.call("GET","/reservations",token=token,base=base)
        availability=self.call("GET","/availability?restaurant_id=r&date=2035-06-04&party_size=2",base=base)
        return (listed[0],listed[1],availability[0],availability[1])
    def records(self,token,base=None):
        status,value,_=self.call("GET","/reservations",token=token,base=base)
        if status!=200:return None
        return sorted(value["reservations"],key=lambda v:v["reference"])
    def deep(self,shape,depth):
        stem=f"deep-{shape}-{depth}";nested=wrap(shape,depth);alias=wrap(shape,depth,LEAF_ALIAS)
        different=wrap(shape,depth,LEAF_DIFFERENT);typed=wrap(shape,depth,LEAF_TYPED)
        def expect(suffix,method,path,raw=None,**kw):
            status,code,_=DEEP[suffix];return self.expect(stem+"-"+suffix,method,path,raw,status=status,code=code,**kw)
        reset=expect("reset","POST","/_test/reset",inject(fixture(),nested))
        if reset[0]!=204:self.blocked.append(dict(case=stem,reason="valid deep reset refused; no deep receipt manufactured"));return
        signed=self.signup(label="source",nested=nested)
        self.check(stem+"-signup",signed[0]==201,{"status":201},{"status":signed[0]})
        if signed[0]!=201:self.blocked.append(dict(case=stem,reason="valid deep signup refused"));return
        token=signed[1]["token"]
        logged=expect("login","POST","/auth/login",inject(shallow(dict(email="source@probe.invalid",password="decoder-probe-pass")),nested))
        expect("second-token","GET","/reservations",token=token)
        second_token=logged[1].get("token") if isinstance(logged[1],dict) else None
        second_session=self.call("GET","/reservations",token=second_token)
        self.check(stem+"-second-token",isinstance(second_token,str) and second_token!=token and second_session[0]==200)
        body=inject(shallow(booking()),nested);create_key="deep-create"
        first=expect("create","POST","/reservations",body,token=token,key=create_key)
        if first[0]!=201:self.blocked.append(dict(case=stem,reason="no successful deep create; receipt and replacement paths remain unverified"));return
        original=first[1];ref=original["reference"]
        expect("create-alias","POST","/reservations",inject(shallow(booking()),alias),token=token,key=create_key,original=original)
        expect("create-precision","POST","/reservations",inject(shallow(booking()),different),token=token,key=create_key)
        expect("create-type","POST","/reservations",inject(shallow(booking()),typed),token=token,key=create_key)
        expect("create-invalid-difference","POST","/reservations",inject(shallow(booking(party=0)),different),token=token,key=create_key)
        expect("create-no-auth","POST","/reservations",body,key="no-auth")
        expect("create-no-key","POST","/reservations",body,token=token)
        second=expect("second-create","POST","/reservations",shallow(booking("b")),token=token,key="second")
        if second[0]!=201:self.blocked.append(dict(case=stem,reason="ordinary swap member control failed"));return
        second_ref=second[1]["reference"]
        # Add the deep value both to the whole request and an ignored item field.
        def move_body(value):
            item=inject(shallow(dict(reference=ref,table_id="b")),value)
            # item already contains deep wrappers. Compose the independently
            # known outer object grammar directly; inject validates only a
            # shallow envelope and must not parse this composed deep object.
            return b'{"moves":['+item+b','+shallow(dict(reference=second_ref,table_id="a"))+b'],"ignored":'+value+b'}'
        moves=move_body(nested);move_key="deep-moves"
        moved=expect("moves","POST","/reservation-moves",moves,token=token,key=move_key)
        if moved[0]!=201:self.blocked.append(dict(case=stem,reason="deep swap refused; real batch replay paths remain unverified"));return
        move_original=moved[1]
        expected_moves=[dict(original,table_id="b",table_ids=["b"],revision=original["revision"]+1),dict(second[1],table_id="a",table_ids=["a"],revision=second[1]["revision"]+1)]
        self.check(stem+"-moves",move_original==dict(reservations=expected_moves),"input-ordered atomic swap; original identity/timestamps/party",move_original)
        expect("moves-alias","POST","/reservation-moves",move_body(alias),token=token,key=move_key,original=move_original)
        expect("moves-precision","POST","/reservation-moves",move_body(different),token=token,key=move_key)
        expect("moves-type","POST","/reservation-moves",move_body(typed),token=token,key=move_key)
        before=self.view(token)
        expect("create-fraction","POST","/reservations",inject(shallow(booking("c",1.5)),nested),token=token,key="failed-create")
        self.check(stem+"-create-fraction-atomic",self.view(token)==before)
        third_booking=expect("create-failed-key","POST","/reservations",inject(shallow(booking("c")),nested),token=token,key="failed-create")
        before=self.view(token)
        bad_move=inject(shallow(dict(moves=[dict(reference=ref,party_size=1.5)])),nested)
        expect("move-fraction","POST","/reservation-moves",bad_move,token=token,key="failed-move")
        self.check(stem+"-move-fraction-atomic",self.view(token)==before)
        fixed_move=inject(shallow(dict(moves=[dict(reference=ref)])),nested)
        no_op=expect("move-failed-key","POST","/reservation-moves",fixed_move,token=token,key="failed-move")
        self.check(stem+"-move-failed-key",no_op[1]==dict(reservations=[expected_moves[0]]),"no-op retains every original field",no_op[1])
        captured_records=self.records(token)
        exported=expect("export","GET","/_test/export");captured=exported[2];captured_hash=digest(captured)
        expected_records=sorted(expected_moves+[third_booking[1]],key=lambda r:r["reference"]) if third_booking[0]==201 else None
        self.check(stem+"-export",captured_records is not None and captured_records==expected_records,"exact independently expected three records",captured_records)
        expect("amend","PATCH","/reservations/"+ref,inject(shallow(dict(party_size=3)),nested),token=token)
        expect("cancel","POST","/reservations/"+ref+"/cancel",b"{}",token=token)
        expect("create-immutable","POST","/reservations",body,token=token,key=create_key,original=original)
        expect("moves-immutable","POST","/reservation-moves",moves,token=token,key=move_key,original=move_original)
        before=self.view(token)
        expect("bad-import","POST","/_test/import",captured[:-1])
        retained_create=self.call("POST","/reservations",body,token=token,key=create_key)
        retained_moves=self.call("POST","/reservation-moves",moves,token=token,key=move_key)
        self.check(stem+"-bad-import-atomic",self.view(token)==before and retained_create[0]==200 and retained_create[1]==original
            and retained_moves[0]==200 and retained_moves[1]==move_original)
        self.check(stem+"-snapshot-lifetime",digest(captured)==captured_hash)
        transfer=captured
        for dest in ["peer","third"]:
            base=getattr(self.args,dest);ds=stem+"-"+dest
            control=self.call("POST","/_test/reset",fixture(),base=base)
            if control[0]!=204:raise RuntimeError("ordinary destination reset control failed")
            old=self.signup(base=base,label="destination")
            if old[0]!=201:raise RuntimeError("ordinary destination signup control failed")
            old_token=old[1]["token"]
            self.expect(ds+"-import","POST","/_test/import",transfer,base=base,status=204)
            self.expect(ds+"-replaced-session","GET","/reservations",token=old_token,base=base,status=401,code="unauthenticated")
            self.expect(ds+"-replaced-login","POST","/auth/login",shallow(dict(email="destination@probe.invalid",password="decoder-probe-pass")),base=base,status=401,code="unauthenticated")
            self.check(ds+"-records",self.records(token,base)==captured_records)
            self.expect(ds+"-create-original","POST","/reservations",body,token=token,key=create_key,base=base,original=original)
            self.expect(ds+"-moves-original","POST","/reservation-moves",moves,token=token,key=move_key,base=base,original=move_original)
            self.expect(ds+"-difference","POST","/reservations",inject(shallow(booking()),different),token=token,key=create_key,base=base,status=409,code="idempotency_key_reuse")
            self.expect(ds+"-cancel","POST","/reservations/"+ref+"/cancel",b"{}",token=token,base=base)
            self.expect(ds+"-replay-cancelled","POST","/reservations",body,token=token,key=create_key,base=base,original=original)
            self.expect(ds+"-repeat-import","POST","/_test/import",transfer,base=base,status=204)
            self.check(ds+"-repeat-records",self.records(token,base)==captured_records)
            if dest=="peer":
                transfer=self.expect(stem+"-peer-export","GET","/_test/export",base=base)[2]
    def grammar(self):
        if self.call("POST","/_test/reset",fixture())[0]!=204:raise RuntimeError("ordinary grammar reset control failed")
        token=self.signup(label="grammar")[1]["token"]
        for case in grammar_cases():
            if not case.valid or case.label in ["empty","bom"]:continue
            stem="grammar-"+case.label;body=inject(shallow(booking()),case.raw);key="grammar-"+case.label
            created=self.expect(stem+"-create","POST","/reservations",body,token=token,key=key,status=201)
            if created[0]!=201:continue
            self.expect(stem+"-replay","POST","/reservations",body,token=token,key=key,original=created[1])
            move=inject(shallow(dict(moves=[dict(reference=created[1]["reference"])])),case.raw)
            moved=self.expect(stem+"-moves","POST","/reservation-moves",move,token=token,key="move-"+key,status=201)
            self.expect(stem+"-move-replay","POST","/reservation-moves",move,token=token,key="move-"+key,original=moved[1])
            self.expect(stem+"-cancel","POST","/reservations/"+created[1]["reference"]+"/cancel",b"{}",token=token)
        control=self.call("POST","/reservations",shallow(booking()),token=token,key="syntax-control")
        if control[0]!=201:raise RuntimeError("ordinary syntax booking control failed")
        reference=control[1]["reference"]
        for case in grammar_cases():
            if case.valid or case.label in ["empty","bom"]:continue
            stem="grammar-"+case.label;before=self.view(token)
            # Syntax refusal is independent of missing credentials/key/fields.
            for route,method,path in [("reset","POST","/_test/reset"),("signup","POST","/auth/signup"),("login","POST","/auth/login"),
                    ("create","POST","/reservations"),("moves","POST","/reservation-moves"),("patch","PATCH","/reservations/"+reference),("import","POST","/_test/import")]:
                self.expect(stem+"-"+route,method,path,case.raw,status=400,code="malformed_request")
            replay=self.call("POST","/reservations",shallow(booking()),token=token,key="syntax-control")
            self.check(stem+"-atomic",self.view(token)==before and replay[0]==200 and replay[1]==control[1])
        for label,raw in dict(null=b"null",array=b"[]",string=b'"x"',number=b"1.0",boolean=b"true").items():
            self.expect("top-level-"+label,"POST","/reservations",raw,status=400,code="malformed_request")
    def random(self):
        if self.call("POST","/_test/reset",fixture())[0]!=204:raise RuntimeError("ordinary random reset control failed")
        token=self.signup(label="random")[1]["token"]
        for item in randomized_values():
            stem="random-"+item["label"];key=item["label"];body=inject(shallow(booking()),item["raw"])
            created=self.expect(stem+"-first","POST","/reservations",body,token=token,key=key,status=201)
            if created[0]!=201:continue
            self.expect(stem+"-alias","POST","/reservations",inject(shallow(booking()),item["alias"]),token=token,key=key,original=created[1])
            self.expect(stem+"-difference","POST","/reservations",inject(shallow(booking()),item["different"]),token=token,key=key,status=409,code="idempotency_key_reuse")
            cancelled=self.call("POST","/reservations/"+created[1]["reference"]+"/cancel",b"{}",token=token)
            replay=self.expect(stem+"-immutable","POST","/reservations",body,token=token,key=key,original=created[1])
            self.check(stem+"-immutable",cancelled[0]==200 and replay[1]==created[1])
    def finish(self):
        self.check("charset",bool(self.media) and all(self.media));self.check("length",bool(self.lengths) and all(self.lengths))
        self.check("json",bool(self.valid_json) and all(self.valid_json));self.check("empty-204",bool(self.empty) and all(self.empty))
        self.check("duration",all(t["duration_seconds"]< (10 if t["path"].startswith("/_test/") else 5) for t in self.trace))
        self.check("no-5xx",bool(self.trace) and all(200<=t["status"]<500 for t in self.trace))
        rows=[]
        for key,value in CASES.items():
            matches=[r for r in self.results if r["requirement_id"]==value["requirement_id"]]
            rows.append(dict(**value,candidate=self.args.candidate,verdict="unverified" if not matches else "verified" if all(r["passed"] for r in matches) else "failed"))
        output=dict(candidate=self.args.candidate,seed=20261004,depths=DEPTHS,shapes=SHAPES,requests=len(self.trace),assertions=len(self.results),
            failed_assertions=sum(not r["passed"] for r in self.results),rows=rows,checks=self.results,operations=self.trace,blocked_paths=self.blocked,runner_errors=self.errors,
            duration_seconds=time.monotonic()-self.began,max_request_bytes=max((t["request_bytes"] for t in self.trace),default=0),
            max_request_seconds=max((t["duration_seconds"] for t in self.trace),default=0),private_payloads="in memory only; deep exports forwarded without decoding")
        (self.out/"probes.json").write_text(json.dumps(output,indent=2))
        return 1 if self.errors or output["failed_assertions"] or any(r["verdict"]=="unverified" for r in rows) else 0

def main():
    p=argparse.ArgumentParser()
    for name in ["base","peer","third","candidate","out"]:p.add_argument("--"+name,required=True)
    a=p.parse_args();probe=DecoderProbe(a)
    try:
        for shape in SHAPES:
            for depth in DEPTHS:probe.deep(shape,depth)
        probe.grammar();probe.random()
    except Exception as error:
        # Never classify an exception from the evidence client as malformed input
        # or a passing/failed HTTP service response.
        probe.errors.append(dict(type=type(error).__name__,message=str(error)))
    raise SystemExit(probe.finish())

if __name__=="__main__":main()
