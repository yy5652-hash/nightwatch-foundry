"""Independent observable-state oracle and deterministic bounded race schedule.

No private export schema or product implementation is used. Generation g moves
all eight records together, so any mixture of generations is observably invalid.
"""
import random
from semantic_oracle import Number,same

SEED=20261004
MODES=("send-barrier","first-byte-held","send-held")
WAVES=4
STEPS=3
MEMBERS=8
PAD_BYTES=16384
IMMUTABLE=("reservation_id","reference","restaurant_id","starts_at_local","starts_at","ends_at","created_at","status")

def schedule():
    rng=random.Random(SEED);result=[]
    for mode in MODES:
        for wave in range(WAVES):
            routes=["export","list","availability"];rng.shuffle(routes)
            result.append(dict(mode=mode,wave=wave,lower=wave*STEPS,upper=(wave+1)*STEPS,
                               route_launch_order=routes,write_generations=list(range(wave*STEPS+1,(wave+1)*STEPS+1))))
    return result

def table_for(index,generation):return "t"+str((index+generation)%MEMBERS)

def projected(originals,generation):
    return [dict(record,table_id=table_for(index,generation),party_size=generation+2) for index,record in enumerate(originals)]

def generation_of(records,originals,lower,upper):
    if not isinstance(records,list) or len(records)!=MEMBERS:return None
    indexed={record.get("reference"):record for record in records if isinstance(record,dict)}
    if len(indexed)!=MEMBERS or set(indexed)!={record["reference"] for record in originals}:return None
    first=indexed[originals[0]["reference"]].get("party_size")
    if isinstance(first,Number):
        try:generation=first.small_integer()-2
        except ValueError:return None
    elif type(first) is int:generation=first-2
    else:return None
    if not lower<=generation<=upper:return None
    expected=projected(originals,generation)
    if not all(same(indexed[record["reference"]],record) for record in expected):return None
    return generation

def identities_retained(records,originals):
    if not isinstance(records,list):return False
    indexed={record.get("reference"):record for record in records if isinstance(record,dict)}
    return len(indexed)==MEMBERS and all(record["reference"] in indexed and
        all(same(indexed[record["reference"]].get(field),record.get(field)) for field in IMMUTABLE) for record in originals)

def expected_availability():
    # Independent half-open minutes oracle: eight tables are occupied [1080,1170).
    slots=[]
    for start in range(1080,1380-90+1,30):
        overlap=start<1170 and 1080<start+90
        slots.append(dict(starts_at_local="2035-06-04T"+f"{start//60:02d}:{start%60:02d}",
                          starts_at="2035-06-04T"+f"{start//60:02d}:{start%60:02d}:00+00:00",
                          available_table_ids=[] if overlap else ["t"+str(i) for i in range(MEMBERS)]))
    return dict(restaurant_id="r",date="2035-06-04",timezone="UTC",slots=slots)

def synthetic_originals():
    # Local oracle inputs only. These are never submitted as exported service state.
    return [dict(reservation_id="local-res-"+str(i),reference="LOCAL"+str(i).zfill(3),restaurant_id="r",
        table_id="t"+str(i),party_size=2,status="confirmed",starts_at_local="2035-06-04T18:00",
        starts_at="2035-06-04T18:00:00+00:00",ends_at="2035-06-04T19:30:00+00:00",
        created_at="2026-10-04T00:00:00+00:00") for i in range(MEMBERS)]

def self_check():
    checks=[];originals=synthetic_originals()
    def check(label,value):
        checks.append(dict(case=label,passed=bool(value)))
        if not value:raise AssertionError(label)
    for generation in range(WAVES*STEPS+1):
        records=projected(originals,generation)
        check("legal-generation-"+str(generation),generation_of(list(reversed(records)),originals,0,WAVES*STEPS)==generation)
        check("identities-"+str(generation),identities_retained(records,originals))
        if generation:
            mixed=list(records);mixed[3]=projected(originals,generation-1)[3]
            check("reject-mixed-generation-"+str(generation),generation_of(mixed,originals,0,WAVES*STEPS) is None)
    controls={"party-boolean":dict(projected(originals,1)[0],party_size=True),
              "identity-change":dict(projected(originals,1)[0],reservation_id="changed"),
              "table-alias":dict(projected(originals,1)[0],table_id="t0")}
    for label,changed in controls.items():
        records=projected(originals,1);records[0]=changed
        check("reject-"+label,generation_of(records,originals,0,WAVES*STEPS) is None)
    check("reject-outside-interval",generation_of(projected(originals,4),originals,0,3) is None)
    check("reject-missing-record",generation_of(projected(originals,1)[:-1],originals,0,3) is None)
    check("reject-duplicate-reference",generation_of(projected(originals,1)[:-1]+[projected(originals,1)[0]],originals,0,3) is None)
    check("schedule-repeatable",schedule()==schedule() and len(schedule())==len(MODES)*WAVES)
    check("half-open-availability",len(expected_availability()["slots"])==8 and expected_availability()["slots"][2]["available_table_ids"]==[] and expected_availability()["slots"][3]["available_table_ids"]==["t"+str(i) for i in range(MEMBERS)])
    return checks
