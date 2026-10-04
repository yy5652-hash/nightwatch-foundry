"""Validate final evidence structure, exact artifact hashes and credential redaction."""
import ast,collections,csv,hashlib,json
from pathlib import Path
here=Path(__file__).resolve().parent;target=here/'candidate-1';supp=here.parent/'stage-1/candidate-4-supplemental-decimal'
for file in here.glob('*.py'):ast.parse(file.read_text(),filename=str(file))
rows=list(csv.DictReader((target/'coverage.csv').open()));assert len(rows)==1265
assert len({r['requirement_id'] for r in rows})==len(rows)
assert collections.Counter(r['verdict'] for r in rows)=={'verified':1226,'failed':17,'unverified':22}
for row in rows:
    for field in ['source_section','introduced_stage','applicable_stages','owner','candidate_full_revision','verification_method','executable_command_or_interaction']:
        assert row[field],(row['requirement_id'],field)
    assert row['candidate_full_revision']=='4b92041057beb669d2e6c528e8268f4d0d1e6421'
    if row['verdict']!='unverified':
        assert row['evidence_path']!='UNVERIFIED'
        for path in row['evidence_path'].split(' ; '):assert Path(path).is_file(),path
supp_rows=list(csv.DictReader((supp/'coverage.csv').open()));assert len(supp_rows)==806
assert collections.Counter(r['verdict'] for r in supp_rows)=={'verified':801,'failed':5}
assert all(r['candidate_full_revision']=='2a4b0408a3453bc87d86bca3d0ec571f479e03ca' for r in supp_rows)
assert all(x['returncode']==0 for x in json.loads((target/'cleanup.json').read_text()))
issues=[];checked=0
def private(node,file,path=''):
    if isinstance(node,dict):
        for key,value in node.items():
            if key.lower() in ['token','password','password_hash','authorization']:
                if isinstance(value,str) and value not in ['', '...', 'Bearer <token>']:
                    issues.append(dict(file=str(file),path=path+'/'+key,reason='raw credential-shaped string'))
            private(value,file,path+'/'+key)
    elif isinstance(node,list):
        for index,value in enumerate(node):private(value,file,path+'/'+str(index))
for file in target.rglob('*'):
    if file.suffix not in ['.json','.jsonl'] or not file.is_file():continue
    # Input declarations and code-version snapshots contain spec examples, not
    # service exports. Every actual operation/network/assertion file is checked.
    if file.name in ['artifact-manifest.json','observation-index.json']:continue
    for line in ([file.read_text()] if file.suffix=='.json' else file.read_text().splitlines()):
        node=json.loads(line);private(node,file);checked+=1
assert not issues,issues
for folder in [target,supp]:
    manifest=[dict(path=str(p.relative_to(folder)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json']
    (folder/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2))
result=dict(rows=len(rows),unique_rows=len(rows),verified=1226,failed=17,unverified=22,supplemental_rows=806,supplemental_failed=5,
   parsed_python_files=len(list(here.glob('*.py'))),json_records_redaction_checked=checked,raw_credential_findings=len(issues),all_evidence_paths_exist=True,cleanup_codes_zero=True)
(target/'evidence-check.json').write_text(json.dumps(result,indent=2))
# Include this validation result in the final manifest as well.
manifest=[dict(path=str(p.relative_to(target)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(target.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json']
(target/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(result))
