"""Independent missing-boundary observations, including labelled opaque counters.

Counter checks use actual shallow exports in memory. No private state is saved,
manufactured or submitted; the private counter observation is explicitly scoped.
"""
import argparse,copy,json,re
from datetime import datetime,timedelta,timezone
from pathlib import Path
from stage3_probe import Client,fixture,policy,create_body,raw,parse,same,integer,validate_release,DAY

def check(c,family,names,value):
 for name in names.split(','):c.check(family+'-'+name,value)
def counters(c):
 state=parse(c.export())['state']
 return {k:integer(v) for k,v in state['restaurant_revisions'].items()}
def publish(c,value,key='p',rid='r',token=None):
 return c.response('policies-manager-allowed',c.call('POST','/restaurants/'+rid+'/policies',value,token=token or c.tokens['m'],key=key),201)
def policies(c):
 f=fixture();f['restaurants'][1]['tables']=copy.deepcopy(f['restaurants'][0]['tables']);f['restaurants'][1]['combinable']=[]
 f['restaurants'][0]['manager_user_ids']=['u','m'];f['restaurants'][1]['manager_user_ids']=['m']
 c.setup(f);original=c.response('policies-original-detail',c.call('GET','/restaurants/r'),200)
 p=policy();p.update(timezone='Pacific/Honolulu',tables=[],combinable=[['a','c']],labels={'a':'Fake'},role='manager',ignored=[False,1])
 first=publish(c,p,'same-key');expected={k:v for k,v in policy().items()};expected['policy_version']=1
 check(c,'policies','supplied-response,unknown-fields,fixed-labels,fixed-tables,fixed-zone,fixed-pairs',same(first,expected) and same(original,c.response('policies-original-detail',c.call('GET','/restaurants/r'),200)))
 user_first=publish(c,policy(), 'same-key',token=c.tokens['u']);second_rest=publish(c,policy(),'same-key',rid='r2')
 check(c,'policies','policies-retry-scoped-user',integer(user_first['policy_version'])==2)
 check(c,'policies','policies-retry-scoped-path,independent-version',integer(second_rest['policy_version'])==1)
 c.response('policies-unknown-list',c.call('GET','/restaurants/missing/policies'),404,'not_found')
 before=c.public_state();bad=policy();bad.pop('capacities');c.response('policies-complete-not-patch',c.call('POST','/restaurants/r/policies',bad,token=c.tokens['m'],key='bad'),422,'validation_failed')
 after=publish(c,policy(),'bad');check(c,'policies','failed-version',integer(after['policy_version'])==3)
 listing=c.response('policies-public-list',c.call('GET','/restaurants/r/policies'),200)['policies']
 check(c,'policies','omit-zero,immutable-policy',same(listing[0],first) and [integer(p['policy_version']) for p in listing]==[1,2,3])
 snapshot=c.export();c.response('upgrade-raw-transfer',c.transfer(c.base,c.base,snapshot),204)
 replay=c.response('policies-policies-retry-replay-after-import',c.call('POST','/restaurants/r/policies',p,token=c.tokens['m'],key='same-key'),200)
 check(c,'policies','policies-retry-replay-after-import',same(replay,first))
 f=fixture();f['restaurants'][0].pop('manager_user_ids');c.setup(f)
 c.response('policies-default-managers',c.call('POST','/restaurants/r/policies',policy(),token=c.tokens['m'],key='default'),403,'forbidden')
 auth=c.response('policies-role-ignored-signup',c.call('POST','/auth/signup',dict(email='role@stage3.invalid',password='independent-pass',display_name='Role Claim',role='manager')),201)
 c.response('policies-role-ignored',c.call('POST','/restaurants/r/policies',policy(),token=auth['token'],key='role'),403,'forbidden')
 f=fixture('America/New_York');c.setup(f);publish(c,policy('2035-06-05'))
 row=c.create(local='2035-06-04T22:00',key='local-date');check(c,'policies','local-not-utc,policy-zero,future-ineligible',integer(row['accepted_terms']['policy_version'])==0 and row['starts_at'].startswith('2035-06-04'))

def explanations(c):
 c.setup();a=c.create(seats=('b','a'),party=9);ref=a['reference']
 p=policy(reservation_duration_minutes=30,slot_minutes=60,capacities=dict(a=2,b=4,c=6));publish(c,p)
 result=c.response('explain-true',c.call('GET','/availability?restaurant_id=r&date='+DAY+'&party_size=9&explain=true'),200)
 check(c,'explain','new-grid',len(result['slots'])==24 and all(s['starts_at_local'].endswith(':00') for s in result['slots']))
 bytime={s['starts_at_local'][-5:]:s for s in result['slots']}
 check(c,'explain','new-duration,half-open',all(t['rules'][1]['holds'] for t in bytime['20:00']['explain']))
 for slot in result['slots']:
  check(c,'explain','empty-slot,table-completeness,rule-completeness,boolean-types',slot['available_table_ids']==[] and [t['table_id'] for t in slot['explain']]==['a','b','c'] and all(len(t['rules'])==2 and type(t['available']) is bool and all(type(r['holds']) is bool for r in t['rules']) for t in slot['explain']))
 c.response('explain-cancel-frees',c.call('POST','/reservations/'+ref+'/cancel',{},token=c.tokens['u']),200)
 result=c.response('explain-cancel-frees',c.call('GET','/availability?restaurant_id=r&date='+DAY+'&party_size=9&explain=true'),200)
 check(c,'explain','cancel-frees',all(t['rules'][1]['holds'] for s in result['slots'] for t in s['explain']))
 publish(c,policy(opening_hours=[]),'closed');result=c.response('explain-closed',c.call('GET','/availability?restaurant_id=r&date='+DAY+'&party_size=1&explain=true'),200)
 check(c,'explain','closed',result['slots']==[])

def history_terms(c):
 f=fixture();seed=create_body(local=DAY+'T17:00');seed.update(id='seed',reference='SEED001',user_id='u');f['reservations']=[seed]
 c.setup(f);record=c.lookup('SEED001');hist=c.history('SEED001')['entries'];base={k:v for k,v in record['accepted_terms'].items()}
 expected=dict(policy_version=0,slot_minutes=30,reservation_duration_minutes=90,cancellation_cutoff_minutes=0,opening_hours=f['restaurants'][0]['opening_hours'],capacities=dict(a=8,b=8,c=8))
 check(c,'terms','seed-revision,seed-zero,terms-complete,terms-no-date',integer(record['revision'])==1 and same(base,expected) and 'effective_from' not in base)
 expected_changes=[dict(field='table_id',**{'from':None,'to':'a'}),dict(field='starts_at_local',**{'from':None,'to':DAY+'T17:00'}),dict(field='party_size',**{'from':None,'to':2})]
 check(c,'history','created-event,seq-start,created-fields,created-from,created-values',len(hist)==1 and integer(hist[0]['seq'])==1 and hist[0]['event']=='created' and same(hist[0]['changes'],expected_changes))
 for fields in [dict(table_ids=['b']),dict(table_ids=['a','b'],starts_at_local=DAY+'T18:00',party_size=5),dict(table_ids=['c','b'],party_size=6),dict(table_ids=['c'])]:
  old=c.lookup('SEED001');before=c.history('SEED001')['entries'];new=c.response('terms-patch-current',c.call('PATCH','/reservations/SEED001',fields,token=c.tokens['u']),200);after=c.history('SEED001')['entries']
  from stage3_oracle import changes
  from types import SimpleNamespace
  expected=changes(SimpleNamespace(seating=old['table_ids'],starts_at_local=old['starts_at_local'],party_size=integer(old['party_size'])),SimpleNamespace(seating=new['table_ids'],starts_at_local=new['starts_at_local'],party_size=integer(new['party_size'])))
  check(c,'history','changed-only,old-from,new-to,changed-order,single-change,single-to-pair,pair-to-pair,pair-to-single',same(after[-1]['changes'],expected) and same(after[:-1],before))
  check(c,'history','revision-event,terms-event,at-format,at-order,seq-order',integer(after[-1]['revision'])==integer(new['revision']) and same(after[-1]['accepted_terms'],new['accepted_terms']) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}',after[-1]['at'])) and [e['at'] for e in after]==sorted(e['at'] for e in after))
 before=c.public_state();c.response('terms-unknown-patch',c.call('PATCH','/reservations/SEED001',dict(unknown={'anything':True}),token=c.tokens['u']),200)
 check(c,'terms','unknown-patch,expected-optional,noop-end',same(before,c.public_state()))
 c.response('terms-expected-noop-stale',c.call('PATCH','/reservations/SEED001',dict(expected_revision=1),token=c.tokens['u']),409,'stale_revision')
 c.response('history-failure-entry',c.call('PATCH','/reservations/SEED001',dict(party_size=999),token=c.tokens['u']),422,'party_exceeds_capacity')
 check(c,'history','failure-entry,no-op-entry',same(before,c.public_state()))
 c.response('terms-cancel-current',c.call('POST','/reservations/SEED001/cancel',{},token=c.tokens['u']),200)
 final=c.history('SEED001')['entries'];c.response('history-cancel-terminal',c.call('PATCH','/reservations/SEED001',{},token=c.tokens['u']),409,'reservation_cancelled')
 decision=c.response('terms-decision-cancelled',c.call('GET','/reservations/SEED001/decision',token=c.tokens['u']),200)
 check(c,'history','cancel-empty,cancel-terminal,cancel-retained',final[-1]['changes']==[] and final[-1]['event']=='cancelled' and same(final,c.history('SEED001')['entries']))
 check(c,'terms','decision-current,decision-cancelled',same(decision['revision'],c.lookup('SEED001')['revision']) and same(decision['accepted_terms'],base))
 # A real-clock future seed within an original very long cutoff. The published
 # cutoff zero would allow it; only the accepted original cutoff must refuse.
 f=fixture();r=f['restaurants'][0];r.update(slot_minutes=1,cancellation_cutoff_minutes=1000000)
 local=(datetime.now(timezone.utc)+timedelta(days=2)).replace(hour=18,minute=0).strftime('%Y-%m-%dT%H:%M')
 seed=create_body(local=local);seed.update(id='cutoff',reference='CUTOFF1',user_id='u');f['reservations']=[seed];c.setup(f);publish(c,policy(local[:10]))
 before=c.public_state()
 c.response('terms-stale-before-cutoff',c.call('PATCH','/reservations/CUTOFF1',dict(expected_revision=2,party_size=False),token=c.tokens['u']),409,'stale_revision')
 for path,body,method,key in [('/reservations/CUTOFF1',{},'PATCH',None),('/reservations/CUTOFF1',dict(party_size=False),'PATCH',None),('/reservations/CUTOFF1/cancel',{},'POST',None),('/series',dict(anchor_reference='CUTOFF1',count=2,interval_weeks=1),'POST','cutoff-series'),('/reservation-moves',dict(moves=[dict(reference='CUTOFF1',party_size=False)]),'POST','cutoff-moves')]:
  c.response('terms-old-cutoff',c.call(method,path,body,token=c.tokens['u'],key=key),409,'cutoff_passed')
 check(c,'terms','noop-editable,amend-old-first,amend-atomic',same(before,c.public_state()))
 # Omitting an unchanged field cannot bypass the newly selected full policy.
 for change in [dict(table_ids=['b']),dict(starts_at_local=DAY+'T19:00')]:
  c.setup();anchor=c.create(party=8);publish(c,policy(capacities=dict(a=2,b=4,c=6)))
  before=c.public_state();c.response('terms-amend-all-fields',c.call('PATCH','/reservations/'+anchor['reference'],change,token=c.tokens['u']),422,'party_exceeds_capacity')
  check(c,'terms','amend-all-fields,amend-atomic',same(before,c.public_state()))

def agreements(c):
 c.setup();anchor=c.create(seats=('b','a'),party=5);body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
 before=counters(c);s=c.response('series-response-status',c.call('POST','/series',body,token=c.tokens['u'],key='adopt'),201);after=counters(c)
 c.series_ids=[s['series_id']];check(c,'series','adopt-restaurant-once',after['r']==before['r']+1 and after['r2']==before['r2'])
 check(c,'series','response-id,response-revision,response-interval,own-party,own-seating,ordinary-history',isinstance(s['series_id'],str) and 1<=len(s['series_id'])<=64 and integer(s['revision'])==1 and integer(s['interval_weeks'])==1 and all(integer(x['reservation']['party_size'])==5 and x['reservation']['table_ids']==['b','a'] and c.history(x['reference'])['entries'] for x in s['occurrences']))
 refs=[x['reference'] for x in s['occurrences']];original=c.public_state();c.response('series-already-adopted',c.call('POST','/series',body,token=c.tokens['u'],key='again'),409,'already_in_series')
 c.response('series-noop-series',c.call('PATCH','/reservations/'+refs[1],dict(party_size=5),token=c.tokens['u']),200)
 c.response('series-failed-series',c.call('PATCH','/reservations/'+refs[1],dict(party_size=99),token=c.tokens['u']),422,'party_exceeds_capacity')
 check(c,'series','noop-series,failed-series,stable-references',same(original,c.public_state()) and after==counters(c))
 c.response('series-patch-exception',c.call('PATCH','/reservations/'+refs[1],dict(party_size=6),token=c.tokens['u']),200)
 c.response('series-cancel-keeps-exception',c.call('POST','/reservations/'+refs[1]+'/cancel',{},token=c.tokens['u']),200)
 current=c.response('series-get-current',c.call('GET','/series/'+s['series_id'],token=c.tokens['u']),200)
 check(c,'series','cancel-keeps-member,cancel-keeps-exception,cancel-series-once,patch-series-once',integer(current['revision'])==3 and len(current['occurrences'])==3 and current['occurrences'][1]['exception'] is True and current['occurrences'][1]['reservation']['status']=='cancelled')
 mixed=c.export();c.response('upgrade-second-transfer',c.transfer(c.base,c.base,mixed),204)
 replay=c.response('series-series-retry-replay-after-import',c.call('POST','/series',body,token=c.tokens['u'],key='adopt'),200)
 check(c,'series','series-retry-replay-after-import,anchor-receipt',same(replay,s))
 for token,status,code,ref in [(None,401,'unauthenticated',refs[0]),(c.tokens['v'],404,'not_found',refs[0]),(c.tokens['u'],404,'not_found','MISSING'),(c.tokens['u'],409,'reservation_cancelled',refs[1])]:
  c.response('series-owned-confirmed-boundary',c.call('POST','/series',dict(anchor_reference=ref,count=2,interval_weeks=1),token=token,key='boundary-'+str(status)),status,code)
 # Failed adoption must preserve private counters as well as public fields.
 c.setup();anchor=c.create();publish(c,policy('2035-06-11',capacities=dict(a=1,b=4,c=6)));before=counters(c);public=c.public_state()
 c.response('series-rollback-counters',c.call('POST','/series',dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1),token=c.tokens['u'],key='failed'),422,'party_exceeds_capacity')
 check(c,'series','rollback-counters,rollback-series,rollback-histories',before==counters(c) and same(public,c.public_state()))
 # Two real agreements, four changed members and one noop in a single batch.
 c.setup();a=c.create(seats=('b','a'),party=5);b=c.create(seats=('c',),key='b');agreements=[]
 for i,r in enumerate([a,b]):agreements.append(c.response('series-response-status',c.call('POST','/series',dict(anchor_reference=r['reference'],count=3,interval_weeks=1),token=c.tokens['u'],key='agreement-'+str(i)),201))
 c.series_ids=[s['series_id'] for s in agreements];aa=[x['reference'] for x in agreements[0]['occurrences']];bb=[x['reference'] for x in agreements[1]['occurrences']]
 body=dict(moves=[dict(reference=aa[0],table_ids=['c'],party_size=5),dict(reference=bb[0],table_ids=['b','a']),dict(reference=aa[1],party_size=6),dict(reference=bb[1],party_size=3),dict(reference=aa[2])])
 before=counters(c);reply=c.response('moves-swap-atomic',c.call('POST','/reservation-moves',body,token=c.tokens['u'],key='batch'),201)
 check(c,'moves','restaurant-once,multiple-series,series-once',counters(c)['r']==before['r']+1 and all(integer(c.response('series-get-current',c.call('GET','/series/'+sid,token=c.tokens['u']),200)['revision'])==2 for sid in c.series_ids))
 for sid in c.series_ids:
  agreement=c.response('series-get-current',c.call('GET','/series/'+sid,token=c.tokens['u']),200)
  check(c,'moves','exception-changed,exception-noop',[o['exception'] for o in agreement['occurrences']]==[True,True,False])
 before=counters(c);public=c.public_state();c.response('moves-replay-counters',c.call('POST','/reservation-moves',body,token=c.tokens['u'],key='batch'),200)
 c.response('moves-noop-retains',c.call('POST','/reservation-moves',dict(moves=[dict(reference=aa[2])]),token=c.tokens['u'],key='noop'),201)
 check(c,'moves','replay-counters,noop-retains',before==counters(c) and same(public,c.public_state()))

FAMILIES=dict(policies=policies,explain=explanations,terms=history_terms,series=agreements)
def main():
 p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);p.add_argument('--family',choices=FAMILIES,required=True);a=p.parse_args()
 release=validate_release(json.loads(Path(a.release).read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
 try:FAMILIES[a.family](c)
 except BaseException as exc:error=dict(kind='failed-expectation' if isinstance(exc,AssertionError) else 'runner-exception',type=type(exc).__name__,message=str(exc));raise
 finally:c.save(error)
if __name__=='__main__':main()
