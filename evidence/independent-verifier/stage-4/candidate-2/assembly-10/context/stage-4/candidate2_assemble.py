"""Fresh immutable current own client, including prospective evidence fixes."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-2'
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    rev=subprocess.check_output(['git','rev-parse',a.revision],cwd=R,text=True).strip();out=Path(a.out).resolve();assert out.is_relative_to(H);out.mkdir(parents=True,exist_ok=False)
    f=json.loads((H/'runtime-01/preflight.json').read_text());context=out/'context';context.mkdir();manifest=[]
    def blob(source,destination):
        argv=['git','show',rev+':evidence/independent-verifier/'+source];data=subprocess.check_output(argv,cwd=R);target=context/destination;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);manifest.append(dict(path=destination,source=source,sha256=hashlib.sha256(data).hexdigest(),argv=argv))
    for folder in ['stage-1','stage-2','stage-3','stage-4','stage-4/repair-1']:
        names=subprocess.check_output(['git','ls-tree','--name-only',rev+':evidence/independent-verifier/'+folder],cwd=R,text=True).splitlines()
        for name in names:
            if name.endswith('.py'):blob(folder+'/'+name,folder+'/'+name)
    blob('stage-4/candidate2_stage3_probe.py','stage-3/stage3_probe.py')
    for folder,name in [('stage-1','candidate-7/coverage.csv'),('stage-2','candidate-1/coverage.csv')]:blob(folder+'/'+name,folder+'/'+name)
    docker='FROM '+f['runner_image']+'\nCOPY stage-1 /verifier/stage-1\nCOPY stage-2 /verifier/stage-2\nCOPY stage-3 /verifier/stage-3\nCOPY stage-4 /verifier/stage-4\n'
    (context/'Dockerfile').write_text(docker);image=f['prefix']+':client-'+rev[:8];argv=['docker','build','-t',image,'.'];began=time.monotonic()
    with (out/'build.log').open('w') as log:rc=subprocess.run(argv,cwd=context,stdout=log,stderr=subprocess.STDOUT).returncode
    (out/'commands.json').write_text(json.dumps([dict(argv=argv,cwd=str(context),returncode=rc,seconds=time.monotonic()-began,log='build.log')],indent=2)+'\n');assert rc==0
    image_id=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]['Id']
    (out/'client-proof.json').write_text(json.dumps(dict(image=image,image_id=image_id,probe_revision=rev,manifest=manifest,base_image=f['runner_image_id']),indent=2)+'\n')
    print(json.dumps(dict(image=image,probe_revision=rev,manifest_files=len(manifest))))
if __name__=='__main__':main()
