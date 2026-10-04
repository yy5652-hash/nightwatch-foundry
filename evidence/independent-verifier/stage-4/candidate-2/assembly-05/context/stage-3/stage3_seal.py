"""Explicit owned pathspec evidence commit, exact resulting-commit inspection."""
import hashlib,json,re,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-1';C='91e2c471acded1b861b3fec725f202297b1c6740'
def main():
 out=H/'seal-01';out.mkdir(exist_ok=False);commands=[];start=datetime.now(timezone.utc)
 def run(argv,allow=False):
  began=time.monotonic();p=subprocess.run(argv,cwd=R,capture_output=True);commands.append(dict(argv=argv,cwd=str(R),returncode=p.returncode,seconds=time.monotonic()-began,stdout=p.stdout.decode(),stderr=p.stderr.decode()));assert allow or p.returncode==0,argv;return p.stdout
 audit=json.loads((H/'artifact-audit-seal.json').read_text());assert not audit['unclassified_private_payload_findings'] and not audit['json_read_errors']
 metadata=json.loads((H/'metadata-self-check.json').read_text());assert metadata['normative_verified']==7359 and metadata['normative_failed']==metadata['normative_unverified']==0
 assert json.loads((H/'final-runtime-proof.json').read_text())['namespace_empty']
 assert not run(['git','diff',C,'--','stage-1','stage-2','stage-3'])
 status=run(['git','status','--porcelain=v1','-z','--untracked-files=all','--','evidence/independent-verifier/stage-3','evidence/independent-verifier/ledger.jsonl']).decode().split('\0')
 paths=sorted(x[3:] for x in status if x and not x[3:].startswith(str(out.relative_to(R))+'/'))
 assert paths and all(x.startswith('evidence/independent-verifier/stage-3/') or x=='evidence/independent-verifier/ledger.jsonl' for x in paths)
 assert all((R/x).is_file() for x in paths)
 spec=out/'owned.pathspec';spec.write_bytes(b''.join((':(literal)'+x).encode()+b'\0' for x in paths))
 run(['git','add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'])
 authored=[x for x in paths if (Path(x).parent==HERE.relative_to(R) and x.endswith('.py')) or (Path(x).parent==H.relative_to(R) and x.endswith('.md'))]
 run(['git','diff','--cached','--check','--',*authored])
 result=run(['git','-c','user.name=Independent Verifier','-c','user.email=independent-verifier@nightwatch-foundry.invalid','commit','--only','--pathspec-from-file='+str(spec),'--pathspec-file-nul','-m','Accept exact Stage 3 candidate with complete independent evidence'])
 short=re.search(rb'\[[^\]]+ ([0-9a-f]{7,40})\]',result).group(1).decode();revision=run(['git','rev-parse',short]).decode().strip()
 changed=run(['git','diff-tree','--no-commit-id','--name-only','-r',revision]).decode().splitlines();assert sorted(changed)==paths
 owner=run(['git','show','-s','--format=%an <%ae>',revision]).decode().strip();assert owner=='Independent Verifier <independent-verifier@nightwatch-foundry.invalid>'
 tree=run(['git','rev-parse',revision+':stage-3']).decode().strip();assert tree=='a0f0a4741bb0ab0125856510a000ade385344a04'
 assert not run(['git','diff',C,revision,'--','stage-1','stage-2','stage-3'])
 (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 (out/'proof.json').write_text(json.dumps(dict(verdict_commit=revision,candidate=C,stage_3_tree=tree,changed_paths=changed,changed_path_count=len(changed),exact_owned_paths_only=True,author=owner,graded_diff_empty=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),separate_inspection_commit='reported later in room after its own exact inspection'),indent=2)+'\n')
 print(json.dumps(dict(verdict_commit=revision,owned_changed_paths=len(changed),stage_3_tree=tree,graded_diff_empty=True)))
if __name__=='__main__':main()
