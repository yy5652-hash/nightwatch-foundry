"""Genuine frozen Stage 1 -> current Stage 2 state/receipt compatibility."""
import argparse
from api import PairProbe, DAY, fixture


def run(probe):
    legacy=probe.args.legacy
    f=fixture(tables=3)
    probe.setup(f,base=legacy)
    body=dict(restaurant_id="r",table_id="t0",starts_at_local=DAY+"T18:10",party_size=2)
    status,original=probe.call("POST","/reservations",body,token=probe.a,key="genuine-stage1-create",base=legacy)
    if status!=201:
        raise RuntimeError("Frozen Stage 1 create refused")
    second=probe.create(dict(body,table_id="t1"),base=legacy)
    batch={"moves":[dict(reference=original["reference"],table_id="t2"),dict(reference=second["reference"],table_id="t0")]}
    status,batch_receipt=probe.call("POST","/reservation-moves",batch,token=probe.a,key="genuine-stage1-batch",base=legacy)
    if status!=201:
        raise RuntimeError("Frozen Stage 1 batch refused")
    probe.call("POST","/reservations/"+second["reference"]+"/cancel",{},token=probe.a,base=legacy)
    _,before=probe.call("GET","/reservations",token=probe.a,base=legacy)
    snapshot=probe.state(base=legacy)
    probe.check("stage1-genuine-export",snapshot.get("track")=="tablekeeper" and snapshot.get("format_version")==1)
    for destination in [probe.args.base,probe.args.peer]:
        status,_=probe.call("POST","/_test/import",snapshot,base=destination)
        probe.check("stage1-import",status==204)
        _,after=probe.call("GET","/reservations",token=probe.a,base=destination)
        records={value["reference"]:value for value in after.get("reservations",[])}
        for record in before["reservations"]:
            current=records.get(record["reference"],{})
            for field in ["reservation_id","reference","created_at","starts_at","ends_at","status"]:
                probe.check("stage1-record-"+field,current.get(field)==record[field],record[field],current.get(field))
            # Owner is private in the public representation: verify ownership through both real tokens.
            owned=probe.call("GET","/reservations/"+record["reference"],token=probe.a,base=destination)[0]
            private=probe.call("GET","/reservations/"+record["reference"],token=probe.b,base=destination)[0]
            probe.check("stage1-record-user_id",owned==200 and private==404)
        probe.check("stage1-token",probe.call("GET","/reservations",token=probe.a,base=destination)[0]==200 and probe.call("GET","/reservations",token=probe.b,base=destination)[0]==200)
        probe.check("stage1-password",probe.call("POST","/auth/login",dict(email="a@probe.invalid",password="verifier-pass-A"),base=destination)[0]==200)
        probe.check("stage1-original-create",probe.call("POST","/reservations",body,token=probe.a,key="genuine-stage1-create",base=destination)==(200,original))
        probe.check("stage1-original-batch",probe.call("POST","/reservation-moves",batch,token=probe.a,key="genuine-stage1-batch",base=destination)==(200,batch_receipt))


def main():
    parser=argparse.ArgumentParser()
    for field in ["base","peer","legacy","candidate","out"]:
        parser.add_argument("--"+field,required=True)
    args=parser.parse_args()
    args.case="upgrade"
    if len(args.candidate)!=40 or any(c not in "0123456789abcdef" for c in args.candidate):
        parser.error("A full named committed candidate is required.")
    probe=PairProbe(args)
    try:
        run(probe)
    except Exception as error:
        probe.results.append(dict(requirement_id="PROBE-CASE-upgrade",passed=False,expected="case completes",observed=str(error)))
    raise SystemExit(bool(probe.finish()))


if __name__=="__main__":
    main()
