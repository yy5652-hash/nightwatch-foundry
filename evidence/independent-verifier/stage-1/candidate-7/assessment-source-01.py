"""Bind current candidate7 observations; no historical passes are reused."""
import copy
import csv
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path
from coverage_metadata import validate

sys.set_int_max_str_digits(0)  # Own evidence reader only; not service/client.
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1];TARGET=HERE/'candidate-7'
CANDIDATE='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
evidence=[];runs={}
def load(path):return json.loads(path.read_text())
def relative(path):return str(path.relative_to(REPO))
def add(checks,path,argv,label):
    for row in checks:
        evidence.append(dict(**row,evidence_path=relative(path)+'#'+row['requirement_id'],command=shlex.join(argv),run=label))
def count(data,requests='requests',assertions='assertions',failed='failed_assertions'):
    return dict(requests=data[requests],assertions=data[assertions],raw_failed_assertions=data[failed],seconds=data['duration_seconds'])
meta=load(TARGET/'baseline-01/preflight.json');base_commands=load(TARGET/'baseline-01/commands.json');extras=load(TARGET/'baseline-01/extra-commands.json')
for label in ['probes','original-minimal','calendar-minimal','race50','legacy','decimal']:
    p=TARGET/'baseline-01'/label;data=load(p/'summary.json');assert data['candidate']==CANDIDATE
    runs['baseline-'+label]=count(data,failed='failures')
    argv=meta['probe_command'] if label=='probes' else next(c['command'] for c in extras if c['log']==label+'-client.log')
    add(load(p/'assertions.json'),p/'assertions.json',argv,'baseline-'+label)
large=load(TARGET/'baseline-01/large-minutes.json');assert large['candidate_full_revision']==CANDIDATE
runs['large-minutes']=count(large,requests='http_operations')
add(large['results'],TARGET/'baseline-01/large-minutes.json',next(c['command'] for c in extras if c['log']=='large-minutes.json'),'large-minutes')
for family in ['semantic','opaque-ids','nesting','snapshot']:
    folder=TARGET/(family+'-01');data=load(folder/'probes/summary.json');assert data['candidate']==CANDIDATE and not data['flow_errors']
    runs[family]=count(data);argv=next(c['argv'] for c in load(folder/'commands.json') if c['log']=='semantic-probe.log')
    add(load(folder/'probes/assertions.json'),folder/'probes/assertions.json',argv,family)
for family in ['numeric','fractional']:
    folder=TARGET/(family+'-01');data=load(folder/'probes.json');assert data['candidate_full_revision']==CANDIDATE
    runs[family]=count(data,requests='http_operations');argv=next(c['argv'] for c in load(folder/'commands.json') if c['log']=='probes.json')
    add(data['results'],folder/'probes.json',argv,family)
deep=load(TARGET/'very-deep-01/probes.json');assert deep['candidate']==CANDIDATE
runs['very-deep']=count(deep);add(deep['checks'],TARGET/'very-deep-01/probes.json',load(TARGET/'very-deep-01/command.json')['argv'],'very-deep')
decoder=load(TARGET/'decoder-02/probes/probes.json');assert decoder['candidate']==CANDIDATE and not decoder['runner_errors'] and not decoder['blocked_paths']
runs['decoder-corrected']=count(decoder)
add(decoder['checks'],TARGET/'decoder-02/probes/probes.json',next(c['argv'] for c in load(TARGET/'decoder-02/commands.json') if c['log']=='decoder-probe.log'),'decoder-corrected')
race=load(TARGET/'deep-race-01/probes.json');assert race['candidate']==CANDIDATE and not race['runner_errors']
runs['deep-race']=count(race)
add(race['checks'],TARGET/'deep-race-01/probes.json',next(c['argv'] for c in load(TARGET/'deep-race-01/commands.json') if c['log']=='client.log'),'deep-race')
partial=load(TARGET/'decoder-01/probes/probes.json');assert partial['runner_errors'] and partial['candidate']==CANDIDATE
partial_run=dict(**count(partial),runner_errors=partial['runner_errors'],coverage_use='No partial check is used for final row verification; fresh corrected run establishes the full affected scope.')

source=load(TARGET/'source-audit.json');images=load(TARGET/'packaged-image-proof.json')
official=load(TARGET/'official/report.json');s1=load(TARGET/'official/stage-1.counts.json');s2=load(TARGET/'official/stage-2.counts.json')
assert official['revision']==CANDIDATE and official['mode']=='isolated' and official['pytest_args']==[]
inspections=[load(TARGET/'baseline-01'/c['log'])[0] for c in base_commands if c['command'][:2]==['docker','inspect']]
network=load(TARGET/'baseline-01'/next(c['log'] for c in base_commands if c['command'][:3]==['docker','network','inspect']))[0]
health=[v for v in meta.values() if isinstance(v,dict) and 'readiness_seconds' in v]
clone=Path(meta['clone']);clean_status=subprocess.check_output(['git','status','--porcelain=v1'],cwd=clone,text=True);clean_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip()
proofs=[load(TARGET/(f+'-01')/'source-runtime-proof.json') for f in ['semantic','opaque-ids','nesting','snapshot']]+[load(TARGET/'decoder-02/source-runtime-proof.json'),load(TARGET/'decoder-01/source-runtime-proof.json')]
cleanup=[dict(command=c['command'],returncode=c['returncode']) for c in extras if c['command'][:3] in [['docker','rm','-f'],['docker','network','rm']]]
for proof in proofs:
    assert proof['status']=='completed' and proof['candidate']==CANDIDATE and all(x['returncode']==0 for x in proof['cleanup'])
    assert proof['source']['current']['stage_files_sha256']==source['files']
    cleanup.extend(proof['cleanup'])
for family in ['numeric-01','fractional-01']:
    for c in load(TARGET/family/'commands.json'):
        if c['argv'][:3] in [['docker','rm','-f'],['docker','network','rm']]:cleanup.append(dict(command=c['argv'],returncode=c['returncode']))
race_runtime=load(TARGET/'deep-race-01/runtime.json');assert race_runtime['status']=='completed' and race_runtime['client_returncode']==0
cleanup.extend(race_runtime['cleanup']);assert cleanup and all(c['returncode']==0 for c in cleanup)
inventory_argv=['docker','ps','-a','--filter','name=independent-verifier-','--format','{{.Names}}']
inventory=subprocess.check_output(inventory_argv,cwd=REPO,text=True);assert not inventory.strip(),inventory
(TARGET/'final-own-resource-inventory.json').write_text(json.dumps(dict(argv=inventory_argv,observed_names=[],returncode=0,scope='Own namespace only; no peer resource inspected or removed'),indent=2)+'\n')
audit={
 'dockerfile':all(c['returncode']==0 for c in base_commands if c['command'][:2]==['docker','build']),
 'run-document':bool((TARGET/'source-inputs/RUN.md').read_text()) and all(v['healthy'] for v in health),
 'single-image':len(inspections)==2 and all(not x['Mounts'] for x in inspections),
 'offline':network['Internal'] is True,
 'cpu':all(x['HostConfig']['NanoCpus']==2000000000 for x in inspections),
 'memory':all(x['HostConfig']['Memory']==2147483648 for x in inspections),
 'startup':len(health)==2 and all(v['healthy'] and v['readiness_seconds']<5 for v in health),
 'packaged-assets':all(p['observed']==p['expected']=={f:source['files'][f] for f in p['observed']} for p in images['proof']),
 'listen-all':proofs[0]['startup']['base']['cross_container_health'] and proofs[0]['startup']['peer']['cross_container_health'],
 'port-default':any(not v['port_override'] and v['internal_port']==8080 for v in health),
 'port-override':any(v['port_override'] and v['internal_port']==18309 for v in health),
 'complete-clone':clean_head==CANDIDATE and not clean_status and not meta['tree_issues'] and not source['symlink_or_submodule_entries'],
 'two-builders':source['two_builders'],'history-preserved':source['history_preserved'],
 'own-stage':official['state']=='completed' and official['claimed_stage']=='1' and s1['passed']==s1['collected']==120,
 'source-provenance':source['complete_initial_handoffs'] and source['empty_root_intake'] and source['unchanged_interface_runtime'] and source['stage_tree_matches_production_revision'],
}
assert all(audit.values()),audit
(TARGET/'runtime-audit.json').write_text(json.dumps(dict(candidate=CANDIDATE,checks=audit,readiness=health,source_image_proof=images,clean_clone_head=clean_head,clean_clone_status=clean_status,cleanup=cleanup,cache='Available; no uncached claim',scope='Fresh full-context exact named baseline build, own constrained/offline service processes, unchanged official checker; additional retained-image race explicitly separate'),indent=2)+'\n')
for key,passed in audit.items():
    evidence.append(dict(requirement_id='TK1-'+key,passed=passed,evidence_path=relative(TARGET/'runtime-audit.json')+'#checks.'+key,command=shlex.join([str(WORKSPACE/'.venv/bin/python'),'-B','evidence/independent-verifier/stage-1/candidate7_assess.py']),run='fresh source/runtime/official audit'))
rows=list(csv.DictReader((TARGET/'coverage-prepared.csv').open()));assert len(rows)==4237
template=copy.deepcopy(rows[0]);existing={r['requirement_id'] for r in rows}
for check in race['checks']:
    assert check['requirement_id'] not in existing;existing.add(check['requirement_id'])
    row=copy.deepcopy(template);row.update(requirement_id=check['requirement_id'],source_section='1 / 2 resource limits / 3.4 / 7 / 10',source_line='10',requirement_text='Independently staged fifty-client depth20000 array/object HTTP waves: '+check['requirement_id'].removeprefix('TK1-deep-race-'),owner='systems-engineer',implementation_owner='systems-engineer',verification_owner='independent-verifier',verification_method='separate raw HTTP client with fifty-worker barrier and unchanged private-byte transfer',case='deep-race',inherited_from='',historical_verdict='',historical_candidate='',historical_evidence_path='',normative='True',preparation_origin='Own sealed raw race source 27aaf9a931893995b62c060dc77a1237dc0f9fd4',interpretation_note='Sampled fifty-client waves and finite depths; no arbitrary-size/depth performance claim.')
    rows.append(row)
bindings={}
for row in rows:
    row['candidate_full_revision']=CANDIDATE;found=[e for e in evidence if e['requirement_id']==row['requirement_id']];bindings[row['requirement_id']]=found
    row['verdict']='verified' if found and all(e['passed'] for e in found) else 'failed' if found else 'unverified'
    row['evidence_path']='; '.join(sorted({e['evidence_path'] for e in found})) if found else relative(TARGET/'opaque-ids-01/probes/admission-diagnostics.json')+'#'+row['requirement_id'] if row['normative']!='True' else 'UNVERIFIED'
    row['executable_command_or_interaction']='\n'.join(sorted({e['command'] for e in found})) if found else 'Observed nonnormative fixture admission diagnostic; actual status retained separately.' if row['normative']!='True' else 'Fresh evidence link missing; acceptance prohibited.'
    if 'very-deep' in row['requirement_id']:
        row['interpretation_note']='Fresh candidate7 controls require successful valid deep bodies and real successful deep receipts. Separate actually malformed signup and invalid party bodies establish refusal rollback/failed-key reuse; successful alias/replacement paths use deep receipts. Historical candidate6 failure remains unchanged.'
    if row['requirement_id']=='TK1-legacy-export-equality':row['interpretation_note']='Fresh genuine-source original public values and receipt replay preserved; adopted private schema2/profile normalization checked. No obsolete whole-envelope comparison is executed as a current normative expectation.'
normative=[r for r in rows if r['normative']=='True'];metadata=validate(rows)
assert len(normative)==4215+len(race['checks']) and len(rows)-len(normative)==22
metadata.update(candidate=CANDIDATE,normative_rows=len(normative),diagnostic_rows=22,missing_owner_fields=0,candidate_bindings_complete=all(r['candidate_full_revision']==CANDIDATE for r in rows))
(TARGET/'metadata-self-check.json').write_text(json.dumps(metadata,indent=2)+'\n')
with (TARGET/'coverage.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
(TARGET/'coverage-bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
now=dt.datetime.now(dt.timezone.utc);intake=load(TARGET/'intake.json');started=dt.datetime.fromisoformat(intake['review_started_at'])
failed=[r['requirement_id'] for r in normative if r['verdict']=='failed'];unverified=[r['requirement_id'] for r in normative if r['verdict']=='unverified']
verdict='reject' if failed or unverified else 'accept'
summary=dict(candidate=CANDIDATE,production_revision=intake['implementation_revision'],stage_tree=intake['stage_1_tree'],verdict=verdict,highest_independently_accepted_stage=1 if verdict=='accept' else 0,normative_rows=len(normative),verified=sum(r['verdict']=='verified' for r in normative),failed=len(failed),unverified=len(unverified),failed_ids=failed,unverified_ids=unverified,diagnostic_rows=22,diagnostic_classification='Nonnormative chosen fixture-ID admission diagnostics remain separate;22/22 admitted,308 conditional usability obligations freshly verified.',metadata=metadata,observed_runs=runs,completed_http_requests=sum(r['requests'] for r in runs.values()),completed_assertions=sum(r['assertions'] for r in runs.values()),completed_failed_assertions=sum(r['raw_failed_assertions'] for r in runs.values()),partial_client_error_run=partial_run,all_current_http_requests=sum(r['requests'] for r in runs.values())+partial_run['requests'],all_current_assertions=sum(r['assertions'] for r in runs.values())+partial_run['assertions'],all_current_failed_assertions=sum(r['raw_failed_assertions'] for r in runs.values())+partial_run['raw_failed_assertions'],official_stage1=s1,official_stage2_overshoot=dict(**s2,not_executed=s2['collected']-s2['passed']-s2['failed']-s2['skipped']-s2['errors']),official_wall_seconds=load(TARGET/'official-command.json')['wall_seconds'],earlier_stage_regression='None applies to Stage1',clean_clone=True,source_image_hashes_match=True,default_readiness_seconds=next(v['readiness_seconds'] for v in health if not v['port_override']),override_readiness_seconds=next(v['readiness_seconds'] for v in health if v['port_override']),cleanup_commands=len(cleanup),review_started_at=started.isoformat(),review_finished_at=now.isoformat(),review_interval_seconds=(now-started).total_seconds(),elapsed_scope='Measured from private review-task activation to final evidence aggregation; whole factory interval coordinator-owned',harness='Codex',configured_model='gpt-6.1-sol',actual_model='unknown',reasoning_effort='unknown',token_usage='unknown',catalog_estimated_cost='unknown',billed_spend='unknown',limits=['Historical exact-instant/nearest representable minute-offset interpretation and immutable legacy offset-seconds strings remain disclosed; incompatible literal offset grammars are not simultaneously claimed.','Numeric whole-value and receipt-scoped genuine legacy comparison follow adopted source interpretation.','Finite sampled depths/payloads and concurrent waves do not establish arbitrary-size/depth performance. Available build cache reused.','Exact instantaneous cutoff boundaries use labelled source supplements; client scheduling does not expose internal serializer timing.','Genuine room export/publication/final submission and hidden judging remain operator-controlled.'])
(TARGET/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['candidate','verdict','normative_rows','verified','failed','unverified','completed_http_requests','completed_assertions','completed_failed_assertions','cleanup_commands']}))
if failed or unverified:print(json.dumps(dict(failed_ids=failed,unverified_ids=unverified)))
