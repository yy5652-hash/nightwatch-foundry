"""Independent serial-prefix oracle for apply versus six real writer families."""
import argparse,copy,json,sys,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from candidate2_atomic import prepare,sha
from stage4_probe import Client,integer,same,raw,DAY
from semantic_oracle import parse

def run(c,release):
    traces=[]
    for kind in ['create','patch','cancel','policy','moves','series']:
        for wave in range(4):
            s,t,_=prepare(c)
            a=c.make(('e',),'2035-07-02T21:00',key='out-a');b=c.make(('f',),'2035-07-02T21:00',key='out-b')
            plan=c.preview(dict(table_id='a',**{'from':DAY+'T17:00:00+00:00'},to='2035-06-18T20:00:00+00:00'),key='race-preview')
            original=parse(c.export())['state'];refs=[x['reference'] for x in plan['assignments']];assignment={x['reference']:x for x in plan['assignments']}
            key='writer-'+kind;applykey='apply-'+kind;barrier=threading.Barrier(50)
            if kind=='create':path='/reservations';body=dict(restaurant_id='r',table_ids=['e'],starts_at_local='2035-07-03T21:00',party_size=1);method='POST';who='u'
            elif kind=='patch':path='/reservations/'+a['reference'];body=dict(party_size=2);method='PATCH';who='u'
            elif kind=='cancel':path='/reservations/'+a['reference']+'/cancel';body={};method='POST';who='u'
            elif kind=='moves':path='/reservation-moves';body=dict(moves=[dict(reference=a['reference'],table_ids=['f']),dict(reference=b['reference'],table_ids=['e'])]);method='POST';who='u'
            elif kind=='series':path='/series/'+s['series_id']+'/amend';body=dict(expected_revision=c.current_series(s)['revision'],from_index=0,local_time='20:00');method='POST';who='u'
            else:
                r=c.response('race-detail',c.call('GET','/restaurants/r'),200);path='/restaurants/r/policies';body={k:copy.deepcopy(r[k]) for k in ['slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','opening_hours']};body.update(effective_from=DAY,capacities={x['id']:8 for x in r['tables']});method='POST';who='m'
            def op(i):
                barrier.wait()
                if i==0:return c.apply(plan,key=applykey)
                if i==1:return c.call(method,path,body,token=c.tokens[who],key=key)
                return c.call('GET','/_test/export',decode=False)
            with ThreadPoolExecutor(max_workers=50) as pool:result=list(pool.map(op,range(50)))
            applied=result[0][0]==201;written=result[1][0] in [200,201]
            c.response('race-apply-serial',result[0],201 if applied else 409,None if applied else 'stale_plan')
            c.response('race-writer-serial',result[1],(200 if kind in ['patch','cancel'] else 201) if written else 409,None if written else 'stale_revision')
            c.check('race-serial-winners',written and (not applied or kind!='series') or applied and not written and kind=='series')
            snapshots=[*result[2:],c.call('GET','/_test/export',decode=False)]
            original_by={r['reference']:r for r in original['reservations']};series_refs={o['reference'] for o in original['series'][s['series_id']]['occurrences'] if not o['exception']}
            for i,response in enumerate(snapshots):
                c.response('race-export',response,200);state=parse(response[2])['state'];current={r['reference']:r for r in state['reservations']}
                has_apply=state['plans'][plan['plan_id']]['applied'];has_writer=(len(current)>len(original_by) if kind=='create' else current[a['reference']]['party_size']!=original_by[a['reference']]['party_size'] if kind=='patch' else current[a['reference']]['status']=='cancelled' if kind=='cancel' else bool(state['policies']['r']) if kind=='policy' else current[a['reference']]['table_ids']==['f'] if kind=='moves' else any(current[r]['starts_at_local'][-5:]=='20:00' for r in series_refs))
                c.check('race-serial-prefix-counter',integer(state['restaurant_revisions']['r'])==integer(original['restaurant_revisions']['r'])+int(has_apply)+int(has_writer))
                c.check('race-plan-closure-whole',sum(x['plan_id']==plan['plan_id'] for x in state['closures'])==int(has_apply))
                for ref in refs:
                    old=original_by[ref];now=current[ref];move=has_apply and assignment[ref]['changed'];amend=kind=='series' and has_writer and ref in series_refs
                    c.check('race-member-serialized-record',same(now['table_ids'],assignment[ref]['table_ids'] if move else old['table_ids']) and integer(now['revision'])==integer(old['revision'])+int(move)+int(amend) and now['starts_at_local']==(old['starts_at_local'][:11]+'20:00' if amend else old['starts_at_local']))
                    c.check('race-member-immutable',all(same(now[k],old[k]) for k in ['reservation_id','reference','user_id','party_size','created_at','accepted_terms']))
                    events=state['histories'][ref];c.check('race-history-whole',len(events)==len(original['histories'][ref])+int(move)+int(amend) and sum(e.get('plan_id')==plan['plan_id'] for e in events)==int(move))
                for agreement in [s,t]:
                    sid=agreement['series_id'];moved=has_apply and any(assignment[o['reference']]['changed'] for o in agreement['occurrences']);changed=has_writer and kind=='series' and sid==s['series_id']
                    c.check('race-agreement-counter-flags',integer(state['series'][sid]['revision'])==integer(original['series'][sid]['revision'])+int(moved)+int(changed) and [o['exception'] for o in state['series'][sid]['occurrences']]==[o['exception'] for o in original['series'][sid]['occurrences']])
                c.check('race-serial-order',not(has_apply and has_writer and kind=='series'))
                c.response('race-detached-prefix-import',c.transfer(c.base,release['urls']['peer'],response[2]),204)
                traces.append(dict(kind=kind,wave=wave,index=i,apply=has_apply,writer=has_writer,bytes=len(response[2]),sha256=sha(response[2]),private_bytes_saved=False))
            if applied:c.response('race-original-apply-replay',c.apply(plan,key=applykey),200)
            elif kind!='series':c.response('race-failed-apply-key-reusable',c.apply(c.preview(key='new-plan'),key=applykey),201)
    c.saved_artifacts={'serial-prefix-traces.json':raw(traces)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate(json.loads(Path(a.release).read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
    try:run(c,release)
    except BaseException as exc:error=repr(exc);raise
    finally:
        c.save(error)
        for name,data in getattr(c,'saved_artifacts',{}).items():(c.out/name).write_bytes(data)
if __name__=='__main__':main()
