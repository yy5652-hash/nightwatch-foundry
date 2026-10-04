"""Prospective copies of own sealed orchestration; never rewrite old evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; P=ROOT.parent
C='58270860cb6a762c8a4c2a551672701fb00bd613'; T='00e208c746a488a9b4cb0761efd04b90c4248dd8'
def main():
    v=json.loads((ROOT/'intake.json').read_text())
    v.update(complete_candidate_package=True,systems_full_handoff=True,interface_full_handoff=True,
        systems_revision='7723ad57402135b37b705660d9feda065374afb8',interface_revision=C,
        accepted_stage1='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b',
        accepted_stage2='4dba10246b07b2dda19de260d529f9d94ba0a1ed',
        accepted_stage3='91e2c471acded1b861b3fec725f202297b1c6740')
    assert not (ROOT/'release-intake.json').exists()
    (ROOT/'release-intake.json').write_text(json.dumps(v,indent=2)+'\n')
    old=(P/'stage4_source_audit.py').read_text()
    old=old.replace('261e4d9456a04a8b57ed46db71a09ac267ff15a9',C).replace('501d27abab7226546da42edb1131ef8aa037deaf',T)
    old=old.replace('candidate-1/intake.json','candidate-2/release-intake.json').replace('TK-20261004-S4-independent-verifier-CANDIDATE-1','TK-20261004-S4-independent-verifier-CANDIDATE-2')
    old=old.replace("('ce078a87f81904195e2484c213bc5582e838f91a','evidence/systems-engineer/',443),(C,'evidence/interface-engineer/',264)","('7723ad57402135b37b705660d9feda065374afb8','evidence/systems-engineer/',256),(C,'evidence/interface-engineer/',272)")
    old=old.replace("['bb2167dd2e2f0b8d70d194e0a790bcdb6e045b2e','04f7371dd8208c2be0b4981d8b281983b81b2cdc','ce078a87f81904195e2484c213bc5582e838f91a']","['969ee95ac1a7bb1d28ecf075f256b6eb4c32f6fb','2601ee9c94838a53f47a3a63bacd1e864b500122','7723ad57402135b37b705660d9feda065374afb8']")
    old=old.replace("('30e6b6edd6e6e061e5b3ff155b42261c9c97568a','Systems Engineer',['stage-4/core.py']),","('30e6b6edd6e6e061e5b3ff155b42261c9c97568a','Systems Engineer',['stage-4/core.py']),('6225a0e6f25afd28ceddac472887a77e5941bba5','Systems Engineer',['stage-4/core.py']),")
    old=old.replace('complete22parts_acknowledged=True','complete23parts_acknowledged=True')
    (P/'candidate2_source_audit.py').write_text(old)
    runtime=(P/'stage4_runtime.py').read_text().replace('261e4d9456a04a8b57ed46db71a09ac267ff15a9',C).replace('501d27abab7226546da42edb1131ef8aa037deaf',T)
    runtime=runtime.replace('candidate-1/intake.json','candidate-2/release-intake.json').replace('candidate-1/source-audit-02/source-proof.json','candidate-2/source-audit-01/source-proof.json').replace("len(intake['all_parts'])==22","len(intake['all_parts'])==23")
    runtime=runtime.replace("for folder,name in [('stage-1','candidate-7/coverage.csv')", "for name in sorted(x.name for x in (HERE/'repair-1').glob('*.py')):\n   argv=['git','show',a.probe_revision+':evidence/independent-verifier/stage-4/repair-1/'+name]\n   data=subprocess.check_output(argv,cwd=R);target=context/'stage-4/repair-1'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);manifest.append(dict(path='stage-4/repair-1/'+name,sha256=sha(data),argv=argv))\n  for folder,name in [('stage-1','candidate-7/coverage.csv')")
    runtime=runtime.replace("COPY stage-4/*.py /verifier/stage-4/\\n'","COPY stage-4/*.py /verifier/stage-4/\\nCOPY stage-4/repair-1/*.py /verifier/stage-4/repair-1/\\n'")
    runtime=runtime.replace("'fresh_clone_verified':True", "'new_complete_execution_package':True,'preparation_only':False,'rejected_evidence_preserved':True,'rejected_preservation_path':str(HERE/'candidate-2/rejected-preservation.json'),'rejected_preservation_sha256':sha((HERE/'candidate-2/rejected-preservation.json').read_bytes()),'fresh_clone_verified':True")
    runtime=runtime.replace("urls['exact-s1']=urls['accepted-s1']", "urls['exact-s1']=urls['accepted-s1']")
    runtime=runtime.replace("'source_revisions':{k:v[0] for k,v in ORIGINS.items()}", "'source_revisions':{**{k:v[0] for k,v in ORIGINS.items()},'exact-s1':S1}")
    runtime=runtime.replace("'fresh_clone_verified':True", "'complete_package':True,'offline_2cpu_2g_no_mounts_verified':True,'fresh_clone_verified':True")
    (P/'candidate2_runtime.py').write_text(runtime)
if __name__=='__main__':main()
