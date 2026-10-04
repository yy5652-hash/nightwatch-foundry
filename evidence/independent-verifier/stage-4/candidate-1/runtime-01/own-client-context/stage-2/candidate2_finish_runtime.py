"""Final exact source/resource observations and removal of this review's own resources."""
import hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1];H=HERE/'candidate-2'
def main():
    facts=json.loads((H/'runtime-01/preflight.json').read_text());C=facts['candidate'];out=H/'final-runtime';out.mkdir(exist_ok=False);commands=[]
    def run(argv,label,cwd=R):
        began=time.monotonic();r=subprocess.run(argv,cwd=cwd,capture_output=True,text=True);(out/(label+'.log')).write_text(r.stdout+r.stderr)
        commands.append(dict(argv=argv,cwd=str(cwd),log=label+'.log',returncode=r.returncode,seconds=time.monotonic()-began));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert r.returncode==0,(label,r.returncode);return r.stdout
    clones=[]
    for name,item in facts['source'].items():
        head=run(['git','rev-parse','HEAD'],name+'-head',item['clone']).strip();status=run(['git','status','--porcelain'],name+'-status',item['clone']);assert head==item['revision'] and not status
        clones.append(dict(source=name,head=head,status=status,clean=True,path=item['clone']))
    empty=run(['git','diff',C,'--','stage-1','stage-2'],'current-production-diff');assert not empty
    frozen=run(['git','diff',facts['intake']['accepted_stage1'],C,'--','stage-1'],'frozen-production-diff');assert not frozen
    kickoff=W/'kickoff';head=run(['git','rev-parse','HEAD'],'kickoff-head',kickoff).strip();status=run(['git','status','--porcelain'],'kickoff-status',kickoff);assert head=='803560d2a678ace1414465c098eb0ab5380ffade' and not status
    inspections=[]
    for container in facts['containers']:
        name=container['name'];assert name.startswith(facts['prefix']+'-')
        actual=json.loads(run(['docker','inspect',name],container['role']+'-inspect'))[0]
        assert actual['State']['Running'] and not actual['State']['OOMKilled'] and actual['HostConfig']['NanoCpus']==2000000000 and actual['HostConfig']['Memory']==2147483648 and actual['Mounts']==[] and actual['Image']==container['actual_image_id']
        health=json.loads(run(['docker','exec',name,'python','-c','import urllib.request,json;print(urllib.request.urlopen("http://127.0.0.1:'+str(container['internal_port'])+'/health",timeout=5).read().decode())'],container['role']+'-health'))
        assert health=={'status':'ok'}
        inspections.append(dict(name=name,running=True,oom_killed=False,cpu=2,memory_bytes=2147483648,mounts=[],image_id=actual['Image'],health=health))
    net=json.loads(run(['docker','network','inspect',facts['network']],'network-inspect'))[0];assert net['Internal'] is True
    cleanup=[]
    for container in facts['containers']:
        argv=['docker','rm','-f',container['name']];run(argv,'cleanup-'+container['role']);cleanup.append(commands[-1])
    run(['docker','network','rm',facts['network']],'cleanup-network');cleanup.append(commands[-1])
    inventory=run(['docker','ps','-a','--filter','name='+facts['prefix'],'--format','{{.Names}}'],'own-review-inventory');assert not inventory.strip()
    seat_inventory=run(['docker','ps','-a','--filter','name=independent-verifier','--format','{{.Names}}'],'own-seat-inventory');assert not seat_inventory.strip()
    proof=dict(candidate=C,clones=clones,current_production_diff_empty=True,frozen_stage1_diff_empty=True,kickoff_head=head,kickoff_clean=True,inspections=inspections,internal_offline_network=True,cleanup=cleanup,own_review_namespace_empty=True,own_seat_namespace_empty=True,images_and_clean_clones_retained=True,scope='Own named six service processes and own internal network only; client --rm exits recorded separately. No other seat resource removed.')
    (H/'final-runtime-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(dict(clean_clones=len(clones),healthy_services=len(inspections),cleanup_commands=len(cleanup),all_cleanup_zero=True,own_namespace_empty=True)))
if __name__=='__main__':main()
