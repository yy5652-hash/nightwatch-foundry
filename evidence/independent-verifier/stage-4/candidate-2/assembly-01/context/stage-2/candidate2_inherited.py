"""Fresh Stage2 interpretation of own preserved inherited probe code.

Only independent expected current representations change. Actual HTTP responses,
original receipt comparisons and the preserved first-run results remain intact.
"""
import argparse, hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;H1=HERE.parent/'stage-1'
p=argparse.ArgumentParser();p.add_argument('--family',choices=['baseline','snapshot','decoder','legacy'],required=True);a,rest=p.parse_known_args()
sys.path.insert(0,str(H1))
script={'baseline':'probe.py','snapshot':'snapshot_probe.py','decoder':'decoder_probe.py','legacy':'legacy_receipts_current.py'}[a.family]
source=(H1/script).read_text();original_hash=hashlib.sha256(source.encode()).hexdigest()
if a.family=='baseline':
    old='all(value[k] == r[k] for k in r if k != "table_id")'
    assert source.count(old)==1
    source=source.replace(old,'all(value[k] == r[k] for k in r if k not in ("table_id", "table_ids")) and value.get("table_ids") == ["t2"]')
elif a.family=='decoder':
    old='expected_moves=[dict(original,table_id="b"),dict(second[1],table_id="a")]';assert source.count(old)==1
    source=source.replace(old,'expected_moves=[dict(original,table_id="b",table_ids=["b"]),dict(second[1],table_id="a",table_ids=["a"])]')
elif a.family=='snapshot':
    import snapshot_oracle as oracle
    original_projected=oracle.projected;original_availability=oracle.expected_availability
    def projected(originals,generation):
        return [dict(row,table_ids=[row['table_id']]) for row in original_projected(originals,generation)]
    def availability():
        result=original_availability()
        for slot in result['slots']:
            slot['available_options']=[dict(table_ids=[table],capacity=64) for table in slot['available_table_ids']]
        return result
    oracle.projected=projected;oracle.expected_availability=availability
else:
    # Old public receipts remain unchanged. Only current-view expectations gain seating.
    for suffix in ['',', base=args.peer']:
        old='p.call("GET", "/reservations/"+old["reference"], token=old_token'+suffix+') == (200, old)'
        assert source.count(old)==1
        source=source.replace(old,'p.call("GET", "/reservations/"+old["reference"], token=old_token'+suffix+') == (200, dict(old, table_ids=[old["table_id"]]))')
    old='p.call("GET", "/reservations/"+future["reference"], token=old_token) == (200, cancelled)';assert source.count(old)==1
    source=source.replace(old,'p.call("GET", "/reservations/"+future["reference"], token=old_token) == (200, dict(cancelled,table_ids=[cancelled["table_id"]]))')
out=Path(rest[rest.index('--out')+1]);out.parent.mkdir(parents=True,exist_ok=True)
(out.parent/(a.family+'-executed-source.py')).write_text(source)
(out.parent/(a.family+'-source-binding.json')).write_text(json.dumps(dict(original_script=script,original_sha256=original_hash,executed_sha256=hashlib.sha256(source.encode()).hexdigest(),wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Own expectation adaptation to complete Stage2 current representation; immutable original receipts never enriched; first run source/results preserved.'),indent=2)+'\n')
sys.argv=[str(H1/script)]+rest
exec(compile(source,str(H1/script),'exec'),{'__name__':'__main__','__file__':str(H1/script)})
