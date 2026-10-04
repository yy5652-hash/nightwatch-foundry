"""Verify verifier assets only; never calls a candidate or counts product passes."""
import ast
import json
from pathlib import Path
from requirements import ROWS
from oracle import canonical, options, serial_orders
import api


def main():
    root=Path(__file__).resolve().parent
    files=sorted(root.glob("*.py"))
    for path in files:
        ast.parse(path.read_text(),filename=str(path))
    assert len(ROWS)==len({row["requirement_id"] for row in ROWS})
    assert all(row["candidate_full_revision"]=="UNASSIGNED" and row["verdict"]=="unverified" for row in ROWS)
    tables=[dict(id="a",capacity=2),dict(id="b",capacity=4),dict(id="c",capacity=6)]
    pairs=[["b","a"],["c","b"]]
    assert canonical(["a","b"],{x["id"]:x for x in tables},pairs)==(["b","a"],None)
    assert canonical(["a","c"],{x["id"]:x for x in tables},pairs)==(None,"combination_not_allowed")
    assert canonical(["a","a"],{x["id"]:x for x in tables},pairs)==(None,"validation_failed")
    assert options(tables,pairs,[],0,90,5)==[dict(table_ids=["c"],capacity=6),dict(table_ids=["b","a"],capacity=6),dict(table_ids=["c","b"],capacity=10)]
    record=dict(reference="A",table_ids=["b","a"],start=0,end=90,status="confirmed")
    assert options(tables,pairs,[record],90,180,5)==options(tables,pairs,[],90,180,5)
    assert options(tables,pairs,[record],89,179,5)==[dict(table_ids=["c"],capacity=6)]
    operations=[dict(kind="cancel",reference="A",started=1,finished=3,observed=dict(status=200)),
                dict(kind="create",record=dict(reference="B",table_ids=["a"],start=0,end=90,status="confirmed"),started=2,finished=4,observed=dict(status=201))]
    assert serial_orders([record],operations)==[(0,1)]
    operations.append(dict(kind="read-export",started=5,finished=6,observed=dict(status=200,view=[("A",("b","a"),"cancelled"),("B",("a",),"confirmed")])))
    assert serial_orders([record],operations)==[(0,1,2)]
    print(json.dumps(dict(source="verifier preparation controls only",parsed_python_files=len(files),oracle_controls=8,
                          api_import=True,rows=len(ROWS),inherited=sum(row["inherited"]=="yes" for row in ROWS),candidate_calls=0,all_rows_unverified=True)))


if __name__=="__main__":
    main()
