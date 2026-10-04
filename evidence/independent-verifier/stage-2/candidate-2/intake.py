"""Record the complete direct release without substituting durable-file markers."""
import csv, datetime as dt, hashlib, json, shutil, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=HERE.parents[3]; W=R.parents[1]
C='4dba10246b07b2dda19de260d529f9d94ba0a1ed'
PARTS=['0f7a549f-fb98-4627-94c3-3b2d58452046','15bf91aa-c35e-42d5-b1f7-c5096916f5e9','7f442611-3a48-4487-b877-a9a0cc1d90a2','cca0b799-065a-4676-92ca-483a22814bff','92cc6c6b-f378-43bd-a5a5-3b19229988ae','a7a14146-76b6-4bff-ad1b-a2214e67eff2','991d818c-7735-4165-b4a7-3b2c6ca2ba23','82e60f4d-a32e-410b-83d1-839d9c9c58da','f5ee463b-95a6-44b0-9ccf-1393a58f8de0','3552fde2-084f-408c-8af5-3f658e0e39c5','09f1b056-3396-43d6-ae66-500c70521147','98ac0757-4ff5-4d5c-aa36-e1dc287e4f7d','06bdfc87-d9d7-42b2-8a2c-dc977bb2fc3e']
src=HERE/'source-inputs'; src.mkdir(exist_ok=False)
paths=[W/'kickoff/docs/participant-guide.md',W/'kickoff/tablekeeper/spec/stage-1.md',W/'kickoff/tablekeeper/spec/stage-2.md',W/'factory/PRODUCT_ACCEPTANCE.md']
paths += [R/'evidence/coordinator'/n for n in ['timestamp-representation-decision.md','receipt-shape-decision.md','numeric-control-decision.md','json-number-semantics-decision.md','stage-2-renewed-base-copy-proof.json']]
paths += [R/'evidence/coordinator/handoffs'/('TK-20261004-S2-independent-verifier-CANDIDATE-2'+ext) for ext in ['.md','.delivery.json']]
paths += [R/'evidence/coordinator/accepted/stage-1-75005d57fe0904753eac4eab5bf4e4c9a78b6d1b.json']
manifest=[]
for p in paths:
    b=p.read_bytes(); (src/p.name).write_bytes(b)
    manifest.append({'source':str(p),'saved':str(src/p.name),'sha256':hashlib.sha256(b).hexdigest()})
rows=list(csv.DictReader((HERE.parent/'reconstruction-preparation-2/checks-03/coverage.csv').open()))
for row in rows:
    row['candidate_full_revision']=C; row['verdict']='unverified'
    row['evidence_path']='PENDING_FRESH_CURRENT_CANDIDATE_EXECUTION'
with (HERE/'coverage-prepared.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
intake=dict(package_id='TK-20261004-S2-independent-verifier-CANDIDATE-2',candidate=C,stage_2_tree='422380c814043021c2df2daad8edbbb34d5b5887',complete_package=True,end_received=True,execution_authorized=True,all_parts=PARTS,end_observed_in_runtime_part=13,acknowledged_before_execution=True,review_started_at='2026-10-04T05:59:20.202000+00:00',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),systems_handoff_revision=C,interface_handoff_revision='1e3af87d78c2d6c037650a9c134453012d4fb0c6',systems_implementation='f783598428a88d53490f68498063ed69e02201b3',interface_implementation='a040054f2a8d00c560bea7f02324d1443c5a3f14',accepted_stage1='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b',stage1_verdict='a22de6b769c1454c35650377da1251edc99de744',base_copy_proof_revision='ab8545fc0f3f9bf1cdf8cd2d3a9e7ed8ad29d3ca',preparation_revision='af6ddc35529d488ba9331a81fb415242fa3ce72f',normative_rows=5179,diagnostic_rows=22,all_rows_unverified=True,source_inputs=manifest,harness='Codex',configured_model='gpt-6.1-sol',actual_model_effort_usage_cost='unknown')
(HERE/'intake.json').write_text(json.dumps(intake,indent=2)+'\n')
print(json.dumps({'candidate':C,'parts':len(PARTS),'source_files':len(manifest),'normative_rows':5179,'status':'intake_bound_no_service_execution'}))
