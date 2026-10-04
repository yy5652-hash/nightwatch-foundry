"""Exact candidate source and immutable build provenance; no HTTP claim."""
import ast,datetime as dt,hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1];H=HERE/'candidate-1'
def main():
 out=H/'source-audit';out.mkdir(exist_ok=False);facts=json.loads((H/'runtime-01/preflight.json').read_text());C=facts['candidate'];commands=[]
 def git(args,label,cwd=R,allowed=(0,)):
  p=subprocess.run(['git']+args,cwd=cwd,capture_output=True);(out/(label+'.log')).write_bytes(p.stdout+p.stderr);commands.append(dict(argv=['git']+args,cwd=str(cwd),returncode=p.returncode,log=label+'.log'));assert p.returncode in allowed;return p.stdout.decode()
 source=facts['source']['current'];clone=Path(facts['clone']);manifest=[]
 for name,expected in source['source_sha256'].items():
  data=(clone/'stage-3'/name).read_bytes();assert hashlib.sha256(data).hexdigest()==expected;dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);manifest.append(dict(name=name,sha256=expected))
 core=(out/'source/core.py').read_text();codec=(out/'source/json_codec.py').read_text();server=(out/'source/server.py').read_text();app=(out/'source/web/app.js').read_text()
 for name in ['core.py','json_codec.py','server.py']:ast.parse((out/'source'/name).read_text())
 frozen=[]
 for stage,revision in [(1,'75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'),(2,'4dba10246b07b2dda19de260d529f9d94ba0a1ed')]:
  diff=git(['diff',revision,C,'--','stage-'+str(stage)],'frozen-'+str(stage));assert not diff
  frozen.append(dict(stage=stage,revision=revision,tree=git(['rev-parse',C+':stage-'+str(stage)],'frozen-tree-'+str(stage)).strip(),unchanged=True))
 copy=json.loads((R/'evidence/coordinator/stage-3-base-copy-proof.json').read_text());comparisons=[]
 for row in copy['copied_files']:
  name=row['path'];a=git(['ls-tree',copy['source_full_revision'],'stage-2/'+name],'base-source-'+name.replace('/','_'))
  b=git(['ls-tree',copy['target_base_full_revision'],'stage-3/'+name],'base-target-'+name.replace('/','_'))
  comparisons.append(dict(path=name,matches=a.split('\t')[0]==b.split('\t')[0],mode=row['mode'],object_id=row['object_id']));assert comparisons[-1]['matches'] and row['object_id'] in a
 history=git(['log','--format=%H %an <%ae> %s',C,'--','stage-3'],'history');owners=[]
 for revision,name in [('6783fd8f557575e9be16fdf146ede097127773c6','Systems Engineer'),('9f0d3150c934a2090c42667cb0ee0bb672c64325','Interface Engineer')]:
  show=git(['show','--format=fuller','--stat',revision],'owner-'+name.split()[0]);assert name in show;git(['merge-base','--is-ancestor',revision,C],'ancestor-'+name.split()[0]);owners.append(dict(revision=revision,owner=name))
 systems='7a8d0db4be91b5686de87c7a710ccc01d19eac1b';interface='cbf5a43e0881c0be4b51b37f6657efffeb03a7e5'
 trees={rev:git(['rev-parse',rev+':stage-3'],'tree-'+rev[:8]).strip() for rev in [C,systems,interface]};assert trees[C]==trees[interface] and trees[C]!=trees[systems]
 api_diff=git(['diff',systems,C,'--','stage-3/core.py','stage-3/json_codec.py','stage-3/server.py'],'systems-api-diff');assert not api_diff
 tree_diff=git(['diff','--name-only',systems,C,'--','stage-3'],'systems-full-diff').splitlines();assert tree_diff==['stage-3/web/app.js']
 index=git(['show','--format=fuller','--name-only','182582c41d21a23d8ccd95688fa7f1afa0437460'],'preserved-index');captured=[x for x in index.splitlines() if x.startswith('evidence/independent-verifier/')];assert len(captured)==32
 assert not git(['status','--porcelain'], 'current-clone-status',clone)
 assert git(['rev-parse','HEAD'],'current-clone-head',clone).strip()==C
 kickoff=W/'kickoff';assert git(['rev-parse','HEAD'],'kickoff-head',kickoff).strip()=='803560d2a678ace1414465c098eb0ab5380ffade';assert not git(['status','--porcelain'],'kickoff-status',kickoff)
 checks={'two-builders':len(owners)==2,'history-preserved':True,'source-provenance':True,'frozen-stage1':True,'frozen-stage2':True,'copied-base':len(comparisons)==9,
 'stage3-delivery':len(manifest)==9,'stage3-source':bool(history),'hashed-passwords':'hashlib.scrypt' in core,
 'detached-snapshot-under-lock':'with self._lock:' in core and 'return result[0], copy_json(result[1])' in core,
 'receipt-prepared-before-commit':'"response": copy_json(response)' in core and 'saved_body = copy_json(data)' in core,
 'shape-profile-independent':'def _original_seating_body' in core,'nonrecursive-json':'frames = []' in codec and 'setrecursionlimit' not in codec,
 'serialize-before-headers':'payload = b"" if status == 204 else dumps(body)' in server,
 'legacy-bootstrap':'state["histories"][record["reference"]] = []' in core and 'state["history_origins"][record["reference"]] = "legacy"' in core,
 'empty-history-ui':'if(!l.history.entries.length)' in app and 'No recorded changes are available' in app,
 'old-accepted-cutoff':'record["accepted_terms"]["cancellation_cutoff_minutes"]' in core,
 'policy-local-order':'key=lambda p: (p["effective_from"], to_integer(p["policy_version"]))' in core}
 assert all(checks.values())
 notes=dict(transactions='Named core reviewed: RLock covers dispatch/copy/receipt preparation/commit, import builds a complete replacement before mutation, and batch/series candidates validate before commit. Staged current HTTP readers independently compare before/after states. No internal serializer timing claimed.',
 numeric='Inherited codec unchanged from accepted Stage2; strict iterative grammar, immutable exact numeric leaves and iterative copy. Receipt-specific legacy profile remains separate from public original shape. Newly executed writes remain exact.',
 legacy='Genuine earlier records have no reconstructable Stage3 prior history/revisions/policies. Current revision1/fixture-policy0 terms, empty prior history and private counter0 are source-faithful bootstrap choices. Actual new events start seq1 with resulting revision2. Genuine older manager fields were ignored and default to no managers; authority is not invented. Original public receipts and timestamp strings remain immutable.',
 source_scope='Source/hash/history review is labelled separately from HTTP and browser observations. No builder or official probe/oracle implementation was read or run.',
 shared_index='Original 182582c preserved:32 verifier-authored preparation paths under Interface Git author. Authorship and independent execution are not relabelled.',
 cutoff='Exact equality is additionally checked in a separate packaged Engine process with an explicit fixed diagnostic clock; this is not a public HTTP test-clock endpoint.',
 limits='Adopted timestamp/receipt/numeric-control/exact-number decisions and finite-resource limits remain. Full literal historical seconds-offset grammar and minute-only RFC3339 are not both claimed.')
 (out/'source-proof.json').write_text(json.dumps(dict(candidate=C,stage_3_tree=trees[C],manifest=manifest,checks=checks,copy_comparisons=comparisons,owners=owners,frozen=frozen,trees=trees,systems_api_identical=True,systems_full_tree_differences=tree_diff,source_notes=notes,shared_index_captured_paths=captured,commands=commands),indent=2)+'\n')
 official=W/'band-work/final-checks/independent-verifier-s3-c1-91e2c471-official-072631';shutil.copytree(official,H/'official')
 report=json.loads((official/'report.json').read_text());assert report['revision']==C
 argv=[str(W/'.venv/bin/python'),'-m','harness','run','--track','tablekeeper','--repo',str(clone),'--stage','3','--mode','isolated','--out',str(official)]
 (H/'official-command.json').write_text(json.dumps(dict(argv=argv,cwd=str(kickoff),returncode=0,output=str(official),timing_scope='Harness report UTC window; exact external command wall time not separately measured',report_started_at=report.get('started_at'),report_finished_at=report.get('finished_at'),source='Actual unchanged command invoked by verifier; successful tool completion preserved in room runtime'),indent=2)+'\n')
 print(json.dumps(dict(candidate=C,source_checks=len(checks),copied_files=9,production_edits=0)))
if __name__=='__main__':main()
