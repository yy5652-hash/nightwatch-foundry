"""Small independent seating and serial-order oracle, with no service imports."""
import copy
import itertools


def overlap(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def canonical(ids, tables, pairs):
    if len(ids) != len(set(ids)) or not ids:
        return None, "validation_failed"
    if any(identifier not in tables for identifier in ids):
        return None, "not_found"
    if len(ids) == 1:
        return list(ids), None
    if len(ids) > 2:
        return None, "combination_not_allowed"
    for pair in pairs:
        if set(ids) == set(pair):
            return list(pair), None
    return None, "combination_not_allowed"


def options(tables, pairs, records, start, end, party):
    candidates = [[table["id"]] for table in tables] + [list(pair) for pair in pairs]
    capacities = {table["id"]: table["capacity"] for table in tables}
    answer = []
    for ids in candidates:
        capacity = sum(capacities[x] for x in ids)
        occupied = any(record["status"] == "confirmed" and set(ids)&set(record["table_ids"])
                       and overlap(start, end, record["start"], record["end"]) for record in records)
        if capacity >= party and not occupied:
            answer.append(dict(table_ids=ids, capacity=capacity))
    return answer


def invariant(records):
    active = [record for record in records if record["status"] == "confirmed"]
    return all(not(set(a["table_ids"])&set(b["table_ids"]) and overlap(a["start"],a["end"],b["start"],b["end"]))
               for a,b in itertools.combinations(active,2))


def step(records, operation):
    """Pure transaction model: integer minute intervals and canonical IDs already valid."""
    current = copy.deepcopy(records)
    kind = operation["kind"]
    if kind in ["read","read-export"]:
        value = [(r["reference"], tuple(r["table_ids"]), r["status"]) for r in current]
        return current, dict(status=200, view=sorted(value))
    if kind == "read-availability":
        value=options(operation["tables"],operation["pairs"],current,0,90,2)
        return current,dict(status=200,options=value)
    if kind == "cancel":
        row = next((r for r in current if r["reference"] == operation["reference"]), None)
        if row is None:
            return records, dict(status=404, code="not_found")
        row["status"] = "cancelled"
        return current, dict(status=200)
    if kind == "create":
        current.append(copy.deepcopy(operation["record"]))
        success = 201
    else:
        changes = operation["moves"] if kind == "moves" else [operation]
        for change in changes:
            row = next((r for r in current if r["reference"] == change["reference"]), None)
            if row is None:
                return records, dict(status=404, code="not_found")
            if row["status"] == "cancelled":
                return records, dict(status=409, code="reservation_cancelled")
            row["table_ids"] = list(change["table_ids"])
        success = 201 if kind == "moves" else 200
    if not invariant(current):
        return records, dict(status=409, code="table_unavailable")
    return current, dict(status=success)


def serial_orders(initial, operations):
    """Exhaustive small oracle; real-time completion constrains each permutation."""
    accepted = []
    for permutation in itertools.permutations(range(len(operations))):
        positions = {index:order for order,index in enumerate(permutation)}
        if any(a["finished"] < b["started"] and positions[i] > positions[j]
               for i,a in enumerate(operations) for j,b in enumerate(operations)):
            continue
        state, valid = copy.deepcopy(initial), True
        for index in permutation:
            state, result = step(state, operations[index])
            observed = operations[index]["observed"]
            if any(result.get(key) != value for key,value in observed.items()):
                valid = False
                break
        if valid:
            accepted.append(permutation)
    return accepted


if __name__ == "__main__":
    tables=[dict(id="a",capacity=2),dict(id="b",capacity=4),dict(id="c",capacity=6)]
    pairs=[["b","a"],["c","b"]]
    assert canonical(["a","b"], {t["id"]:t for t in tables}, pairs) == (["b","a"],None)
    assert canonical(["a","c"], {t["id"]:t for t in tables}, pairs)[1] == "combination_not_allowed"
    assert options(tables,pairs,[],0,90,5) == [dict(table_ids=["c"],capacity=6),dict(table_ids=["b","a"],capacity=6),dict(table_ids=["c","b"],capacity=10)]
    record=dict(reference="A",table_ids=["b","a"],start=0,end=90,status="confirmed")
    assert options(tables,pairs,[record],90,180,5) == options(tables,pairs,[],90,180,5)
    assert options(tables,pairs,[record],89,179,5) == [dict(table_ids=["c"],capacity=6)]
    operations=[dict(kind="cancel",reference="A",started=1,finished=3,observed=dict(status=200)),
                dict(kind="create",record=dict(reference="B",table_ids=["a"],start=0,end=90,status="confirmed"),started=2,finished=4,observed=dict(status=201))]
    assert serial_orders([record],operations) == [(0,1)]
    print("Independent oracle: 6 hand-derived controls passed; no candidate called.")
