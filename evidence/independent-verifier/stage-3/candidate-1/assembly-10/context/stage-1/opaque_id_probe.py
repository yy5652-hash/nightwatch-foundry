"""Prepared encoded-ID HTTP probes; no service executes during preparation."""
import argparse
import json
import re
import time
from pathlib import Path
from opaque_id_requirements import CASES,OBLIGATIONS,VARIANTS,availability_path,detail_path,fixture
from semantic_oracle import same
from semantic_probe import Probe,safe

class IdProbe(Probe):
    def check(self,key,condition,expected=None,observed=None):
        assert key in CASES,key
        self.results.append(dict(requirement_id=CASES[key]["requirement_id"],passed=bool(condition),expected=safe(expected),observed=safe(observed)))
    def scenario(self,surface,label,value):
        stem=surface+"-"+label;f=fixture(surface,value)
        restaurant=f["restaurants"][0];rid=restaurant["id"];tables=[table["id"] for table in restaurant["tables"]]
        reset=self.call("POST","/_test/reset",f)
        # Admission is a separately saved source diagnostic. Until format
        # applicability is resolved, a refusal is not relabelled as a defect.
        self.admissions.append(dict(requirement_id=CASES[stem+"-admission"]["requirement_id"],surface=surface,label=label,fixture_id=value,characters=len(value),utf8_bytes=len(value.encode()),status=reset.status,source_applicability="accepted IDs usable" if reset.status==204 else "requires chosen-format/source adjudication",verdict="unverified"))
        if reset.status!=204:return
        listing=self.call("GET","/restaurants")
        self.check(stem+"-list",listing.status==200 and [r.get("id") for r in listing.data.get("restaurants",[])]==[rid],rid,listing.data)
        detail=self.call("GET",detail_path(rid))
        self.check(stem+"-detail-status",detail.status==200,200,detail.status)
        self.check(stem+"-detail-identity",detail.status==200 and detail.data.get("id")==rid and [t.get("id") for t in detail.data.get("tables",[])]==tables,dict(restaurant=rid,tables=tables),detail.data)
        available=self.call("GET",availability_path(rid))
        self.check(stem+"-availability",available.status==200 and available.data.get("restaurant_id")==rid and len(available.data.get("slots",[]))==8 and all(slot.get("available_table_ids")==tables for slot in available.data.get("slots",[])),dict(restaurant=rid,tables=tables),available.data)
        login=self.call("POST","/auth/login",dict(email="semantic@probe.invalid",password="semantic-probe-pass"))
        if login.status!=200:
            self.errors.append(dict(case=stem,phase="seeded authentication",status=login.status));return
        token=login.data["token"]
        body=dict(restaurant_id=rid,table_id=tables[0],starts_at_local="2035-06-04T18:00",party_size=2)
        created=self.call("POST","/reservations",body,token=token,key="opaque-create")
        self.check(stem+"-create-status",created.status==201,201,created.status)
        valid=created.status==201 and created.data.get("restaurant_id")==rid and created.data.get("table_id")==tables[0] and re.fullmatch(r"[A-Z0-9]{6,12}",created.data.get("reference","")) is not None
        self.check(stem+"-create-identity",valid,dict(restaurant=rid,table=tables[0]),created.data)
        if not valid:return
        ref=created.data["reference"];identity=created.data["reservation_id"]
        replay=self.call("POST","/reservations",body,token=token,key="opaque-create")
        self.check(stem+"-create-replay",replay.status==200 and same(replay.data,created.data))
        lookup=self.call("GET","/reservations/"+ref,token=token)
        self.check(stem+"-lookup",lookup.status==200 and same(lookup.data,created.data))
        amended=self.call("PATCH","/reservations/"+ref,dict(table_id=tables[1]),token=token)
        self.check(stem+"-amend",amended.status==200 and amended.data.get("restaurant_id")==rid and amended.data.get("table_id")==tables[1] and amended.data.get("reference")==ref and amended.data.get("reservation_id")==identity)
        moved=self.call("POST","/reservation-moves",dict(moves=[dict(reference=ref,table_id=tables[0])]),token=token,key="opaque-move")
        records=moved.data.get("reservations",[]) if isinstance(moved.data,dict) else []
        self.check(stem+"-moves",moved.status==201 and len(records)==1 and records[0].get("restaurant_id")==rid and records[0].get("table_id")==tables[0] and records[0].get("reservation_id")==identity and records[0].get("reference")==ref)
        snapshot=self.snapshot();imported=self.call("POST","/_test/import",raw=snapshot.raw,base=self.args.peer)
        current=self.call("GET","/reservations/"+ref,token=token,base=self.args.peer)
        self.check(stem+"-import-current",imported.status==204 and current.status==200 and current.data.get("restaurant_id")==rid and current.data.get("table_id")==tables[0] and current.data.get("reservation_id")==identity and current.data.get("reference")==ref)
        original=self.call("POST","/reservations",body,token=token,key="opaque-create",base=self.args.peer)
        self.check(stem+"-import-original",original.status==200 and same(original.data,created.data))
        cancelled=self.call("POST","/reservations/"+ref+"/cancel",{},token=token,base=self.args.peer)
        freed=self.call("GET",availability_path(rid),base=self.args.peer)
        self.check(stem+"-cancel-release",cancelled.status==200 and cancelled.data.get("status")=="cancelled" and freed.status==200 and freed.data.get("restaurant_id")==rid and len(freed.data.get("slots",[]))==8 and all(slot.get("available_table_ids")==tables for slot in freed.data.get("slots",[])))
        unknown=self.call("GET",detail_path("missing route?%/餐厅"))
        self.check(stem+"-unknown-route",unknown.status==404 and unknown.data.get("error",{}).get("code")=="not_found")
    def finish(self):
        rows=[]
        for case in CASES.values():
            found=[result for result in self.results if result["requirement_id"]==case["requirement_id"]]
            rows.append(dict(**case,verdict="unverified" if not found else "verified" if all(result["passed"] for result in found) else "failed"))
        summary=dict(candidate=self.args.candidate,kind="independent accepted opaque-ID HTTP",requests=len(self.trace),assertions=len(self.results),failed_assertions=sum(not result["passed"] for result in self.results),normative_rows=sum(row["normative"] for row in rows),admission_diagnostic_rows=len(self.admissions),
                     verified=sum(row["verdict"]=="verified" for row in rows),failed=sum(row["verdict"]=="failed" for row in rows),unverified=sum(row["verdict"]=="unverified" for row in rows),flow_errors=self.errors,duration_seconds=time.monotonic()-self.started,
                     max_ordinary_seconds=max((item["duration_seconds"] for item in self.trace if not item["path"].startswith("/_test/")),default=0),max_control_seconds=max((item["duration_seconds"] for item in self.trace if item["path"].startswith("/_test/")),default=0))
        for name,data in [("trace.json",self.trace),("assertions.json",self.results),("admission-diagnostics.json",self.admissions),("coverage-observed.json",rows),("summary.json",summary)]:
            (self.out/name).write_text(json.dumps(data,indent=2))
        print(json.dumps(summary));return bool(summary["failed_assertions"] or summary["flow_errors"])

def main():
    parser=argparse.ArgumentParser()
    for name in ["base","peer","candidate","out"]:parser.add_argument("--"+name,required=True)
    args=parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}",args.candidate) is None:parser.error("full named final candidate required")
    probe=IdProbe(args);probe.admissions=[]
    for surface in ["restaurant","table"]:
        for label,value in VARIANTS.items():
            try:probe.scenario(surface,label,value)
            except Exception as error:probe.errors.append(dict(case=surface+"-"+label,type=type(error).__name__,message=str(error)))
    raise SystemExit(1 if probe.finish() else 0)

if __name__=="__main__":main()
