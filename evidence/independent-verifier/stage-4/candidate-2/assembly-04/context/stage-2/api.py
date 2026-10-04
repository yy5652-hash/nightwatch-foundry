"""Stage 2 HTTP probes derived from specs; no product or shipped-test imports."""
import argparse
import concurrent.futures
import copy
import csv
import datetime as dt
import http.client
import json
import random
import sys
import threading
import time
import urllib.parse
from pathlib import Path

from requirements import ROWS
from oracle import canonical, invariant, options, serial_orders
sys.path.append(str(Path(__file__).resolve().parents[1]/"stage-1"))
from probe import Probe, fixture, fingerprint, safe

DAY = "2035-06-04"


def pair_fixture(zone="UTC", opens="18:10", closes="23:10", duration=90):
    f = fixture(zone=zone, opens=opens, closes=closes, duration=duration, tables=4)
    f["restaurants"][0]["tables"] = [dict(id="t"+str(i), label=label, capacity=2+2*i)
                                      for i,label in enumerate(["Window Alcove", "Garden Bench", "Cedar Booth", "Kitchen Nook"])]
    f["restaurants"][0]["combinable"] = [["t1","t0"],["t3","t2"],["t2","t1"]]
    other = copy.deepcopy(f["restaurants"][0])
    other.update(id="other", name="Other Kitchen")
    for table in other["tables"]:
        table["id"] = "other-"+table["id"]
        table["label"] = "Orchard "+table["label"]
    other["combinable"] = [["other-"+x for x in pair] for pair in other["combinable"]]
    f["restaurants"].append(other)
    return f


class PairProbe(Probe):
    def check(self, key, condition, expected=None, observed=None):
        with self.lock:
            self.results.append(dict(requirement_id="TK2-"+key, passed=bool(condition), expected=safe(expected), observed=safe(observed)))

    def finish(self):
        by_id={}
        for result in self.results:
            by_id.setdefault(result["requirement_id"],[]).append(result)
        rows=copy.deepcopy(ROWS)
        command=["python3",str(Path(__file__).resolve()),"--base",self.args.base,"--peer",self.args.peer,"--candidate",self.args.candidate,"--out",str(self.out),"--case",self.args.case]
        for row in rows:
            row["candidate_full_revision"]=self.args.candidate
            results=by_id.get(row["requirement_id"],[])
            row["verdict"]="verified" if results and all(x["passed"] for x in results) else "failed" if results else "unverified"
            if results:
                row["evidence_path"]=str(self.out/"assertions.json")+"#"+row["requirement_id"]
                row["executable_command_or_interaction"]=json.dumps(command)
        fields=list(dict.fromkeys(key for row in rows for key in row))
        with (self.out/"coverage.csv").open("w",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        (self.out/"assertions.json").write_text(json.dumps(self.results,indent=2))
        with (self.out/"operations.jsonl").open("w") as handle:
            for operation in self.trace:
                handle.write(json.dumps(operation)+"\n")
        summary=dict(candidate=self.args.candidate,stage=2,seed=20261005,source="Independent specification-derived HTTP probes; no judging suite available",
                     requests=len(self.trace),assertions=len(self.results),failures=sum(not x["passed"] for x in self.results),
                     rows=len(rows),verified=sum(x["verdict"]=="verified" for x in rows),failed=sum(x["verdict"]=="failed" for x in rows),
                     unverified=sum(x["verdict"]=="unverified" for x in rows),duration_seconds=time.monotonic()-self.started)
        (self.out/"summary.json").write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary))
        return summary["failures"]

    def setup(self, f=None, base=None):
        super().setup(f or pair_fixture(), base=base)

    def body(self, ids=None, local=DAY+"T18:10", party=2, restaurant="r"):
        return dict(restaurant_id=restaurant, table_ids=ids or ["t1","t0"], starts_at_local=local, party_size=party)

    def assert_shape(self, endpoint, receipt, ids):
        prefix = endpoint+"-"+("single" if len(ids)==1 else "pair")
        self.check(prefix+"-table-ids", receipt.get("table_ids") == ids, ids, receipt)
        key = "-table-id" if len(ids)==1 else "-no-table-id"
        valid = receipt.get("table_id") == ids[0] if len(ids)==1 else "table_id" not in receipt
        self.check(prefix+key, valid, ids[0] if len(ids)==1 else "table_id omitted", receipt)

    def model(self):
        self.setup()
        detail = self.call("GET", "/restaurants/r")[1]
        self.check("fixture-combinable", detail.get("combinable") == self.f["restaurants"][0]["combinable"])
        created = self.create(self.body(["t0","t1"],party=6))
        self.check("pair-unordered", created.get("table_ids") == ["t1","t0"])
        self.check("pair-capacity", created.get("party_size") == 6)
        self.expect("pair-no-transitive", "POST", "/reservations", self.body(["t0","t2"],party=7),token=self.a,key="transitive",status=422,code="combination_not_allowed")
        available = self.availability(day=DAY)
        relevant = [slot for slot in available["slots"] if DAY+"T18:10" <= slot["starts_at_local"] < DAY+"T19:40"]
        self.check("pair-full-duration", bool(relevant) and all(not({"t0","t1"}&set(slot["available_table_ids"])) for slot in relevant))
        legacy = pair_fixture()
        del legacy["restaurants"][0]["combinable"]
        self.setup(legacy)
        available = self.availability(day=DAY)
        self.check("fixture-absent-combinable", all(all(len(option["table_ids"])==1 for option in slot.get("available_options",[])) for slot in available["slots"]))
        for label, fields, ids in [("legacy",dict(table_id="t0"),["t0"]),("array",dict(table_ids=["t0"]),["t0"]),("pair",dict(table_ids=["t0","t1"]),["t1","t0"])]:
            for cancelled in [False,True]:
                f=pair_fixture()
                record=dict(id="seed",reference="SEED01",user_id="u_a",restaurant_id="r",starts_at_local=DAY+"T18:10",party_size=2,**fields)
                if cancelled:
                    record["status"]="cancelled"
                f["reservations"]=[record]
                self.setup(f)
                value=self.call("GET","/reservations/SEED01",token=self.a)[1]
                self.check("seed-single-"+label if label!="pair" else "seed-pair", value.get("table_ids")==ids)
                self.check("seed-cancelled-status" if cancelled else "seed-default-status",value.get("status")==("cancelled" if cancelled else "confirmed"))
                available=self.availability(day=DAY)["slots"][0]["available_table_ids"]
                self.check("seed-cancelled-status" if cancelled else "seed-default-status", all((identifier in available)==cancelled for identifier in ids))

    def fixture_case(self):
        invalid=[("outer-string","bad",400),("entry-string",["t0"],400),("member-number",[[1,"t0"]],400),
                 ("one-member",[["t0"]],422),("three-members",[["t0","t1","t2"]],422),
                 ("same-member-twice",[["t0","t0"]],422),("unknown-member",[["t0","missing"]],422),
                 ("foreign-member",[["t0","other-t0"]],422)]
        for name,value,status in invalid:
            self.setup()
            bad=copy.deepcopy(self.f)
            bad["restaurants"][0]["combinable"]=value
            self.expect("fixture-pair-"+name,"POST","/_test/reset",bad,status=status,code="malformed_request" if status==400 else "validation_failed")

    def availability_case(self):
        self.setup()
        restaurant=self.f["restaurants"][0]
        for party in [1,2,4,5,6,8,10,14,15]:
            value=self.availability(party=party,day=DAY)
            expected=options(restaurant["tables"],restaurant["combinable"],[],0,90,party)
            for slot in value["slots"]:
                actual=slot.get("available_options")
                self.check("available-options",isinstance(actual,list))
                self.check("available-options-complete",actual==expected,expected,actual)
                self.check("available-options-table-ids",isinstance(actual,list) and all(isinstance(x.get("table_ids"),list) for x in actual))
                self.check("available-options-capacity",isinstance(actual,list) and all(x.get("capacity")==sum(t["capacity"] for t in restaurant["tables"] if t["id"] in x["table_ids"]) for x in actual))
                self.check("available-options-capacity-filter",isinstance(actual,list) and all(x["capacity"]>=party for x in actual))
                self.check("available-options-singles",slot["available_table_ids"]==[x["table_ids"][0] for x in expected if len(x["table_ids"])==1])
                for rid in ["single-order","pair-order","member-order"]:
                    self.check("available-options-"+rid,actual==expected,expected,actual)
                if party==15:
                    self.check("available-options-empty",actual==[])
        self.create(self.body(["t0"],party=2))
        value=self.availability(day=DAY)
        record=dict(table_ids=["t0"],start=0,end=90,status="confirmed")
        for index,slot in enumerate(value["slots"]):
            expected=options(restaurant["tables"],restaurant["combinable"],[record],index*30,index*30+90,2)
            self.check("available-options-member-filter",slot.get("available_options")==expected,expected,slot)
            if index==3:
                self.check("pair-half-open",slot.get("available_options")==options(restaurant["tables"],restaurant["combinable"],[],90,180,2))

    def action(self, endpoint, original, fields, key):
        if endpoint=="create":
            body=self.body()
            body.update(fields)
            if "table_id" in fields and "table_ids" not in fields:
                body.pop("table_ids")
            return self.call("POST","/reservations",body,token=self.a,key=key)
        if endpoint=="patch":
            return self.call("PATCH","/reservations/"+original["reference"],fields,token=self.a)
        return self.call("POST","/reservation-moves",{"moves":[dict(reference=original["reference"],**fields)]},token=self.a,key=key)

    def validation(self):
        cases=[("legacy-single",dict(table_id="t0"),201,None),("array-single",dict(table_ids=["t0"]),201,None),
               ("array-pair",dict(table_ids=["t0","t1"]),201,None),
               ("both-fields",dict(table_id="t0",table_ids=["t0"]),422,"validation_failed"),
               ("unlisted-pair",dict(table_ids=["t0","t3"]),422,"combination_not_allowed"),
               ("transitive-pair",dict(table_ids=["t0","t2"]),422,"combination_not_allowed"),
               ("too-many",dict(table_ids=["t0","t1","t2"]),422,"combination_not_allowed"),
               ("duplicate",dict(table_ids=["t0","t0"]),422,"validation_failed"),
               ("wrong-array-type",dict(table_ids="t0"),400,"malformed_request"),
               ("wrong-member-type",dict(table_ids=[1,"t0"]),400,"malformed_request"),
               ("empty-array",dict(table_ids=[]),422,"validation_failed"),
               ("unknown-table",dict(table_ids=["missing"]),404,"not_found"),
               ("foreign-table",dict(table_ids=["other-t0"]),404,"not_found"),
               ("capacity",dict(table_ids=["t0","t1"],party_size=7),422,"party_exceeds_capacity"),
               ("taken-first",dict(table_ids=["t0","t1"]),409,"table_unavailable"),
               ("taken-second",dict(table_ids=["t0","t1"]),409,"table_unavailable")]
        for endpoint in ["create","patch","moves"]:
            for name,fields,status,code in cases:
                self.setup()
                original=self.create(self.body(["t3"])) if endpoint!="create" else None
                if name.startswith("taken"):
                    member="t1" if name.endswith("first") else "t0"
                    self.create(self.body([member]))
                before=self.state()
                actual,value=self.action(endpoint,original,fields,"case-"+name)
                expected=200 if endpoint=="patch" and status==201 else status
                self.check(endpoint+"-"+name,actual==expected and (code is None or value.get("error",{}).get("code")==code),dict(status=expected,code=code),dict(status=actual,body=value))
                if status!=201:
                    self.check(endpoint+"-rollback",self.state()==before)

    def responses(self):
        for ids in [["t0"],["t0","t1"]]:
            self.setup()
            canonical_ids=["t0"] if len(ids)==1 else ["t1","t0"]
            created=self.create(self.body(ids))
            ref=created["reference"]
            self.assert_shape("create",created,canonical_ids)
            self.assert_shape("lookup",self.call("GET","/reservations/"+ref,token=self.a)[1],canonical_ids)
            self.assert_shape("list",self.call("GET","/reservations",token=self.a)[1]["reservations"][0],canonical_ids)
            self.assert_shape("patch",self.call("PATCH","/reservations/"+ref,{"party_size":1},token=self.a)[1],canonical_ids)
            moved=self.call("POST","/reservation-moves",{"moves":[{"reference":ref}]},token=self.a,key="shape-move")[1]
            self.assert_shape("moves",moved["reservations"][0],canonical_ids)
            self.assert_shape("cancel",self.call("POST","/reservations/"+ref+"/cancel",{},token=self.a)[1],canonical_ids)

    def dst(self):
        for label,zone,spring,fall,repeated in [("berlin","Europe/Berlin","2026-03-29","2026-10-25","02:30"),
                                              ("new-york","America/New_York","2026-03-08","2026-11-01","01:30")]:
            self.setup(pair_fixture(zone,opens="00:00",closes="06:00"))
            spring_slots=self.availability(day=spring)["slots"]
            self.check("pair-"+label+"-gap-availability",all(not slot["starts_at_local"].startswith(spring+"T02:") for slot in spring_slots))
            self.expect("pair-"+label+"-gap-create","POST","/reservations",self.body(local=spring+"T02:30"),token=self.a,key="gap",status=422,code="invalid_local_time")
            slots=self.availability(day=fall)["slots"]
            local=fall+"T"+repeated
            self.check("pair-"+label+"-repeat-once",sum(slot["starts_at_local"]==local for slot in slots)==1)
            record=self.create(self.body(local=local))
            expected=local+":00"+("+02:00" if label=="berlin" else "-04:00")
            self.check("pair-"+label+"-repeat-first",record["starts_at"]==expected,expected,record)
            start=dt.datetime.fromisoformat(record["starts_at"]).timestamp()
            end=dt.datetime.fromisoformat(record["ends_at"]).timestamp()
            self.check("pair-"+label+"-absolute-duration",end-start==90*60,5400,end-start)

    def transactions(self):
        self.setup()
        original=self.create(self.body(["t0"]))
        ref=original["reference"]
        for key,ids,expected in [("single-to-pair",["t0","t1"],["t1","t0"]),("pair-to-pair",["t1","t2"],["t2","t1"]),("pair-to-single",["t0"],["t0"])]:
            status,value=self.call("PATCH","/reservations/"+ref,{"table_ids":ids},token=self.a)
            self.check("patch-"+key,status==200 and value.get("table_ids")==expected)
            for field in ["reservation_id","reference","created_at"]:
                self.check("patch-retained-"+field,value.get(field)==original[field])
            self.check("patch-retained-user_id",self.call("GET","/reservations/"+ref,token=self.a)[0]==200 and self.call("GET","/reservations/"+ref,token=self.b)[0]==404)
        self.setup()
        a=self.create(self.body(["t0","t1"]))
        b=self.create(self.body(["t2","t3"]))
        moves={"moves":[dict(reference=a["reference"],table_ids=["t2","t3"]),dict(reference=b["reference"],table_ids=["t0","t1"])]}
        status,receipt=self.call("POST","/reservation-moves",moves,token=self.a,key="pair-swap")
        self.check("moves-pair-swap",status==201 and [r["table_ids"] for r in receipt.get("reservations",[])]==[["t3","t2"],["t1","t0"]])
        self.call("POST","/reservations/"+a["reference"]+"/cancel",{},token=self.a)
        available=self.availability(day=DAY)["slots"][0]
        self.check("cancel-pair-all-members",set(["t2","t3"]).issubset(available["available_table_ids"]))
        replay=self.call("POST","/reservation-moves",moves,token=self.a,key="pair-swap")
        self.check("pair-move-receipt",replay==(200,receipt))
        self.setup()
        body=self.body(["t0","t1"])
        status,receipt=self.call("POST","/reservations",body,token=self.a,key="pair-original")
        self.call("PATCH","/reservations/"+receipt["reference"],{"party_size":1},token=self.a)
        self.call("POST","/reservations/"+receipt["reference"]+"/cancel",{},token=self.a)
        self.check("pair-create-receipt",self.call("POST","/reservations",body,token=self.a,key="pair-original")== (200,receipt))
        reverse=dict(body,table_ids=["t1","t0"])
        self.expect("pair-reversed-key-conflict","POST","/reservations",reverse,token=self.a,key="pair-original",status=409,code="idempotency_key_reuse")
        self.expect("pair-key-validation-priority","POST","/reservations",dict(body,table_ids=["missing","t0","t1"]),token=self.a,key="pair-original",status=409,code="idempotency_key_reuse")
        snapshot=self.state()
        imported=self.call("POST","/_test/import",snapshot,base=self.args.peer)[0]
        restored=self.state(base=self.args.peer)
        for aspect in ["configuration","records","tokens","original-receipts"]:
            self.check("pair-import-"+aspect,imported==204 and restored==snapshot)
        self.check("pair-import-original-receipts",self.call("POST","/reservations",body,token=self.a,key="pair-original",base=self.args.peer)==(200,receipt))
        self.setup()
        a=self.create(self.body(["t0","t1"]))
        snapshot=self.state()
        self.call("POST","/_test/import",snapshot,base=self.args.peer)
        self.check("pair-import-occupancy",self.availability(day=DAY,base=self.args.peer)==self.availability(day=DAY))
        payload={"moves":[dict(reference=a["reference"],table_ids=["t1","t2"])]}
        b=self.create(self.body(["t3"]))
        payload["moves"].append(dict(reference=b["reference"],table_ids=["t2"]))
        self.expect("moves-result-overlap","POST","/reservation-moves",payload,token=self.a,key="bad-result",status=409,code="table_unavailable")
        self.setup()
        a=self.create(self.body(["t0","t1"]))
        b=self.create(self.body(["t2","t3"]))
        payload={"moves":[dict(reference=a["reference"],table_ids=["t1","t2"])]}
        self.expect("moves-unlisted-overlap","POST","/reservation-moves",payload,token=self.a,key="bad-unlisted",status=409,code="table_unavailable")
        payload["moves"].append(dict(reference=b["reference"]))
        self.expect("moves-unchanged-occupancy","POST","/reservation-moves",payload,token=self.a,key="bad-unchanged",status=409,code="table_unavailable")
        bad={"moves":[dict(reference=a["reference"],table_ids=["missing"]),dict(reference=b["reference"],table_ids=["t0","t2"])]}
        self.expect("moves-pair-order-errors","POST","/reservation-moves",bad,token=self.a,key="bad-order",status=404,code="not_found")
        bad["moves"].reverse()
        self.expect("moves-pair-order-errors","POST","/reservation-moves",bad,token=self.a,key="bad-order",status=422,code="combination_not_allowed")
        good={"moves":[dict(reference=a["reference"])]}
        self.expect("pair-failed-key-reusable","POST","/reservation-moves",good,token=self.a,key="bad-order",status=201)
        self.expect("pair-failed-key-reusable","POST","/reservations",self.body(["t2"]),token=self.a,key="failed-create",status=409,code="table_unavailable")
        self.expect("pair-failed-key-reusable","POST","/reservations",self.body(["t2"],local=DAY+"T20:10"),token=self.a,key="failed-create",status=201)

    def staged(self, identical):
        self.setup()
        uri=urllib.parse.urlsplit(self.args.base)
        ready=threading.Barrier(51)
        release=threading.Event()
        results=[]
        lock=threading.Lock()
        def send(index):
            ids=["t0","t1"] if identical else [["t0","t1"],["t1","t2"],["t1"]][index%3]
            body=json.dumps(self.body(ids)).encode()
            began=time.monotonic()
            connection=http.client.HTTPConnection(uri.hostname,uri.port,timeout=5)
            connection.putrequest("POST","/reservations")
            for key,value in {"Content-Type":"application/json; charset=utf-8","Content-Length":str(len(body)),"Authorization":"Bearer "+self.a,
                              "Idempotency-Key":"identical" if identical else "competing-"+str(index)}.items():
                connection.putheader(key,value)
            connection.endheaders()
            connection.send(body[:-1])
            ready.wait(timeout=4)
            release.wait(timeout=4)
            connection.send(body[-1:])
            response=connection.getresponse()
            status,value=response.status,json.loads(response.read())
            connection.close()
            with lock:
                finished=time.monotonic()
                results.append(dict(index=index,status=status,body=safe(value),started=began,finished=finished))
            with self.lock:
                self.counter+=1
                self.trace.append(dict(operation=self.counter,method="POST",path="/reservations",peer=self.args.base,body=safe(json.loads(body)),
                                       key="identical" if identical else "competing-"+str(index),status=status,response=safe(value),
                                       duration_seconds=finished-began,request_started_monotonic=began,request_finished_monotonic=finished,staged_final_byte=True))
                self.latencies.append(("/reservations",finished-began,status))
                self.statuses.append(status)
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
            pending=[pool.submit(send,i) for i in range(50)]
            ready.wait(timeout=4)
            released=time.monotonic()
            release.set()
            for future in pending:
                future.result()
        successes=[r for r in results if r["status"]==201]
        expected=200 if identical else 409
        valid=len(successes)==1 and sum(r["status"]==expected for r in results)==49
        if identical and successes:
            valid=valid and all(r["body"]==successes[0]["body"] for r in results)
        records=self.call("GET","/reservations",token=self.a)[1]["reservations"]
        valid=valid and len(records)==1
        valid=valid and all(r["finished"]-r["started"]<5 for r in results)
        self.check("pair-retry-50" if identical else "pair-race-50",valid,"1x201;49x"+str(expected)+";one record",results)
        (self.out/("pair-retry" if identical else "pair-race")).with_suffix(".json").write_text(json.dumps(dict(released=released,prepared=50,operations=results),indent=2))

    def serial(self, moves):
        self.setup()
        a=self.create(self.body(["t0","t1"]))
        initial=[dict(reference=a["reference"],table_ids=["t1","t0"],start=0,end=90,status="confirmed")]
        if moves:
            b=self.create(self.body(["t2","t3"]))
            initial.append(dict(reference=b["reference"],table_ids=["t3","t2"],start=0,end=90,status="confirmed"))
            changes=[dict(reference=a["reference"],table_ids=["t3","t2"]),dict(reference=b["reference"],table_ids=["t1","t0"])]
            plan=[dict(kind="moves",moves=changes),dict(kind="cancel",reference=a["reference"]),dict(kind="read"),dict(kind="read")]
        else:
            plan=[dict(kind="patch",reference=a["reference"],table_ids=["t2","t1"]),
                  dict(kind="create",record=dict(reference="NEW",table_ids=["t0"],start=0,end=90,status="confirmed")),dict(kind="read"),dict(kind="read")]
        restaurant=self.f["restaurants"][0]
        plan.extend([dict(kind="read-availability",tables=restaurant["tables"],pairs=restaurant["combinable"]),dict(kind="read-export")])
        ready=threading.Barrier(len(plan))
        def run(operation):
            ready.wait()
            began=time.monotonic()
            if operation["kind"]=="read":
                status,value=self.call("GET","/reservations",token=self.a)
                observed=dict(status=status,view=sorted((r["reference"],tuple(r["table_ids"]),r["status"]) for r in value.get("reservations",[])))
            elif operation["kind"]=="read-availability":
                value=self.availability(day=DAY)
                status=200
                observed=dict(status=200,options=value["slots"][0].get("available_options"))
            elif operation["kind"]=="read-export":
                snapshot=self.state()
                exported=time.monotonic()
                imported=self.call("POST","/_test/import",snapshot,base=self.args.peer)[0]
                status,value=self.call("GET","/reservations",token=self.a,base=self.args.peer)
                if imported!=204:
                    raise RuntimeError("Concurrent export could not transfer intact state")
                observed=dict(status=status,view=sorted((r["reference"],tuple(r["table_ids"]),r["status"]) for r in value.get("reservations",[])))
            elif operation["kind"]=="moves":
                status,value=self.call("POST","/reservation-moves",{"moves":operation["moves"]},token=self.a,key="serial-moves")
                observed=dict(status=status)
            elif operation["kind"]=="cancel":
                status,value=self.call("POST","/reservations/"+operation["reference"]+"/cancel",{},token=self.a)
                observed=dict(status=status)
            elif operation["kind"]=="patch":
                status,value=self.call("PATCH","/reservations/"+operation["reference"],{"table_ids":operation["table_ids"]},token=self.a)
                observed=dict(status=status)
            else:
                status,value=self.call("POST","/reservations",self.body(["t0"]),token=self.a,key="serial-create")
                observed=dict(status=status)
                if status==201:
                    operation["record"]["reference"]=value["reference"]
            if status>=400:
                observed["code"]=value.get("error",{}).get("code")
            operation.update(started=began,finished=exported if operation["kind"]=="read-export" else time.monotonic(),observed=observed)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(plan)) as pool:
            list(pool.map(run,plan))
        accepted=serial_orders(initial,plan)
        self.check("pair-move-cancel-serial" if moves else "pair-create-patch-serial",bool(accepted),"a serial order respecting real-time completion",dict(operations=plan,orders=accepted))
        self.check("pair-reads-atomic",bool(accepted))
        (self.out/("serial-moves" if moves else "serial-patch")).with_suffix(".json").write_text(json.dumps(dict(initial=initial,operations=plan,accepted_orders=accepted),indent=2))

    def random_case(self):
        self.setup()
        rng=random.Random(20261005)
        restaurant=self.f["restaurants"][0]
        candidates=[[t["id"]] for t in restaurant["tables"]]+restaurant["combinable"]
        records=[]
        for index in range(160):
            start=rng.randrange(8)*30
            ids=rng.choice(candidates)
            party=rng.randrange(1,16)
            capacities={t["id"]:t["capacity"] for t in restaurant["tables"]}
            capacity=sum(capacities[x] for x in ids)
            fits=capacity>=party
            blocked=any(set(ids)&set(record["table_ids"]) and start<record["end"] and record["start"]<start+90 for record in records)
            expected=422 if not fits else 409 if blocked else 201
            clock=dt.datetime.fromisoformat(DAY+"T18:10")+dt.timedelta(minutes=start)
            status,value=self.call("POST","/reservations",self.body(ids,local=clock.strftime("%Y-%m-%dT%H:%M"),party=party),token=self.a,key="random-"+str(index))
            self.check("pair-random-oracle",status==expected,expected,dict(status=status,body=value))
            if status==201:
                records.append(dict(reference=value["reference"],table_ids=value["table_ids"],start=start,end=start+90,status="confirmed"))
            value=self.availability(party=party,day=DAY)
            for slot_index,slot in enumerate(value["slots"]):
                expected_options=options(restaurant["tables"],restaurant["combinable"],records,slot_index*30,slot_index*30+90,party)
                self.check("pair-random-oracle",slot.get("available_options")==expected_options,expected_options,slot)
            self.check("pair-reads-atomic",invariant(records))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True)
    p.add_argument("--peer",required=True)
    p.add_argument("--candidate",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--case",default="all")
    args=p.parse_args()
    if len(args.candidate)!=40 or any(x not in "0123456789abcdef" for x in args.candidate):
        p.error("A full named committed candidate is required.")
    probe=PairProbe(args)
    cases=dict(model=probe.model,fixture=probe.fixture_case,availability=probe.availability_case,validation=probe.validation,responses=probe.responses,
               dst=probe.dst,transactions=probe.transactions,concurrency=lambda:(probe.staged(False),probe.staged(True),probe.serial(False),probe.serial(True)),invariants=probe.random_case)
    for case in cases if args.case=="all" else args.case.split(","):
        try:
            cases[case]()
        except Exception as error:
            probe.results.append(dict(requirement_id="PROBE-CASE-"+case,passed=False,expected="case completes",observed=str(error)))
    raise SystemExit(bool(probe.finish()))


if __name__=="__main__":
    main()
