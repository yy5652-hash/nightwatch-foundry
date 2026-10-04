"""Inspect then remove only runtime resources named by this seat's manifest."""
import datetime as dt, json, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1];H=HERE/'candidate-1'
def main():
 runtime=H/'runtime-01';f=json.loads((runtime/'preflight.json').read_text());out=H/'cleanup-01';out.mkdir(exist_ok=False);commands=[];states=[]
 def run(argv,label):
  begin=time.monotonic();p=subprocess.run(argv,cwd=R,capture_output=True);(out/(label+'.log')).write_bytes(p.stdout+p.stderr)
  commands.append(dict(argv=argv,cwd=str(R),returncode=p.returncode,seconds=time.monotonic()-begin,log=label+'.log'));assert p.returncode==0;return p.stdout
 assert f['prefix'].startswith('independent-verifier-s4-')
 for row in f['containers']:
  name=row['name'];assert name.startswith(f['prefix']+'-')
  i=json.loads(run(['docker','inspect',name],name+'-inspect'))[0];assert i['State']['Running'] and not i['State']['OOMKilled'];assert not i['Mounts']
  states.append(dict(name=name,running_before_removal=True,oom_killed=False,image=i['Image']))
 for row in f['containers']:run(['docker','rm','-f',row['name']],row['role']+'-remove')
 run(['docker','network','rm',f['network']],'network-remove')
 namespaces=run(['docker','ps','-a','--filter','name='+f['prefix'],'--format','{{.Names}}'],'namespace-containers').decode().strip();assert not namespaces
 nets=run(['docker','network','ls','--filter','name='+f['network'],'--format','{{.Name}}'],'namespace-network').decode().strip();assert not nets
 clones=[]
 for role,source in f['source'].items():
  path=Path(source['clone']);assert path.is_relative_to(W/'band-work') and path.name.startswith('independent-verifier-')
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip();clean=not subprocess.check_output(['git','status','--porcelain'],cwd=path,text=True).strip();assert head==source['revision'] and clean
  clones.append(dict(role=role,path=str(path),revision=head,clean=True))
 subprocess.run(['git','diff','--quiet',f['candidate'],'--','stage-1','stage-2','stage-3','stage-4'],cwd=R,check=True)
 (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');(out/'executed-source.py').write_bytes(Path(__file__).read_bytes())
 proof=dict(candidate=f['candidate'],completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),service_states=states,removals=len(states)+1,all_removal_codes_zero=True,empty_own_namespace=True,clones=clones,graded_diff_empty=True,production_edits=0,images_and_clones_retained=True)
 (out/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
