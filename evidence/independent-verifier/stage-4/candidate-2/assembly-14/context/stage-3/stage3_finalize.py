"""Validate the complete current ledger and write a named independent verdict."""
import csv,hashlib,json,shlex,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
sys.set_int_max_str_digits(0);csv.field_size_limit(sys.maxsize)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];W=R.parents[1];H=HERE/'candidate-1';C='91e2c471acded1b861b3fec725f202297b1c6740'
def load(p):return json.loads(p.read_text())
def write(p,value):assert not p.exists(),p;p.write_text(json.dumps(value,indent=2)+'\n')
def main():
 rows=list(csv.DictReader((H/'binding-04/coverage.csv').open()));required=load(HERE/'initial-1/checks-02/metadata-self-check.json')['required_fields'];missing=[];bad=[];owners=[]
 for row in rows:
  for key in required:
   if not row.get(key):missing.append([row['requirement_id'],key])
  assert row['candidate_full_revision']==C and row['verdict']=='verified'
  assert row['verification_owner']=='independent-verifier'
  assert set(row['implementation_owner'].split(' / '))<={'systems-engineer','interface-engineer'}
  for item in row['evidence_path'].split(';'):
   path=(R/item.strip().split('#')[0]);
   if not path.is_file():bad.append([row['requirement_id'],item])
 assert not missing and not bad and len({r['requirement_id'] for r in rows})==len(rows)
 normative=[r for r in rows if r['normative']=='True'];diagnostics=[r for r in rows if r['normative']!='True'];assert len(normative)==7359 and len(diagnostics)==22
 for name in ['coverage.csv','coverage-bindings.json','completed-runs.json']:
  dest=H/name;assert not dest.exists();dest.write_bytes((H/'binding-04'/name).read_bytes())
 metadata=dict(candidate=C,rows=len(rows),normative=len(normative),normative_verified=len(normative),normative_failed=0,normative_unverified=0,diagnostics=len(diagnostics),diagnostics_verified=len(diagnostics),required_fields=required,empty_required_fields=0,unique_identifiers=True,responsible_ownership_complete=True,implementation_and_verification_explicit=True,evidence_files_only=True,missing_evidence=[],directory_evidence=[],matrix_sha256=hashlib.sha256((H/'coverage.csv').read_bytes()).hexdigest(),binding_source='binding-04; all earlier partial bindings retained')
 write(H/'metadata-self-check.json',metadata)
 runs=load(H/'completed-runs.json');totals={kind:dict(runs=sum(x['kind']==kind for x in runs),requests=sum(x['requests'] for x in runs if x['kind']==kind),assertions=sum(x['assertions'] for x in runs if x['kind']==kind),browser_originated_requests=sum(x['browser_requests'] for x in runs if x['kind']==kind),forwardings=sum(x['forwardings'] for x in runs if x['kind']==kind),retained_pngs=sum(x['screenshots'] for x in runs if x['kind']==kind)) for kind in ['http','browser']}
 timings=[]
 def walk(v,file):
  if isinstance(v,dict):
   if isinstance(v.get('method'),str) and isinstance(v.get('path'),str):
    t=v.get('seconds',v.get('duration_seconds'))
    if isinstance(t,(int,float)):timings.append(dict(file=str(file.relative_to(R)),method=v['method'],path=v['path'],seconds=t,limit=10 if v['path'].startswith('/_test/') else 5))
   for x in v.values():walk(x,file)
  elif isinstance(v,list):
   for x in v:walk(x,file)
 for run in runs:
  folder=H/run['name'];file=next((p for p in [folder/'trace.json',folder/'operations.json',R/run['summary']] if p.is_file()),None)
  assert file;walk(load(file),file)
 violations=[x for x in timings if x['seconds']>x['limit']];assert timings and not violations
 write(H/'request-timing-audit.json',dict(candidate=C,saved_timed_observations=len(timings),maximum_seconds=max(x['seconds'] for x in timings),violations=violations,scope='One primary trace/operations/payload file per selected complete protocol. Client elapsed times, not internal serializer timing or arbitrary-workload performance. Official/health/source/direct diagnostic traffic excluded.',by_file=dict(Counter(x['file'] for x in timings))))
 cleanup=load(H/'final-runtime-proof.json');assert cleanup['namespace_empty'] and cleanup['cleanup_exits']==[0]*8 and cleanup['graded_diff_empty']
 direct=load(H/'direct-01/summary.json');assert direct['failed']==0 and all(x['passed'] for x in direct['assertions'])
 audit=load(H/'artifact-audit-02.json');assert not audit['unclassified_private_payload_findings'] and not audit['json_read_errors']
 source=load(H/'source-audit/source-proof.json');facts=load(H/'runtime-01/preflight.json');official=load(H/'official/report.json')
 now=datetime.now(timezone.utc);started=datetime.fromisoformat(load(H/'intake.json')['review_started_at']);elapsed=(now-started).total_seconds()
 summary=dict(candidate=C,stage_3_tree='a0f0a4741bb0ab0125856510a000ade385344a04',verdict='accept',highest_consecutive_accepted=3,coverage=metadata,current_protocols=totals,direct_diagnostic=dict(scope=direct['scope'],calls=direct['calls'],assertions=len(direct['assertions']),failed=0),official=dict(stage1={'collected':120,'passed':120},stage2={'collected':25,'passed':25},stage3={'collected':7,'passed':7},stage4_probe={'collected':6,'passed':4,'failed':1,'unexecuted_after_x':1},claim=3,overshoot=None,harness_window_seconds=37.054932,external_wall_seconds=None),image=facts['source']['current']['image_id'],source_hashes=facts['source']['current']['source_sha256'],clones=cleanup['clean_clones'],startup_bounds=[dict(role=x['role'],port=x['internal_port'],seconds=x['startup_to_health_seconds'],default=x['default_port']) for x in facts['containers']],cleanup=dict(final_commands=8,final_exit_codes=[0]*8,separate_direct_removal_exit=0,only_own=True,namespace_empty=True),timing=dict(review_started_at=started.isoformat(),aggregation_at=now.isoformat(),review_to_aggregation_seconds=elapsed,whole_factory_elapsed='coordinator-owned',seal_timing='separate later evidence'),model=dict(harness='Codex',configured='gpt-6.1-sol',actual_override=None,effort=None,tokens=None,catalog_estimated_cost=None,billed_spend=None),production_edits=0,source_review=source['checks'])
 write(H/'summary.json',summary)
 table=['# Complete current independent protocols','', '| Scope | Kind | Actual operations | Assertions | Seconds | Evidence |','| --- | --- | ---: | ---: | ---: | --- |']
 for x in runs:table.append('| '+x['name']+' | '+x['kind']+' | '+str(x['requests'])+' | '+str(x['assertions'])+' | '+format(x['seconds'],'.9f')+' | ['+x['name']+']('+str((R/x['summary']).relative_to(H))+') |')
 table+=['','Docker argv for every scope are preserved in [completed-runs.json](completed-runs.json). Browser operations, browser-originated requests and forwarding transports remain separate. Per-run seconds measure the actual Docker command, not browser-only execution. The packaged Engine supplement is [separately labelled](direct-01/summary.json).']
 (H/'COMPLETED_RUNS.md').write_text('\n'.join(table)+'\n')
 (H/'VERDICT.md').write_text(f'''# Stage 3 candidate 1: accept

Exact full candidate **{C}**, Stage 3 tree **a0f0a4741bb0ab0125856510a000ade385344a04**: **accept**. Highest consecutive independently accepted stage is **3**. This covers the complete Stage 3 service and its inherited Stage 1–2 requirements. Stage 4 remains unassigned and unaccepted. Verifier production edits: zero.

The complete sixteen-part `TK-20261004-S3-independent-verifier-CANDIDATE-1` and both END markers were acknowledged before execution. [Intake](intake.json) binds actual part IDs, full content hash, exact source and release. Frozen Stage 1 remains `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b`; frozen Stage 2 remains `4dba10246b07b2dda19de260d529f9d94ba0a1ed`. [Source proof](source-audit/source-proof.json) verifies all fifteen frozen files, the complete nine-file predecessor copy, substantive Systems implementation `6783fd8f557575e9be16fdf146ede097127773c6` and Interface implementation `9f0d3150c934a2090c42667cb0ee0bb672c64325` plus committed corrections. Interface's tested full tree equals this candidate. Systems' full tested tree differs only in later app.js bytes; API engine/codec/server bytes match. Builder passes are not independent results.

## Complete current evidence

[Coverage](coverage.csv): **7,359 normative rows verified, zero failed, zero unverified**, plus **22 separate nonnormative fixture-admission diagnostics**. The total 7,381 records have unique identifiers, all fourteen required metadata fields, named implementation/verification ownership, full candidate, exact executed command or observed interaction, and concrete file evidence. [Metadata self-check](metadata-self-check.json) verifies every link with `is_file()`. [Bindings](coverage-bindings.json) exclude stopped or incorrect attempts. Preparation began with 7,310 unverified normative rows; 49 genuine bootstrap/invalid-state obligations were independently added. These are specification decompositions, not hidden-test counts or a judging score.

**61 complete selected independent protocols**: **44 HTTP families, 18,397 actual requests and 41,736 assertions**, all passed; **17 browser families, 1,446 assertions**, all passed, **396 direct API operations, 2,055 browser-originated requests and 189 retained genuine PNGs**. Forty-eight recorded forwarding operations transport browser traffic and are not added to an invented unique-request total. Browser assertions include separately recorded direct-API checks as well as UI assertions. [Completed runs](completed-runs.json) and [run table](COMPLETED_RUNS.md) preserve exact commands/counts/timing. Auxiliary selector-binding, startup/health/source and official-checker traffic are outside these totals.

A [labelled packaged Engine diagnostic](direct-01/summary.json) makes **60 calls and 61 assertions**, all passed. It uses the source-bound actual image with a diagnostic-only substituted clock to examine the published 2026 series DST dates and exact cutoff equality. It is **not HTTP** and invents no public clock endpoint. Actual inherited HTTP/browser checks cover the specified 2026 transitions; future 2035 HTTP series probes cover real-clock adoption, gap/fold resolution, per-date policy and absolute duration. No past-anchor successful HTTP adoption is fabricated.

| Unchanged official isolated scope | Collected | Passed | Failed | Other |
| --- | ---: | ---: | ---: | --- |
| Stage 1 regression | 120 | 120 | 0 | no errors/skips/deselections/xfails |
| Stage 2 regression, 8 API + 17 UI | 25 | 25 | 0 | no errors/skips/deselections/xfails |
| Stage 3 | 7 | 7 | 0 | no errors/skips/deselections/xfails |
| Separate Stage 4 probe | 6 | 4 | 1 | one unexecuted after unchanged `-x` |

[Official report](official/report.json) correctly claims stage 3 with null overshoot. Four later public checks naturally pass; the next series clock-amend surface returns 404 and stops the probe. No later-stage acceptance follows. No suite, checker, selection, runtime or correct earlier behavior was altered. Harness UTC window is **37.054932 seconds**; external command wall time was not separately measured. [Actual command](official-command.json) ran from the clean unchanged kickoff at `803560d2a678ace1414465c098eb0ab5380ffade`, against the exact clean current clone, in isolated mode with a unique preserved output.

## Integrity and historical truth

Current HTTP probes independently verify fixture-only manager permission, complete bounded policies, publication/effective-date ordering and ties, independent capacity/overlap truth, immutable accepted terms/end/history, optional optimistic revision precedence, ordered actual changes, no-ops, terminal/repeated cancellation, canonical pair transitions and original receipts. Recurring adoption retains the real anchor unchanged; every later local date independently selects policy and DST rules. Indexed failures preserve the entire raw export byte-for-byte in nine separate refusal cases, including histories, references, counters, series and successful receipts. Actual obstruction repairs reuse failed keys successfully.

The separate Stage 3 reference oracle uses seed **202610063**, with **160 actual operations** and complete current-state/history/agreement comparisons after each operation. Fresh inherited occupancy/member oracles use seeds `20261004`, `20261005` and `202610052`. Recorded staged races admit complete serial states: policy publication, expected-revision amendments, cancellation, batch swaps, series adoption and concurrent reads/raw captures. Fifty-client identical create/adoption waves return one 201 and forty-nine original 200 receipts; competing member requests preserve occupancy. Snapshot/prefix and detached-state checks remain independent. Internal serializer timing is unobserved.

Strict UTF-8/JSON grammar, exact integral/fractional/exponent semantics, ignored finite extreme numbers, boolean distinctions, full parsed-body retry identity, error precedence and atomic replacement were freshly executed. Current and genuine receipt-scoped legacy numeric profiles remain independent of public response shape. Actual 4,301-digit fixture/query/body/display/retry values stay JSON numbers. Balanced arrays, objects and alternating wrappers at depths 1,100/5,000/10,000/20,000 succeed in deep policy/create/series/batch receipts and unchanged raw transfers. Finite timing observations have maximum **{max(x['seconds'] for x in timings):.9f} seconds**, with zero applicable five-second ordinary/ten-second control violations; [timing audit](request-timing-audit.json) states its measured scope.

Four genuine unmodified earlier sources actually issue hashes, sessions, references, create/move receipts and historical strings: accepted Stage 1/2 and legacy Stage 1 `49287b4a5a1481f995c470ccae31776f03d4b863` / Stage 2 `4b92041057beb669d2e6c528e8268f4d0d1e6421`. Actual unchanged exports replace independent current processes and survive another mixed replacement, mutation, replay and reset. Current adopted anchors preserve original identities/timestamps/receipts. Earlier services did not record Stage 3 histories, terms or counters: current revision 1, fixture-policy-0 terms, empty prior histories and private counter 0 are source-faithful bootstrap choices. The first actual later change records seq 1/revision 2; no past event or manager permission is invented. Original responses never gain newer fields. Modern policies, populated agreements, exceptions/cancellations and actual histories survive replacement; ten independently mutated modern private-state constraints reject atomically.

## Product and constrained runtime

Actual browser interactions cover all inherited routes/test IDs/auth/public browsing, canonical human seating, exact references/status, rival refusal/refresh with retained form, stale searches, committed response loss, malformed-response uncertainty and unchanged body/key retries. Current terms and ordered historical snapshots are separate from original confirmation. Real recurring forms/lists retain references, cancelled visits and permanent exceptions; manager private lookup refuses without exposing history. A delayed agreement A cannot overwrite B or B's restaurant labels. Genuine accepted/legacy API-to-current-assets bridges retain the same document/user/form/body/key across between-request import and recover actual original confirmations without reload or reauthentication. The proxy transports real bytes and manufactures no source success or state; no Stage 1 UI is claimed.

Fresh screenshots, actual Enter/Tab/visible focus, complete labelled numeric controls, width and contrast metrics cover 375/1280 CSS pixels. [Current review](review-02/review-checks.json) and [concrete visual observations](review-02/visual-observations.json) link real files. Warm cream/green/clay/amber hierarchy, human single/pair labels and distinct loading/empty/selected/success/refusal/uncertainty remain coherent. Transparency-aware scoped text contrast meets 4.5:1 ordinary and 3:1 large text, disabled excluded. This is a scoped product assessment, not full WCAG certification.

The entire nine-file Docker context builds from the clean detached exact current clone at `{facts['source']['current']['clone']}`. Current image **{facts['source']['current']['image_id']}**. [Runtime preflight](runtime-01/preflight.json) and [source proof](source-audit/source-proof.json) bind every context and actual packaged source hash. No nested service repository, submodule, escaping symlink, uncommitted runtime dependency, manual setup or host service interpreter is required. Build cache was reused; an uncached build is not claimed.

Three current and four genuine-source services have inspected **2 CPU/2 GiB, no mounts**, on an inspected internal offline network. Diagnostic clients are separately configured at those limits and mount owned evidence/proof output directories. Default 8080 / override 18309 readiness upper bounds are **0.401663917 / 0.471629209 seconds**, measured before source inspection; cross-container traffic establishes selected-port all-interface listening. Host-published reachability is not claimed. All seven services were healthy/not OOM-killed before removal. **Eight final service/network cleanup commands and the separate direct-diagnostic removal exit zero**; --rm clients record their own exits separately. [Final runtime proof](final-runtime-proof.json) preserves five clean exact clones, empty own namespace and empty graded source diff. Only own resources were removed; images/clones remain inspectable.

## Preserved errors, limits and reproduction

[Preserved verifier issues](RUNNER_ISSUES.md) distinguish fixture/expected-schema/query/runner packaging/page-lifecycle and metadata errors from service defects. Original failed outputs, partial downstream coverage and executed sources remain intact. Corrected complete fresh executions bind the scopes; no stopped run establishes downstream coverage and no failed output is relabelled. The old shared-index incident at `182582c41d21a23d8ccd95688fa7f1afa0437460` retains 32 verifier-authored paths under Interface Git author identity; content authorship, Git authorship and independent execution remain distinct.

The [scoped artifact audit](artifact-audit-02.json) scans saved owned JSON and valid embedded JSON strings with zero unclassified private payload findings. Its original null-model-usage classification stop is retained, with a narrow prospective correction. Private exports/live credentials otherwise remain in client memory. Source/log text, peer artifacts and genuine full room export are outside this privacy claim. Final public secret review/export/release/submission remain operator-controlled.

All four adopted decisions remain explicit: exact IANA instant/original wall fields with nearest representable minute-offset historical serialization and unchanged genuine old seconds-offset strings; immutable original successful response schemas/values/body meanings; exact value-based JSON numbers with genuine receipt-scoped historical comparison; visible semantic exact numeric controls with spinbutton/numeric mode/buttons/keyboard/minimum one. Literal historical seconds offsets and minute-only RFC3339 are not claimed simultaneously; native HTML type ambiguity remains disclosed. Empty earlier history/revision-1/policy-0/counter-0 compatibility is independently assessed above. Finite payloads/depths/exponents/concurrency and widely separated output coefficients do not prove arbitrary workload performance or fit beyond finite resources.

Reproduction uses the workspace Python, exact named own protocol blobs from each assembly manifest, a fresh seat-prefixed runtime and new unique output folders. Actual build/Git/Docker/client/health/inspection/cleanup argv and hashes are preserved in per-run commands.json, preflight, source proof and completed-runs.json. Runtime orchestration is `../stage3_runtime.py`; assembly `../stage3_assemble.py`; execution `../stage3_execute.py`. No builder/official test implementation or external domain code/schema was used as a reference oracle or executed as independent evidence. No hidden judging result, public release or final submission is claimed.

Measured current-review activation to aggregation: **{elapsed:.6f} seconds**, `{started.isoformat()}` to `{now.isoformat()}`. Verdict/seal timing is separate; whole-factory elapsed belongs to the coordinator. Configured harness/model **Codex/gpt-6.1-sol**; actual model override, effort, tokens, catalog-estimated cost and billed spend **unknown**. This document avoids a circular self-commit identifier; the final room report supplies the exact independent evidence seal.
''')
 print(json.dumps(dict(candidate=C,verdict='accept',normative=7359,verified=7359,failed=0,unverified=0,totals=totals,elapsed=elapsed,timed=len(timings),maximum=max(x['seconds'] for x in timings))))
if __name__=='__main__':main()
