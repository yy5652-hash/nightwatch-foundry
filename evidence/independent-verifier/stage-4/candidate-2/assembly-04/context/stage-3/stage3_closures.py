"""Independently executed row-level closures after the coverage gap audit.

Opaque state remains unchanged bytes in memory. Equality of before/after exports
establishes failure rollback of all private counters as well as public records.
No private payload is saved and no production helper is used.
"""
import argparse,json
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
from stage3_probe import Client,fixture,policy,create_body,same,integer,validate_release,DAY

def multi(c,names,condition):
 for name in names.split(','):c.check(name,condition)
def run(c):
 c.setup();p=c.create(seats=('a','b'),party=9)
 h=c.history(p['reference'])['entries']
 c.check('history-pair-created',same(h[0]['changes'][0],dict(field='table_ids',**{'from':None,'to':['b','a']})))
 before=c.history(p['reference']);c.response('history-replay-entry',c.call('POST','/reservations',create_body(('a','b'),party=9),token=c.tokens['u'],key='create'),200)
 c.check('history-replay-entry',same(before,c.history(p['reference'])))
 for party,cap in [(2,True),(9,False)]:
  slots=c.response('explain-true',c.call('GET','/availability?restaurant_id=r&date='+DAY+'&party_size='+str(party)+'&explain=true'),200)['slots']
  for free,clock in [(False,'18:00'),(True,'21:00')]:
   row=next(s for s in slots if s['starts_at_local'].endswith(clock))['explain'][0]
   c.check('explain-truth-'+str(int(cap))+str(int(free)),same(row['rules'],[dict(rule='capacity',holds=cap),dict(rule='no_overlap',holds=free)]) and row['available'] is (cap and free))
  row=next(s for s in slots if s['starts_at_local'].endswith('18:00'))['explain']
  c.check('explain-pair-members',all(t['rules'][1]['holds'] is False for t in row[:2]))
 c.setup();anchor=c.create();body=dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1,ignored={'finite':123,'array':[False,None]})
 # Same literal key belongs independently to a user and an HTTP path.
 other=c.response('setup-create',c.call('POST','/reservations',create_body(('b',)),token=c.tokens['v'],key='other'),201)
 s=c.response('series-owned-confirmed',c.call('POST','/series',body,token=c.tokens['u'],key='shared'),201)
 sv=c.response('series-series-retry-scoped-user',c.call('POST','/series',dict(anchor_reference=other['reference'],count=2,interval_weeks=1),token=c.tokens['v'],key='shared'),201)
 r=c.response('series-series-retry-scoped-path',c.call('POST','/reservations',create_body(('c',)),token=c.tokens['u'],key='shared'),201)
 multi(c,'series-adopts-anchor,series-unknown-fields,series-same-clock,series-own-duration,series-ordinary-occupancy',
       same(s['occurrences'][0]['reservation'],anchor) and s['series_id']!=sv['series_id'] and r['reference']!=anchor['reference'] and all(o['reservation']['starts_at_local'].endswith('18:00') and (datetime.fromisoformat(o['reservation']['ends_at'])-datetime.fromisoformat(o['reservation']['starts_at'])).total_seconds()==5400 for o in s['occurrences']))
 for token,ref,status,code,name in [(None,anchor['reference'],401,'unauthenticated','no-token'),(c.tokens['u'],'MISSING',404,'not_found','unknown-anchor'),(c.tokens['v'],anchor['reference'],404,'not_found','other-owner')]:
  c.response('series-'+name,c.call('POST','/series',dict(anchor_reference=ref,count=2,interval_weeks=1),token=token,key='boundary-'+name),status,code)
 c.response('series-cancelled-anchor',c.call('POST','/reservations/'+r['reference']+'/cancel',{},token=c.tokens['u']),200)
 c.response('series-cancelled-anchor',c.call('POST','/series',dict(anchor_reference=r['reference'],count=2,interval_weeks=1),token=c.tokens['u'],key='cancelled'),409,'reservation_cancelled')
 history=c.history(r['reference']);c.response('history-repeat-cancel',c.call('POST','/reservations/'+r['reference']+'/cancel',{},token=c.tokens['u']),200)
 c.check('history-repeat-cancel',same(history,c.history(r['reference'])))
 # Whole raw snapshot equality closes each separately numbered rollback atom.
 for scenario in ['capacity','grid','closed','outside','occupied-single','occupied-pair','gap','first-capacity-second-gap','first-gap-second-occupied']:
  special='gap' in scenario;f=fixture('Europe/Berlin' if special else 'UTC');c.setup(f)
  local='2035-03-11T02:30' if scenario=='first-capacity-second-gap' else '2035-03-18T02:30' if special else DAY+'T18:00'
  a=c.create(seats=('b','a'),local=local,party=5);block=None;pol=None
  if scenario in ('capacity','grid','closed','outside'):
   pol=policy('2035-06-11')
   if scenario=='capacity':pol['capacities']=dict(a=1,b=1,c=6)
   if scenario=='grid':pol.update(slot_minutes=75,opening_hours=[dict(weekday=d,opens='17:00',closes='23:59') for d in ('mon','tue','wed','thu','fri','sat','sun')])
   if scenario=='closed':pol['opening_hours']=[]
   if scenario=='outside':pol['opening_hours']=[dict(weekday=d,opens='19:00',closes='23:59') for d in ('mon','tue','wed','thu','fri','sat','sun')]
  elif scenario.startswith('occupied'):block=c.create(seats=('a',) if scenario=='occupied-single' else ('b','a'),local='2035-06-11T18:00',key='block')
  elif scenario=='first-capacity-second-gap':pol=policy('2035-03-18',capacities=dict(a=1,b=1,c=6))
  elif scenario=='first-gap-second-occupied':block=c.create(local='2035-04-01T02:30',key='block')
  if pol:c.response('setup-policies',c.call('POST','/restaurants/r/policies',pol,token=c.tokens['m'],key='block-policy'),201)
  body=dict(anchor_reference=a['reference'],count=3,interval_weeks=1);before=c.export()
  code='party_exceeds_capacity' if 'capacity' in scenario else 'invalid_local_time' if special else 'not_on_slot_grid' if scenario=='grid' else 'outside_opening_hours' if scenario in ('closed','outside') else 'table_unavailable'
  c.response('series-first-failure',c.call('POST','/series',body,token=c.tokens['u'],key='failed'),409 if code=='table_unavailable' else 422,code)
  after=c.export();unchanged=before==after
  for field in ['records','history','series','versions']:c.check('series-reject-'+scenario+'-'+field,unchanged)
  c.trace.append(dict(event='rollback-whole-raw-snapshot',scenario=scenario,before_sha256=__import__('hashlib').sha256(before).hexdigest(),after_sha256=__import__('hashlib').sha256(after).hexdigest(),bytes=len(before),decoded=False,equal=unchanged))
  if block:c.response('setup-cancel',c.call('POST','/reservations/'+block['reference']+'/cancel',{},token=c.tokens['u']),200)
  if pol:c.response('setup-policies',c.call('POST','/restaurants/r/policies',policy(pol['effective_from']),token=c.tokens['m'],key='repair'),201)
  if special:c.response('setup-patch',c.call('PATCH','/reservations/'+a['reference'],dict(starts_at_local=local[:10]+'T03:30'),token=c.tokens['u']),200)
  c.response('series-reject-'+scenario+'-key',c.call('POST','/series',body,token=c.tokens['u'],key='failed'),201)
 # Current response terms and matching optimistic revisions, separately read.
 c.setup();a=c.create();path='/reservations/'+a['reference']
 multi(c,'terms-lookup-current,terms-list-current',all('revision' in r and 'accepted_terms' in r for r in [c.lookup(a['reference']),*c.public_state()['reservations']['reservations']]))
 before=c.export();c.response('terms-expected-match',c.call('PATCH',path,dict(expected_revision=1),token=c.tokens['u']),200)
 c.check('terms-expected-noop',before==c.export())
 c.response('terms-expected-stale',c.call('PATCH',path,dict(expected_revision=2),token=c.tokens['u']),409,'stale_revision')
 c.response('setup-policies',c.call('POST','/restaurants/r/policies',policy(reservation_duration_minutes=30),token=c.tokens['m'],key='p'),201)
 moved=c.response('setup-moves',c.call('POST','/reservation-moves',dict(moves=[dict(reference=a['reference'],table_ids=['b','a'],party_size=6)]),token=c.tokens['u'],key='moves'),201)['reservations'][0]
 multi(c,'terms-moves-current,terms-pair-capacity,terms-amend-new-end,moves-new-policy,moves-optional-revision,moves-changed-event',integer(moved['revision'])==2 and integer(moved['accepted_terms']['policy_version'])==1 and integer(moved['party_size'])==6 and moved['table_ids']==['b','a'] and (datetime.fromisoformat(moved['ends_at'])-datetime.fromisoformat(moved['starts_at'])).total_seconds()==1800 and len(c.history(a['reference'])['entries'])==2)
 for change in [dict(party_size=99),dict(table_ids=['c'],party_size=7)]:
  snapshot=c.export();c.response('moves-all-fields',c.call('POST','/reservation-moves',dict(moves=[dict(reference=a['reference'],**change)]),token=c.tokens['u'],key='failure'),422,'party_exceeds_capacity')
  for field in ['terms','histories','revisions','exceptions']:c.check('moves-failure-'+field,snapshot==c.export())
 c.response('moves-failure-key',c.call('POST','/reservation-moves',dict(moves=[dict(reference=a['reference'])]),token=c.tokens['u'],key='failure'),201)

def main():
 p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate_release(json.loads(Path(a.release).read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
 try:run(c)
 except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc));raise
 finally:c.save(error)
if __name__=='__main__':main()
