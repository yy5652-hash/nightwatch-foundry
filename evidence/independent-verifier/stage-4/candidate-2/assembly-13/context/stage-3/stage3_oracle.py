"""Small independent policy/calendar/history/member reference model.

This is deliberately a finite model of specified state transitions, not a service
implementation. Abstract `editable` controls are model inputs, not an HTTP clock.
All production and builder modules are excluded.
"""
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from itertools import permutations
from zoneinfo import ZoneInfo

UTC=timezone.utc
FIELDS=('slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','opening_hours','capacities')

class Refusal(Exception):
    def __init__(self,code): self.code=code; super().__init__(code)

def terms(policy):
    return {'policy_version':policy['policy_version'],**{k:deepcopy(policy[k]) for k in FIELDS}}

def selected(base,published,local_date):
    eligible=[p for p in published if p['effective_from']<=local_date]
    return deepcopy(max(eligible,key=lambda p:(p['effective_from'],p['policy_version'])) if eligible else base)

def canonical(ids,tables,pairs):
    if len(ids)!=len(set(ids)):raise Refusal('validation_failed')
    if any(t not in tables for t in ids):raise Refusal('not_found')
    if len(ids)==1:return tuple(ids)
    if len(ids)!=2:raise Refusal('combination_not_allowed')
    for pair in pairs:
        if set(pair)==set(ids):return tuple(pair)
    raise Refusal('combination_not_allowed')

def resolve(local,zone):
    naive=datetime.fromisoformat(local)
    tz=ZoneInfo(zone)
    possible=[]
    for fold in (0,1):
        aware=naive.replace(tzinfo=tz,fold=fold)
        instant=aware.astimezone(UTC)
        if instant.astimezone(tz).replace(tzinfo=None)==naive:possible.append(instant)
    if not possible:raise Refusal('invalid_local_time')
    return min(possible) # The first occurrence, independently by absolute order.

def weekly(local,count,interval_weeks):
    d=date.fromisoformat(local[:10]);clock=local[10:]
    return [(d+timedelta(days=i*interval_weeks*7)).isoformat()+clock for i in range(count)]

def interval(local,zone,duration):
    start=resolve(local,zone)
    return start,start+timedelta(minutes=duration)

def conflict(a,b):
    return a.status==b.status=='confirmed' and bool(set(a.seating)&set(b.seating)) and a.start<b.end and b.start<a.end

def changes(before,after):
    result=[]
    if before is None or before.seating!=after.seating:
        pair=len(after.seating)>1 or (before is not None and len(before.seating)>1)
        result.append(dict(field='table_ids' if pair else 'table_id',
            **{'from':None if before is None else list(before.seating) if pair else before.seating[0]},
            to=list(after.seating) if pair else after.seating[0]))
    for field_name in ('starts_at_local','party_size'):
        current=getattr(after,field_name)
        if before is None or getattr(before,field_name)!=current:
            result.append(dict(field=field_name,**{'from':None if before is None else getattr(before,field_name)},to=current))
    return result

@dataclass
class Booking:
    reference:str
    seating:tuple
    starts_at_local:str
    party_size:int
    accepted_terms:dict
    start:datetime
    end:datetime
    revision:int=1
    status:str='confirmed'
    history:list=field(default_factory=list)
    series_id:str|None=None
    exception:bool=False

    def event(self,kind,changed):
        self.history.append(dict(seq=len(self.history)+1,event=kind,changes=deepcopy(changed),
            revision=self.revision,accepted_terms=deepcopy(self.accepted_terms)))

@dataclass
class Agreement:
    series_id:str
    references:list
    interval_weeks:int
    revision:int=1

class Model:
    def __init__(self,tables=('a','b','c'),pairs=(('b','a'),('b','c')),zone='UTC'):
        self.tables=tuple(tables);self.pairs=tuple(tuple(p) for p in pairs);self.zone=zone
        self.base={'policy_version':0,'slot_minutes':30,'reservation_duration_minutes':90,'cancellation_cutoff_minutes':0,
            'opening_hours':[dict(weekday=d,opens='00:00',closes='23:59') for d in ('mon','tue','wed','thu','fri','sat','sun')],
            'capacities':{t:8 for t in tables}}
        self.policies=[];self.bookings={};self.series={};self.restaurant_revision=0

    def snapshot(self):return deepcopy((self.policies,self.bookings,self.series,self.restaurant_revision))

    def publish(self,effective_from,**overrides):
        policy={**deepcopy(self.base),**deepcopy(overrides),'effective_from':effective_from,'policy_version':len(self.policies)+1}
        self.policies.append(policy)
        # The published Stage 3 text only explicitly specifies restaurant counters
        # for adoption and collective moves. Do not invent a publication increment.
        return deepcopy(policy)

    def proposal(self,reference,seating,local,party_size):
        seats=canonical(seating,self.tables,self.pairs)
        policy=selected(self.base,self.policies,local[:10])
        if party_size<1:raise Refusal('validation_failed')
        if party_size>sum(policy['capacities'][t] for t in seats):raise Refusal('party_exceeds_capacity')
        start,end=interval(local,self.zone,policy['reservation_duration_minutes'])
        day=('mon','tue','wed','thu','fri','sat','sun')[date.fromisoformat(local[:10]).weekday()]
        hours=next((h for h in policy['opening_hours'] if h['weekday']==day),None)
        if hours is None:raise Refusal('outside_opening_hours')
        minutes=int(local[11:13])*60+int(local[14:16])
        opening=int(hours['opens'][:2])*60+int(hours['opens'][3:])
        if (minutes-opening)%policy['slot_minutes']:raise Refusal('not_on_slot_grid')
        close=resolve(local[:10]+'T'+hours['closes'],self.zone)
        if minutes<opening or start>=close or end>close:raise Refusal('outside_opening_hours')
        return Booking(reference,seats,local,party_size,terms(policy),start,end)

    def occupy(self,records):
        values=list(records.values())
        if any(conflict(a,b) for i,a in enumerate(values) for b in values[i+1:]):raise Refusal('table_unavailable')

    def create(self,reference,seating,local,party_size):
        item=self.proposal(reference,seating,local,party_size)
        proposed={**self.bookings,reference:item};self.occupy(proposed)
        item.event('created',changes(None,item));self.bookings=proposed
        return deepcopy(item)

    def batch(self,moves,editable=True):
        staged=deepcopy(self.bookings);affected=set();changed=[]
        for move in moves:
            ref=move['reference'];old=self.bookings[ref]
            expected=move.get('expected_revision')
            if expected is not None and expected!=old.revision:raise Refusal('stale_revision')
            if old.status=='cancelled':raise Refusal('reservation_cancelled')
            if not editable:raise Refusal('cutoff_passed')
            seats=canonical(move.get('table_ids',old.seating),self.tables,self.pairs)
            local=move.get('starts_at_local',old.starts_at_local);party=move.get('party_size',old.party_size)
            if (seats,local,party)==(old.seating,old.starts_at_local,old.party_size):continue
            item=self.proposal(ref,seats,local,party)
            item.revision=old.revision+1;item.history=deepcopy(old.history)
            item.series_id=old.series_id;item.exception=old.exception or old.series_id is not None
            item.event('changed',changes(old,item));staged[ref]=item;changed.append(ref)
            if old.series_id:affected.add(old.series_id)
        self.occupy(staged)
        self.bookings=staged
        if changed:self.restaurant_revision+=1
        for sid in affected:self.series[sid].revision+=1
        return changed

    def cancel(self,ref,editable=True):
        old=self.bookings[ref]
        if old.status=='cancelled':return False
        if not editable:raise Refusal('cutoff_passed')
        old.status='cancelled';old.revision+=1;old.event('cancelled',[])
        if old.series_id:self.series[old.series_id].revision+=1
        return True

    def adopt(self,ref,count,interval_weeks,editable=True):
        anchor=self.bookings[ref]
        if anchor.status=='cancelled':raise Refusal('reservation_cancelled')
        if anchor.series_id:raise Refusal('already_in_series')
        if not editable:raise Refusal('cutoff_passed')
        sid='agreement-'+str(len(self.series)+1)
        staged=deepcopy(self.bookings);refs=[ref]
        for i,local in enumerate(weekly(anchor.starts_at_local,count,interval_weeks)[1:],1):
            newref=ref+'-'+str(i)
            item=self.proposal(newref,anchor.seating,local,anchor.party_size)
            # Validate progressively, so the first failing index determines error.
            self.occupy({**staged,newref:item})
            item.event('created',changes(None,item));staged[newref]=item;refs.append(newref)
        for member in refs:staged[member].series_id=sid
        self.bookings=staged;self.series[sid]=Agreement(sid,refs,interval_weeks);self.restaurant_revision+=1
        return sid

def serial_histories(initial,operations,observations):
    """Exhaustively enumerate small atomic operation orders against saved reads.

    Each operation callable acts on a copied finite model and returns an observed
    public result. Bounds and real request interval precedence are supplied by the
    independent future client, never the production solver.
    """
    legal=[]
    for order in permutations(range(len(operations))):
        model=deepcopy(initial);results={}
        for i in order:
            try:results[i]=operations[i](model)
            except Refusal as error:results[i]=error.code
        if all(results[i]==expected for i,expected in observations.items()):legal.append(list(order))
    return legal
