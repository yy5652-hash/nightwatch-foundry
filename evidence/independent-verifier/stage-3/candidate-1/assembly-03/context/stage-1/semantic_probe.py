"""Independent raw HTTP probes; execute only after the complete named handoff.

No service imports, builder tests, fabricated export state or production oracle.
Exports and bearer/password values stay in memory or appear as fingerprints.
"""
import argparse
import copy
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from semantic_oracle import Number,encode,parse,same
from semantic_requirements import ALIASES,BAD_JSON,CASES,CURRENT_EQ,FIELDS,FRACTIONS,LEGACY_EQ,WRONG_TYPES

DAY="2035-06-04"
N="1"+"0"*4299+"1"
EXP="9"*80
HUGE=Number("1e"+EXP)
PRIVATE={"token","tokens","sessions","password","password_hash","password_salt","salt","hash","state"}
def digest(value): return hashlib.sha256(encode(value).encode()).hexdigest()
def safe(value):
    if isinstance(value,Number): return {"exact_json_number_token":value.raw}
    if isinstance(value,dict): return {key:({"private_value_sha256":digest(child)} if key in PRIVATE else safe(child)) for key,child in value.items()}
    if isinstance(value,list): return [safe(child) for child in value]
    return value
def fixture():
    return dict(users=[dict(id="semantic-owner",email="semantic@probe.invalid",password="semantic-probe-pass",display_name="Semantic Diner")],
        restaurants=[dict(id="r",name="Exact Kitchen",timezone="UTC",slot_minutes=30,reservation_duration_minutes=90,cancellation_cutoff_minutes=0,
            opening_hours=[dict(weekday=d,opens="18:00",closes="23:00") for d in ["mon","tue","wed","thu","fri","sat","sun"]],
            tables=[dict(id="t"+str(i),label="Table "+str(i),capacity=4) for i in range(3)])],reservations=[])
def booking(table="t0",start=DAY+"T18:00",party=2):
    return dict(restaurant_id="r",table_id=table,starts_at_local=start,party_size=party)
def feature():
    return dict(precise=Number("0.100000000000000005"),large=Number("9007199254740993.0"),tiny=Number("1e-4300"),
                enormous=HUGE,zero=Number("-0.000"),array=[Number("1.00"),True,"1"],obj={"a":Number("2e0"),"b":False},
                escaped='quote:" number:1e4300 slash:\\ Unicode:é汉')
def legacy_feature():
    value=feature();value.pop("enormous")
    return value
def nodes(value):
    if isinstance(value,dict):
        yield value
        for child in value.values(): yield from nodes(child)
    elif isinstance(value,list):
        for child in value: yield from nodes(child)
def profiles(state): return [node for node in nodes(state) if "numeric_profile" in node]
def archived(state,key):
    return next(node for node in profiles(state) if node.get("key")==key)["body"]
@dataclass
class Response:
    status:int
    data:object
    raw:bytes

class Probe:
    def __init__(self,args):
        self.args=args;self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=False)
        self.started=time.monotonic();self.trace=[];self.results=[];self.errors=[]
        self.charsets=[];self.lengths=[];self.json_valid=[];self.empty204=[];self.number_tokens=[];self.public_profiles=[]
    def check(self,key,condition,expected=None,observed=None):
        assert key in CASES,"Undeclared obligation: "+key
        self.results.append(dict(requirement_id="TK1-semantic-"+key,passed=bool(condition),expected=safe(expected),observed=safe(observed)))
    def call(self,method,path,body=None,raw=None,token=None,key=None,base=None):
        data=raw if raw is not None else None if body is None else encode(body).encode("utf-8")
        if isinstance(data,str):data=data.encode("utf-8")
        headers={"Content-Type":"application/json; charset=utf-8"}
        if token is not None:headers["Authorization"]="Bearer "+token
        if key is not None:headers["Idempotency-Key"]=key
        target=(base or self.args.base)+path
        req=urllib.request.Request(target,data=data,headers=headers,method=method)
        began=time.monotonic();response_headers={}
        try:
            try:response=urllib.request.urlopen(req,timeout=10 if path.startswith("/_test/") else 5)
            except urllib.error.HTTPError as error:response=error
            with response:status,payload,response_headers=response.status,response.read(),dict(response.headers)
            try:value=parse(payload) if payload else None;valid=True
            except (ValueError,UnicodeError):value={"invalid_json":True};valid=False
        except Exception as error:status,payload,value,valid=0,b"",{"transport_error":str(error)},False
        elapsed=time.monotonic()-began
        ctype=next((v for k,v in response_headers.items() if k.lower()=="content-type"),"")
        length=next((v for k,v in response_headers.items() if k.lower()=="content-length"),"")
        if payload:
            self.charsets.append(ctype.lower().replace(" ","")=="application/json;charset=utf-8")
            self.json_valid.append(valid)
        self.lengths.append(length.isdigit() and int(length)==len(payload))
        if status==204:self.empty204.append(not payload)
        if path.startswith("/reservations") and value is not None:
            self.public_profiles.append(all("numeric_profile" not in node for node in nodes(value)))
            for node in nodes(value):
                if "party_size" in node:self.number_tokens.append(isinstance(node["party_size"],Number))
        public_request=not path.startswith("/auth") and not path.startswith("/_test/")
        raw_text=None
        if data is not None and public_request and method!="GET" and not path.endswith("cancel"):
            try:raw_text=data.decode("utf-8")
            except UnicodeError:raw_text="[invalid UTF-8 bytes; exact request hex: "+data.hex()+"]"
        self.trace.append(dict(operation=len(self.trace)+1,method=method,path=path,base=base or self.args.base,
            request_bytes=0 if data is None else len(data),request_sha256=None if data is None else hashlib.sha256(data).hexdigest(),
            raw_request_utf8=raw_text,
            has_token=token is not None,key=key,status=status,response=safe(value),response_sha256=hashlib.sha256(payload).hexdigest(),
            content_type=ctype,content_length=length,response_bytes=len(payload),duration_seconds=elapsed))
        return Response(status,value,payload)
    def expect(self,rid,method,path,body=None,status=200,code=None,**kwargs):
        response=self.call(method,path,body=body,**kwargs)
        observed_code=response.data.get("error",{}).get("code") if isinstance(response.data,dict) else None
        self.check(rid,response.status==status and (code is None or observed_code==code),dict(status=status,code=code),dict(status=response.status,body=response.data))
        return response
    def setup(self,f=None,base=None):
        response=self.call("POST","/_test/reset",f or fixture(),base=base)
        if response.status!=204:raise RuntimeError("Fixture setup refused: "+str(response.status))
        response=self.call("POST","/auth/login",dict(email="semantic@probe.invalid",password="semantic-probe-pass"),base=base)
        if response.status!=200:raise RuntimeError("Seeded login refused: "+str(response.status))
        return response.data["token"]
    def snapshot(self,base=None):
        response=self.call("GET","/_test/export",base=base)
        if response.status!=200:raise RuntimeError("Export refused: "+str(response.status))
        return response
    def state_same(self,snapshot,base=None):return same(snapshot.data,self.snapshot(base).data)
    def create(self,body=None,key="control",base=None,token=None):
        response=self.call("POST","/reservations",body or booking(),token=token,key=key,base=base)
        if response.status!=201:raise RuntimeError("Real booking setup refused: "+str(response.status))
        return response
    def syntax(self):
        for label,raw in BAD_JSON.items():
            self.expect("syntax-"+label,"POST","/reservations",raw=raw,status=400,code="malformed_request")
    def counts(self):
        alias_values={"integer":Number("2"),"decimal":Number("2.0"),"exponent":Number("2e0"),"trailing-zero":Number("20e-1"),"giant-decimal":Number(N+".0"),"compact-exponent":HUGE}
        fractions={"ordinary":Number("1.5"),"giant":Number(N+".5"),"tiny-exponent":Number("1e-"+EXP)}
        wrong={"boolean":True,"string":"2","null":None,"array":[],"object":{}}
        for field in FIELDS:
            for alias in ALIASES:
                value=alias_values[alias];f=fixture();f["restaurants"][0]["tables"][0]["capacity"]=Number("1e"+str(int(EXP)+1))
                if field=="party_size":
                    token=self.setup(f)
                    response=self.expect("count-"+field+"-"+alias,"POST","/reservations",booking(party=value),token=token,key="alias-"+alias,status=201)
                    observed=response.data.get(field) if isinstance(response.data,dict) else None
                else:
                    config=f["restaurants"][0]["tables"][0] if field=="capacity" else f["restaurants"][0]
                    config[field]=value
                    self.expect("count-"+field+"-"+alias,"POST","/_test/reset",f,status=204)
                    response=self.call("GET","/restaurants/r")
                    observed=response.data["tables"][0].get(field) if field=="capacity" else response.data.get(field)
                self.check("count-"+field+"-"+alias+"-wire",isinstance(observed,Number) and same(observed,value),value,observed)
            for family,mapping in [("fraction",fractions),("wrong",wrong)]:
                for label,value in mapping.items():
                    token=self.setup();before=self.snapshot();body=booking(party=value)
                    path="/reservations"
                    if field!="party_size":
                        body=fixture();config=body["restaurants"][0]["tables"][0] if field=="capacity" else body["restaurants"][0]
                        config[field]=value;path="/_test/reset"
                    status=422 if family=="fraction" or field=="party_size" else 400
                    rid=family+"-"+field+"-"+label
                    self.expect(rid,"POST",path,body,token=token,key="refused",status=status,code="validation_failed" if status==422 else "malformed_request")
                    self.check(rid+"-atomic",self.state_same(before))
            for label,value in [("zero",Number("-0e-"+EXP)),("negative",Number("-2.0"))]:
                token=self.setup();body=booking(party=value);path="/reservations"
                if field!="party_size":
                    body=fixture();config=body["restaurants"][0]["tables"][0] if field=="capacity" else body["restaurants"][0]
                    config[field]=value;path="/_test/reset"
                allowed=field=="cancellation_cutoff_minutes" and label=="zero"
                self.expect("minimum-"+field+"-"+label,"POST",path,body,token=token,key="minimum",status=204 if allowed else 422,code=None if allowed else "validation_failed")
            token=self.setup();body=booking();path="/reservations"
            if field=="party_size":body.pop(field)
            else:
                body=fixture();config=body["restaurants"][0]["tables"][0] if field=="capacity" else body["restaurants"][0]
                config.pop(field);path="/_test/reset"
            self.expect("missing-"+field,"POST",path,body,token=token,key="missing",status=422,code="validation_failed")
        for field,family in [("slot_minutes","grid"),("reservation_duration_minutes","duration"),("cancellation_cutoff_minutes","cutoff"),("capacity","capacity")]:
            f=fixture();config=f["restaurants"][0]["tables"][0] if field=="capacity" else f["restaurants"][0];config[field]=HUGE
            token=self.setup(f);available=self.call("GET","/availability?restaurant_id=r&date="+DAY+"&party_size=2")
            if family=="grid":
                valid=available.status==200 and [slot["starts_at_local"] for slot in available.data.get("slots",[])]==[DAY+"T18:00"]
            elif family=="duration":
                refused=self.call("POST","/reservations",booking(),token=token,key="huge-duration")
                valid=available.status==200 and available.data.get("slots")==[] and refused.status==422 and refused.data.get("error",{}).get("code")=="outside_opening_hours"
            elif family=="cutoff":
                receipt=self.create(token=token);ref=receipt.data["reference"]
                checks=[self.call("POST","/reservations/"+ref+"/cancel",{},token=token),self.call("PATCH","/reservations/"+ref,{"party_size":Number(N+".5")},token=token),self.call("POST","/reservation-moves",{"moves":[{"reference":ref,"party_size":Number(N+".5")}]},token=token,key="cutoff")]
                valid=all(r.status==409 and r.data.get("error",{}).get("code")=="cutoff_passed" for r in checks)
            else:
                receipt=self.create(booking(party=HUGE),token=token)
                valid=isinstance(receipt.data.get("party_size"),Number) and same(receipt.data["party_size"],HUGE)
            self.check("bounded-"+family,valid)
        self.setup()
        for label,query in [("fraction","2.0"),("plus","%2B2"),("negative","-2"),("exponent","2e0"),("spaces","%202%20"),("zero","0")]:
            self.expect("query-"+label,"GET","/availability?restaurant_id=r&date="+DAY+"&party_size="+query,status=422,code="validation_failed")
    def ignored(self):
        token=self.setup();nested=feature()
        for route in ["signup","login"]:
            body=dict(email="ignored@probe.invalid" if route=="signup" else "semantic@probe.invalid",password="semantic-probe-pass",display_name="é汉",unused=nested)
            raw=encode(body).replace("\\u00e9","é").replace("\\u6c49","汉").encode()
            response=self.expect("ignored-"+route,"POST","/auth/"+route,raw=raw,status=201 if route=="signup" else 200)
            if route=="signup":self.check("valid-utf8",response.data.get("display_name")=="é汉")
        receipt=self.expect("ignored-create","POST","/reservations",dict(booking(),unused=nested),token=token,key="ignored",status=201)
        ref=receipt.data["reference"]
        self.check("escaped-string",receipt.status==201)
        self.expect("ignored-patch","PATCH","/reservations/"+ref,{"unused":nested},token=token)
        self.expect("ignored-moves","POST","/reservation-moves",{"moves":[{"reference":ref,"unused":nested}],"unused":nested},token=token,key="ignored-moves",status=201)
        snapshot=self.snapshot();body=copy.deepcopy(snapshot.data);body["unused"]=nested
        self.expect("ignored-import","POST","/_test/import",body,status=204)
        self.expect("ignored-reset","POST","/_test/reset",dict(fixture(),unused=nested),status=204)
    def current(self):
        for endpoint in ["create","moves"]:
            token=self.setup();payload=feature()
            if endpoint=="create":body=dict(booking(party=Number("2.0")),unused=payload);path="/reservations"
            else:
                member=self.create(token=token)
                body={"moves":[{"reference":member.data["reference"],"party_size":Number("1.0")}],"unused":payload};path="/reservation-moves"
            original=self.call("POST",path,body,token=token,key="identity")
            if original.status!=201:raise RuntimeError("Exact identity setup refused: "+str(original.status))
            snapshot=self.snapshot()
            for variant in CURRENT_EQ:
                proposed=copy.deepcopy(body);ignored=proposed["unused"]
                if variant=="numeric-alias":
                    ignored.update(precise=Number("100000000000000005e-18"),large=Number("9007199254740993"),tiny=Number("10e-4301"),enormous=Number("10e"+str(int(EXP)-1)))
                    if endpoint=="create":proposed["party_size"]=Number("2e0")
                    else:proposed["moves"][0]["party_size"]=Number("1e0")
                elif variant=="zero-alias":ignored["zero"]=Number("0e"+EXP)
                elif variant=="object-order":proposed=dict(reversed(list(proposed.items())));proposed["unused"]=dict(reversed(list(ignored.items())))
                elif variant=="tiny-difference":ignored["tiny"]=Number("1e-4301")
                elif variant=="large-rounded-difference":ignored["large"]=Number("9007199254740992.0")
                elif variant=="boolean-difference":ignored["array"][0]=True
                elif variant=="string-difference":ignored["array"][0]="1"
                elif variant=="array-order":ignored["array"]=list(reversed(ignored["array"]))
                elif variant=="missing-ignored":proposed.pop("unused")
                elif variant=="invalid-party-difference":
                    if endpoint=="create":proposed["party_size"]=Number(N+".5")
                    else:proposed["moves"][0]["party_size"]=Number(N+".5")
                elif variant=="unknown-resource-difference":
                    if endpoint=="create":proposed["restaurant_id"]="unknown"
                    else:proposed["moves"][0]["reference"]="UNKNOWN"
                equal=same(body,proposed)
                response=self.expect("identity-"+endpoint+"-"+variant,"POST",path,proposed,token=token,key="identity",status=200 if equal else 409,code=None if equal else "idempotency_key_reuse")
                if equal and not same(response.data,original.data):self.check("identity-"+endpoint+"-"+variant,False,original.data,response.data)
            self.check("identity-"+endpoint+"-atomic",self.state_same(snapshot))
            self.check("profile-new-"+endpoint,bool(profiles(snapshot.data)) and all(node["numeric_profile"]=="exact-v1" for node in profiles(snapshot.data)))
            self.check("archived-exact-"+endpoint,same(archived(snapshot.data,"identity"),body))
            invalid=copy.deepcopy(body)
            if endpoint=="create":invalid["party_size"]=Number(N+".5")
            else:invalid["moves"][0]["party_size"]=Number(N+".5")
            self.expect("precedence-"+endpoint+"-missing-key","POST",path,invalid,token=token,status=400,code="missing_idempotency_key")
            self.expect("precedence-"+endpoint+"-missing-auth","POST",path,invalid,key="no-auth",status=401,code="unauthenticated")
            self.expect("precedence-"+endpoint+"-fraction","POST",path,invalid,token=token,key="failed",status=422,code="validation_failed")
            corrected=copy.deepcopy(body)
            if endpoint=="create":corrected["starts_at_local"]=DAY+"T20:00"
            else:corrected["moves"][0]["party_size"]=2
            self.expect("precedence-"+endpoint+"-failed-key-reuse","POST",path,corrected,token=token,key="failed",status=201)
            ref=original.data["reference"] if endpoint=="create" else original.data["reservations"][0]["reference"]
            self.call("POST","/reservations/"+ref+"/cancel",{},token=token)
            replay=self.expect("precedence-"+endpoint+"-immutable","POST",path,body,token=token,key="identity")
            self.check("precedence-"+endpoint+"-immutable",same(replay.data,original.data),original.data,replay.data)
            exported=self.snapshot();self.call("POST","/_test/import",raw=exported.raw,base=self.args.peer)
            replay=self.expect("precedence-"+endpoint+"-import-original","POST",path,body,token=token,key="identity",base=self.args.peer)
            self.check("precedence-"+endpoint+"-import-original",same(replay.data,original.data))
        token=self.setup();past=self.create(booking(start="2001-01-01T18:00"),token=token,key="past")
        future=self.create(token=token,key="future");self.call("POST","/reservations/"+future.data["reference"]+"/cancel",{},token=token)
        for reason,receipt in [("cutoff",past),("cancelled",future)]:
            ref=receipt.data["reference"];code="cutoff_passed" if reason=="cutoff" else "reservation_cancelled"
            self.expect("ordering-patch-"+reason,"PATCH","/reservations/"+ref,{"party_size":Number(N+".5")},token=token,status=409,code=code)
            self.expect("ordering-moves-"+reason,"POST","/reservation-moves",{"moves":[{"reference":ref,"party_size":Number(N+".5")}]},token=token,key=reason,status=409,code=code)
    def old_alias(self,body,alias):
        value=copy.deepcopy(body);extra=value["unused"]
        if alias=="rounded-alias":extra.update(precise=Number("0.1"),large=Number("9007199254740992.0"),tiny=Number("0.0"))
        elif alias=="underflow-alias":extra["tiny"]=Number("1e-5000")
        elif alias=="same-integer":extra["large"]=Number("9007199254740992")
        elif alias=="different-integer":extra["large"]=Number("9007199254740993")
        elif alias=="boolean":extra["tiny"]=False
        elif alias=="string":extra["tiny"]="0"
        elif alias=="overflow":extra["large"]=Number("1e4300")
        return value
    def historical(self):
        source=self.args.legacy;token=self.setup(base=source)
        second=self.call("POST","/auth/login",dict(email="semantic@probe.invalid",password="semantic-probe-pass"),base=source).data["token"]
        bodies={};receipts={};paths={"create":"/reservations","moves":"/reservation-moves"};keys={"create":"historic-create","moves":"historic-moves"}
        bodies["create"]=dict(booking(),unused=legacy_feature())
        receipts["create"]=self.create(bodies["create"],key=keys["create"],base=source,token=token)
        member=self.create(booking(table="t1"),key="historic-second",base=source,token=token)
        bodies["moves"]={"moves":[{"reference":receipts["create"].data["reference"],"table_id":"t1"},{"reference":member.data["reference"],"table_id":"t0"}],"unused":legacy_feature()}
        receipts["moves"]=self.call("POST",paths["moves"],bodies["moves"],token=token,key=keys["moves"],base=source)
        if receipts["moves"].status!=201:raise RuntimeError("Genuine old swap setup refused")
        def replay_phase(phase,base):
            for endpoint in ["create","moves"]:
                for alias in LEGACY_EQ:
                    body=self.old_alias(bodies[endpoint],alias)
                    equal=same(bodies[endpoint],body,legacy=True)
                    status=200 if equal else 400 if phase=="source" and alias=="overflow" else 409
                    response=self.expect("legacy-"+phase+"-"+endpoint+"-"+alias,"POST",paths[endpoint],body,token=token,key=keys[endpoint],base=base,status=status,code=None if status==200 else "malformed_request" if status==400 else "idempotency_key_reuse")
                    if equal:self.check("legacy-"+phase+"-"+endpoint+"-"+alias,same(response.data,receipts[endpoint].data))
        replay_phase("source",source)
        ref=receipts["create"].data["reference"]
        self.call("PATCH","/reservations/"+ref,{"party_size":1},token=token,base=source)
        self.call("POST","/reservations/"+ref+"/cancel",{},token=token,base=source)
        old=self.snapshot(source);old_fingerprint=hashlib.sha256(old.raw).hexdigest()
        later=self.create(booking(table="t2",start=DAY+"T20:00"),key="source-later",base=source,token=token)
        foreign={}
        for phase,base in [("base",self.args.base),("peer",self.args.peer),("third",self.args.third)]:
            foreign[phase]=self.setup(base=base)
            self.expect("legacy-"+phase+"-unchanged-import","POST","/_test/import",raw=old.raw,base=base,status=204)
            replay_phase(phase,base)
            self.expect("legacy-"+phase+"-token","GET","/reservations",token=token,base=base)
            self.expect("legacy-"+phase+"-second-token","GET","/reservations",token=second,base=base)
            self.expect("legacy-"+phase+"-password","POST","/auth/login",dict(email="semantic@probe.invalid",password="semantic-probe-pass"),base=base)
            current=self.expect("legacy-"+phase+"-reference","GET","/reservations/"+ref,token=token,base=base)
            self.check("legacy-"+phase+"-reference",current.data.get("status")=="cancelled")
            replay=self.call("POST",paths["create"],bodies["create"],token=token,key=keys["create"],base=base)
            self.check("legacy-"+phase+"-old-response",same(replay.data,receipts["create"].data))
            profile_nodes=profiles(self.snapshot(base).data)
            self.check("legacy-"+phase+"-profile",len(profile_nodes)==3 and all(node["numeric_profile"]=="python-json-v1" for node in profile_nodes))
            state=self.snapshot(base).data
            expected_old={"precise":Number("0.1"),"large":Number("9007199254740992.0"),"tiny":Number("0.0")}
            old_values=[archived(state,keys[endpoint])["unused"] for endpoint in ["create","moves"]]
            self.check("legacy-"+phase+"-archived-numbers",all(all(isinstance(value[field],Number) and same(value[field],number) for field,number in expected_old.items()) for value in old_values))
            absent=self.call("GET","/reservations/"+later.data["reference"],token=token,base=base)
            self.check("legacy-"+phase+"-snapshot-readonly",absent.status==404 and hashlib.sha256(old.raw).hexdigest()==old_fingerprint)
        exact_body=dict(booking(table="t2",start=DAY+"T20:00"),unused=legacy_feature())
        exact_receipt=self.create(exact_body,key="new-exact",token=token)
        exact_move={"moves":[{"reference":exact_receipt.data["reference"],"party_size":Number("1.0")}],"unused":legacy_feature()}
        move_receipt=self.call("POST","/reservation-moves",exact_move,token=token,key="new-exact-move")
        if move_receipt.status!=201:raise RuntimeError("Mixed exact move setup refused")
        mixed=self.snapshot()
        for phase,base in [("base",self.args.base),("peer",self.args.peer),("third",self.args.third)]:
            if phase!="base":self.call("POST","/_test/import",raw=mixed.raw,base=base)
            pn=profiles(self.snapshot(base).data)
            self.check("mixed-"+phase+"-profiles",Counter(node["numeric_profile"] for node in pn)=={"python-json-v1":3,"exact-v1":2})
            alias=copy.deepcopy(exact_body);alias["unused"]["precise"]=Number("100000000000000005e-18")
            response=self.expect("mixed-"+phase+"-exact-alias","POST","/reservations",alias,token=token,key="new-exact",base=base)
            self.check("mixed-"+phase+"-exact-alias",same(response.data,exact_receipt.data))
            for label,field,value in [("rounded","large",Number("9007199254740992.0")),("underflow","tiny",Number("0")),("integer","large",Number("9007199254740992"))]:
                altered=copy.deepcopy(exact_body);altered["unused"][field]=value
                self.expect("mixed-"+phase+"-exact-"+label+"-conflict","POST","/reservations",altered,token=token,key="new-exact",base=base,status=409,code="idempotency_key_reuse")
            alias=copy.deepcopy(exact_move);alias["moves"][0]["party_size"]=Number("1e0");alias["unused"]["precise"]=Number("100000000000000005e-18")
            response=self.expect("mixed-"+phase+"-exact-move-alias","POST","/reservation-moves",alias,token=token,key="new-exact-move",base=base)
            self.check("mixed-"+phase+"-exact-move-alias",same(response.data,move_receipt.data))
            for label,field,value in [("rounded","large",Number("9007199254740992.0")),("underflow","tiny",Number("0")),("integer","large",Number("9007199254740992"))]:
                altered=copy.deepcopy(exact_move);altered["unused"][field]=value
                self.expect("mixed-"+phase+"-exact-move-"+label+"-conflict","POST","/reservation-moves",altered,token=token,key="new-exact-move",base=base,status=409,code="idempotency_key_reuse")
            if phase!="base":replay_phase(phase,base)
            before=self.snapshot(base)
            self.expect("mixed-"+phase+"-repeat-import","POST","/_test/import",raw=mixed.raw,base=base,status=204)
            self.check("mixed-"+phase+"-repeat-import",same(before.data,self.snapshot(base).data))
            self.expect("mixed-"+phase+"-replaced-token","GET","/reservations",token=foreign[phase],base=base,status=401,code="unauthenticated")
        for profile in ["exact-v1","python-json-v1"]:
            for problem in ["missing","unknown","wrong-type"]:
                invalid=copy.deepcopy(mixed.data);node=next(node for node in profiles(invalid) if node["numeric_profile"]==profile)
                if problem=="missing":node.pop("numeric_profile")
                else:node["numeric_profile"]="unsupported-profile" if problem=="unknown" else True
                before=self.snapshot(self.args.peer)
                rid="invalid-profile-"+profile+"-"+problem
                self.expect(rid,"POST","/_test/import",invalid,base=self.args.peer,status=422,code="validation_failed")
                self.check(rid+"-atomic",self.state_same(before,self.args.peer))
    def finish(self):
        for key,flags in [("charset",self.charsets),("byte-length",self.lengths),("finite-response-json",self.json_valid),("empty-204",self.empty204),("bare-numbers",self.number_tokens),("public-no-profile",self.public_profiles)]:
            self.check(key,bool(flags) and all(flags),"all observed applicable responses",dict(count=len(flags),failed=sum(not x for x in flags)))
        self.check("request-duration",all(x["duration_seconds"]<(10 if x["path"].startswith("/_test/") else 5) for x in self.trace))
        self.check("no-5xx",all(x["status"]<500 for x in self.trace))
        observed={x["requirement_id"] for x in self.results}
        rows=[]
        for key,case in CASES.items():
            rid=case["requirement_id"];found=[x for x in self.results if x["requirement_id"]==rid]
            rows.append(dict(**case,verdict="unverified" if not found else "verified" if all(x["passed"] for x in found) else "failed"))
        summary=dict(candidate=self.args.candidate,kind="independent exact/legacy raw HTTP",requests=len(self.trace),assertions=len(self.results),failed_assertions=sum(not x["passed"] for x in self.results),
            rows=len(rows),verified=sum(row["verdict"]=="verified" for row in rows),failed=sum(row["verdict"]=="failed" for row in rows),unverified=sum(row["verdict"]=="unverified" for row in rows),
            duration_seconds=time.monotonic()-self.started,max_ordinary_seconds=max([x["duration_seconds"] for x in self.trace if not x["path"].startswith("/_test/")],default=0),
            max_control_seconds=max([x["duration_seconds"] for x in self.trace if x["path"].startswith("/_test/")],default=0),flow_errors=self.errors)
        for name,value in [("trace.json",self.trace),("assertions.json",self.results),("coverage-observed.json",rows),("summary.json",summary)]:
            (self.out/name).write_text(json.dumps(value,indent=2))
        print(json.dumps(summary))
        return bool(summary["failed_assertions"] or summary["flow_errors"])
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--base",required=True);parser.add_argument("--peer",required=True)
    parser.add_argument("--third",required=True);parser.add_argument("--legacy",required=True);parser.add_argument("--candidate",required=True);parser.add_argument("--out",required=True)
    args=parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}",args.candidate) is None:parser.error("requires the full named final candidate")
    probe=Probe(args)
    try:
        probe.syntax();probe.counts();probe.ignored();probe.current();probe.historical()
    except Exception as error:
        probe.errors.append(dict(type=type(error).__name__,message=str(error)))
    failed=probe.finish()
    raise SystemExit(1 if failed else 0)
if __name__=="__main__":main()
