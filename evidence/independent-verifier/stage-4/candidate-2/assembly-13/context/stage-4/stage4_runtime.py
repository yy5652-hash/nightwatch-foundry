"""Independent named Stage 4 runtime, derived from this seat's own Stage 2 driver.

Only owned evidence and freshly named clones/resources are written. Services have
no mounts. Diagnostic clients may mount owned output/proof files, explicitly.
"""
import argparse, datetime as dt, hashlib, json, subprocess, time
from pathlib import Path

HERE=Path(__file__).resolve().parent; R=HERE.parents[2]; W=R.parents[1]
C='261e4d9456a04a8b57ed46db71a09ac267ff15a9'
S1='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
S2='4dba10246b07b2dda19de260d529f9d94ba0a1ed'
TREE='501d27abab7226546da42edb1131ef8aa037deaf'
S3='91e2c471acded1b861b3fec725f202297b1c6740'
ORIGINS={'accepted-s3':(S3,3),'accepted-s1':(S1,1),'accepted-s2':(S2,2),
 'legacy-s1':('49287b4a5a1481f995c470ccae31776f03d4b863',1),
 'legacy-s2':('4b92041057beb669d2e6c528e8268f4d0d1e6421',2)}
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--probe-revision',required=True);a=p.parse_args()
 out=Path(a.out).resolve();assert out.is_relative_to(W);out.mkdir(parents=True,exist_ok=False)
 intake=json.loads((HERE/'candidate-1/intake.json').read_text())
 assert intake['complete_candidate_package'] and intake['end_received'] and intake['acknowledged_before_execution'] and len(intake['all_parts'])==22
 audit=json.loads((HERE/'candidate-1/source-audit-02/source-proof.json').read_text())
 assert audit['candidate']==C and audit['stage_4_tree']==TREE and audit['complete_nine_file_copy_verified'] and len(audit['frozen'])==24
 prefix='independent-verifier-s4-'+dt.datetime.now(dt.timezone.utc).strftime('%m%d%H%M%S')
 facts=dict(candidate=C,stage_4_tree=TREE,probe_revision=a.probe_revision,prefix=prefix,
  started_at=dt.datetime.now(dt.timezone.utc).isoformat(),status='building',source={},containers=[],intake=intake)
 commands=[];containers=[];network=prefix+'-net';created_network=False
 def save():
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');(out/'preflight.json').write_text(json.dumps(facts,indent=2)+'\n')
 def run(argv,label,cwd=R,required=True):
  began=time.monotonic();log=label+'.log'
  with (out/log).open('w') as f:proc=subprocess.run(argv,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
  commands.append(dict(argv=argv,cwd=str(cwd),log=log,returncode=proc.returncode,seconds=time.monotonic()-began));save()
  if required and proc.returncode:raise RuntimeError('Failed own command; retained '+str(out/log))
  return (out/log).read_text()
 try:
  for role,(rev,stage_num) in {'current':(C,4),**ORIGINS}.items():
   clone=W/'band-work'/(prefix+'-'+role)
   run(['git','clone','--no-hardlinks','--no-checkout',str(R),str(clone)],role+'-clone')
   run(['git','checkout','--detach',rev],role+'-checkout',clone)
   assert run(['git','rev-parse','HEAD'],role+'-head',clone).strip()==rev
   assert not run(['git','status','--porcelain=v1'],role+'-status',clone).strip()
   listing=run(['git','ls-tree','-r',rev],role+'-tree',clone);assert '160000 ' not in listing
   stage=clone/('stage-'+str(stage_num));issues=[str(x) for x in stage.rglob('*') if x.is_symlink() or x.name in ['.git','.gitmodules']]
   assert not issues,issues
   hashes={str(x.relative_to(stage)):sha(x.read_bytes()) for x in stage.rglob('*') if x.is_file()}
   facts['source'][role]=dict(revision=rev,stage=stage_num,clone=str(clone),source_sha256=hashes,tree_issues=issues,clean=True,image_tag=prefix+':'+role)
   (out/(role+'-RUN.md')).write_bytes((stage/'RUN.md').read_bytes())
   if role=='current':
    assert run(['git','rev-parse',rev+':stage-4'],role+'-stage4-tree',clone).strip()==TREE
    for n,accepted in [(1,S1),(2,S2),(3,S3)]:
     assert not run(['git','diff',accepted,rev,'--','stage-'+str(n)],'frozen-stage'+str(n)+'-diff',clone).strip()
     facts['frozen_stage'+str(n)+'_unchanged']=True
    facts['clone']=str(clone)
   run(['docker','build','-t',prefix+':'+role,'.'],role+'-build',stage)
   image=json.loads(run(['docker','image','inspect',prefix+':'+role],role+'-image'))[0]
   facts['source'][role]['image_id']=image['Id'];save()
  context=out/'own-client-context';context.mkdir();manifest=[]
  for folder in ['stage-1','stage-2','stage-3','stage-4']:
   (context/folder).mkdir()
   names=run(['git','ls-tree','--name-only',a.probe_revision+':evidence/independent-verifier/'+folder],folder+'-client-list').splitlines()
   for name in names:
    if not (name.endswith('.py') or name=='Browser.Dockerfile'):continue
    argv=['git','show',a.probe_revision+':evidence/independent-verifier/'+folder+'/'+name]
    data=subprocess.check_output(argv,cwd=R);(context/folder/name).write_bytes(data)
    manifest.append(dict(path=folder+'/'+name,sha256=sha(data),argv=argv))
  for folder,name in [('stage-1','candidate-7/coverage.csv'),('stage-2','candidate-1/coverage.csv')]:
   argv=['git','show',a.probe_revision+':evidence/independent-verifier/'+folder+'/'+name];data=subprocess.check_output(argv,cwd=R)
   target=context/folder/name;target.parent.mkdir(parents=True);target.write_bytes(data);manifest.append(dict(path=folder+'/'+name,sha256=sha(data),argv=argv))
  docker=(context/'stage-2/Browser.Dockerfile').read_text()+'\nCOPY stage-3/*.py /verifier/stage-3/\nCOPY stage-4/*.py /verifier/stage-4/\n'
  (context/'Dockerfile').write_text(docker);facts['client_manifest']=manifest;facts['runner_image']=prefix+':client'
  run(['docker','build','-t',facts['runner_image'],'.'],'client-build',context)
  facts['runner_image_id']=json.loads(run(['docker','image','inspect',facts['runner_image']],'client-image'))[0]['Id']
  run(['docker','network','create','--internal',network],'network-create');created_network=True
  info=json.loads(run(['docker','network','inspect',network],'network-inspect'))[0];assert info['Internal']
  facts['network']=network;urls={}
  roles=[('target','current',18309,18300,True),('peer','current',8080,18301,False),('third','current',18311,18303,True),
   ('accepted-s1','accepted-s1',18312,18304,True),('accepted-s2','accepted-s2',18313,18305,True),
   ('legacy-s1','legacy-s1',18314,18306,True),('legacy-s2','legacy-s2',18315,18307,True),('accepted-s3','accepted-s3',18316,18308,True)]
  for role,source,port,host,override in roles:
   name=prefix+'-'+role;assert len(name)<=63
   argv=['docker','run','-d','--name',name,'--network',network,'--cpus','2','--memory','2g','-p',f'127.0.0.1:{host}:{port}']
   if override:argv+=['-e','PORT='+str(port)]
   argv+=[facts['source'][source]['image_tag']]
   launch_at=dt.datetime.now(dt.timezone.utc).isoformat();began=time.monotonic()
   run(argv,role+'-start');containers.append(name);urls[role]=f'http://{name}:{port}'
   run(['docker','run','--rm','--name',prefix+'-health','--network',network,'--cpus','2','--memory','2g','--entrypoint','python',facts['runner_image'],
    '/verifier/stage-1/health.py','--url',urls[role]+'/health','--timeout','57'],role+'-health')
   elapsed=time.monotonic()-began;assert elapsed<60
   inspected=json.loads(run(['docker','inspect',name],role+'-inspect'))[0]
   assert inspected['HostConfig']['NanoCpus']==2000000000 and inspected['HostConfig']['Memory']==2147483648 and not inspected['Mounts'] and inspected['HostConfig']['NetworkMode']==network
   names=[n for n in facts['source'][source]['source_sha256'] if n.endswith('.py') or n.startswith('web/')]
   code='import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in '+repr(names)+'}))'
   packaged=json.loads(run(['docker','exec',name,'python','-c',code],role+'-packaged-hashes'))
   assert packaged=={n:facts['source'][source]['source_sha256'][n] for n in names}
   assert inspected['Image']==facts['source'][source]['image_id']
   facts['containers'].append(dict(name=name,role=role,source=source,url=urls[role],default_port=not override,internal_port=port,host_port=host,
    startup_to_health_seconds=elapsed,launch_at=launch_at,healthy_at=dt.datetime.now(dt.timezone.utc).isoformat(),health_before_source_inspection=True,
    cross_container_access=True,cpu=2,memory_bytes=2147483648,mounts=[],actual_image_id=inspected['Image'],packaged_sha256=packaged));save()
  urls['exact-s1']=urls['accepted-s1']
  source_proof=out/'source-proof.json';source_proof.write_text(json.dumps(dict(candidate=C,stage_4_tree=TREE,source=facts['source'],client_manifest=manifest,
   frozen_stage1_unchanged=True,frozen_stage2_unchanged=True,frozen_stage3_unchanged=True),indent=2)+'\n')
  resources=out/'resource-proof.json';resources.write_text(json.dumps(dict(network=network,internal=True,containers=facts['containers'],runner_image_id=facts['runner_image_id']),indent=2)+'\n')
  package=HERE/'candidate-1/intake.json'
  release={**intake,'urls':urls,'source_revisions':{k:v[0] for k,v in ORIGINS.items()},'stage':4,'image_id':facts['source']['current']['image_id'],
   'fresh_clone_verified':True,'current_packaged_hashes_verified':True,'offline_2cpu_2g_no_service_mounts_verified':True,
   'frozen_stage1_verified':True,'frozen_stage2_verified':True,'frozen_stage3_verified':True,'complete_nine_file_copy_verified':True,'runtime':str(out),
   'source_proof_path':str(source_proof),'source_proof_sha256':sha(source_proof.read_bytes()),
   'resource_proof_path':str(resources),'resource_proof_sha256':sha(resources.read_bytes()),
   'package_intake_path':str(package),'package_intake_sha256':sha(package.read_bytes())}
  (out/'release.json').write_text(json.dumps(release,indent=2)+'\n')
  facts.update(status='running_for_independent_checks',urls=urls,retained_services=True);save()
  print(json.dumps({'candidate':C,'runtime':str(out),'clone':facts['clone'],'readiness':{x['role']:x['startup_to_health_seconds'] for x in facts['containers']}}))
 except Exception as e:
  facts['status']='runner_error';facts['runner_error']=dict(type=type(e).__name__,message=str(e));save()
  for name in containers:run(['docker','rm','-f',name],name+'-cleanup',required=False)
  if created_network:run(['docker','network','rm',network],'network-cleanup',required=False)
  raise
if __name__=='__main__':main()
