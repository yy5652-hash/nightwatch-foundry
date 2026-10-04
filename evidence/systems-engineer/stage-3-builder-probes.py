"""Own specification-derived Stage 3 transition/HTTP probes; private state stays in memory."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

p=argparse.ArgumentParser()
for name in ('url','peer','stage1','stage2','legacy','out'): p.add_argument('--'+name)
args,rest=p.parse_known_args()
sys.set_int_max_str_digits(0)
trace=[]; assertions=0; operations=0
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class Client:
    def __init__(self,url=None,stage=3):
        self.url=url
        if not url:
            folder=Path(__file__).resolve().parents[2]/('stage-'+str(stage))
            codec_spec=importlib.util.spec_from_file_location('json_codec',folder/'json_codec.py')
            codec=importlib.util.module_from_spec(codec_spec);sys.modules['json_codec']=codec;codec_spec.loader.exec_module(codec)
            spec=importlib.util.spec_from_file_location('systems_stage_'+str(stage),folder/'core.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);self.engine=module.Engine()
    def request(self,method,path,body=None,headers=None):
        global operations
        started=time.monotonic()
        if self.url:
            request=Request(self.url+path,method=method,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json',**(headers or {})})
            try: response=urlopen(request,timeout=10 if path.startswith('/_test/') else 5)
            except HTTPError as error: response=error
            with response:
                raw=response.read(); result=(response.status,json.loads(raw) if raw else None)
        else: result=self.engine.request(method,path,headers or {},body)
        elapsed=time.monotonic()-started;operations+=1
        trace.append({'method':method,'path':path,'body_sha256':digest(body),'status':result[0],
                      'response_sha256':digest(result[1]),'error_code':result[1].get('error',{}).get('code') if isinstance(result[1],dict) else None,'seconds':elapsed})
        return result

def fixture(zone='UTC',opening='18:00',closing='23:00',duration=90,grid=30):
    return {'users':[{'id':u,'email':u+'@example.test','password':'fixture password','display_name':u.upper()} for u in ('u','v','m')],
      'restaurants':[{'id':'r','name':'Garden Room','timezone':zone,'slot_minutes':grid,'reservation_duration_minutes':duration,'cancellation_cutoff_minutes':0,
        'opening_hours':[{'weekday':d,'opens':opening,'closes':closing} for d in ('mon','tue','wed','thu','fri','sat','sun')],
        'tables':[{'id':'a','label':'Window','capacity':2},{'id':'b','label':'Garden','capacity':4},{'id':'c','label':'Courtyard','capacity':3}],
        'combinable':[['b','a'],['b','c']],'manager_user_ids':['m']}],'reservations':[]}

class StageThree(unittest.TestCase):
    def assertEqual(self,a,b,msg=None):
        global assertions;assertions+=1;super().assertEqual(a,b,msg)
    def assertTrue(self,a,msg=None):
        global assertions;assertions+=1;super().assertTrue(a,msg)
    def setUp(self):
        self.c=Client(args.url);self.peer=Client(args.peer);self.seq=0
        self.f=fixture();self.expect(self.c.request('POST','/_test/reset',self.f),204)
        self.h=self.login(self.c,'u');self.m=self.login(self.c,'m');self.v=self.login(self.c,'v')
    def expect(self,response,status,code=None):
        self.assertEqual(response[0],status,'status mismatch; response fingerprint '+digest(response[1]))
        if code:self.assertEqual(response[1]['error']['code'],code)
        return response[1]
    def login(self,c,user):
        value=self.expect(c.request('POST','/auth/login',{'email':user+'@example.test','password':'fixture password'}),200)
        return {'Authorization':'Bearer '+value['token']}
    def write(self,path,body,headers=None,key=None):
        self.seq+=1
        return self.c.request('POST',path,body,{**(self.h if headers is None else headers),'Idempotency-Key':key or 's3-'+str(self.seq)})
    def create(self,members=('a',),start='2099-04-16T18:00',party=2,key=None):
        return self.write('/reservations',{'restaurant_id':'r','table_ids':list(members),'starts_at_local':start,'party_size':party},key=key)
    def patch(self,r,body):return self.c.request('PATCH','/reservations/'+r['reference'],body,self.h)
    def cancel(self,r):return self.c.request('POST','/reservations/'+r['reference']+'/cancel',headers=self.h)
    def current(self,r):return self.expect(self.c.request('GET','/reservations/'+r['reference'],headers=self.h),200)
    def history(self,r):return self.expect(self.c.request('GET','/reservations/'+r['reference']+'/history',headers=self.h),200)['entries']
    def export(self,c=None):return self.expect((c or self.c).request('GET','/_test/export'),200)
    def unchanged(self,before):self.assertEqual(digest(self.export()),digest(before))
    def policy(self,effective='2099-01-01',duration=60,grid=30,cutoff=0,capacities=None,hours=None):
        return {'effective_from':effective,'slot_minutes':grid,'reservation_duration_minutes':duration,'cancellation_cutoff_minutes':cutoff,
                'opening_hours':self.f['restaurants'][0]['opening_hours'] if hours is None else hours,
                'capacities':capacities or {'a':2,'b':4,'c':3}}
    def publish(self,policy,key=None):return self.write('/restaurants/r/policies',policy,self.m,key)
    def adopt(self,r,count=3,interval=1,key=None):return self.write('/series',{'anchor_reference':r['reference'],'count':count,'interval_weeks':interval},key=key)
    def series(self,s):return self.expect(self.c.request('GET','/series/'+s['series_id'],headers=self.h),200)

    def test_01_policy_permission_publication_selection_and_receipts(self):
        data=self.policy();before=self.export()
        self.expect(self.c.request('POST','/restaurants/r/policies',data),401,'unauthenticated')
        self.expect(self.write('/restaurants/r/policies',data,self.h),403,'forbidden')
        self.expect(self.write('/restaurants/missing/policies',data,self.m),404,'not_found')
        self.unchanged(before)
        policies=[self.policy('2099-04-20',duration=30),self.policy('2099-04-01',duration=60),self.policy('2099-04-20',duration=120)]
        issued=[]
        for i,policy in enumerate(policies,1):
            item=self.expect(self.publish(policy,key='p'+str(i)),201);self.assertEqual(item['policy_version'],i);issued.append(item)
        self.assertEqual(self.expect(self.c.request('GET','/restaurants/r/policies'),200)['policies'],issued)
        self.assertEqual(self.expect(self.c.request('GET','/restaurants/r'),200)['reservation_duration_minutes'],90)
        for day,version in (('2099-03-31',0),('2099-04-16',2),('2099-04-20',3)):
            made=self.expect(self.create(start=day+'T18:00'),201);self.assertEqual(made['accepted_terms']['policy_version'],version)
        self.assertEqual(self.expect(self.publish(policies[0],key='p1'),200),issued[0])
        self.expect(self.publish({'bogus':True},key='p1'),409,'idempotency_key_reuse')
        self.assertEqual(len(self.expect(self.c.request('GET','/restaurants/r/policies'),200)['policies']),3)

    def test_02_policy_bounds_types_complete_shape_atomicity(self):
        variants=[]
        for key,low,high in (('slot_minutes',1,1440),('reservation_duration_minutes',1,1440),('cancellation_cutoff_minutes',0,10080)):
            for value in (True,None,'1',[],{},low-1,high+1,1.5):variants.append({**self.policy(),key:value})
        variants.extend([{k:v for k,v in self.policy().items() if k!=name} for name in self.policy()])
        for value in ('2099-2-01','2099-02-30',True,None):variants.append({**self.policy(),'effective_from':value})
        for caps in ({'a':2,'b':4},{'a':2,'b':4,'c':3,'x':1},{'a':True,'b':4,'c':3},{'a':101,'b':4,'c':3},{'a':1.5,'b':4,'c':3}):variants.append({**self.policy(),'capacities':caps})
        variants.extend([{**self.policy(),'opening_hours':v} for v in (None,[{'weekday':'mon','opens':'18:00','closes':'18:00'}],[{'weekday':'mon','opens':'18:00','closes':'23:00'}]*2)])
        for data in variants:
            before=self.export();self.expect(self.publish(data,key='failed'),422,'validation_failed');self.unchanged(before)
        result=self.expect(self.publish({**self.policy(grid=1.0,duration=1440.0,cutoff=10080.0),'ignored':{'a':[True]}},key='failed'),201)
        self.assertEqual(result['policy_version'],1)

    def test_03_explanations_independent_truth_order_absence(self):
        made=self.expect(self.create(members=('b',),party=2),201)
        path='/availability?restaurant_id=r&date=2099-04-16&party_size=4'
        plain=self.expect(self.c.request('GET',path),200)
        self.assertTrue(all('explain' not in s for s in plain['slots']))
        detailed=self.expect(self.c.request('GET',path+'&explain=true'),200)
        first=detailed['slots'][0];self.assertEqual([e['table_id'] for e in first['explain']],['a','b','c'])
        self.assertEqual([e['rules'] for e in first['explain']],[[{'rule':'capacity','holds':False},{'rule':'no_overlap','holds':True}],[{'rule':'capacity','holds':True},{'rule':'no_overlap','holds':False}],[{'rule':'capacity','holds':False},{'rule':'no_overlap','holds':True}]])
        for slot in detailed['slots']:
            self.assertEqual([e['table_id'] for e in slot['explain'] if e['available']],slot['available_table_ids'])
            for e in slot['explain']:self.assertEqual(e['available'],all(r['holds'] for r in e['rules']))
        for value in ('false','1','', 'TRUE'):
            self.expect(self.c.request('GET',path+'&explain='+value),422,'validation_failed')
        self.expect(self.publish(self.policy(capacities={'a':5,'b':4,'c':3})),201)
        result=self.expect(self.c.request('GET',path+'&explain=true'),200)
        self.assertEqual(result['slots'][0]['explain'][0]['policy_version'],1)
        self.assertEqual(result['slots'][0]['available_table_ids'],['a'])
        self.expect(self.publish(self.policy(hours=[])),201)
        self.assertEqual(self.expect(self.c.request('GET',path+'&explain=true'),200)['slots'],[])

    def test_04_history_revision_terms_noops_and_privacy(self):
        original=self.expect(self.create(key='original'),201);entries=self.history(original)
        self.assertEqual(entries[0]['changes'],[{'field':'table_id','from':None,'to':'a'},{'field':'starts_at_local','from':None,'to':original['starts_at_local']},{'field':'party_size','from':None,'to':2}])
        self.assertEqual(entries[0]['revision'],1);self.assertEqual(entries[0]['accepted_terms'],original['accepted_terms'])
        self.expect(self.publish(self.policy(duration=30,capacities={'a':1,'b':4,'c':3})),201)
        noop=self.expect(self.patch(original,{'party_size':2.0,'expected_revision':1}),200)
        self.assertEqual(noop,original);self.assertEqual(self.history(original),entries)
        moved=self.expect(self.patch(original,{'table_ids':['a','b'],'starts_at_local':'2099-04-16T19:00','party_size':5,'expected_revision':1}),200)
        self.assertEqual(moved['revision'],2);self.assertEqual(moved['table_ids'],['b','a']);self.assertEqual(moved['accepted_terms']['policy_version'],1)
        self.assertEqual([c['field'] for c in self.history(original)[1]['changes']],['table_ids','starts_at_local','party_size'])
        before=self.export();self.expect(self.patch(original,{'expected_revision':1,'party_size':False}),409,'stale_revision');self.unchanged(before)
        for value in (True,0,-1,'2',1.5):self.expect(self.patch(original,{'expected_revision':value}),422,'validation_failed')
        self.assertEqual(self.expect(self.patch(original,{'table_ids':['a','b']}),200),moved)
        self.assertEqual(len(self.history(original)),2)
        cancelled=self.expect(self.cancel(original),200);self.assertEqual(cancelled['revision'],3)
        self.assertEqual(self.expect(self.cancel(original),200),cancelled)
        self.assertEqual([e['seq'] for e in self.history(original)],[1,2,3])
        self.assertEqual(self.history(original)[2]['changes'],[])
        self.assertEqual(self.expect(self.create(key='original'),200),original)
        for suffix in ('history','decision'):
            for headers in ({},self.v,self.m):self.expect(self.c.request('GET','/reservations/'+original['reference']+'/'+suffix,headers=headers),404,'not_found')
        decision=self.expect(self.c.request('GET','/reservations/'+original['reference']+'/decision',headers=self.h),200)
        self.assertEqual(decision,{'reference':original['reference'],'revision':3,'accepted_terms':moved['accepted_terms']})

    def test_05_accepted_cutoff_new_policy_and_optional_revision(self):
        day=(datetime.now(timezone.utc).date()+timedelta(days=2)).isoformat()
        original=self.expect(self.create(start=day+'T18:00'),201)
        self.expect(self.publish(self.policy(effective=day,cutoff=10080)),201)
        self.expect(self.cancel(original),200)
        fresh=self.expect(self.create(members=('b',),start=day+'T18:00'),201)
        before=self.export();self.expect(self.patch(fresh,{'expected_revision':1,'party_size':1}),409,'cutoff_passed');self.unchanged(before)
        self.expect(self.patch(fresh,{'expected_revision':2,'party_size':False}),409,'stale_revision')
        self.expect(self.cancel(fresh),409,'cutoff_passed')

    def test_06_optimistic_two_and_fifty_identical_writes(self):
        original=self.expect(self.create(members=('b',),party=1),201);gate=threading.Barrier(2)
        def amend(value):gate.wait();return self.patch(original,{'party_size':value,'expected_revision':1})
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(amend,[2,3]))
        self.assertEqual(sorted(r[0] for r in results),[200,409]);self.assertEqual(self.current(original)['revision'],2);self.assertEqual(len(self.history(original)),2)
        body={'restaurant_id':'r','table_ids':['a'],'starts_at_local':'2099-04-16T20:00','party_size':1};gate=threading.Barrier(50)
        def create(_):gate.wait();return self.c.request('POST','/reservations',body,{**self.h,'Idempotency-Key':'fifty'})
        with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(create,range(50)))
        self.assertEqual(sum(s==201 for s,b in results),1);self.assertEqual(sum(s==200 for s,b in results),49)
        self.assertTrue(all(b==results[0][1] for s,b in results));self.assertEqual(len(self.history(results[0][1])),1)

    def test_07_series_anchor_policy_occurrences_exceptions_receipt(self):
        anchor=self.expect(self.create(),201);old_history=self.history(anchor)
        self.expect(self.publish(self.policy('2099-04-23',duration=30)),201)
        series=self.expect(self.adopt(anchor,key='adoption'),201)
        self.assertEqual(series['occurrences'][0]['reservation'],anchor);self.assertEqual(self.history(anchor),old_history)
        self.assertEqual([o['reservation']['accepted_terms']['policy_version'] for o in series['occurrences']],[0,1,1])
        self.assertEqual([o['reservation']['starts_at_local'] for o in series['occurrences']],['2099-04-16T18:00','2099-04-23T18:00','2099-04-30T18:00'])
        second=series['occurrences'][1]['reservation'];self.expect(self.patch(second,{'party_size':1}),200)
        current=self.series(series);self.assertEqual(current['revision'],2);self.assertEqual([o['exception'] for o in current['occurrences']],[False,True,False])
        self.expect(self.patch(second,{'party_size':1}),200);self.assertEqual(self.series(series)['revision'],2)
        self.expect(self.cancel(anchor),200);current=self.series(series);self.assertEqual(current['revision'],3);self.assertEqual(current['occurrences'][0]['exception'],False)
        self.assertEqual(current['occurrences'][2]['reservation']['status'],'confirmed')
        self.expect(self.cancel(anchor),200);self.assertEqual(self.series(series)['revision'],3)
        self.assertEqual(self.expect(self.adopt(anchor,key='adoption'),200),series)
        self.expect(self.adopt(second),409,'already_in_series')
        for h in ({},self.v,self.m):self.expect(self.c.request('GET','/series/'+series['series_id'],headers=h),404,'not_found')

    def test_08_series_invalid_atomic_order_and_failed_key_reuse(self):
        anchor=self.expect(self.create(members=('b',),party=3),201)
        for field,values in (('count',(True,1,13,2.5,'3')),('interval_weeks',(True,0,5,1.5,'1'))):
            for value in values:
                body={'anchor_reference':anchor['reference'],'count':3,'interval_weeks':1,field:value};before=self.export()
                self.expect(self.write('/series',body,key='failed'),422,'validation_failed');self.unchanged(before)
        self.expect(self.publish(self.policy('2099-04-30',capacities={'a':2,'b':2,'c':3})),201)
        before=self.export();self.expect(self.adopt(anchor,key='failed'),422,'party_exceeds_capacity');self.unchanged(before)
        self.expect(self.publish(self.policy('2099-04-30')),201)
        self.expect(self.adopt(anchor,key='failed'),201)
        self.expect(self.write('/series',{'bogus':True},key='failed'),409,'idempotency_key_reuse')

    def test_09_series_dst_gap_and_first_repeated_occurrence(self):
        for zone,anchor_time,gap in (('Europe/Berlin','2027-03-21T02:30',True),('America/New_York','2027-03-07T02:30',True),('Europe/Berlin','2026-10-18T02:30',False),('America/New_York','2026-10-25T01:30',False)):
            self.f=fixture(zone,'00:00','06:00',duration=90,grid=30)
            self.expect(self.c.request('POST','/_test/reset',self.f),204);self.h=self.login(self.c,'u')
            anchor=self.expect(self.create(start=anchor_time),201);before=self.export()
            response=self.adopt(anchor,count=2)
            if gap:self.expect(response,422,'invalid_local_time');self.unchanged(before)
            else:
                series=self.expect(response,201);second=series['occurrences'][1]['reservation']
                local=datetime.fromisoformat(second['starts_at_local']).replace(tzinfo=ZoneInfo(zone),fold=0)
                self.assertEqual(datetime.fromisoformat(second['starts_at']).astimezone(timezone.utc),local.astimezone(timezone.utc))
                self.assertEqual(datetime.fromisoformat(second['ends_at']).astimezone(timezone.utc)-local.astimezone(timezone.utc),timedelta(minutes=90))

    def test_10_collective_moves_series_counters_histories_and_rollback(self):
        anchor=self.expect(self.create(members=('b','a'),party=2),201);series=self.expect(self.adopt(anchor),201)
        records=[o['reservation'] for o in series['occurrences']];before=self.export();counter=before['state']['restaurant_revisions']['r']
        moves=[{'reference':r['reference'],'table_ids':['c'],'expected_revision':1} for r in records]
        response=self.expect(self.write('/reservation-moves',{'moves':moves},key='batch'),201)
        self.assertEqual(self.series(series)['revision'],2);self.assertEqual([o['exception'] for o in self.series(series)['occurrences']],[True]*3)
        self.assertEqual(self.export()['state']['restaurant_revisions']['r'],counter+1)
        for r in response['reservations']:
            self.assertEqual(r['revision'],2);self.assertEqual(self.history(r)[1]['changes'],[{'field':'table_ids','from':['b','a'],'to':['c']}])
        self.assertEqual(self.expect(self.write('/reservation-moves',{'moves':moves},key='batch'),200),response)
        before=self.export();bad=[{'reference':records[0]['reference'],'party_size':1,'expected_revision':2},{'reference':records[1]['reference'],'party_size':False,'expected_revision':1}]
        self.expect(self.write('/reservation-moves',{'moves':bad},key='rollback'),409,'stale_revision');self.unchanged(before)
        noop=[{'reference':r['reference'],'table_ids':['c']} for r in records]
        self.expect(self.write('/reservation-moves',{'moves':noop},key='rollback'),201)
        self.assertEqual(self.series(series)['revision'],2);self.assertEqual(self.export()['state']['restaurant_revisions']['r'],counter+1)

    def test_11_current_state_replace_histories_terms_series_receipts(self):
        anchor=self.expect(self.create(),201);self.expect(self.publish(self.policy('2099-04-23')),201)
        agreement=self.expect(self.adopt(anchor,key='series'),201);second=agreement['occurrences'][1]['reservation']
        self.expect(self.patch(second,{'table_ids':['a','b'],'party_size':5}),200);self.expect(self.cancel(anchor),200)
        captured=self.export();current=self.series(agreement);history=self.history(second)
        self.expect(self.peer.request('POST','/_test/reset',fixture()),204)
        self.expect(self.peer.request('POST','/_test/import',captured),204)
        self.assertEqual(self.expect(self.peer.request('GET','/series/'+agreement['series_id'],headers=self.h),200),current)
        self.assertEqual(self.expect(self.peer.request('GET','/reservations/'+second['reference']+'/history',headers=self.h),200)['entries'],history)
        self.assertEqual(self.expect(self.peer.request('POST','/series',{'anchor_reference':anchor['reference'],'count':3,'interval_weeks':1},{**self.h,'Idempotency-Key':'series'}),200),agreement)
        self.expect(self.peer.request('POST','/_test/import',captured),204);self.assertEqual(digest(self.export(self.peer)),digest(captured))
        for field,value in (('schema',9),('policies',{}),('histories',{}),('series',{'bad':{}}),('restaurant_revisions',{})):
            altered=json.loads(json.dumps(captured));altered['state'][field]=value
            self.expect(self.peer.request('POST','/_test/import',altered),422,'validation_failed');self.assertEqual(digest(self.export(self.peer)),digest(captured))
        self.expect(self.peer.request('POST','/_test/reset',fixture()),204);self.expect(self.peer.request('GET','/reservations/'+anchor['reference'],headers=self.h),401,'unauthenticated')

    def test_12_genuine_earlier_stage_origins_adoption_and_receipts(self):
        for stage,url in ((1,args.stage1),(2,args.stage2)):
            old=Client(url,stage);self.expect(old.request('POST','/_test/reset',fixture()),204);auth=self.login(old,'u')
            body={'restaurant_id':'r','table_id':'a','starts_at_local':'2099-04-16T18:00','party_size':2,'ignored':{'n':1}}
            if stage==1:body['table_ids']={'formerly':'ignored'}
            original=self.expect(old.request('POST','/reservations',body,{**auth,'Idempotency-Key':'old'}),201)
            captured=self.export(old)
            self.expect(old.request('POST','/reservations/'+original['reference']+'/cancel',headers=auth),200)
            self.expect(self.c.request('POST','/_test/import',captured),204);self.h=auth
            current=self.current(original);self.assertEqual(current['revision'],1);self.assertEqual(current['accepted_terms']['policy_version'],0)
            self.assertEqual(self.history(original),[])
            self.assertEqual(self.expect(self.c.request('POST','/reservations',body,{**auth,'Idempotency-Key':'old'}),200),original)
            series=self.expect(self.adopt(original,key='adopted'),201);self.assertEqual(series['occurrences'][0]['reservation'],current)
            changed=self.expect(self.patch(original,{'party_size':1}),200);self.assertEqual(self.history(original)[0]['event'],'changed');self.assertEqual(self.history(original)[0]['seq'],1)
            mixed=self.export();self.expect(self.peer.request('POST','/_test/import',mixed),204)
            self.assertEqual(self.expect(self.peer.request('POST','/reservations',body,{**auth,'Idempotency-Key':'old'}),200),original)
            self.assertEqual(self.expect(self.peer.request('GET','/reservations/'+original['reference'],headers=auth),200),changed)
            self.assertEqual(self.expect(self.peer.request('GET','/series/'+series['series_id'],headers=auth),200),self.series(series))

    def test_13_seed_history_and_private_ownership(self):
        seeded=fixture();seeded['reservations']=[{'id':'seed','reference':'SEEDED1','user_id':'u','restaurant_id':'r','table_ids':['a','b'],'party_size':5,'starts_at_local':'2099-04-16T18:00'}]
        self.expect(self.c.request('POST','/_test/reset',seeded),204);self.h=self.login(self.c,'u')
        r={'reference':'SEEDED1'};record=self.current(r);self.assertEqual(record['revision'],1)
        self.assertEqual(self.history(r)[0]['changes'][0],{'field':'table_ids','from':None,'to':['b','a']})
        self.expect(self.c.request('POST','/_test/import',self.export()),204)

    def test_14_deterministic_history_oracle(self):
        rng=random.Random(2026100404);r=self.expect(self.create(members=('b',),party=1),201)
        oracle=[];revision=1;party=1
        for index in range(120):
            choice=rng.randint(1,4);before=self.export();response=self.patch(r,{'party_size':choice,'expected_revision':revision})
            current=self.expect(response,200)
            if choice!=party:
                revision+=1;oracle.append({'field':'party_size','from':party,'to':choice});party=choice
            self.assertEqual(current['revision'],revision)
            entries=self.history(r);self.assertEqual([e['changes'][0] for e in entries[1:]],oracle)
            self.assertEqual([e['seq'] for e in entries],list(range(1,len(oracle)+2)))
            trace.append({'oracle_seed':2026100404,'index':index,'party':choice,'expected_revision':revision,'observed_revision':current['revision']})

if __name__=='__main__':
    out=Path(args.out or 'evidence/systems-engineer/systems-engineer-s3-direct-01');out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();runner=unittest.TextTestRunner(verbosity=2);result=runner.run(unittest.defaultTestLoader.loadTestsFromTestCase(StageThree))
    summary={'scenarios':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'assertions':assertions,'operations':operations,
             'wall_seconds':time.monotonic()-started,'method':'HTTP' if args.url else 'direct Engine; not HTTP','seed':2026100404}
    (out/'trace.json').write_text(json.dumps({'summary':summary,'operations':trace},indent=2)+'\n')
    (out/'executed-probe.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(summary));sys.exit(not result.wasSuccessful())
