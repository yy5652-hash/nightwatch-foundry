"""Conservative row binding and complete rejected-candidate record."""
import csv, datetime as dt, hashlib, json, shutil, sys
from collections import Counter, defaultdict
from pathlib import Path
csv.field_size_limit(sys.maxsize)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-1';C='261e4d9456a04a8b57ed46db71a09ac267ff15a9'
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def main():
 assert not (H/'coverage.csv').exists()
 prior=HERE/'initial-1/checks-04/coverage.csv';rows=list(csv.DictReader(prior.open()));fields=list(rows[0]);assert len(rows)==7850
 summaries={p.parent.name:json.loads(p.read_text()) for p in (H/'current-http-01').glob('*/summary.json')}
 assert len(summaries)==7 and summaries['closure-errors']['failed']==12
 records=defaultdict(list)
 for family in summaries:
  p=H/'current-http-01'/family/'assertions.json'
  for index,a in enumerate(json.loads(p.read_text())):
   records[a.get('requirement_id') or a.get('requirement')].append(dict(file=str(p.relative_to(R)),index=index,record=a,family=family))
 allowed=set('''TK4-preview-status TK4-preview-anonymous TK4-preview-nonmanager TK4-preview-response-revision TK4-preview-response-all TK4-preview-response-changed TK4-preview-response-moved TK4-preview-no-booking-write TK4-apply-status TK4-apply-restaurant-once TK4-apply-moved-revision TK4-apply-moved-event TK4-apply-event-field TK4-apply-event-plan TK4-apply-applied-different-key TK4-apply-wrong-restaurant TK4-apply-stale TK4-apply-stale-atomic TK4-closure-create TK4-closure-explain-no-overlap TK4-amend-series-once TK4-amend-retain-reference TK4-amend-member-revision TK4-amend-no-exceptions TK4-amend-skip-exception TK4-amend-skip-cancelled TK4-amend-retain-seating TK4-amend-noop-success TK4-amend-anonymous TK4-amend-other-owner TK4-concurrency-apply-identical50 TK4-concurrency-amend-identical50 TK4-instants-to-after-18'''.split())
 allowed.update(k for k in records if k and k.startswith('TK4-numeric-'))
 commands=json.loads((H/'current-http-01/commands.json').read_text());by_family={c['family']:c for c in commands};bindings={}
 for row in rows:
  row['candidate_full_revision']=C
  if row['requirement_id'] in allowed:
   observations=records[row['requirement_id']];assert observations and all(o['record']['passed'] for o in observations)
   row.update(verdict='verified',verification_method='Fresh independent HTTP; concrete assertion-level scope',evidence_path=observations[0]['file'],executable_command_or_interaction=json.dumps(by_family[observations[0]['family']]['argv']),preparation_status='current executed evidence')
   bindings[row['requirement_id']]=observations
  else:
   row['verdict']='unverified';row['verification_method']='Unexecuted current obligation; rejected review stops before complete acceptance scope';row['preparation_status']='No current passing binding; prior preparation/history retained only'
   if not row['executable_command_or_interaction'].startswith(('PENDING','UNEXECUTED')):row['executable_command_or_interaction']='UNEXECUTED CURRENT SCOPE: '+row['executable_command_or_interaction']
 # Twelve independently explicit inherited field-type obligations were not split
 # in the initial Stage4 inventory. Add them transparently; hide no old rows.
 failed=[]
 for field in ['from','to']:
  for name in ['null','true','false','number','array','object']:
   observation=records['closure-'+field+'-wrong-type-'+name];assert len(observation)==1 and not observation[0]['record']['passed']
   ident='TK4-closure-type-'+field+'-'+name;row={k:'' for k in fields}
   row.update(requirement_id=ident,requirement_text='Closure '+field+' JSON '+name+' is a wrong endpoint field type:400 malformed_request; not422 invalid interval.',source_section='Stage1 section5 inherited wrong-field-type rule; Stage4 Seating changes after a table closure',source_line='20',source_file='stage-4.md',introduced_stage='4',applicable_stages='4',owner='systems-engineer',implementation_owner='systems-engineer',verification_owner='independent-verifier',candidate_full_revision=C,verification_method='Fresh exact-current independent raw HTTP; wrong-type error classification',executable_command_or_interaction=json.dumps(by_family['closure-errors']['argv']),evidence_path=observation[0]['file'],verdict='failed',normative='True',case=field+'-'+name,interpretation_note='See candidate-1/CLOSURE_ERROR_RECONCILIATION.md; no new coordinator interpretation adopted.',inherited_from='Stage1 section5',preparation_status='actual current failure')
   rows.append(row);bindings[ident]=observation;failed.append(ident)
 with (H/'coverage.csv').open('w',newline='') as f:writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows(rows)
 required=['requirement_id','requirement_text','source_section','source_line','source_file','introduced_stage','applicable_stages','owner','candidate_full_revision','verification_method','executable_command_or_interaction','evidence_path','verdict','normative']
 assert len({r['requirement_id'] for r in rows})==len(rows)
 for row in rows:
  assert all(row[k] for k in required),row['requirement_id'];assert (R/row['evidence_path']).is_file(),row['evidence_path']
  assert row['implementation_owner'] and row['verification_owner']=='independent-verifier'
 normative=[r for r in rows if r['normative'].lower()=='true'];counts=Counter(r['verdict'] for r in normative)
 assert len(normative)==7840 and len(failed)==12
 save(H/'coverage-bindings.json',bindings);save(H/'metadata-self-check.json',dict(candidate=C,total_records=len(rows),normative_records=len(normative),diagnostics=len(rows)-len(normative),normative_verdicts=dict(counts),unique_identifiers=True,required_fields=required,all_owners_present=True,all_concrete_file_links=True,unverified_links_are_preparation_only=True,added_requirements=failed,removed_rows=0,prior_csv_sha256=hashlib.sha256(prior.read_bytes()).hexdigest()))
 command=json.loads((H/'official-command.json').read_text());official=Path(command['output']);shutil.copytree(official,H/'official')
 official_report=json.loads((H/'official/report.json').read_text());assert official_report['revision']==C
 totals=dict(requests=sum(s['requests'] for s in summaries.values()),assertions=sum(s['assertions'] for s in summaries.values()),failed=sum(s['failed'] for s in summaries.values()));totals['passed']=totals['assertions']-totals['failed']
 runtime=json.loads((H/'runtime-01/preflight.json').read_text());cleanup=json.loads((H/'cleanup-01/proof.json').read_text());assert cleanup['all_removal_codes_zero']
 save(H/'completed-runs.json',dict(candidate=C,protocols=summaries,totals=totals,official=official_report['checks'],current_browser_protocols=0,direct_model_calls=0,hidden_judging_results=None))
 save(H/'verdict.json',dict(candidate=C,stage_4_tree=runtime['stage_4_tree'],verdict='reject',highest_consecutive_accepted=3,normative_rows=len(normative),verdict_counts=dict(counts),separate_diagnostics=22,failed_obligations=failed,totals=totals,official=official_report['checks'],unverified_scope='Full inherited private decoder/numeric/deep/profile chains, staged race/export histories, heterogenous full-bound/fixed/prior closure oracle, current product/recovery/upgrade/contrast and every other unbound obligation remain unverified; early genuine conformance failure prevents acceptance.',production_edits=0,configured_harness='Codex',configured_model='gpt-6.1-sol',actual_model=None,actual_effort=None,token_usage=None,catalog_estimated_cost=None,billed_spend=None))
 report=f'''# Stage4 candidate1: reject

Exact full candidate **{C}**, tree **{runtime['stage_4_tree']}**: **reject**. Highest consecutive independently accepted stage remains **3**. Twelve fresh endpoint-type obligations fail: null, both booleans, number, array and object on each closure endpoint return422 `validation_failed`, while inherited Stage1 section5 requires400 `malformed_request`. Missing endpoints, bad strings and invalid interval ordering remain422. [Independent reconciliation](CLOSURE_ERROR_RECONCILIATION.md) gives the complete source reading and smallest reproduction. No new interpretation is adopted and no production source is edited.

All22parts and both END markers of CANDIDATE-1 were acknowledged on final inbound ce6b0a70-931d-476d-89ef-d35dd424c4f1 before execution. [Intake](intake.json) binds every actual part ID; the reciprocal acknowledgment ID is unknown. [Source audit](source-audit-02/source-proof.json) verifies all24 frozen files, the complete nine-file predecessor copy, substantive ownership and matching owning-builder tested/current trees. Builder results remain separate from this review.

Seven complete independent HTTP protocols make **{totals['requests']} requests / {totals['assertions']} assertions: {totals['passed']} passed,12 failed**, no client errors or skips. The closure protocol alone completes153requests/121assertions,109passed/12failed. All failed requests preserve raw exported bytes and permit corrected-body reuse of their keys. Malformed whole bodies/wrong table type return400; missing endpoints/bad formats/nonpositive intervals return422; used-key differences precede validation. Actual18-digit fractional boundary probes distinguish exact adjacency from positive submicrosecond overlap. Six separate preview/apply/six-booking oracle/amend/numeric/50-client families pass. The oracle is one actual finite six-table/four-pair/six-booking construction; full heterogeneous accepted policies/fixed bookings/prior closures and160 prepared model constructions are not claimed as current execution. [Exact selected runs](completed-runs.json) preserve each count separately.

Unchanged official isolated checks against the exact clean clone pass **120/120 Stage1,25/25 Stage2,7/7 Stage3,6/6 Stage4**; all errors/skips/deselections/xfails zero. Official claimed stage4 is directional shipped-check feedback, and does not override this rejected specification verdict. No suite, checker, selection or correct earlier behavior was altered. [Command](official-command.json) records actual argv, unique output, measured38.221281125seconds and exact clean kickoff803560d2a678ace1414465c098eb0ab5380ffade. Official UI traffic is separate from owned browser protocols, which are zero.

[Coverage](coverage.csv): **7,840 normative rows**, {counts['verified']}verified/12failed/{counts['unverified']}unverified, plus22separate unverified diagnostics;7,862unique total records. Initial7,828rows are retained and12 explicit new endpoint-type obligations are added transparently. The fourteen required fields, ownership/full candidate and every concrete file link pass [metadata audit](metadata-self-check.json). Current passing bindings are conservative individual assertions; unverified links point only to preparation/history and never imply a current pass. Entire remaining cumulative browser/upgrade/deep/decoder/numeric/atomic-prefix/private-state/full-bound scopes are unverified because the decisive failure stops promotion. No missing scope is suppressed, no old acceptance is rebound and no full-coverage acceptance is claimed.

The fresh clean detached clone is `{runtime['clone']}`; current image **{runtime['source']['current']['image_id']}**. All nine context and actual packaged hashes match. Eight current/genuine source services have inspected2CPU/2GiB/no mounts on an inspected internal offline network. Diagnostic clients explicitly mount owned proof/output files and are separately limited. Default8080 readiness upper bound is {next(c['startup_to_health_seconds'] for c in runtime['containers'] if c['role']=='peer'):.9f}s; override18309 upper bound is {next(c['startup_to_health_seconds'] for c in runtime['containers'] if c['role']=='target'):.9f}s, measured before later source inspection. Cross-container health/API traffic establishes selected-port listening; host-published reachability and uncached build are not claimed. Eight services were running/not OOM-killed before removal. [Cleanup](cleanup-01/proof.json) records **nine own service/network removals, all exit0**, empty own namespace, six retained exact clean clones, images retained and empty graded diff. Genuine sources were built/started, but independent genuine upgrade probes were not executed in this rejected review.

The first own source audit failed on an overbroad all-commit-path comparison: implementation commits also contain owned evidence. Original source/partial output/failure are preserved in source-audit. The fresh corrected audit explicitly compares the production subset and retains all other paths. A read-only CSV inspection hit Python's131072-character field limit; the full current reader raises its own CSV limit and preserves all fields. Neither error is a service pass or a rewritten result. All historical Stage1–3 rejections, repairs and shared-index attribution remain unchanged.

Four adopted decisions remain explicit: exact historical IANA instant/original wall with nearest minute serialization and immutable old seconds-offset strings; immutable original successful receipt/body meaning; exact numeric values with genuinely receipt-scoped old comparison; visible exact semantic numeric controls with native-type judging ambiguity. Older bootstrap revision1/policy0/empty prior history/private counter0 remains source-faithful. Finite observations prove no arbitrary workload guarantee or full accessibility certification. Saved private tokens/raw exports remain in memory; later scoped saved-JSON audit excludes source/log/handoff/peer/room-export text.

Configured harness/model Codex/gpt-6.1-sol; actual override/effort/tokens/catalog estimate/billed spend **unknown**. Timings are scoped per-command/protocol; whole-factory elapsed remains coordinator-owned. This document does not embed a circular self-seal; final room report supplies the exact owned evidence revision after inspection. Public release, genuine room export, operator README/FACTORY and submission remain operator-controlled. A repaired candidate requires a complete new acknowledged execution package and fresh independent review.
'''
 (H/'VERDICT.md').write_text(report);(H/'executed-aggregation-source.py').write_bytes(Path(__file__).read_bytes())
 print(json.dumps(dict(verdict='reject',normative=len(normative),counts=dict(counts),diagnostics=22,totals=totals)))
if __name__=='__main__':main()
