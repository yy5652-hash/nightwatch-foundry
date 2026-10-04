"""Finite reference oracle independently derived from Stage4, not service code.

Exact closure instants use Fraction seconds. Reference state is in memory only;
serialized model traces are constructions, never opaque production exports.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from itertools import product
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage-3'))
from stage3_oracle import Refusal, resolve, selected, terms, changes

GRAMMAR=re.compile(r'^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$')
EPOCH=date(1970,1,1).toordinal()

def instant(text):
    """Independent tested RFC3339 subset; arbitrary fractional precision retained.

    Leap seconds and broader input grammar require separate source reconciliation;
    this helper is not used to declare their HTTP verdicts.
    """
    m=GRAMMAR.fullmatch(text)
    if not m:raise Refusal('validation_failed')
    d,h,minute,sec,fraction,offset=m.groups()
    try:
        day=date.fromisoformat(d);h=int(h);minute=int(minute);sec=int(sec)
        if h>23 or minute>59 or sec>59:raise ValueError('clock')
        off=0
        if offset!='Z':
            oh,om=int(offset[1:3]),int(offset[4:6])
            if oh>23 or om>59:raise ValueError('offset')
            off=(oh*3600+om*60)*(1 if offset[0]=='+' else -1)
        return Fraction((day.toordinal()-EPOCH)*86400+h*3600+minute*60+sec-off)+(Fraction(int(fraction),10**len(fraction)) if fraction else 0)
    except (ValueError,OverflowError):raise Refusal('validation_failed')

def overlap(a,b):return a['start']<b['end'] and b['start']<a['end']
def members(record):return frozenset(record['seating'])
def occupied(a,b):return a.get('status','confirmed')==b.get('status','confirmed')=='confirmed' and bool(members(a)&members(b)) and overlap(a,b)
def forbidden(record,seats,closures):
    return any(c['table_id'] in seats and overlap(record,c) for c in closures)

def options(tables,pairs):return tuple((t,) for t in tables)+tuple(tuple(p) for p in pairs)
def objective(records,choices,all_options):
    return (sum(frozenset(s)!=members(b) for b,s in zip(records,choices)),
            sum(sum(b['accepted_terms']['capacities'][t] for t in s)-b['party_size'] for b,s in zip(records,choices)),
            tuple(all_options.index(s) for s in choices))

def seating_plan(tables,pairs,bookings,closures,proposed):
    """Enumerate complete assignments with feasibility pruning, no mutation.

    Supports full6/4/6. Larger reference problems raise planning_limit; service
    may instead correctly support a larger problem under the published contract.
    """
    all_options=options(tables,pairs)
    considered=sorted((b for b in bookings if b.get('status','confirmed')=='confirmed' and overlap(b,proposed)),key=lambda b:b['reference'])
    fixed=[b for b in bookings if b not in considered and b.get('status','confirmed')=='confirmed']
    if len(tables)>6 or len(pairs)>4 or len(considered)>6:raise Refusal('planning_limit')
    viable=[]
    for b in considered:
        choices=[]
        for s in all_options:
            if sum(b['accepted_terms']['capacities'][t] for t in s)<b['party_size']:continue
            if forbidden(b,s,[*closures,proposed]):continue
            if any(bool(set(s)&members(f)) and overlap(b,f) for f in fixed):continue
            choices.append(s)
        if not choices:raise Refusal('no_feasible_plan')
        viable.append(choices)
    best=None;winner=None;visited=0
    def walk(index,chosen):
        nonlocal best,winner,visited
        if index==len(considered):
            visited+=1;score=objective(considered,chosen,all_options)
            if best is None or score<best:best=score;winner=tuple(chosen)
            return
        b=considered[index]
        for s in viable[index]:
            if any(bool(set(s)&set(previous)) and overlap(b,considered[j]) for j,previous in enumerate(chosen)):continue
            walk(index+1,(*chosen,s))
    walk(0,())
    if winner is None:raise Refusal('no_feasible_plan')
    return dict(assignments=[dict(reference=b['reference'],table_ids=list(s),changed=frozenset(s)!=members(b)) for b,s in zip(considered,winner)],
                moved_count=best[0],unused_seats=best[1],rank_vector=list(best[2]),feasible_complete_assignments=visited)

def cartesian_control(tables,pairs,bookings,closures,proposed):
    """Separate unpruned full-product control for small oracle constructions."""
    records=sorted([b for b in bookings if b.get('status','confirmed')=='confirmed' and overlap(b,proposed)],key=lambda b:b['reference'])
    fixed=[b for b in bookings if b not in records and b.get('status','confirmed')=='confirmed']
    opts=options(tables,pairs);feasible=[]
    for choices in product(opts,repeat=len(records)):
        valid=True
        for i,(b,s) in enumerate(zip(records,choices)):
            if sum(b['accepted_terms']['capacities'][t] for t in s)<b['party_size'] or forbidden(b,s,[*closures,proposed]):valid=False;break
            if any(bool(set(s)&members(f)) and overlap(b,f) for f in fixed):valid=False;break
            if any(bool(set(s)&set(choices[j])) and overlap(b,records[j]) for j in range(i)):valid=False;break
        if valid:feasible.append(objective(records,choices,opts))
    return min(feasible) if feasible else None

def booking(ref,seats,start,end,capacities,party=1,**kw):
    result=dict(reference=ref,reservation_id='id-'+ref,owner='u',seating=tuple(seats),start=Fraction(start),end=Fraction(end),
                party_size=party,status='confirmed',accepted_terms=dict(policy_version=0,capacities=dict(capacities)),revision=1,history=[],
                series_id=None,exception=False,created_at='original')
    result.update(deepcopy(kw));return result

class State:
    """Finite transition model, not a transport or production state schema."""
    def __init__(self,tables,pairs,bookings=(),closures=()):
        self.tables=tuple(tables);self.pairs=tuple(tuple(p) for p in pairs)
        self.bookings={b['reference']:deepcopy(b) for b in bookings};self.closures=deepcopy(list(closures));self.plans={}
        self.restaurant_revision=0;self.series={}
    def snapshot(self):return deepcopy(vars(self))
    def preview(self,proposed):
        if proposed['start']>=proposed['end']:raise Refusal('validation_failed')
        if proposed['table_id'] not in self.tables:raise Refusal('not_found')
        result=seating_plan(self.tables,self.pairs,list(self.bookings.values()),self.closures,proposed)
        pid='plan-'+str(len(self.plans)+1)
        plan=dict(plan_id=pid,restaurant_revision=self.restaurant_revision,closure=deepcopy(proposed),**result,applied=False)
        self.plans[pid]=plan;return deepcopy(plan)
    def apply(self,pid):
        if pid not in self.plans:raise Refusal('not_found')
        p=self.plans[pid]
        if p['applied']:raise Refusal('plan_already_applied')
        if p['restaurant_revision']!=self.restaurant_revision:raise Refusal('stale_plan')
        staged=deepcopy(self.bookings);affected=set()
        for assignment in p['assignments']:
            b=staged[assignment['reference']]
            if not assignment['changed']:continue
            old=list(b['seating']);b['seating']=tuple(assignment['table_ids']);b['revision']+=1
            b['history'].append(dict(seq=len(b['history'])+1,event='reassigned',revision=b['revision'],accepted_terms=deepcopy(b['accepted_terms']),
                changes=[dict(field='table_ids',**{'from':old},to=list(b['seating']))],plan_id=pid))
            if b['series_id']:affected.add(b['series_id'])
        self.bookings=staged;self.closures.append(deepcopy(p['closure']));self.restaurant_revision+=1
        for sid in affected:self.series[sid]['revision']+=1
        p['applied']=True
        return dict(plan_id=pid,restaurant_revision=self.restaurant_revision,reservations=[deepcopy(staged[a['reference']]) for a in p['assignments']])

    def amend(self,sid,expected,from_index,clock,base,published,zone='UTC',now=Fraction(-10**20)):
        if sid not in self.series:raise Refusal('not_found')
        s=self.series[sid]
        if isinstance(expected,bool) or not isinstance(expected,int) or expected<1:raise Refusal('validation_failed')
        if isinstance(from_index,bool) or not isinstance(from_index,int) or not 0<=from_index<len(s['references']):raise Refusal('validation_failed')
        if not isinstance(clock,str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',clock):raise Refusal('validation_failed')
        if expected!=s['revision']:raise Refusal('stale_revision')
        staged=deepcopy(self.bookings);changed=[]
        for index,ref in enumerate(s['references']):
            old=self.bookings[ref]
            if index<from_index or old['status']=='cancelled' or old['exception']:continue
            local=s['scheduled_dates'][index]+'T'+clock
            if local==old['starts_at_local']:continue
            cutoff=old['accepted_terms']['cancellation_cutoff_minutes']*60
            if now>=old['start']-cutoff:raise Refusal('cutoff_passed')
            pol=selected(base,published,local[:10]);seats=old['seating']
            if old['party_size']>sum(pol['capacities'][t] for t in seats):raise Refusal('party_exceeds_capacity')
            start_dt=resolve(local,zone);end_dt=start_dt+timedelta(minutes=pol['reservation_duration_minutes'])
            start=instant(start_dt.isoformat());end=instant(end_dt.isoformat())
            weekday=('mon','tue','wed','thu','fri','sat','sun')[date.fromisoformat(local[:10]).weekday()]
            hours=next((h for h in pol['opening_hours'] if h['weekday']==weekday),None)
            if hours is None:raise Refusal('outside_opening_hours')
            minutes=int(clock[:2])*60+int(clock[3:]);opening=int(hours['opens'][:2])*60+int(hours['opens'][3:])
            if (minutes-opening)%pol['slot_minutes']:raise Refusal('not_on_slot_grid')
            close=instant(resolve(local[:10]+'T'+hours['closes'],zone).isoformat())
            if minutes<opening or start>=close or end>close:raise Refusal('outside_opening_hours')
            b=staged[ref];b.update(starts_at_local=local,start=start,end=end,accepted_terms=terms(pol),revision=old['revision']+1)
            b['history'].append(dict(seq=len(old['history'])+1,event='changed',revision=b['revision'],accepted_terms=deepcopy(b['accepted_terms']),
                changes=[dict(field='starts_at_local',**{'from':old['starts_at_local']},to=local)]))
            changed.append(ref)
        records=list(staged.values())
        for i,b in enumerate(records):
            if b['status']!='confirmed':continue
            if forbidden(b,b['seating'],self.closures) or any(occupied(b,x) for x in records[i+1:]):raise Refusal('table_unavailable')
        if changed:
            self.bookings=staged;s['revision']+=1;self.restaurant_revision+=1
        return changed

def serial_orders(initial,operations,outcomes):
    """Small exhaustive observed-history oracle; caller supplies finite actions."""
    from itertools import permutations
    matches=[]
    for order in permutations(range(len(operations))):
        state=deepcopy(initial);actual={}
        for i in order:
            try:actual[i]=operations[i](state)
            except Refusal as error:actual[i]=error.code
        if actual==outcomes:matches.append(list(order))
    return matches
