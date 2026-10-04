"""Actual raw serial prefixes, detached replacement and single-field corruption."""
import argparse,copy,hashlib,json,sys,threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from stage4_probe import Client,closure,DAY,raw,same,integer
from stage3_probe import parse
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare(c):
    c.seed();s=c.adopt(c.make(key='a'),count=3,key='s');t=c.adopt(c.make(local=DAY+'T19:00',key='b'),count=3,key='t')
    c.response('atomic-exception',c.call('PATCH','/reservations/'+s['occurrences'][1]['reference'],dict(party_size=2),token=c.tokens['u']),200)
    p=c.preview(closure(start=DAY+'T17:00:00+00:00',end='2035-06-18T20:00:00+00:00'))
    return s,t,p
def prefix(c,release):
    snapshots=[]
    for wave in range(5):
        s,t,p=prepare(c);before=c.export();original=c.public_state();barrier=threading.Barrier(50)
        def operation(i):
            barrier.wait()
            return c.apply(p,key='whole-'+str(wave)) if i==0 else c.call('GET','/_test/export',decode=False)
        with ThreadPoolExecutor(max_workers=50) as pool:responses=list(pool.map(operation,range(50)))
        applied=c.response('atomic-prefix-apply',responses[0],201);after=c.export();final=c.public_state()
        for index,response in enumerate(responses[1:]):
            c.response('atomic-prefix-export',response,200);body=response[2]
            c.check('atomic-prefix-whole-state',body in [before,after])
            c.response('atomic-prefix-independent-import',c.transfer(c.base,release['urls']['peer'],body),204)
            base=c.base;c.base=release['urls']['peer']
            try:current=c.public_state()
            finally:c.base=base
            c.check('atomic-prefix-public-history-counters',same(current,original if body==before else final))
            if body==after:
                replay=c.response('atomic-prefix-original-apply-receipt',c.call('POST','/restaurants/r/replans/'+p['plan_id']+'/apply',{},token=c.tokens['m'],key='whole-'+str(wave),url=release['urls']['peer']),200)
                c.check('atomic-prefix-receipt',same(replay,applied))
            snapshots.append(dict(wave=wave,index=index,bytes=len(body),sha256=sha(body),prefix='before' if body==before else 'after',unchanged_raw_transfer=True,private_bytes_saved=False))
    c.saved_artifacts={'raw-prefix-traces.json':(json.dumps(snapshots,indent=2)+'\n').encode()}
def invalid(c,release):
    s,t,p=prepare(c);c.response('atomic-invalid-apply',c.apply(p),201)
    c.response('atomic-invalid-cancel',c.call('POST','/reservations/'+s['occurrences'][2]['reference']+'/cancel',{},token=c.tokens['u']),200)
    before=c.export();template=parse(before);pid=p['plan_id'];sid=s['series_id'];ref=p['assignments'][0]['reference']
    def change(kind,state):
        plan=state['plans'][pid]
        if kind=='plans-wrongtype':state['plans']=[]
        elif kind=='closure-list-wrongtype':state['closures']={}
        elif kind=='plan-id':plan['plan_id']='missing'
        elif kind=='plan-applied-type':plan['applied']=1
        elif kind=='plan-revision-negative':plan['restaurant_revision']=-1
        elif kind=='plan-revision-future':plan['restaurant_revision']=999
        elif kind=='plan-closure-type':plan['closure']['from']=None
        elif kind=='plan-closure-order':plan['closure']['to']=plan['closure']['from']
        elif kind=='plan-originals-shape':plan['originals']={}
        elif kind=='plan-assignment-count':plan['assignments'].pop()
        elif kind=='plan-assignment-reference':plan['assignments'][0]['reference']='missing'
        elif kind=='plan-changed-type':plan['assignments'][0]['changed']=1
        elif kind=='plan-changed-truth':plan['assignments'][0]['changed']=not plan['assignments'][0]['changed']
        elif kind=='plan-moved-objective':plan['moved_count']=99
        elif kind=='plan-unused-objective':plan['unused_seats']=-1
        elif kind=='closure-plan-link':state['closures'][0]['plan_id']='missing'
        elif kind=='closure-restaurant-link':state['closures'][0]['restaurant_id']='other'
        elif kind=='closure-interval-link':state['closures'][0]['to']='2035-06-19T20:00:00+00:00'
        elif kind=='closure-duplicate':state['closures'].append(copy.deepcopy(state['closures'][0]))
        elif kind=='closure-omitted':state['closures']=[]
        elif kind=='history-plan-link':next(e for e in state['histories'][ref] if e['event']=='reassigned')['plan_id']='missing'
        elif kind=='history-terms':state['histories'][ref][-1]['accepted_terms']['capacities']['a']=99
        elif kind=='series-index':state['series'][sid]['occurrences'][1]['index']=999
        elif kind=='series-reference':state['series'][sid]['occurrences'][1]['reference']='missing'
        elif kind=='series-schedule':state['series'][sid]['occurrences'][1]['scheduled_starts_at_local']='invalid'
        elif kind=='series-exception-type':state['series'][sid]['occurrences'][1]['exception']=1
        elif kind=='counter-negative':state['restaurant_revisions']['r']=-1
        else:raise ValueError(kind)
    cases=['plans-wrongtype','closure-list-wrongtype','plan-id','plan-applied-type','plan-revision-negative','plan-revision-future','plan-closure-type','plan-closure-order','plan-originals-shape','plan-assignment-count','plan-assignment-reference','plan-changed-type','plan-changed-truth','plan-moved-objective','plan-unused-objective','closure-plan-link','closure-restaurant-link','closure-interval-link','closure-duplicate','closure-omitted','history-plan-link','history-terms','series-index','series-reference','series-schedule','series-exception-type','counter-negative']
    traces=[]
    for kind in cases:
        rejection_before=c.export();altered=copy.deepcopy(template);change(kind,altered['state']);payload=raw(altered)
        c.response('atomic-invalid-'+kind,c.call('POST','/_test/import',body=payload),422,'validation_failed')
        c.check('atomic-invalid-'+kind+'-unchanged',rejection_before==c.export())
        c.response('atomic-invalid-original-accepted',c.transfer(c.base,c.base,before),204)
        c.check('atomic-invalid-original-preserved',same(template,parse(c.export())))
        traces.append(dict(case=kind,request_bytes=len(payload),request_sha256=sha(payload),expected_status=422,private_payload_saved=False))
    c.saved_artifacts={'corruption-traces.json':(json.dumps(traces,indent=2)+'\n').encode()}
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);p.add_argument('--family',choices=['prefix','invalid'],required=True);a=p.parse_args();release=validate(json.loads(Path(a.release).read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
    try:(prefix if a.family=='prefix' else invalid)(c,release)
    except BaseException as exc:error=repr(exc);raise
    finally:
        c.save(error)
        for name,data in getattr(c,'saved_artifacts',{}).items():(c.out/name).write_bytes(data)
if __name__=='__main__':main()
