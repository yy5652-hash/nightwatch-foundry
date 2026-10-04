"""Explicit specification-derived current-view expectations for own old clients.

Source responses are untouched. Original receipt equality remains exact; only
independently expected amendment generations/current representations change.
"""
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;H1=HERE.parent/'stage-1';H2=HERE.parent/'stage-2'
p=argparse.ArgumentParser();p.add_argument('--family',choices=['baseline','snapshot','decoder','retained-amend','general','old-supplement'],required=True);a,rest=p.parse_known_args()
sys.path.insert(0,str(H1))
script={'baseline':'probe.py','snapshot':'snapshot_probe.py','decoder':'decoder_probe.py','retained-amend':'amend_retained.py','general':'browser.py','old-supplement':'candidate2_supplement.py'}[a.family]
origin=H2 if a.family in ('retained-amend','general','old-supplement') else H1
if origin==H2:sys.path.insert(0,str(H2))
source=(origin/script).read_text();original_hash=hashlib.sha256(source.encode()).hexdigest()
if a.family=='old-supplement':
 old="{'restaurant_id':[rid],'date':[DAY],'party_size':[digits]}";assert source.count(old)==1
 source=source.replace(old,"{'restaurant_id':[rid],'date':[DAY],'party_size':[digits],'explain':['true']}")
elif a.family=='general':
 old='await page.get_by_test_id("party-size-input").get_attribute("type")=="number"';assert source.count(old)==1
 source=source.replace(old,'await page.get_by_test_id("party-size-input").get_attribute("role")=="spinbutton" and await page.get_by_test_id("party-size-input").get_attribute("inputmode")=="numeric" and await page.get_by_test_id("party-size-input").is_visible()')
 old='dict(restaurant_id=["r"],date=[DAY],party_size=["2"]) in queries';assert source.count(old)==1
 source=source.replace(old,'dict(restaurant_id=["r"],date=[DAY],party_size=["2"],explain=["true"]) in queries')
elif a.family=='retained-amend':
 source=source.replace("{'table_id','table_ids'}","{'table_id','table_ids','revision'}")
 source=source.replace('status==200 and all(current[k]==original[k] for k in retained)','status==200 and current["revision"]==original["revision"]+1 and all(current[k]==original[k] for k in retained)')
elif a.family=='baseline':
 old='all(value[k] == r[k] for k in r if k != "table_id")';assert source.count(old)==1
 source=source.replace(old,'all(value[k] == r[k] for k in r if k not in ("table_id", "table_ids", "revision")) and value.get("table_ids") == ["t2"] and value.get("revision") == r["revision"]+1')
elif a.family=='decoder':
 old='expected_moves=[dict(original,table_id="b"),dict(second[1],table_id="a")]';assert source.count(old)==1
 source=source.replace(old,'expected_moves=[dict(original,table_id="b",table_ids=["b"],revision=original["revision"]+1),dict(second[1],table_id="a",table_ids=["a"],revision=second[1]["revision"]+1)]')
else:
 import snapshot_oracle as oracle
 original_projected=oracle.projected;original_availability=oracle.expected_availability
 def projected(originals,generation):
  return [dict(row,table_ids=[row['table_id']],revision=originals[index]['revision'].small_integer()+generation) for index,row in enumerate(original_projected(originals,generation))]
 def availability():
  result=original_availability()
  for slot in result['slots']:slot['available_options']=[dict(table_ids=[table],capacity=64) for table in slot['available_table_ids']]
  return result
 oracle.projected=projected;oracle.expected_availability=availability
out=Path(rest[rest.index('--out')+1]);out.parent.mkdir(parents=True,exist_ok=True)
(out.parent/(a.family+'-executed-source.py')).write_text(source)
(out.parent/(a.family+'-source-binding.json')).write_text(json.dumps(dict(original_script=script,original_sha256=original_hash,
 executed_sha256=hashlib.sha256(source.encode()).hexdigest(),wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 scope='Current Stage 3 expected real amendment revisions and Stage 2 seating; no response transformation or original receipt enrichment.'),indent=2)+'\n')
sys.argv=[str(origin/script)]+rest
exec(compile(source,str(origin/script),'exec'),{'__name__':'__main__','__file__':str(origin/script)})
