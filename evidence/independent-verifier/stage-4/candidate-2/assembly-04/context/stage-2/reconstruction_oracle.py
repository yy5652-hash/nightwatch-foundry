"""Independent member/interval transaction oracle; no product/helper imports."""
import copy
import itertools
import random

SEED=202610052

def overlap(a,b):
    return a['start'] < b['end'] and b['start'] < a['end']

def members(ids,tables,pairs):
    if not isinstance(ids,list) or any(type(x) is not str for x in ids): return None,'malformed_request'
    if not ids or len(set(ids)) != len(ids): return None,'validation_failed'
    if any(x not in tables for x in ids): return None,'not_found'
    if len(ids)==1: return list(ids),None
    if len(ids)>2: return None,'combination_not_allowed'
    match=next((p for p in pairs if set(p)==set(ids)),None)
    return (list(match),None) if match else (None,'combination_not_allowed')

def fits(records):
    confirmed=[r for r in records if r['status']=='confirmed']
    return all(not(set(a['table_ids']) & set(b['table_ids']) and overlap(a,b)) for a,b in itertools.combinations(confirmed,2))

def available(tables,pairs,records,start,end,party):
    candidates=[[x] for x in tables]+[list(p) for p in pairs]
    interval=dict(start=start,end=end)
    return [dict(table_ids=ids,capacity=sum(tables[x] for x in ids)) for ids in candidates
        if sum(tables[x] for x in ids)>=party and not any(r['status']=='confirmed' and set(ids)&set(r['table_ids']) and overlap(interval,r) for r in records)]

def step(records,op,tables,pairs):
    """Apply one operation; retained immutable fields and error ordering are explicit."""
    next_records=copy.deepcopy(records)
    kind=op['kind']
    if kind=='read': return next_records,dict(status=200,records=copy.deepcopy(next_records))
    if kind=='availability': return next_records,dict(status=200,options=available(tables,pairs,next_records,op['start'],op['end'],op['party_size']))
    if kind=='cancel':
        record=next((r for r in next_records if r['reference']==op['reference'] and r['owner']==op['owner']),None)
        if record is None: return records,dict(status=404,code='not_found')
        if record['status']=='cancelled': return next_records,dict(status=200)
        if op.get('cutoff_passed'): return records,dict(status=409,code='cutoff_passed')
        record['status']='cancelled'; return next_records,dict(status=200)
    changes=[op] if kind!='moves' else op['moves']
    if kind=='moves' and (not 1<=len(changes)<=8 or len({c['reference'] for c in changes})!=len(changes)):
        return records,dict(status=422,code='validation_failed')
    for c in changes:
        if kind=='create': record=copy.deepcopy(c['record'])
        else:
            record=next((r for r in next_records if r['reference']==c['reference'] and r['owner']==op['owner']),None)
            if record is None: return records,dict(status=404,code='not_found')
            if record['status']=='cancelled': return records,dict(status=409,code='reservation_cancelled')
            if c.get('cutoff_passed'): return records,dict(status=409,code='cutoff_passed')
        ids,error=members(c.get('table_ids',record['table_ids']),tables,pairs)
        if error: return records,dict(status=400 if error=='malformed_request' else 404 if error=='not_found' else 422,code=error)
        party=c.get('party_size',record['party_size'])
        if type(party) is not int or party<1: return records,dict(status=422,code='validation_failed')
        if party>sum(tables[t] for t in ids): return records,dict(status=422,code='party_exceeds_capacity')
        record.update(table_ids=ids,party_size=party,start=c.get('start',record['start']),end=c.get('end',record['end']))
        if kind=='create': next_records.append(record)
    if not fits(next_records): return records,dict(status=409,code='table_unavailable')
    return next_records,dict(status=201 if kind in ('create','moves') else 200)

def serial_witness(initial,operations,tables,pairs):
    witnesses=[]
    for order in itertools.permutations(range(len(operations))):
        positions={x:i for i,x in enumerate(order)}
        if any(a['finished']<=b['started'] and positions[i]>positions[j] for i,a in enumerate(operations) for j,b in enumerate(operations) if i!=j): continue
        state=copy.deepcopy(initial)
        for index in order:
            state,result=step(state,operations[index],tables,pairs)
            if any(result.get(k)!=v for k,v in operations[index]['observed'].items()): break
        else: witnesses.append(list(order))
    return witnesses

def seeded_trace(count=160):
    rng=random.Random(SEED); tables={'a':2,'b':4,'c':6,'d':3}; pairs=[['b','a'],['d','c'],['c','b']]
    state=[];trace=[]
    for i in range(count):
        selected=rng.choice([[x] for x in tables]+pairs)
        start=rng.choice([0,30,90,120,180]); party=rng.randrange(1,15)
        if not state or rng.randrange(4)==0:
            op=dict(kind='create',table_ids=selected,record=dict(reference=f'R{i:06}',owner='A',table_ids=selected,party_size=party,start=start,end=start+90,status='confirmed',created_at=i))
        else:
            ref=rng.choice(state)['reference'];kind=rng.choice(['patch','cancel','read','availability','moves'])
            op=dict(kind=kind,owner='A',reference=ref,table_ids=selected,party_size=party,start=start,end=start+90)
            if kind=='moves':op['moves']=[dict(reference=ref,table_ids=selected,party_size=party,start=start,end=start+90)]
        old=copy.deepcopy(state);state,outcome=step(state,op,tables,pairs)
        assert fits(state)
        if outcome['status']>=400: assert state==old
        trace.append(dict(index=i,operation=op,expected=outcome,resulting_records=copy.deepcopy(state)))
    return dict(seed=SEED,scope='reference model construction only; no candidate observations',tables=tables,pairs=pairs,operations=trace)
