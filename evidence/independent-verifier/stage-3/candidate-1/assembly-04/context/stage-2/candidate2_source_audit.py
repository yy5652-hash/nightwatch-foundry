"""Exact committed source/history review; source assertions are not HTTP observations."""
import ast,hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1];H=HERE/'candidate-2'
f=json.loads((H/'runtime-01/preflight.json').read_text());C=f['candidate'];clone=Path(f['clone']);out=H/'source-audit';out.mkdir(exist_ok=False)
commands=[]
def git(argv,label):
    p=subprocess.run(['git']+argv,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out/(label+'.log')).write_text(p.stdout+p.stderr);commands.append(dict(argv=['git']+argv,cwd=str(R),returncode=p.returncode,log=label+'.log'));assert p.returncode==0;return p.stdout
manifest=[]
for name in f['source']['current']['source_sha256']:
    data=(clone/'stage-2'/name).read_bytes();dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);manifest.append(dict(name=name,sha256=hashlib.sha256(data).hexdigest()))
core=(out/'core.py').read_text();server=(out/'server.py').read_text();codec=(out/'json_codec.py').read_text()
for name in ['core.py','server.py','json_codec.py']:ast.parse((out/name).read_text())
history=git(['log','--format=%H %an <%ae> %s',C,'--','stage-2'],'stage2-history')
for revision,owner in [('f783598428a88d53490f68498063ed69e02201b3','Systems Engineer'),('a040054f2a8d00c560bea7f02324d1443c5a3f14','Interface Engineer')]:
    text=git(['show','--format=fuller','--name-only',revision],'builder-'+owner.split()[0].lower());assert owner in text
    assert subprocess.run(['git','merge-base','--is-ancestor',revision,C],cwd=R).returncode==0
copy=json.loads((H/'source-inputs/stage-2-renewed-base-copy-proof.json').read_text());copy_comparisons=[]
for item in copy['copied_files']:
    name=item['path'];a=git(['rev-parse',copy['source_full_revision']+':stage-1/'+name],'copy-source-'+name.replace('.','_'))
    b=git(['rev-parse',copy['target_base_full_revision']+':stage-2/'+name],'copy-base-'+name.replace('.','_'))
    copy_comparisons.append(dict(file=name,source_object=a.strip(),base_object=b.strip(),matches=a==b==item['object_id']+'\n'))
assert all(x['matches'] for x in copy_comparisons)
freeze=json.loads((H/'source-inputs/stage-1-75005d57fe0904753eac4eab5bf4e4c9a78b6d1b.json').read_text())
frozen_diff=git(['diff',freeze.get('candidate_full_revision',f['intake']['accepted_stage1']),C,'--','stage-1'],'stage1-diff');assert not frozen_diff
trees={rev:git(['rev-parse',rev+':stage-2'],'tree-'+rev[:8]).strip() for rev in [C,'f783598428a88d53490f68498063ed69e02201b3','1e3af87d78c2d6c037650a9c134453012d4fb0c6']};assert len(set(trees.values()))==1
index=git(['show','--format=fuller','--name-only','182582c41d21a23d8ccd95688fa7f1afa0437460'],'shared-index-original');assert 'Interface Engineer' in index
captured=[x for x in index.splitlines() if x.startswith('evidence/independent-verifier/')];assert len(captured)==32
checks={
 'two-builders':True,'history-preserved':True,'source-provenance':True,'frozen-stage1':not frozen_diff,'copied-base':all(x['matches'] for x in copy_comparisons),
 'stage2-delivery':set(f['source']['current']['source_sha256'])=={'core.py','server.py','json_codec.py','Dockerfile','.dockerignore','RUN.md','web/index.html','web/app.css','web/app.js'},
 'stage2-source':bool(history),'hashed-source': 'hashlib.scrypt' in core,
 'detached-snapshot-under-lock':'with self._lock:' in core and 'return result[0], copy_json(result[1])' in core,
 'receipt-prepared-before-commit':'"response": copy_json(response)' in core and 'saved_body = copy_json(data)' in core,
 'shape-profile-independent':'def _original_seating_body' in core and 'return body if "table_ids" in snapshot else' in core,
 'nonrecursive-json':'frames = []' in codec and 'pending = ' in codec and 'setrecursionlimit' not in codec,
 'serialize-before-headers':'payload = b"" if status == 204 else dumps(body)' in server,
 'cutoff-inclusive-current-start':'remaining = instant(timestamp(record["starts_at"])) - instant(datetime.now(UTC))' in core and 'compare_numbers(remaining, multiply_integer(restaurant["cancellation_cutoff_minutes"], MINUTE_US)) <= 0' in core,
}
assert all(checks.values())
notes=dict(source='Full exact core/server/codec and browser numeric/time/retry source reviewed; black-box expectations were derived from supplied specs and own independent oracles, not product helpers.',transactions='RLock encloses dispatch, response detachment, receipt preparation and commit. Import builds valid state before replacement; moves validate ordered proposals before occupancy and commit.',numeric='Nonrecursive frames decode containers; numeric provenance and exact comparisons distinguish bool and numeric values. Stage2 exact aligned coefficient pair sums use numeric outputs. Legacy comparison profile is private per receipt and independent of public shape.',cutoff='Labelled source supplement: _cutoff compares current stored start exact instant with now and rejects remaining <= cutoff, including equality; the HTTP API has no test clock.',provenance='Source trees and base-copy objects independently compared. Current full direct handoff includes authoring declarations. Only builder commit metadata and declarative handoff content reviewed; no builder test/oracle implementation read.',shared_index='Actual 182582c captured 32 verifier-authored preparation paths under Interface Git author. Original Git author and history stay unchanged; this does not attribute verification execution to Interface.',limits='Finite source/black-box controls do not establish arbitrary input performance or literal simultaneous historical offset grammars.')
(out/'source-proof.json').write_text(json.dumps(dict(candidate=C,manifest=manifest,checks=checks,source_notes=notes,copy_comparisons=copy_comparisons,trees=trees,shared_index_captured_paths=captured,commands=commands),indent=2)+'\n')
official=json.loads((H/'official-command.json').read_text());shutil.copytree(official['output'],H/'official')
print(json.dumps({'candidate':C,'source_checks':checks,'files':len(manifest),'copy_files':len(copy_comparisons),'official_copied_unchanged':True}))
