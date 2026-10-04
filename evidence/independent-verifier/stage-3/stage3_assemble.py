"""New immutable own-client image; retained service images/outputs never change."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--out',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
 runtime=Path(a.runtime).resolve();out=Path(a.out).resolve();assert out.is_relative_to(W);out.mkdir(parents=True,exist_ok=False)
 a.revision=subprocess.check_output(['git','rev-parse',a.revision],cwd=R,text=True).strip()
 assert len(a.revision)==40
 f=json.loads((runtime/'preflight.json').read_text());context=out/'context';context.mkdir();manifest=[];commands=[]
 for folder in ('stage-1','stage-2','stage-3'):
  target=context/folder;target.mkdir()
  names=subprocess.check_output(['git','ls-tree','--name-only',a.revision+':evidence/independent-verifier/'+folder],cwd=R,text=True).splitlines()
  for name in names:
   if not name.endswith('.py'):continue
   argv=['git','show',a.revision+':evidence/independent-verifier/'+folder+'/'+name];data=subprocess.check_output(argv,cwd=R)
   (target/name).write_bytes(data);manifest.append(dict(path=folder+'/'+name,sha256=hashlib.sha256(data).hexdigest(),argv=argv))
 docker='FROM '+f['runner_image']+'\nCOPY stage-1 /verifier/stage-1\nCOPY stage-2 /verifier/stage-2\nCOPY stage-3 /verifier/stage-3\n'
 (context/'Dockerfile').write_text(docker);image=f['prefix']+':client-'+a.revision[:8]
 argv=['docker','build','-t',image,'.'];began=time.monotonic()
 with (out/'build.log').open('w') as log:rc=subprocess.run(argv,cwd=context,stdout=log,stderr=subprocess.STDOUT).returncode
 commands.append(dict(argv=argv,cwd=str(context),returncode=rc,seconds=time.monotonic()-began,log='build.log'));assert rc==0
 image_id=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]['Id']
 proof=dict(image=image,image_id=image_id,probe_revision=a.revision,manifest=manifest,base_image=f['runner_image_id'],dockerfile_sha256=hashlib.sha256(docker.encode()).hexdigest())
 (out/'client-proof.json').write_text(json.dumps(proof,indent=2)+'\n');(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 release=json.loads((runtime/'release.json').read_text());release.update(complete_package=True,offline_2cpu_2g_no_mounts_verified=True)
 release['source_revisions']['exact-s1']=release['source_revisions']['accepted-s1']
 (out/'release.json').write_text(json.dumps(release,indent=2)+'\n');print(json.dumps(dict(image=image,image_id=image_id,output=str(out))))
if __name__=='__main__':main()
