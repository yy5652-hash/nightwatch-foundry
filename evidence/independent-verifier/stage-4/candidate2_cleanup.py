"""Inspect and remove only the eight independently created current-run services."""
import hashlib,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-2';C='58270860cb6a762c8a4c2a551672701fb00bd613'
def main():
 out=H/'cleanup-01';out.mkdir(exist_ok=False);f=json.loads((H/'runtime-01/preflight.json').read_text());commands=[];services=[];clones=[]
 def run(argv):
  start=time.monotonic();got=subprocess.run(argv,cwd=R,capture_output=True,text=True);commands.append(dict(argv=argv,cwd=str(R),returncode=got.returncode,seconds=time.monotonic()-start,stdout=got.stdout,stderr=got.stderr));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert got.returncode==0,argv;return got.stdout
 for old in f['containers']:
  assert old['name'].startswith(f['prefix']+'-')
  inspect=json.loads(run(['docker','inspect',old['name']]))[0]
  health=json.loads(run(['docker','exec',old['name'],'python','-c',"import json,os,urllib.request; print(urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8080')+'/health',timeout=5).read().decode())"]))
  assert health=={'status':'ok'} and inspect['State']['Running'] and not inspect['State']['OOMKilled']
  assert inspect['HostConfig']['NanoCpus']==2000000000 and inspect['HostConfig']['Memory']==2147483648 and inspect['Mounts']==[]
  services.append(dict(name=old['name'],role=old['role'],image=inspect['Image'],healthy=True,oom_killed=False,cpu=2,memory_bytes=2147483648,mounts=[]))
 for role,src in f['source'].items():
  status=run(['git','-C',src['clone'],'status','--porcelain']);revision=run(['git','-C',src['clone'],'rev-parse','HEAD']).strip();assert not status and revision==src['revision']
  clones.append(dict(role=role,clone=src['clone'],revision=revision,clean=True))
 run(['git','diff','--exit-code',C,'--','stage-1','stage-2','stage-3','stage-4'])
 removals=[]
 for old in f['containers']:run(['docker','rm','-f',old['name']]);removals.append(old['name'])
 run(['docker','network','rm',f['network']]);removals.append(f['network'])
 remaining=run(['docker','ps','-a','--filter','name='+f['prefix'],'--format','{{.Names}}']).splitlines();networks=run(['docker','network','ls','--filter','name='+f['prefix'],'--format','{{.Name}}']).splitlines();assert not remaining and not networks
 (H/'final-runtime-proof.json').write_text(json.dumps(dict(candidate=C,services_before_removal=services,clean_clones=clones,graded_diff_empty=True,cleanup_commands=9,cleanup_exits=[0]*9,only_own_resources_removed=True,namespace_empty=True,remaining_containers=remaining,remaining_networks=networks,completed_at=datetime.now(timezone.utc).isoformat(),images_and_clones_retained=True,commands_path=str((out/'commands.json').relative_to(R)),executed_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
 print(json.dumps(dict(healthy_services=len(services),own_cleanup_exits=[0]*9,namespace_empty=True,clean_clones=len(clones))))
if __name__=='__main__':main()
