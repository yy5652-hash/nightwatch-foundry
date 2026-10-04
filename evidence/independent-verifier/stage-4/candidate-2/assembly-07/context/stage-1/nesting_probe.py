"""Prepared bounded deep JSON protocol; no production import or fabricated state."""
import argparse
import json
import re
import time
from nesting_input import DEPTHS,SHAPES,configure_client,max_container_depth,tree
from nesting_requirements import CASES
from semantic_oracle import Number,encode,same
from semantic_probe import Probe,booking,fixture,safe

class NestingProbe(Probe):
    def check(self,key,condition,expected=None,observed=None):
        assert key in CASES,key
        self.results.append(dict(requirement_id=CASES[key]["requirement_id"],passed=bool(condition),expected=safe(expected),observed=safe(observed)))
    def scenario(self,shape,depth):
        stem=shape+"-"+str(depth);nested=tree(shape,depth)
        f=fixture();f["unused"]=nested
        reset=self.expect(stem+"-reset","POST","/_test/reset",f,status=204)
        if reset.status!=204:return
        self.expect(stem+"-signup","POST","/auth/signup",dict(email="deep-new@probe.invalid",password="semantic-probe-pass",display_name="Nested Diner",unused=nested),status=201)
        login=self.expect(stem+"-login","POST","/auth/login",dict(email="semantic@probe.invalid",password="semantic-probe-pass",unused=nested))
        if login.status!=200:return
        token=login.data["token"];receipts={};bodies={};paths={"create":"/reservations","moves":"/reservation-moves"}
        for endpoint in ["create","moves"]:
            if endpoint=="create":body=dict(booking(),unused=nested)
            else:
                member=self.create(booking(table="t1"),token=token,key="deep-member")
                body=dict(moves=[dict(reference=member.data["reference"],party_size=2,unused=nested)],unused=nested)
            path=paths[endpoint];key="deep-"+endpoint
            original=self.expect(stem+"-"+endpoint+"-first","POST",path,body,token=token,key=key,status=201)
            if original.status!=201:return
            receipts[endpoint]=original;bodies[endpoint]=body
            before=self.snapshot()
            def replace(value,variant):
                result=dict(value);result["unused"]=tree(shape,depth,variant)
                if endpoint=="moves":result["moves"]=[dict(value["moves"][0],unused=tree(shape,depth,variant))]
                return result
            alias=replace(body,"alias");alias=dict(reversed(list(alias.items())))
            replay=self.expect(stem+"-"+endpoint+"-alias","POST",path,alias,token=token,key=key)
            self.check(stem+"-"+endpoint+"-alias",same(replay.data,original.data))
            for variant in ["number-difference","type-difference"]:
                self.expect(stem+"-"+endpoint+"-"+variant,"POST",path,replace(body,variant),token=token,key=key,status=409,code="idempotency_key_reuse")
            self.expect(stem+"-"+endpoint+"-missing-auth","POST",path,body,key="unauth",status=401,code="unauthenticated")
            self.expect(stem+"-"+endpoint+"-missing-key","POST",path,body,token=token,status=400,code="missing_idempotency_key")
            invalid=dict(body)
            # Use explicit numeric JSON spelling without native float coercion.
            if endpoint=="create":invalid["party_size"]=Number("1.5")
            else:invalid["moves"]=[dict(body["moves"][0],party_size=Number("1.5"))]
            self.expect(stem+"-"+endpoint+"-failed-value","POST",path,invalid,token=token,key="failed-"+endpoint,status=422,code="validation_failed")
            self.check(stem+"-"+endpoint+"-atomic",self.state_same(before))
            fixed=dict(body)
            if endpoint=="create":fixed["starts_at_local"]="2035-06-04T20:00"
            else:fixed["moves"]=[dict(body["moves"][0],party_size=3)]
            self.expect(stem+"-"+endpoint+"-failed-key-reuse","POST",path,fixed,token=token,key="failed-"+endpoint,status=201)
            ref=original.data["reference"] if endpoint=="create" else original.data["reservations"][0]["reference"]
            if endpoint=="create":
                current=self.snapshot();patched=self.call("PATCH","/reservations/"+ref,dict(unused=nested),token=token)
                self.check(stem+"-patch",patched.status==200 and self.state_same(current))
            self.call("POST","/reservations/"+ref+"/cancel",{},token=token)
            immutable=self.expect(stem+"-"+endpoint+"-immutable","POST",path,body,token=token,key=key)
            self.check(stem+"-"+endpoint+"-immutable",same(immutable.data,original.data))
        before=self.snapshot()
        malformed=self.expect(stem+"-malformed","POST","/reservations",raw=encode(bodies["create"]).encode()[:-1],status=400,code="malformed_request")
        self.check(stem+"-malformed-atomic",self.state_same(before))
        exported=self.snapshot()
        self.check(stem+"-export",exported.status==200 and isinstance(exported.data,dict) and exported.data.get("track")=="tablekeeper" and same(exported.data.get("format_version"),1) and isinstance(exported.data.get("state"),dict))
        self.export_metrics.append(dict(case=stem,export_bytes=len(exported.raw),export_max_container_depth=max_container_depth(exported.data)))
        imported=self.expect(stem+"-import","POST","/_test/import",raw=exported.raw,base=self.args.peer,status=204)
        if imported.status!=204:return
        self.check(stem+"-replacement",same(self.snapshot(self.args.peer).data,exported.data))
        source_list=self.call("GET","/reservations",token=token);peer_list=self.call("GET","/reservations",token=token,base=self.args.peer)
        self.check(stem+"-retained-token",source_list.status==200 and peer_list.status==200 and same(source_list.data,peer_list.data))
        for endpoint in ["create","moves"]:
            response=self.expect(stem+"-"+endpoint+"-import-original","POST",paths[endpoint],bodies[endpoint],token=token,key="deep-"+endpoint,base=self.args.peer)
            self.check(stem+"-"+endpoint+"-import-original",same(response.data,receipts[endpoint].data))
            changed=dict(bodies[endpoint]);changed["unused"]=tree(shape,depth,"number-difference")
            self.expect(stem+"-"+endpoint+"-import-difference","POST",paths[endpoint],changed,token=token,key="deep-"+endpoint,base=self.args.peer,status=409,code="idempotency_key_reuse")
    def finish(self):
        self.check("charset",bool(self.charsets) and all(self.charsets))
        self.check("byte-length",bool(self.lengths) and all(self.lengths))
        self.check("duration",all(item["duration_seconds"]<(10 if item["path"].startswith("/_test/") else 5) for item in self.trace))
        self.check("no-5xx",all(item["status"]<500 for item in self.trace))
        rows=[]
        for case in CASES.values():
            found=[result for result in self.results if result["requirement_id"]==case["requirement_id"]]
            rows.append(dict(**case,verdict="unverified" if not found else "verified" if all(result["passed"] for result in found) else "failed"))
        summary=dict(candidate=self.args.candidate,kind="Independent bounded nesting raw HTTP",requests=len(self.trace),assertions=len(self.results),failed_assertions=sum(not result["passed"] for result in self.results),rows=len(rows),verified=sum(row["verdict"]=="verified" for row in rows),failed=sum(row["verdict"]=="failed" for row in rows),unverified=sum(row["verdict"]=="unverified" for row in rows),flow_errors=self.errors,
                     wrapper_depths=DEPTHS,shapes=SHAPES,client_recursion_limit=20000,service_configuration_changed=False,duration_seconds=time.monotonic()-self.started,max_ordinary_seconds=max((item["duration_seconds"] for item in self.trace if not item["path"].startswith("/_test/")),default=0),max_control_seconds=max((item["duration_seconds"] for item in self.trace if item["path"].startswith("/_test/")),default=0))
        for name,data in [("trace.json",self.trace),("assertions.json",self.results),("coverage-observed.json",rows),("export-size-depth.json",self.export_metrics),("summary.json",summary)]:
            (self.out/name).write_text(json.dumps(data,indent=2))
        print(json.dumps(summary));return bool(summary["failed_assertions"] or summary["flow_errors"])

def main():
    configure_client();parser=argparse.ArgumentParser()
    for name in ["base","peer","candidate","out"]:parser.add_argument("--"+name,required=True)
    args=parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}",args.candidate) is None:parser.error("full final named candidate required")
    probe=NestingProbe(args);probe.export_metrics=[]
    for shape in SHAPES:
        for depth in DEPTHS:
            try:probe.scenario(shape,depth)
            except Exception as error:probe.errors.append(dict(case=shape+"-"+str(depth),type=type(error).__name__,message=str(error)))
    raise SystemExit(1 if probe.finish() else 0)

if __name__=="__main__":main()
