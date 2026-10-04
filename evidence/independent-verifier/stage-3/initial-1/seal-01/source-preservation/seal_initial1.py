"""Scoped preparation integrity/privacy audit and explicit owned-path seal."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]

def sha(data):return hashlib.sha256(data).hexdigest()
def save(p,value):p.write_text(json.dumps(value,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--commit',action='store_true');a=p.parse_args()
    out=Path(a.out).resolve()
    if not out.is_relative_to(ROOT) or out.exists():raise SystemExit('New owned unique output required')
    out.mkdir(parents=True);start=time.monotonic();commands=[]
    def execute(argv):
        for attempt in range(20):
            began=time.monotonic();process=subprocess.run(argv,cwd=REPO,capture_output=True)
            commands.append(dict(argv=argv,cwd=str(REPO),returncode=process.returncode,seconds=time.monotonic()-began,
                stdout_sha256=sha(process.stdout),stderr_sha256=sha(process.stderr),stdout=process.stdout.decode(errors='replace'),stderr=process.stderr.decode(errors='replace')))
            if process.returncode==0:return process.stdout.decode().strip()
            if b'index.lock' not in process.stderr:raise RuntimeError(process.stderr.decode(errors='replace'))
            time.sleep(.5)
        raise RuntimeError('shared index lock persisted; own files preserved')
    latest=ROOT/'initial-1/checks-02';rows=list(csv.DictReader((latest/'coverage.csv').open()))
    assert len(rows)==7332 and sum(x['normative'].lower()=='true' for x in rows)==7310
    assert all(x['verdict']=='unverified' for x in rows)
    assert all((REPO/x['evidence_path'].split('#',1)[0]).is_file() for x in rows)
    for run_name,preserved in [('checks-01','checks-01-source-preservation'),('checks-02','checks-02/executed-source')]:
        manifest=json.loads((ROOT/'initial-1'/run_name/'prepared-source-manifest.json').read_text())
        for entry in manifest:
            assert sha((ROOT/'initial-1'/preserved/Path(entry['path']).name).read_bytes())==entry['sha256']
            if run_name=='checks-02':assert sha(Path(entry['path']).read_bytes())==entry['sha256']
    for name in ('checks-01','checks-02'):
        summary=json.loads((ROOT/'initial-1'/name/'summary.json').read_text())
        assert all(summary[k]==0 for k in ('candidate_http_requests','browser_interactions','service_images_built','official_checks','production_edits','verified','failed'))
        assert summary['local_controls']==summary['local_controls_passed']
        for item in json.loads((ROOT/'initial-1'/name/'artifact-manifest.json').read_text()):
            assert sha((REPO/item['path']).read_bytes())==item['sha256']
    findings=[];objects=0;json_files=0;whitespace=[];manifest=[]
    def inspect(value,path,pointer=''):
        nonlocal objects
        if isinstance(value,dict):
            objects+=1
            for key,child in value.items():
                if key in ('password','password_hash','token','tokens','authorization') and child not in (None,'unknown'):
                    findings.append(dict(path=path,pointer=pointer+'/'+key,classification='unexpected raw private field'))
                inspect(child,path,pointer+'/'+key)
        elif isinstance(value,list):
            for i,child in enumerate(value):inspect(child,path,pointer+'/'+str(i))
    for file in sorted(ROOT.rglob('*')):
        if not file.is_file():continue
        assert not file.is_symlink()
        data=file.read_bytes();relative=str(file.relative_to(REPO));forensic='source-inputs' in file.parts
        manifest.append(dict(path=relative,bytes=len(data),sha256=sha(data),classification='immutable forensic source' if forensic else 'owned preparation'))
        if file.suffix=='.json' and not forensic:json_files+=1;inspect(json.loads(data),relative)
        if file.suffix in ('.py','.md') and not forensic:
            whitespace.extend(dict(path=relative,line=i+1) for i,line in enumerate(data.decode().splitlines()) if line!=line.rstrip())
    assert not findings and not whitespace
    save(out/'artifact-audit.json',dict(files=len(manifest),bytes=sum(x['bytes'] for x in manifest),json_files=json_files,json_objects=objects,
        raw_private_payload_findings=findings,authored_whitespace_findings=whitespace,manifest=manifest,
        limitations='Scoped owned non-forensic JSON only. Source/log text, forensic source, historical CSV and genuine room export are not a general secret audit. No live exported state was saved.'))
    save(out/'integrity.json',dict(utc=datetime.now(timezone.utc).isoformat(),rows=7332,normative_unverified=7310,separate_unverified_diagnostics=22,
        original_outputs_and_source_hashes_preserved=True,current_prepared_source_matches_checks02=True,all_current_links_are_files=True,
        service_execution=0,production_edits=0,seconds=time.monotonic()-start))
    if a.commit:
        # Every exact file is owned; no directory pathspec, blanket index operation
        # or unrelated staged file is included in this commit.
        paths=[str(file.relative_to(REPO)) for file in sorted(ROOT.rglob('*')) if file.is_file()]
        save(out/'owned-paths.json',paths)
        paths.append(str((out/'owned-paths.json').relative_to(REPO)))
        execute(['git','add','--',*paths])
        output=execute(['git','-c','user.name=Independent Verifier','-c','user.email=independent-verifier@nightwatch-foundry.invalid',
            'commit','--only','-m','Prepare independent cumulative Stage 3 coverage and protocols','--',*paths])
        import re
        abbreviated=re.search(r'\[[^\]]+ ([0-9a-f]+)\]',output).group(1)
        revision=execute(['git','rev-parse',abbreviated])
        actual=execute(['git','diff-tree','--no-commit-id','--name-only','-r',revision]).splitlines()
        assert set(actual)==set(paths) and all(x.startswith('evidence/independent-verifier/stage-3/') for x in actual)
        author=execute(['git','show','-s','--format=%an <%ae>',revision])
        assert author=='Independent Verifier <independent-verifier@nightwatch-foundry.invalid>'
        save(out/'commit-inspection.json',dict(revision=revision,author=author,files=actual,exact_owned_paths=True,production_changed=False,commands=commands))
        execute(['git','add','--',str((out/'commit-inspection.json').relative_to(REPO))])
        output=execute(['git','-c','user.name=Independent Verifier','-c','user.email=independent-verifier@nightwatch-foundry.invalid',
            'commit','--only','-m','Seal exact Stage 3 preparation commit inspection','--',str((out/'commit-inspection.json').relative_to(REPO))])
        seal=execute(['git','rev-parse',re.search(r'\[[^\]]+ ([0-9a-f]+)\]',output).group(1)])
        sealed=execute(['git','diff-tree','--no-commit-id','--name-only','-r',seal]).splitlines()
        assert sealed==[str((out/'commit-inspection.json').relative_to(REPO))]
        print(json.dumps(dict(preparation_revision=revision,inspection_seal=seal,files=len(paths),audit_files=len(manifest),json_files=json_files,json_objects=objects,errors=0),indent=2))
    else:
        save(out/'commands.json',commands);print(json.dumps(dict(files=len(manifest),json_files=json_files,json_objects=objects,errors=0),indent=2))

if __name__=='__main__':main()
