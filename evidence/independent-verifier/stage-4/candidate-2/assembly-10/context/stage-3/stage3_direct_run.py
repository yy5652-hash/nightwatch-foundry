"""Inspect and execute an immutable own diagnostic in the retained service image."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--out',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
 out=Path(a.out).resolve();assert out.is_relative_to(W);out.mkdir(parents=True,exist_ok=False);facts=json.loads((Path(a.runtime)/'preflight.json').read_text());commands=[]
 def run(argv,label,input=None):
  began=time.monotonic();result=subprocess.run(argv,cwd=R,input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(label+'.log')).write_bytes(result.stdout)
  commands.append(dict(argv=argv,cwd=str(R),returncode=result.returncode,seconds=time.monotonic()-began,log=label+'.log',stdin_sha256=hashlib.sha256(input).hexdigest() if input else None));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return result
 revision=subprocess.check_output(['git','rev-parse',a.revision],cwd=R,text=True).strip();path='evidence/independent-verifier/stage-3/stage3_direct.py';source=run(['git','show',revision+':'+path],'source').stdout;(out/'executed-source.py').write_bytes(source)
 name=facts['prefix']+'-direct';image=next(x['actual_image_id'] for x in facts['containers'] if x['role']=='target')
 created=run(['docker','create','-i','--name',name,'--network','none','--cpus','2','--memory','2g','--entrypoint','python',image,'-'],'create');assert created.returncode==0
 try:
  proof=json.loads(run(['docker','inspect',name],'inspect-before').stdout)[0];assert proof['HostConfig']['NanoCpus']==2000000000 and proof['HostConfig']['Memory']==2147483648 and proof['HostConfig']['NetworkMode']=='none' and not proof['Mounts']
  result=run(['docker','start','-a','-i',name],'execute',source)
  after=json.loads(run(['docker','inspect',name],'inspect-after').stdout)[0];assert not after['State']['OOMKilled']
  if result.returncode==0:
   data=json.loads(result.stdout);assert data['failed']==0;(out/'summary.json').write_text(json.dumps(data,indent=2)+'\n')
  (out/'source-runtime-proof.json').write_text(json.dumps(dict(candidate=facts['candidate'],probe_revision=revision,image_id=image,source_sha256=hashlib.sha256(source).hexdigest(),resources=dict(cpus=2,memory=2147483648,network='none',mounts=[]),returncode=result.returncode,scope='retained source-bound image, labelled Engine diagnostic; no HTTP or fresh build claim'),indent=2)+'\n')
 finally:assert run(['docker','rm',name],'cleanup').returncode==0
 raise SystemExit(result.returncode)
if __name__=='__main__':main()
