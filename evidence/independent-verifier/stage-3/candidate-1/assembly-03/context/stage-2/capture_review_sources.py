"""Preserve normative sources and actual own helper-image code versions, never shipped tests."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
here=Path(__file__).resolve().parent;repo=here.parents[2];workspace=repo.parents[1];target=here/'candidate-1'
snapshots=target/'source-specifications';snapshots.mkdir(exist_ok=True)
for name,path in [('stage-1.md','kickoff/tablekeeper/spec/stage-1.md'),('stage-2.md','kickoff/tablekeeper/spec/stage-2.md'),('participant-guide.md','kickoff/docs/participant-guide.md'),('PRODUCT_ACCEPTANCE.md','factory/PRODUCT_ACCEPTANCE.md')]:
    source=workspace/path;shutil.copy2(source,snapshots/name)
    assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256((snapshots/name).read_bytes()).digest()
runtime=json.loads((target/'runtime-evidence/preflight.json').read_text())
images=[runtime['runner_image']]+['independent-verifier-s2:review-runner-%02d'%n for n in range(4,10)]
versions=target/'helper-source-versions';versions.mkdir(exist_ok=True);commands=[]
code='import json,pathlib;print(json.dumps({str(p.relative_to("/verifier")):p.read_text() for p in pathlib.Path("/verifier").rglob("*.py")}))'
for index,image in enumerate(images):
    argv=['docker','run','--rm','--name','independent-verifier-s2-source-capture-%02d'%index,'--network','none','--cpus','2','--memory','2g','--entrypoint','python',image,'-c',code]
    start=time.monotonic();v=subprocess.run(argv,text=True,capture_output=True);assert v.returncode==0
    data=json.loads(v.stdout);folder=versions/('runner-%02d'%index);folder.mkdir(exist_ok=True)
    for path,contents in data.items():
        file=folder/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(contents)
    commands.append(dict(image=image,argv=argv,returncode=v.returncode,seconds=time.monotonic()-start,
        files={path:hashlib.sha256(contents.encode()).hexdigest() for path,contents in data.items()}))
(target/'helper-source-identities.json').write_text(json.dumps(commands,indent=2))
print(json.dumps(dict(normative_sources=4,own_helper_images=len(commands),total_source_files=sum(len(x['files']) for x in commands))))
