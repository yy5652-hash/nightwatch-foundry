"""Owned preparation audit and explicit-path commit. Never execute production."""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
def save(p,value):p.write_text(json.dumps(value,indent=2)+'\n')

def run(out,commit=False):
    if out.exists():raise ValueError('unique audit output required')
    out.mkdir(parents=True);started=datetime.now(timezone.utc);tick=time.monotonic();commands=[]
    def command(argv):
        t=time.monotonic();p=subprocess.run(argv,cwd=REPO,capture_output=True)
        commands.append(dict(argv=argv,returncode=p.returncode,seconds=time.monotonic()-t,stdout_bytes=len(p.stdout),stdout_sha256=sha(p.stdout),stderr_bytes=len(p.stderr),stderr_sha256=sha(p.stderr)))
        if p.returncode:raise RuntimeError(repr(argv)+' exited '+str(p.returncode))
        return p.stdout
    try:
        findings=[];classified=[];manifest=[];objects=0;embedded=0;whitespace=[]
        def scan(value,path,location=''):
            nonlocal objects,embedded
            if isinstance(value,dict):
                objects+=1
                for k,v in value.items():
                    key=k.lower();here=location+'/'+k
                    if key in ['password','password_hash','token','tokens','authorization','state']:
                        metric=key=='tokens' and path.name=='summary.json' and here=='/tokens' and v=='unknown'
                        model=key=='state' and path.name=='series-model.json' and here=='/state' and value.get('scope')=='finite local reference transitions only'
                        if metric or model:classified.append(dict(path=str(path.relative_to(REPO)),location=here,classification='unknown model usage' if metric else 'finite reference model, not private service state',sha256=sha(json.dumps(v,sort_keys=True).encode())))
                        else:findings.append(dict(path=str(path.relative_to(REPO)),location=here,sha256=sha(json.dumps(v,sort_keys=True).encode())))
                    scan(v,path,here)
            elif isinstance(value,list):
                for i,v in enumerate(value):scan(v,path,location+'/'+str(i))
            elif isinstance(value,str) and value[:1] in ['{','[']:
                try:v=json.loads(value)
                except (ValueError,RecursionError):return
                embedded+=1;scan(v,path,location+'/embedded')
        for p in sorted(ROOT.rglob('*')):
            if not p.is_file() or out in p.parents:continue
            data=p.read_bytes();manifest.append(dict(path=str(p.relative_to(REPO)),bytes=len(data),sha256=sha(data)))
            if p.suffix=='.json':scan(json.loads(data),p)
            if p.parent==ROOT and p.suffix=='.py':
                ast.parse(data,filename=str(p))
                for i,line in enumerate(data.decode().splitlines(),1):
                    if line.rstrip()!=line:whitespace.append(dict(path=str(p.relative_to(REPO)),line=i))
        audit=dict(files=len(manifest),saved_json_objects=objects,embedded_json_strings=embedded,private_classifications=classified,unclassified_private_findings=findings,whitespace=whitespace,manifest=manifest,
                   scope='Owned saved JSON/valid embedded JSON only; source/log/handoff text, prior-stage/peer artifacts and genuine room export excluded. Numeric/reference vectors are constructions, not candidate state.')
        save(out/'artifact-audit.json',audit)
        assert not findings and not whitespace
        from stage4_requirements import S1,S2,S3
        frozen=[]
        for n,rev in [(1,S1),(2,S2),(3,S3)]:
            command(['git','diff','--quiet',rev,'--','stage-'+str(n)])
            frozen.append(dict(stage=n,revision=rev,graded_diff_empty=True))
        save(out/'proof.json',dict(audit='artifact-audit.json',frozen=frozen,production_edits=0,candidate_execution=0,stage4_candidate_verdict='not issued',
                    start=started.isoformat(),end=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-tick,commit_author='Independent Verifier',scope='preparation only'))
        save(out/'commands.json',commands)
        if commit:
            paths=sorted(str(p.relative_to(REPO)) for p in ROOT.rglob('*') if p.is_file())
            pathspec=out/'owned.pathspec';paths.append(str(pathspec.relative_to(REPO)));paths=sorted(set(paths))
            pathspec.write_bytes(b''.join(p.encode()+b'\0' for p in paths))
            command(['git','add','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul'])
            command(['git','-c','user.name=Independent Verifier','-c','user.email=independent-verifier@nightwatch-foundry.invalid','commit','--only',
                     '--pathspec-from-file='+str(pathspec),'--pathspec-file-nul','-m','Prepare independent Stage4 coverage, exact oracle and release-gated protocols'])
            revision=command(['git','rev-parse','HEAD']).decode().strip()
            changed=command(['git','diff-tree','--root','--no-commit-id','--name-only','-r',revision]).decode().splitlines()
            assert set(changed)==set(paths)
            author=command(['git','show','-s','--format=%an <%ae>',revision]).decode().strip()
            assert author=='Independent Verifier <independent-verifier@nightwatch-foundry.invalid>'
            assert all(p.startswith('evidence/independent-verifier/stage-4/') for p in changed)
            save(out/'commit-inspection.json',dict(revision=revision,changed_paths=changed,changed_count=len(changed),exact_owned_pathset=True,author=author,stage3_tree=command(['git','rev-parse',revision+':stage-3']).decode().strip()))
            save(out/'commands-after-commit.json',commands)
            print(json.dumps(dict(revision=revision,owned_paths=len(changed),audit_files=audit['files'],saved_json_objects=objects,unclassified_findings=len(findings))))
    except Exception as e:
        save(out/'FAILED_AUDIT.json',dict(error=repr(e),start=started.isoformat(),end=datetime.now(timezone.utc).isoformat(),commands=commands));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--commit',action='store_true');a=p.parse_args();run(a.out.resolve(),a.commit)
