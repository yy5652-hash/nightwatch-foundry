"""Genuine old ignored fields preserve original meaning and exact retry identity."""
import argparse
from api import PairProbe,fixture,DAY
def main():
    p=argparse.ArgumentParser()
    for k in ['base','peer','legacy','candidate','out']:p.add_argument('--'+k,required=True)
    a=p.parse_args();a.case='ignored-upgrade';q=PairProbe(a);q.setup(fixture(tables=3),base=a.legacy)
    body=dict(restaurant_id='r',table_id='t0',table_ids={'previously':'ignored'},starts_at_local=DAY+'T18:10',party_size=2)
    status,original=q.call('POST','/reservations',body,token=q.a,key='ignored-create',base=a.legacy)
    q.check('legacy-ignored-create-source',status==201 and 'table_ids'not in original)
    batch={'moves':[dict(reference=original['reference'],table_id='t1',table_ids=17)]}
    status,receipt=q.call('POST','/reservation-moves',batch,token=q.a,key='ignored-moves',base=a.legacy)
    q.check('legacy-ignored-batch-source',status==201 and 'table_ids'not in receipt['reservations'][0])
    snapshot=q.state(base=a.legacy)
    for target in [a.base,a.peer]:
        status,_=q.call('POST','/_test/import',snapshot,base=target)
        q.check('legacy-ignored-import',status==204)
        q.check('legacy-ignored-create-replay',q.call('POST','/reservations',body,token=q.a,key='ignored-create',base=target)==(200,original))
        q.check('legacy-ignored-batch-replay',q.call('POST','/reservation-moves',batch,token=q.a,key='ignored-moves',base=target)==(200,receipt))
        q.expect('legacy-ignored-create-new','POST','/reservations',body,token=q.a,key='new-ignored-create',base=target,status=422,code='validation_failed')
        q.expect('legacy-ignored-batch-new','POST','/reservation-moves',batch,token=q.a,key='new-ignored-batch',base=target,status=422,code='validation_failed')
        q.expect('legacy-ignored-key-conflict','POST','/reservations',dict(body,party_size=0),token=q.a,key='ignored-create',base=target,status=409,code='idempotency_key_reuse')
    raise SystemExit(bool(q.finish()))
if __name__=='__main__':main()
