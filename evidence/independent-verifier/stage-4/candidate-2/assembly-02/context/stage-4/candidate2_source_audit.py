"""Independent named Stage4 intake/source/ownership audit, not runtime evidence."""
import argparse, ast, datetime as dt, hashlib, json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent; R=HERE.parents[2]; W=R.parents[1]
C='58270860cb6a762c8a4c2a551672701fb00bd613'; T='00e208c746a488a9b4cb0761efd04b90c4248dd8'
FROZEN={1:'75005d57fe0904753eac4eab5bf4e4c9a78b6d1b',2:'4dba10246b07b2dda19de260d529f9d94ba0a1ed',3:'91e2c471acded1b861b3fec725f202297b1c6740'}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
 out=Path(args.out).resolve();assert out.is_relative_to(HERE);out.mkdir(exist_ok=False);commands=[]
 (out/'executed-source.py').write_bytes(Path(__file__).read_bytes())
 def git(args,label,cwd=R):
  p=subprocess.run(['git',*args],cwd=cwd,capture_output=True);(out/(label+'.log')).write_bytes(p.stdout+p.stderr)
  commands.append(dict(argv=['git',*args],cwd=str(cwd),returncode=p.returncode,log=label+'.log'))
  assert p.returncode==0,(label,p.returncode);return p.stdout
 intake=json.loads((HERE/'candidate-2/release-intake.json').read_text())
 handoff=R/'evidence/coordinator/handoffs/TK-20261004-S4-independent-verifier-CANDIDATE-2.txt'
 delivery=handoff.with_name(handoff.stem+'-delivery.json');d=json.loads(delivery.read_text())
 assert [(r['part'],r['message_id']) for r in d['deliveries']]==[(r['part'],r['message_id']) for r in intake['all_parts']]
 text=handoff.read_text();assert 'END TK-20261004-S4-independent-verifier-CANDIDATE-2' in text
 for name,p in [('full-handoff.txt',handoff),('transport-delivery.json',delivery)]: (out/name).write_bytes(p.read_bytes())
 frozen=[]
 for n,rev in FROZEN.items():
  assert not git(['diff',rev,C,'--',f'stage-{n}'],f'frozen-{n}-diff')
  names=git(['ls-tree','-r','--name-only',rev,f'stage-{n}'],f'frozen-{n}-files').decode().splitlines()
  for i,name in enumerate(names):
   b=git(['show',rev+':'+name],f'frozen-{n}-blob-{i}')
   assert (R/name).read_bytes()==b
   frozen.append(dict(path=name,revision=rev,sha256=sha(b),working_bytes_equal=True))
 assert len(frozen)==24
 source=[]
 lines=git(['ls-tree','-r',C,'stage-4'],'candidate-tree').decode().splitlines();assert len(lines)==9
 assert git(['rev-parse',C+':stage-4'],'candidate-stage4-tree').decode().strip()==T
 for i,line in enumerate(lines):
  meta,path=line.split('\t');mode,kind,blob=meta.split();assert mode in ('100644','100755') and kind=='blob'
  b=git(['show',C+':'+path],'candidate-blob-'+str(i));assert (R/path).read_bytes()==b
  name=path.removeprefix('stage-4/');p=out/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  if name.endswith('.py'):ast.parse(b.decode())
  source.append(dict(path=path,mode=mode,blob=blob,sha256=sha(b),working_bytes_equal=True))
 base='4590d38411590f7d0c2bd6b0faaa8f5b17ea8d2a';copies=[]
 for row in source:
  name=row['path'].removeprefix('stage-4/')
  a=git(['ls-tree',FROZEN[3],'stage-3/'+name],'copy-source-'+name.replace('/','_')).decode().split('\t')[0]
  b=git(['ls-tree',base,'stage-4/'+name],'copy-target-'+name.replace('/','_')).decode().split('\t')[0]
  assert a==b;copies.append(dict(path=name,mode_kind_blob=a,identical=True))
 owners=[]
 for rev,owner,allowed in [('30e6b6edd6e6e061e5b3ff155b42261c9c97568a','Systems Engineer',['stage-4/core.py']),('6225a0e6f25afd28ceddac472887a77e5941bba5','Systems Engineer',['stage-4/core.py']),('83dccc909250800384d29d8d05d70a6cee383b6a','Interface Engineer',['stage-4/RUN.md','stage-4/server.py','stage-4/web/app.css','stage-4/web/app.js'])]:
  author=git(['show','-s','--format=%an <%ae>',rev],owner.split()[0]+'-author').decode().strip();assert author.startswith(owner+' <')
  paths=git(['diff-tree','--no-commit-id','--name-only','-r',rev],owner.split()[0]+'-paths').decode().splitlines();assert sorted(p for p in paths if p.startswith('stage-'))==allowed
  git(['merge-base','--is-ancestor',rev,C],owner.split()[0]+'-ancestor');owners.append(dict(revision=rev,author=author,paths=paths))
 seals=[]
 for rev,prefix,count in [('7723ad57402135b37b705660d9feda065374afb8','evidence/systems-engineer/',256),(C,'evidence/interface-engineer/',272)]:
  paths=git(['diff-tree','--no-commit-id','--name-only','-r',rev],'seal-'+rev[:8]).decode().splitlines();assert len(paths)==count and all(p.startswith(prefix) for p in paths)
  seals.append(dict(revision=rev,count=count,all_owned_evidence=True,paths=paths))
 for rev in ['969ee95ac1a7bb1d28ecf075f256b6eb4c32f6fb','2601ee9c94838a53f47a3a63bacd1e864b500122','7723ad57402135b37b705660d9feda065374afb8']:
  assert git(['rev-parse',rev+':stage-4'],'tested-tree-'+rev[:8]).decode().strip()==T
 git(['log','--format=%H %an <%ae> %s',C,'--','stage-4'],'stage4-history')
 assert git(['rev-parse','HEAD'],'kickoff-head',W/'kickoff').decode().strip()=='803560d2a678ace1414465c098eb0ab5380ffade'
 assert not git(['status','--porcelain'],'kickoff-status',W/'kickoff')
 proof=dict(candidate=C,stage_4_tree=T,completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),handoff_sha256=sha(handoff.read_bytes()),transport_sha256=sha(delivery.read_bytes()),complete23parts_acknowledged=True,frozen=frozen,source=source,whole_copy_base=base,copy_comparisons=copies,complete_nine_file_copy_verified=True,owners=owners,evidence_seals=seals,commands=commands,production_edits=0)
 (out/'source-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
 (out/'executed-source.py').write_bytes(Path(__file__).read_bytes())
 print(json.dumps(dict(candidate=C,frozen_files=len(frozen),copy_files=len(copies),source_files=len(source),ownership='verified')))
if __name__=='__main__':main()
