"""Own cumulative HTTP protocols and an independently enumerated seating oracle.

No production helper is imported. Raw exports and credentials remain in memory.
The inherited fourteen scenarios are our own previously committed protocol.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys
import time
import unittest

p = argparse.ArgumentParser()
for key in ('url', 'peer', 'stage1', 'stage2', 'stage3', 'legacy', 'out'):
    p.add_argument('--' + key)
args = p.parse_args()
saved_argv = sys.argv
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location('own_previous', Path(__file__).with_name('stage-3-builder-probes.py'))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
sys.argv = saved_argv
old.args = args
sys.set_int_max_str_digits(0)

def oracle(fixture, bookings, closure, previous=()):
    """Enumerate product of fixture options using standalone interval/set math."""
    r = fixture['restaurants'][0]
    def epoch(value):
        return Decimal(str(datetime.fromisoformat(value).timestamp()))
    def interval(b):
        start = epoch(b['starts_at'])
        return start, epoch(b['ends_at'])
    lo, hi = epoch(closure['from']), epoch(closure['to'])
    considered = sorted([b for b in bookings if b['status'] == 'confirmed' and b['restaurant_id'] == r['id']
                         and interval(b)[0] < hi and lo < interval(b)[1]], key=lambda b: b['reference'])
    refs = {b['reference'] for b in considered}
    fixed = [b for b in bookings if b['status'] == 'confirmed' and b['reference'] not in refs and b['restaurant_id'] == r['id']]
    options = [[t['id']] for t in r['tables']] + r['combinable']
    def clashes(b, members, other, other_members):
        a0, a1 = interval(b); b0, b1 = interval(other)
        return bool(set(members) & set(other_members)) and a0 < b1 and b0 < a1
    choices = []
    for b in considered:
        rows = []
        for rank, members in enumerate(options):
            capacity = sum(b['accepted_terms']['capacities'][m] for m in members)
            if capacity < b['party_size']:
                continue
            if any(clashes(b, members, f, f['table_ids']) for f in fixed):
                continue
            a0, a1 = interval(b)
            if any(c['table_id'] in members and a0 < epoch(c['to']) and epoch(c['from']) < a1 for c in [*previous, closure]):
                continue
            rows.append((rank, members, capacity - b['party_size']))
        choices.append(rows)
    best = None
    for selection in itertools.product(*choices):
        if any(clashes(considered[i], selection[i][1], considered[j], selection[j][1])
               for i in range(len(considered)) for j in range(i)):
            continue
        objective = (sum(set(b['table_ids']) != set(s[1]) for b, s in zip(considered, selection)),
                     sum(s[2] for s in selection), tuple(s[0] for s in selection))
        if best is None or objective < best[0]:
            best = objective, selection
    if best is None:
        return None
    return {'moved_count': best[0][0], 'unused_seats': best[0][1], 'assignments': [
        {'reference': b['reference'], 'table_ids': list(s[1]), 'changed': set(b['table_ids']) != set(s[1])}
        for b, s in zip(considered, best[1])]}

class StageFour(old.StageThree):
    def preview(self, table='a', start='2099-04-16T18:00:00+00:00', end='2099-04-16T23:00:00+00:00', key=None, headers=None):
        return self.write('/restaurants/r/replans', {'table_id': table, 'from': start, 'to': end}, self.m if headers is None else headers, key)
    def apply(self, plan, key=None, headers=None, restaurant='r'):
        return self.write('/restaurants/' + restaurant + '/replans/' + plan['plan_id'] + '/apply', {}, self.m if headers is None else headers, key)
    def amend(self, series, revision=None, index=0, clock='20:00', key=None, headers=None):
        return self.write('/series/' + series['series_id'] + '/amend', {'expected_revision': series['revision'] if revision is None else revision,
            'from_index': index, 'local_time': clock}, headers, key)
    def raw(self, c=None):
        # Only the request trace digests are saved by the inherited client.
        from urllib.request import urlopen
        with urlopen((c or self.c).url + '/_test/export', timeout=10) as response:
            value = response.read()
        old.operations += 1
        return value
    def transfer(self, source, destination):
        from urllib.request import Request, urlopen
        raw = self.raw(source)
        with urlopen(Request(destination.url + '/_test/import', data=raw, method='POST', headers={'Content-Type': 'application/json'}), timeout=10) as response:
            self.assertEqual(response.status, 204)
        old.operations += 1
        old.trace.append({'raw_transfer': True, 'decoded': False, 'export_bytes': len(raw), 'import_bytes': len(raw),
                          'export_sha256': hashlib.sha256(raw).hexdigest(), 'import_sha256': hashlib.sha256(raw).hexdigest()})

    def test_15_preview_objective_readonly_then_atomic_apply(self):
        a = self.expect(self.create(), 201)
        b = self.expect(self.create(members=('b',), start='2099-04-16T19:30', party=3), 201)
        bookings = [self.current(a), self.current(b)]
        before = self.export()
        plan = self.expect(self.preview(key='preview'), 201)
        expected = oracle(self.f, bookings, plan['closure'])
        for key in expected:
            self.assertEqual(plan[key], expected[key])
        after = self.export()
        for key in ('reservations', 'histories', 'restaurant_revisions', 'series', 'closures'):
            self.assertEqual(after['state'][key], before['state'][key])
        self.assertEqual(self.expect(self.preview(key='preview'), 200), plan)
        applied = self.expect(self.apply(plan, key='apply'), 201)
        self.assertEqual([r['reference'] for r in applied['reservations']], [a['reference'], b['reference']] if a['reference'] < b['reference'] else [b['reference'], a['reference']])
        self.assertEqual(applied['restaurant_revision'], plan['restaurant_revision'] + 1)
        for original in bookings:
            assignment = next(x for x in plan['assignments'] if x['reference'] == original['reference'])
            current = self.current(original)
            for key in ('reference', 'reservation_id', 'starts_at_local', 'starts_at', 'ends_at', 'party_size', 'created_at', 'accepted_terms'):
                self.assertEqual(current[key], original[key])
            self.assertEqual(current['revision'], original['revision'] + int(assignment['changed']))
            if assignment['changed']:
                entry = self.history(original)[-1]
                self.assertEqual(entry['event'], 'reassigned')
                self.assertEqual(entry['plan_id'], plan['plan_id'])
                self.assertEqual(entry['changes'], [{'field': 'table_ids', 'from': original['table_ids'], 'to': assignment['table_ids']}])
        self.assertEqual(self.expect(self.apply(plan, key='apply'), 200), applied)
        self.expect(self.apply(plan, key='different'), 409, 'plan_already_applied')
        self.transfer(self.c, self.peer)
        self.assertEqual(self.expect(self.peer.request('POST', '/restaurants/r/replans/' + plan['plan_id'] + '/apply', {}, {**self.m, 'Idempotency-Key':'apply'}), 200), applied)

    def test_16_capacity_accepted_policy_and_pair_order_identity(self):
        original = self.expect(self.create(members=('a','b'), party=6), 201)
        self.expect(self.publish(self.policy(capacities={'a':1,'b':1,'c':1})), 201)
        plan = self.expect(self.preview(table='c', key='canonical'), 201)
        self.assertEqual(plan['moved_count'], 0)
        self.assertEqual(plan['assignments'][0]['table_ids'], ['b','a'])
        applied = self.expect(self.apply(plan), 201)
        self.assertEqual(applied['reservations'][0], original)
        self.assertEqual(self.history(original)[-1]['event'], 'created')
        self.expect(self.preview(table='a'), 409, 'no_feasible_plan')

    def test_17_closures_exact_fractional_boundaries_and_explanations(self):
        a = self.expect(self.create(), 201)
        # A positive submicrosecond interval after the exact end considers none.
        tiny = self.expect(self.preview(start='2099-04-16T19:30:00.0000000000001Z', end='2099-04-16T19:30:00.0000000000002Z'), 201)
        self.assertEqual(tiny['assignments'], [])
        self.expect(self.apply(tiny), 201)
        # It touches neither [18,19:30) nor a start exactly at 19:30 after removing a.
        self.expect(self.cancel(a), 200)
        self.expect(self.create(start='2099-04-16T19:30'), 409, 'table_unavailable')
        plan = self.expect(self.preview(start='2099-04-16T19:29:59.999999999999999999Z', end='2099-04-16T19:30:00Z'), 201)
        self.assertEqual(plan['assignments'], [])
        self.expect(self.apply(plan), 201)
        slots = self.expect(self.c.request('GET','/availability?restaurant_id=r&date=2099-04-16&party_size=1&explain=true'), 200)['slots']
        for start in ('18:00','19:00','19:30'):
            slot = next(s for s in slots if s['starts_at_local'].endswith(start))
            self.assertEqual(slot['explain'][0]['rules'][1]['holds'], False)
            self.assertTrue(all('a' not in o['table_ids'] for o in slot['available_options']))
        end_plan = self.expect(self.preview(table='b',start='2099-04-16T19:30:00Z',end='2099-04-16T20:00:00Z'),201)
        self.assertEqual(end_plan['assignments'], [])
        for start,end in [('2099-04-16T19:30:00.0000000000002Z','2099-04-16T19:30:00.0000000000001Z'),('2099-04-16T19:30:00Z','2099-04-16T19:30:00+00:00'),('2099-04-16T19:00','2099-04-16T20:00Z'),('2099-02-30T19:00:00Z','2099-04-16T20:00:00Z')]:
            self.expect(self.preview(start=start,end=end),422,'validation_failed')
        # A submicrosecond before a booking's end must consider and move it.
        self.expect(self.c.request('POST','/_test/reset',self.f),204);self.h=self.login(self.c,'u');self.m=self.login(self.c,'m')
        a=self.expect(self.create(),201)
        plan=self.expect(self.preview(start='2099-04-16T19:29:59.9999999999999Z',end='2099-04-16T19:30:00Z'),201)
        self.assertEqual(plan['assignments'][0]['reference'],a['reference']);self.assertEqual(plan['moved_count'],1)

    def test_18_auth_scope_stale_apply_precedence_and_failed_keys(self):
        self.expect(self.create(),201)
        self.expect(self.preview(headers={}),401,'unauthenticated')
        self.expect(self.preview(headers=self.h),403,'forbidden')
        plan=self.expect(self.preview(),201)
        self.expect(self.apply(plan,restaurant='unknown'),404,'not_found')
        self.expect(self.publish(self.policy()),201)
        before=self.raw();self.expect(self.apply(plan,key='failed'),409,'stale_plan');self.assertEqual(self.raw(),before)
        fresh=self.expect(self.preview(),201);applied=self.expect(self.apply(fresh,key='failed'),201)
        self.expect(self.publish(self.policy()),201)
        self.assertEqual(self.expect(self.apply(fresh,key='failed'),200),applied)
        self.expect(self.apply(fresh,key='new'),409,'plan_already_applied')
        self.expect(self.write('/restaurants/r/replans/'+fresh['plan_id']+'/apply',{'invalid':True},self.m,'failed'),409,'idempotency_key_reuse')

    def test_19_full_bound_fixed_prior_closure_exhaustive_seed(self):
        rng=random.Random(202610044)
        for iteration in range(45):
            f=old.fixture(opening='17:00',duration=60)
            r=f['restaurants'][0];r['tables']=[{'id':chr(97+i),'label':'Seat '+str(i),'capacity':rng.randint(2,6)} for i in range(6)]
            r['combinable']=[['a','b'],['c','b'],['d','e'],['e','f']]
            f['reservations']=[{'id':'seed'+str(i),'reference':'ORACLE'+str(i),'user_id':'u','restaurant_id':'r','table_id':chr(97+i),
                'party_size':rng.randint(1,r['tables'][i]['capacity']),'starts_at_local':'2099-04-16T'+['18:00','18:30','19:00','19:30','20:00','20:30'][i]} for i in range(6)]
            f['reservations'].append({'id':'fixed','reference':'FIXED001','user_id':'v','restaurant_id':'r','table_id':'f','party_size':1,'starts_at_local':'2099-04-16T17:00'})
            self.expect(self.c.request('POST','/_test/reset',f),204);self.h=self.login(self.c,'u');self.m=self.login(self.c,'m');self.f=f
            prior=self.expect(self.preview(table='f',start='2099-04-16T17:00:00Z',end='2099-04-16T17:30:00Z'),201)
            self.expect(self.apply(prior),201)
            bookings=self.export()['state']['reservations']
            self.assertEqual(len(bookings),7)
            for b in bookings:
                if 'table_ids' not in b:b['table_ids']=[b['table_id']]
            closure={'table_id':rng.choice('abcdef'),'from':'2099-04-16T18:29:00Z','to':'2099-04-16T20:31:00Z'}
            expected=oracle(f,bookings,closure,[prior['closure']])
            response=self.preview(table=closure['table_id'],start=closure['from'],end=closure['to'])
            if expected is None:self.expect(response,409,'no_feasible_plan')
            else:
                plan=self.expect(response,201)
                self.assertEqual(len(plan['assignments']),6)
                for key in expected:self.assertEqual(plan[key],expected[key])
                self.expect(self.apply(plan),201)
                self.transfer(self.c,self.peer)
            old.trace.append({'oracle_seed':202610044,'iteration':iteration,'closure':closure,'expected':expected,'observed_status':response[0]})

    def test_20_infeasible_limits_and_rollback(self):
        f=old.fixture();f['restaurants'][0]['tables']=f['restaurants'][0]['tables'][:1];f['restaurants'][0]['combinable']=[]
        self.expect(self.c.request('POST','/_test/reset',f),204);self.h=self.login(self.c,'u');self.m=self.login(self.c,'m')
        self.expect(self.create(),201);before=self.raw();self.expect(self.preview(key='fail'),409,'no_feasible_plan');self.assertEqual(self.raw(),before)
        self.expect(self.preview(table='x'),404,'not_found')
        f=old.fixture();f['restaurants'][0]['tables'] += [{'id':'t'+str(i),'label':'Seat','capacity':4} for i in range(4)]
        self.expect(self.c.request('POST','/_test/reset',f),204);self.m=self.login(self.c,'m')
        self.expect(self.preview(),422,'planning_limit')

    def test_21_series_amend_eligible_original_dates_no_exceptions(self):
        anchor=self.expect(self.create(),201);s=self.expect(self.adopt(anchor,count=5),201)
        occurrences=s['occurrences'];exception=occurrences[1]['reservation'];cancelled=occurrences[2]['reservation']
        self.expect(self.patch(exception,{'starts_at_local':'2099-05-01T18:00'}),200)
        self.expect(self.cancel(cancelled),200)
        current=self.series(s);before=self.export()
        changed=self.expect(self.amend(current,clock='20:00',key='amend'),201)
        self.assertEqual(changed['revision'],current['revision']+1)
        for i,o in enumerate(changed['occurrences']):
            self.assertEqual(o['reference'],occurrences[i]['reference'])
            self.assertEqual(o['exception'],i==1)
            if i in (1,2):self.assertEqual(o['reservation'],current['occurrences'][i]['reservation'])
            else:
                self.assertEqual(o['reservation']['starts_at_local'],occurrences[i]['reservation']['starts_at_local'][:10]+'T20:00')
                self.assertEqual(o['reservation']['revision'],2)
        after=self.export();self.assertEqual(after['state']['restaurant_revisions']['r'],before['state']['restaurant_revisions']['r']+1)
        self.assertEqual(self.expect(self.amend(current,clock='20:00',key='amend'),200),changed)
        before=self.raw();self.assertEqual(self.expect(self.amend(changed,clock='20:00'),201),changed);self.assertEqual(self.raw()==before,False) # successful receipt alone changes export
        again=self.series(s);self.expect(self.amend(again,index=4,clock='21:00'),201)
        self.transfer(self.c,self.peer)
        self.assertEqual(self.expect(self.peer.request('POST','/series/'+s['series_id']+'/amend',{'expected_revision':current['revision'],'from_index':0,'local_time':'20:00'}, {**self.h,'Idempotency-Key':'amend'}),200),changed)

    def test_22_series_stale_validation_occupancy_rollback_and_failed_reuse(self):
        a=self.expect(self.create(),201);s=self.expect(self.adopt(a),201)
        for field,values in [('expected_revision',[True,0,-1,'1',1.5]),('from_index',[True,-1,3,'0',0.5]),('local_time',['1:00','24:00','20:00:00',True,None])]:
            for value in values:
                data={'expected_revision':1,'from_index':0,'local_time':'20:00',field:value}
                self.expect(self.write('/series/'+s['series_id']+'/amend',data),422,'validation_failed')
        self.expect(self.amend(s,revision=99,clock='17:00'),409,'stale_revision')
        obstruction=self.expect(self.create(start='2099-04-23T20:00'),201)
        before=self.raw();self.expect(self.amend(s,key='repair'),409,'table_unavailable');self.assertEqual(self.raw(),before)
        self.expect(self.cancel(obstruction),200);self.expect(self.amend(s,key='repair'),201)
        self.expect(self.amend(s,headers=self.v),404,'not_found')
        self.expect(self.amend(s,headers={}),401,'unauthenticated')

    def test_23_series_repaired_members_current_seating_preserved(self):
        a=self.expect(self.create(),201);s=self.expect(self.adopt(a),201)
        plan=self.expect(self.preview(),201);before=self.series(s)
        self.expect(self.apply(plan),201);current=self.series(s)
        self.assertEqual(current['revision'],before['revision']+1)
        self.assertTrue(all(not o['exception'] for o in current['occurrences']))
        amended=self.expect(self.amend(current),201)
        self.assertEqual(amended['occurrences'][0]['reservation']['table_ids'],plan['assignments'][0]['table_ids'])
        self.assertEqual(amended['occurrences'][1]['reservation']['table_ids'],['a'])
        self.transfer(self.c,self.peer)
        self.assertEqual(self.expect(self.peer.request('GET','/series/'+s['series_id'],headers=self.h),200),amended)

    def test_24_series_nonoccupancy_first_index_policy_and_noop_terms(self):
        a=self.expect(self.create(),201);s=self.expect(self.adopt(a),201)
        self.expect(self.publish(self.policy(duration=60,capacities={'a':1,'b':4,'c':3})),201)
        before=self.series(s);same=self.expect(self.amend(before,clock='18:00'),201);self.assertEqual(same,before)
        snapshot=self.raw();self.expect(self.amend(before,clock='20:00'),422,'party_exceeds_capacity');self.assertEqual(self.raw(),snapshot)
        self.expect(self.publish(self.policy(duration=60)),201)
        newer=self.expect(self.amend(before,clock='20:00'),201)
        self.assertTrue(all(o['reservation']['accepted_terms']['policy_version']==2 for o in newer['occurrences']))

    def test_25_simultaneous_apply_expected_series_revision_and_reads(self):
        a=self.expect(self.create(),201);s=self.expect(self.adopt(a),201);plan=self.expect(self.preview(),201)
        with ThreadPoolExecutor(max_workers=50) as pool:
            results=list(pool.map(lambda _:self.apply(plan,key='same'),range(50)))
        self.assertEqual([r[0] for r in results].count(201),1);self.assertEqual([r[0] for r in results].count(200),49)
        self.assertTrue(all(r[1]==results[0][1] for r in results))
        current=self.series(s)
        with ThreadPoolExecutor(max_workers=50) as pool:
            results=list(pool.map(lambda i:self.amend(current,clock='20:00' if i%2 else '21:00',key='race'+str(i)),range(50)))
        self.assertEqual([r[0] for r in results].count(201),1)
        self.assertTrue(all(r[0]==201 or (r[0]==409 and r[1]['error']['code']=='stale_revision') for r in results))
        self.transfer(self.c,self.peer)

    def test_26_genuine_three_stage_origins_receipts_and_mixed_state(self):
        for label,url in [('stage1',args.stage1),('stage2',args.stage2),('stage3',args.stage3)]:
            source=old.Client(url)
            self.expect(source.request('POST','/_test/reset',old.fixture()),204)
            auth=self.login(source,'u');manager=self.login(source,'m')
            body={'restaurant_id':'r','table_id':'a','party_size':2,'starts_at_local':'2099-04-16T18:00'}
            original=self.expect(source.request('POST','/reservations',body,{**auth,'Idempotency-Key':'genuine'}),201)
            series=None
            if label=='stage3':
                series=self.expect(source.request('POST','/series',{'anchor_reference':original['reference'],'count':4,'interval_weeks':1},{**auth,'Idempotency-Key':'genuine-series'}),201)
                self.expect(source.request('PATCH','/reservations/'+series['occurrences'][1]['reference'],{'table_id':'b'},auth),200)
                self.expect(source.request('POST','/reservations/'+series['occurrences'][2]['reference']+'/cancel',headers=auth),200)
                # Stage3 moved and cancelled members and permanent exception are real.
            self.transfer(source,self.c);self.h=auth;self.m=manager
            current=self.current(original)
            self.assertEqual(self.expect(self.c.request('POST','/reservations',body,{**auth,'Idempotency-Key':'genuine'}),200),original)
            if series is None:series=self.expect(self.adopt(current,count=4),201)
            else:series=self.series(series)
            # Source-stage manager ids were ignored before Stage3; no permission fabricated.
            if label=='stage3':
                plan=self.expect(self.preview(),201);self.expect(self.apply(plan),201);series=self.series(series)
            amended=self.expect(self.amend(series,clock='20:00',key='mixed'),201)
            self.transfer(self.c,self.peer);self.transfer(self.peer,self.c)
            self.assertEqual(self.series(series),amended)
            self.assertEqual(self.expect(self.c.request('POST','/reservations',body,{**auth,'Idempotency-Key':'genuine'}),200),original)
            self.expect(self.c.request('POST','/_test/import',{'track':'bad','format_version':1,'state':{}}),422,'validation_failed')

    def test_27_empty_eligible_and_zero_moves_counters(self):
        a=self.expect(self.create(),201);s=self.expect(self.adopt(a,count=2),201)
        for occurrence in s['occurrences']:self.expect(self.cancel(occurrence['reservation']),200)
        current=self.series(s);before=self.export()
        self.assertEqual(self.expect(self.amend(current),201),current)
        after=self.export()
        for field in ('reservations','histories','restaurant_revisions','series','closures'):self.assertEqual(after['state'][field],before['state'][field])
        plan=self.expect(self.preview(),201);applied=self.expect(self.apply(plan),201)
        self.assertEqual(applied['reservations'],[]);self.assertEqual(applied['restaurant_revision'],plan['restaurant_revision']+1)
        self.transfer(self.c,self.peer)

if __name__=='__main__':
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    began=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StageFour))
    summary={'scenarios':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'assertions':old.assertions,'operations':old.operations,'wall_seconds':time.monotonic()-began,'method':'HTTP','oracle_seed':202610044}
    (out/'trace.json').write_text(json.dumps({'summary':summary,'operations':old.trace},indent=2)+'\n')
    (out/'executed-probe.py').write_bytes(Path(__file__).read_bytes())
    (out/'executed-inherited-probe.py').write_bytes(Path(__file__).with_name('stage-3-builder-probes.py').read_bytes())
    print(json.dumps(summary));sys.exit(not result.wasSuccessful())
