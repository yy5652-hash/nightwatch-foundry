"""Stage 2 seating changes update both representations; omitted independent fields retain values."""
import argparse
from api import PairProbe
def main():
    p=argparse.ArgumentParser()
    for name in ['base','peer','candidate','out']: p.add_argument('--'+name,required=True)
    a=p.parse_args(); a.case='amend-retained'; probe=PairProbe(a); probe.setup()
    original=probe.create(probe.body(['t0']))
    status,current=probe.call('PATCH','/reservations/'+original['reference'],{'table_id':'t1'},token=probe.a)
    retained=[k for k in original if k not in {'table_id','table_ids','revision'}]
    probe.results.append(dict(requirement_id='TK1-patch-retain-omitted',passed=status==200 and current["revision"]==original["revision"]+1 and all(current[k]==original[k] for k in retained),expected={k:original[k] for k in retained},observed={k:current.get(k) for k in retained}))
    probe.check('amend-seating-derived',current.get('table_id')=='t1' and current.get('table_ids')==['t1'],{'table_id':'t1','table_ids':['t1']},current)
    raise SystemExit(bool(probe.finish()))
if __name__=='__main__': main()
