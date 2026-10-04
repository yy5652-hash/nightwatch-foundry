"""Execute only a sealed own supplement against inspected own current services."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--probe-revision',required=True);p.add_argument('--cases',nargs='+',choices=['oracle','browser'],default=['oracle','browser']);a=p.parse_args()
    out=Path(a.out).resolve();assert out.is_relative_to(W);out.mkdir(parents=True,exist_ok=False)
    root=HERE/'candidate-2';facts=json.loads((root/'runtime-01/preflight.json').read_text());assembly=root/'assembly-03'
    image=json.loads((assembly/'client-proof.json').read_text())['image'];path='evidence/independent-verifier/stage-2/candidate2_supplement.py'
    argv=['git','show',a.probe_revision+':'+path];data=subprocess.check_output(argv,cwd=R);source=out/'executed-source.py';source.write_bytes(data)
    proof=dict(probe_revision=a.probe_revision,source_path=path,argv=argv,source_sha256=hashlib.sha256(data).hexdigest(),client_image=image,candidate=facts['candidate'])
    (out/'source-proof.json').write_text(json.dumps(proof,indent=2)+'\n');commands=[]
    for case in a.cases:
        argv=['docker','run','--rm','--name',facts['prefix']+'-supplement-'+case,'--network',facts['network'],'--cpus','2','--memory','2g','-v',str(out)+':/evidence','-v',str(assembly/'release.json')+':/release.json:ro','-v',str(source)+':/verifier/stage-2/candidate2_supplement.py:ro','--entrypoint','python',image,'/verifier/stage-2/candidate2_supplement.py','--release','/release.json','--case',case,'--out','/evidence/'+case]
        start=time.monotonic()
        with (out/(case+'.log')).open('w') as f:result=subprocess.run(argv,cwd=R,stdout=f,stderr=subprocess.STDOUT)
        commands.append(dict(argv=argv,cwd=str(R),log=case+'.log',returncode=result.returncode,seconds=time.monotonic()-start));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        print(json.dumps(dict(case=case,returncode=result.returncode,seconds=commands[-1]['seconds'])),flush=True)
    raise SystemExit(any(x['returncode'] for x in commands))
if __name__=='__main__':main()
