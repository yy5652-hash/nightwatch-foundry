"""Genuine historical bootstrap and invalid modern-state checks over HTTP.

Opaque shallow state is inspected only in memory for labelled counter/profile
observations. No private export, password hash or token is written to evidence.
"""
import argparse,copy,json
from pathlib import Path
from stage3_probe import Client,fixture,policy,create_body,raw,parse,same,integer,validate_release,DAY

def run(c,release):
 for origin,stage,profile in [('accepted-s1',1,'exact-v1'),('accepted-s2',2,'exact-v1'),('legacy-s1',1,'python-json-v1'),('legacy-s2',2,'python-json-v1')]:
  source=release['urls'][origin];peer=release['urls']['peer'];c.setup(fixture('Europe/Berlin'),url=source)
  token=c.tokens['u'];seats=('a',) if stage==1 else ('b','a')
  body=create_body(seats,local=DAY+'T18:00',stage=stage,ignored=parse('9007199254740993.0'),expected_revision=False)
  if stage==1:body['table_ids']={'ignored-in-source':True}
  anchor=c.response('upgrade-'+origin+'-real-source',c.call('POST','/reservations',body,token=token,key='source-create',url=source),201)
  companion=c.create(seats=('c',),local=DAY+'T20:00',key='companion',url=source,stage=stage)
  move=dict(moves=[dict(reference=anchor['reference'],party_size=3,expected_revision=False)])
  moved=c.response('upgrade-'+origin+'-moves-receipt',c.call('POST','/reservation-moves',move,token=token,key='source-moves',url=source),201)
  historic=c.create(seats=('c',),local='0001-01-01T18:00',key='historic',url=source,stage=stage)
  cancelled=c.response('upgrade-'+origin+'-cancelled-state',c.call('POST','/reservations/'+companion['reference']+'/cancel',{},token=token,url=source),200)
  export=c.export(source);c.response('upgrade-'+origin+'-raw-transfer',c.transfer(source,c.base,export),204)
  current=c.lookup(anchor['reference']);history=c.history(anchor['reference']);decision=c.response('upgrade-bootstrap-decision',c.call('GET','/reservations/'+anchor['reference']+'/decision',token=token),200)
  c.check('upgrade-bootstrap-old-fields-'+origin,all(same(current[k],v) for k,v in moved['reservations'][0].items()))
  c.check('upgrade-bootstrap-revision-one-'+origin,integer(current['revision'])==1 and integer(decision['revision'])==1)
  c.check('upgrade-bootstrap-policy-zero-'+origin,integer(current['accepted_terms']['policy_version'])==0 and same(current['accepted_terms'],decision['accepted_terms']))
  c.check('upgrade-bootstrap-empty-history-'+origin,history['entries']==[] and c.history(companion['reference'])['entries']==[])
  now_historic=c.lookup(historic['reference']);c.check('upgrade-bootstrap-original-timestamps-'+origin,all(now_historic[k]==historic[k] for k in ('starts_at','ends_at','starts_at_local','created_at')))
  state=parse(c.export())['state']
  c.check('upgrade-bootstrap-zero-counter-'+origin,all(integer(x)==0 for x in state['restaurant_revisions'].values()))
  c.check('upgrade-'+origin+'-numeric-profile',all(r['numeric_profile']==profile for r in state['receipts']))
  c.check('upgrade-'+origin+'-public-shape',('table_ids' in anchor)==(stage==2))
  # Genuine earlier services ignored manager_user_ids. Import must not invent
  # publishing authority for an account merely named Manager in that old state.
  c.response('upgrade-bootstrap-default-managers',c.call('POST','/restaurants/r/policies',policy(capacities=dict(a=8,b=8,c=8)),token=c.tokens['m'],key='current-policy'),403,'forbidden')
  changed=c.response('upgrade-bootstrap-actual-change',c.call('PATCH','/reservations/'+anchor['reference'],dict(party_size=4),token=token),200)
  entries=c.history(anchor['reference'])['entries']
  c.check('upgrade-bootstrap-first-actual-event-'+origin,len(entries)==1 and integer(entries[0]['seq'])==1 and entries[0]['event']=='changed' and integer(entries[0]['revision'])==2 and same(entries[0]['accepted_terms'],changed['accepted_terms']) and [x['field'] for x in entries[0]['changes']]==['party_size'])
  original_history=copy.deepcopy(entries);adoption=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
  agreement=c.response('upgrade-'+origin+'-adoption',c.call('POST','/series',adoption,token=token,key='adopt'),201);c.series_ids=[agreement['series_id']]
  c.check('upgrade-bootstrap-anchor-unchanged-'+origin,same(c.lookup(anchor['reference']),changed) and same(c.history(anchor['reference'])['entries'],original_history))
  for path,value,key,old in [('/reservations',body,'source-create',anchor),('/reservation-moves',move,'source-moves',moved)]:
   replay=c.response('upgrade-original-shape',c.call('POST',path,value,token=token,key=key),200)
   c.check('upgrade-original-shape',same(replay,old))
  new_historic=c.create(seats=('a',),local='0001-01-01T20:00',key='new-historic')
  c.check('upgrade-bootstrap-new-timestamp-minute-offset-'+origin,len(new_historic['starts_at'].split('+')[-1])==5)
  mixed=c.export();c.response('upgrade-'+origin+'-second-import',c.transfer(c.base,peer,mixed),204)
  after=c.response('upgrade-history-roundtrip',c.call('GET','/reservations/'+anchor['reference']+'/history',token=token,url=peer),200)
  c.check('upgrade-history-roundtrip',same(after['entries'],original_history))
  c.response('upgrade-series-roundtrip',c.call('GET','/series/'+agreement['series_id'],token=token,url=peer),200)
  bad=dict(anchor_reference='missing',count=True,interval_weeks=False)
  c.response('upgrade-'+origin+'-failed-key',c.call('POST','/series',bad,token=token,key='fresh-failed',url=peer),404,'not_found')
  c.response('upgrade-'+origin+'-failed-key',c.call('POST','/series',dict(anchor_reference=new_historic['reference'],count=2,interval_weeks=1),token=token,key='fresh-failed',url=peer),409,'cutoff_passed')
  # Failed key is repaired using a genuinely current, unadopted future record.
  fresh=c.create(seats=('c',),local='2035-07-02T18:00',key='fresh')
  export2=c.export();c.response('upgrade-raw-transfer',c.transfer(c.base,peer,export2),204)
  c.response('upgrade-'+origin+'-failed-key',c.call('POST','/series',dict(anchor_reference=fresh['reference'],count=2,interval_weeks=1),token=token,key='fresh-failed',url=peer),201)
 # Populated genuine current state: change/exception/cancel/history/policy/receipt.
 c.setup();anchor=c.create();c.response('policies-manager-allowed',c.call('POST','/restaurants/r/policies',policy(capacities=dict(a=4,b=4,c=6)),token=c.tokens['m'],key='p'),201)
 s=c.response('series-response-status',c.call('POST','/series',dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1),token=c.tokens['u'],key='s'),201);c.series_ids=[s['series_id']]
 c.response('series-patch-exception',c.call('PATCH','/reservations/'+s['occurrences'][1]['reference'],dict(party_size=3),token=c.tokens['u']),200)
 c.response('series-cancel-no-exception',c.call('POST','/reservations/'+s['occurrences'][2]['reference']+'/cancel',{},token=c.tokens['u']),200)
 before=c.export();observed=c.public_state();template=parse(before)
 def mutate(kind,value):
  state=value['state'];ref=anchor['reference'];sid=s['series_id']
  if kind=='history-seq':state['histories'][ref][0]['seq']=2
  elif kind=='history-terms':state['histories'][ref][0]['accepted_terms']['slot_minutes']=7
  elif kind=='history-origin':state['history_origins'][ref]='invented'
  elif kind=='series-index':state['series'][sid]['occurrences'][1]['index']=9
  elif kind=='series-reference':state['series'][sid]['occurrences'][1]['reference']='MISSING'
  elif kind=='series-revision':state['series'][sid]['revision']=0
  elif kind=='counter-negative':state['restaurant_revisions']['r']=-1
  elif kind=='policy-version':state['policies']['r'][0]['policy_version']=2
  elif kind=='receipt-profile':state['receipts'][0]['numeric_profile']='unsupported'
  elif kind=='reservation-revision':state['reservations'][0]['revision']=0
 for kind in ['history-seq','history-terms','history-origin','series-index','series-reference','series-revision','counter-negative','policy-version','receipt-profile','reservation-revision']:
  bad=copy.deepcopy(template);mutate(kind,bad)
  c.response('upgrade-invalid-'+kind,c.call('POST','/_test/import',body=raw(bad),decode=False),422)
  c.check('upgrade-invalid-atomic',before==c.export() and same(observed,c.public_state()))
 c.response('upgrade-repeat-import',c.transfer(c.base,c.base,before),204)
 c.check('upgrade-repeat-import',same(observed,c.public_state()))

def main():
 p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate_release(json.loads(Path(a.release).read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
 try:run(c,release)
 except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc));raise
 finally:c.save(error)
if __name__=='__main__':main()
