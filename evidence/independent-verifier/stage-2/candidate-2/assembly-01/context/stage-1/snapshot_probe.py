"""Prepared black-box snapshot races. Execution needs the named handoff driver.

Captures remain opaque raw bytes until actually imported. No credential-bearing
export, bearer token or password is written to evidence. Gate events are client
observations, never claims about Engine locks or internal serializer scheduling.
"""
import argparse
import hashlib
import http.client
import json
import re
import socket
import threading
import time
from urllib.parse import urlsplit
from semantic_oracle import encode,parse,same
from semantic_probe import Probe,Response,booking,fixture,safe
from snapshot_oracle import MEMBERS,MODES,PAD_BYTES,SEED,STEPS,WAVES,expected_availability,generation_of,identities_retained,projected,schedule,table_for
from snapshot_requirements import CASES

class Capture:
    """One ordinary HTTP GET with deterministic client receive gates."""
    def __init__(self,base,path,token,mode,resume,event):
        self.base=base;self.path=path;self.token=token;self.mode=mode;self.resume=resume;self.event=event
        self.ready=threading.Event();self.result=None;self.record={};self.runner_error=None
        self.thread=threading.Thread(target=self.run,name="snapshot-capture",daemon=True)
    def run(self):
        began=time.monotonic();payload=b"";status=0;headers={};valid=False;data=None;sock=None
        try:
            url=urlsplit(self.base);sock=socket.create_connection((url.hostname,url.port),timeout=10)
            # Per-client socket only; does not change machine or Docker settings.
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,4096);sock.settimeout(10)
            request="GET "+self.path+" HTTP/1.1\r\nHost: "+url.netloc+"\r\nConnection: close\r\nAccept: application/json\r\n"
            if self.token is not None:request+="Authorization: Bearer "+self.token+"\r\n"
            sock.sendall((request+"\r\n").encode("ascii"));sent=time.monotonic()
            self.event("capture-sent",path=self.path,mode=self.mode)
            if self.mode!="first-byte-held":
                self.ready.set()
                if not self.resume.wait(10):raise RuntimeError("Client schedule gate did not release")
            response=http.client.HTTPResponse(sock);response.begin();status=response.status;headers=dict(response.getheaders())
            header_time=time.monotonic()
            if self.mode=="first-byte-held":
                payload=response.read(1);self.event("capture-first-byte",path=self.path,received_bytes=len(payload))
                self.ready.set()
                if not self.resume.wait(10):raise RuntimeError("Client schedule gate did not release")
            resumed=time.monotonic()
            try:payload+=response.read()
            except http.client.IncompleteRead as error:
                payload+=error.partial;self.record["response_read_error"]="IncompleteRead"
            try:data=parse(payload);valid=True
            except (ValueError,UnicodeError):data={"invalid_json":True}
            response.close()
            self.record.update(request_sent_at=sent,response_headers_at=header_time,receive_resumed_at=resumed,
                               controlled_hold_seconds=max(0,resumed-(header_time if self.mode=="first-byte-held" else sent)))
        except (OSError,http.client.HTTPException) as error:
            self.record["transport_error"]=dict(type=type(error).__name__,message=str(error))
        except Exception as error:
            self.runner_error=dict(type=type(error).__name__,message=str(error))
        finally:
            self.ready.set()
            if sock is not None:sock.close()
            self.result=Response(status,data,payload)
            ended=time.monotonic();ctype=next((value for key,value in headers.items() if key.lower()=="content-type"),"")
            length=next((value for key,value in headers.items() if key.lower()=="content-length"),"")
            self.record.update(method="GET",path=self.path,base=self.base,key=None,has_token=self.token is not None,
                request_bytes=0,request_sha256=None,raw_request_utf8=None,status=status,response=safe(data),
                response_sha256=hashlib.sha256(payload).hexdigest(),response_bytes=len(payload),content_type=ctype,content_length=length,
                json_valid=valid,framing_valid=ctype.lower().replace(" ","")=="application/json;charset=utf-8" and length.isdigit() and int(length)==len(payload),
                began_at=began,ended_at=ended,duration_seconds=ended-began,client_controlled_receive=True,mode=self.mode,
                requested_receive_buffer_bytes=4096)
            self.event("capture-finished",path=self.path,status=status,response_bytes=len(payload))

class SnapshotProbe(Probe):
    def __init__(self,args):
        super().__init__(args);self.events=[];self.event_lock=threading.Lock();self.captured_metrics=[]
    def event(self,kind,**detail):
        with self.event_lock:self.events.append(dict(sequence=len(self.events)+1,kind=kind,at=time.monotonic(),**detail))
    def check(self,key,condition,expected=None,observed=None):
        assert key in CASES,key
        self.results.append(dict(requirement_id=CASES[key]["requirement_id"],passed=bool(condition),expected=safe(expected),observed=safe(observed)))
    def bootstrap(self,mode):
        f=fixture();f["restaurants"][0]["tables"]=[dict(id="t"+str(i),label="Seat "+str(i),capacity=64) for i in range(MEMBERS)]
        token=self.setup(f);originals=[];receipts=[]
        for index in range(MEMBERS):
            body=dict(booking(table="t"+str(index)),unused=dict(padding="p"*PAD_BYTES,member=index,precise=parse("0.100000000000000005")))
            key=mode+"-create-"+str(index);response=self.create(body,key=key,token=token)
            originals.append(response.data);receipts.append(dict(key=key,path="/reservations",body=body,response=response.data))
        return token,originals,receipts
    def replace_capture(self,stem,role,raw,lower,upper,token,originals,creates,moves):
        base=getattr(self.args,role);prefix=stem+"-"+role
        f=fixture();f["users"][0].update(id="destination-only",email="destination@probe.invalid",display_name="Previous Destination")
        reset=self.call("POST","/_test/reset",f,base=base)
        login=self.call("POST","/auth/login",dict(email="destination@probe.invalid",password="semantic-probe-pass"),base=base)
        if reset.status!=204 or login.status!=200:raise RuntimeError("Destination setup refused")
        old_token=login.data["token"];self.create(booking(start="2035-06-04T20:00"),key="destination-only",token=old_token,base=base)
        imported=self.expect(prefix+"-import","POST","/_test/import",raw=raw,base=base,status=204)
        if imported.status!=204:return
        capture=parse(raw);before=self.snapshot(base)
        listing=self.call("GET","/reservations",token=token,base=base)
        self.check(prefix+"-valid-token",listing.status==200)
        records=listing.data.get("reservations") if isinstance(listing.data,dict) else None
        generation=generation_of(records,originals,lower,upper)
        self.check(prefix+"-generation",generation is not None,dict(lower=lower,upper=upper),dict(generation=generation))
        self.check(prefix+"-identities",identities_retained(records,originals))
        self.check(prefix+"-old-records-removed",isinstance(records,list) and len(records)==MEMBERS and {r.get("reference") for r in records}=={r["reference"] for r in originals})
        old=self.call("GET","/reservations",token=old_token,base=base)
        self.check(prefix+"-old-token-removed",old.status==401 and old.data.get("error",{}).get("code")=="unauthenticated")
        def replay(receipt):
            result=self.call("POST",receipt["path"],receipt["body"],token=token,key=receipt["key"],base=base)
            return result.status==200 and same(result.data,receipt["response"])
        self.check(prefix+"-create-receipts",all([replay(receipt) for receipt in creates]))
        if generation is not None:
            required=[receipt for g,receipt in moves.items() if g<=generation]
            self.check(prefix+"-move-receipts",len(required)==generation and all([replay(receipt) for receipt in required]))
            absent=[]
            for g,receipt in moves.items():
                if g>generation:
                    invalid=dict(receipt["body"]);invalid["moves"]=[dict(member,party_size=-1) for member in invalid["moves"]]
                    result=self.call("POST",receipt["path"],invalid,token=token,key=receipt["key"],base=base)
                    absent.append(result.status==422 and result.data.get("error",{}).get("code")=="validation_failed")
            # A fresh never-written key is a nonvacuous control even when the
            # capture lands at the last completed generation of this wave.
            fresh=self.call("POST","/reservation-moves",dict(moves=[dict(reference=originals[0]["reference"],party_size=-1)]),
                            token=token,key=prefix+"-fresh-unused",base=base)
            absent.append(fresh.status==422 and fresh.data.get("error",{}).get("code")=="validation_failed")
            self.check(prefix+"-future-keys-absent",all(absent))
        self.check(prefix+"-replay-readonly",same(self.snapshot(base).data,before.data))
        repeated=self.call("POST","/_test/import",raw=raw,base=base)
        after=self.snapshot(base)
        self.check(prefix+"-repeat-import",repeated.status==204 and same(after.data,before.data))
        self.check(prefix+"-captured-unchanged",same(before.data,capture) and same(after.data,capture))
        self.captured_metrics.append(dict(case=stem,destination=role,generation=generation,original_create_receipts_checked=len(creates),prefix_move_receipts_checked=generation,
            later_move_keys_checked=None if generation is None else sum(g>generation for g in moves),capture_bytes=len(raw),capture_sha256=hashlib.sha256(raw).hexdigest(),interval=dict(lower=lower,upper=upper)))
    def wave(self,item,token,originals,creates,moves):
        mode=item["mode"];wave=item["wave"];stem=mode+"-"+str(wave);resume=threading.Event()
        paths={"export":"/_test/export","list":"/reservations","availability":"/availability?restaurant_id=r&date=2035-06-04&party_size=1"}
        captures={}
        self.event("wave-start",**item)
        for route in item["route_launch_order"]:
            capture=Capture(self.args.base,paths[route],token if route=="list" else None,mode,resume,self.event)
            captures[route]=capture;capture.thread.start()
        try:
            if not all(capture.ready.wait(10) for capture in captures.values()):raise RuntimeError("Capture readiness gate timed out")
            self.event("writer-start",mode=mode,wave=wave)
            if mode=="send-barrier":resume.set();self.event("receive-gate-release",mode=mode,wave=wave)
            for position,generation in enumerate(item["write_generations"]):
                body=dict(moves=[dict(reference=record["reference"],table_id=table_for(index,generation),party_size=generation+2) for index,record in enumerate(originals)],
                          unused=dict(padding="m"*PAD_BYTES,generation=generation,precise=parse("100000000000000005e-18")))
                key=mode+"-move-"+str(generation);rid=mode+"-write-"+str(generation)
                result=self.expect(rid+"-status","POST","/reservation-moves",body,token=token,key=key,status=201)
                expected=dict(reservations=projected(originals,generation))
                self.check(rid+"-order",result.status==201 and same(result.data,expected))
                if result.status!=201:raise RuntimeError("Move prerequisite failed; descendants remain unverified")
                moves[generation]=dict(key=key,path="/reservation-moves",body=body,response=result.data)
                self.event("write-committed-response",mode=mode,wave=wave,generation=generation)
                if mode=="first-byte-held" and position==0:resume.set();self.event("receive-gate-release",mode=mode,wave=wave)
            if mode=="send-held":resume.set();self.event("receive-gate-release",mode=mode,wave=wave)
        finally:
            resume.set()
            for capture in captures.values():capture.thread.join(12)
        self.event("wave-settled",mode=mode,wave=wave)
        for route,capture in captures.items():
            if capture.thread.is_alive():raise RuntimeError("Capture thread did not finish")
            if capture.runner_error:self.errors.append(dict(case=stem,route=route,kind="client_runner_error",**capture.runner_error))
            capture.record["operation"]=len(self.trace)+1;self.trace.append(capture.record)
            self.check(stem+"-"+route+"-status",capture.result.status==200)
            self.check(stem+"-"+route+"-json",capture.record["json_valid"])
            self.check(stem+"-"+route+"-framing",capture.record["framing_valid"])
        listing=captures["list"].result.data
        records=listing.get("reservations") if isinstance(listing,dict) else None
        generation=generation_of(records,originals,item["lower"],item["upper"])
        self.check(stem+"-list-coherent",generation is not None,dict(lower=item["lower"],upper=item["upper"]),dict(generation=generation))
        self.check(stem+"-list-identities",identities_retained(records,originals))
        self.check(stem+"-availability-coherent",same(captures["availability"].result.data,expected_availability()))
        exported=captures["export"].result
        self.check(stem+"-export-envelope",isinstance(exported.data,dict) and exported.data.get("track")=="tablekeeper" and same(exported.data.get("format_version"),1) and isinstance(exported.data.get("state"),dict))
        before=self.snapshot()
        current=self.call("GET","/reservations",token=token)
        self.call("GET",paths["availability"]);self.snapshot()
        latest=moves[item["upper"]]
        replay=self.call("POST",latest["path"],latest["body"],token=token,key=latest["key"])
        self.check(stem+"-source-readonly",generation_of(current.data.get("reservations",[]),originals,item["upper"],item["upper"])==item["upper"] and replay.status==200 and same(replay.data,latest["response"]) and self.state_same(before))
        if captures["export"].record["json_valid"] and exported.status==200:
            for role in ["peer","third"]:self.replace_capture(stem,role,exported.raw,item["lower"],item["upper"],token,originals,creates,moves)
    def finish(self):
        self.check("no-5xx",bool(self.trace) and all(item["status"]<500 for item in self.trace))
        ordinary=[item for item in self.trace if not item["path"].startswith("/_test/") and not item.get("client_controlled_receive")]
        controls=[item for item in self.trace if item["path"].startswith("/_test/") and not item.get("client_controlled_receive")]
        self.check("ordinary-duration",bool(ordinary) and all(item["duration_seconds"]<5 for item in ordinary))
        self.check("control-duration",bool(controls) and all(item["duration_seconds"]<10 for item in controls))
        rows=[]
        for case in CASES.values():
            found=[result for result in self.results if result["requirement_id"]==case["requirement_id"]]
            rows.append(dict(**case,verdict="unverified" if not found else "verified" if all(result["passed"] for result in found) else "failed"))
        summary=dict(candidate=self.args.candidate,kind="Independent export/read lifetime concurrency captures",seed=SEED,modes=MODES,waves=WAVES,steps=STEPS,members=MEMBERS,requests=len(self.trace),assertions=len(self.results),failed_assertions=sum(not result["passed"] for result in self.results),rows=len(rows),verified=sum(row["verdict"]=="verified" for row in rows),failed=sum(row["verdict"]=="failed" for row in rows),unverified=sum(row["verdict"]=="unverified" for row in rows),flow_errors=self.errors,duration_seconds=time.monotonic()-self.started,
            internal_serializer_interleaving="unobserved; client send/receive/writer events only",controlled_receive_excluded_from_server_latency_claim=True,export_payload_saved=False)
        for name,data in [("trace.json",self.trace),("event-trace.json",self.events),("schedule.json",schedule()),("assertions.json",self.results),("coverage-observed.json",rows),("capture-import-metrics.json",self.captured_metrics),("summary.json",summary)]:
            (self.out/name).write_text(json.dumps(data,indent=2))
        print(json.dumps(summary));return bool(summary["failed_assertions"] or summary["flow_errors"])

def main():
    parser=argparse.ArgumentParser()
    for name in ["base","peer","third","candidate","out"]:parser.add_argument("--"+name,required=True)
    args=parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}",args.candidate) is None:parser.error("full final named candidate required")
    probe=SnapshotProbe(args)
    for mode in MODES:
        try:
            token,originals,creates=probe.bootstrap(mode);moves={}
            for item in [item for item in schedule() if item["mode"]==mode]:probe.wave(item,token,originals,creates,moves)
        except Exception as error:probe.errors.append(dict(case=mode,type=type(error).__name__,message=str(error),classification="flow prerequisite or client runner; inspect actual request/assertions"))
    raise SystemExit(1 if probe.finish() else 0)

if __name__=="__main__":main()
