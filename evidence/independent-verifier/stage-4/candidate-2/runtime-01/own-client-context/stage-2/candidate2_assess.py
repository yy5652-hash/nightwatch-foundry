"""Final named verdict from complete current proof and metadata; no product mutation."""
import csv,datetime as dt,json,shlex,subprocess,sys
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent;H=HERE/'candidate-2';R=HERE.parents[2];W=R.parents[1]
sys.path.insert(0,str(HERE.parent/'stage-1'))
from coverage_metadata import validate
def load(p):return json.loads(p.read_text())
def main():
    C='4dba10246b07b2dda19de260d529f9d94ba0a1ed';intake=load(H/'intake.json');facts=load(H/'runtime-01/preflight.json');runtime=load(H/'final-runtime-proof.json');official=load(H/'official/report.json');source=load(H/'source-audit/source-proof.json');bindings=load(H/'coverage-bindings.json')
    assert intake['complete_package'] and intake['end_received'] and intake['acknowledged_before_execution'] and all(x['candidate']==C for x in [facts,runtime,source]) and official['revision']==C
    rows=list(csv.DictReader((H/'coverage-draft.csv').open()));metadata=validate(rows)
    missing=[]
    for rid,links in bindings.items():
        assert links and all(x['passed'] for x in links)
        for item in links:
            for path in item['evidence_path'].split(';'):
                if not (R/path.strip().split('#')[0]).exists():missing.append((rid,path))
    assert not missing
    norm=[r for r in rows if r['normative']=='True'];assert all(r['candidate_full_revision']==C and r['verdict']=='verified' for r in rows)
    assert len(norm)==6549 and len(rows)-len(norm)==22
    metadata.update(candidate=C,normative_rows=len(norm),diagnostic_rows=22,missing_owner_fields=0,missing_evidence_files=0,all_current_rows_verified=True)
    (H/'metadata-self-check.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (H/'coverage.csv').write_bytes((H/'coverage-draft.csv').read_bytes())
    commands=[]
    for argv,name in [(['docker','ps','-a','--filter','name=independent-verifier','--format','{{.Names}}'],'final-own-inventory'),(['git','diff',C,'--','stage-1','stage-2'],'final-graded-diff')]:
        result=subprocess.run(argv,cwd=R,capture_output=True,text=True);(H/(name+'.log')).write_text(result.stdout+result.stderr);assert result.returncode==0 and not result.stdout.strip();commands.append(dict(argv=argv,cwd=str(R),returncode=result.returncode,log=name+'.log'))
    (H/'final-seal-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    s1=load(H/'official/stage-1.counts.json');s2=load(H/'official/stage-2.counts.json');s3=load(H/'official/stage-3.counts.json')
    assert official['state']=='completed' and official['claimed_stage']=='2' and official['pytest_args']==[] and official['mode']=='isolated'
    for data,n in [(s1,120),(s2,25)]:assert data['collected']==data['passed']==n and not any(data[k] for k in ['failed','errors','skipped','deselected','xfailed'])
    assert s3['collected']==7 and s3['failed']==1 and s3['passed']==0
    runs=load(H/'completed-runs.json');pure=[r for r in runs if r['name'].split('/')[0] in ['http-01','inherited-02','origins-02','reconstruction-http-01','supplement-oracle-02'] or r['name']=='coverage-closures-01/coverage'];browser=[r for r in runs if r not in pure]
    partial=[]
    for path in ['http-01/baseline/summary.json','http-01/snapshot/summary.json','http-01/decoder/probes.json','reconstruction-http-01/origins/summary.json']:
        data=load(H/path);partial.append(dict(path=path,requests=data['requests'],assertions=data['assertions'],raw_failed_expectations=data.get('failures',data.get('failed_assertions')),classification='own obsolete current-view or source-fixture expectation; no product defect established; corrected complete scope rerun'))
    partial.append(dict(path='supplement-01/oracle',requests=len(load(H/'supplement-01/oracle/trace.json')),assertions=len(load(H/'supplement-01/oracle/assertions.json')),raw_failed_expectations=0,classification='own evidence-writer TypeError after checks; completed corrected new run bound instead'))
    cleanup=runtime['cleanup']+load(H/'calendar-browser-01/cleanup.json');assert len(cleanup)==9 and all(x['returncode']==0 for x in cleanup)
    now=dt.datetime.now(dt.timezone.utc);started=dt.datetime.fromisoformat(intake['review_started_at']);audit=load(H/'artifact-audit.json');assert not audit['unclassified_private_payload_findings']
    summary=dict(candidate=C,stage_2_tree=intake['stage_2_tree'],verdict='accept',highest_independently_accepted_stage=2,accepted_stage1=intake['accepted_stage1'],stage1_verdict=intake['stage1_verdict'],systems_implementation=intake['systems_implementation'],interface_implementation=intake['interface_implementation'],normative_rows=len(norm),verified=len(norm),failed=0,unverified=0,diagnostic_rows=22,metadata=metadata,
        completed_http_only_runs=len(pure),completed_http_only_requests=sum(r['requests'] for r in pure),completed_http_only_assertions=sum(r['assertions'] for r in pure),completed_http_only_failed_assertions=0,
        completed_browser_runs=len(browser),completed_browser_assertions=sum(r['assertions'] for r in browser),completed_browser_direct_operations=sum(r['requests'] or (r['counts'] or {}).get('http',(r['counts'] or {}).get('direct',0)) for r in browser),completed_browser_originated_requests=sum(r['browser_requests'] or (r['counts'] or {}).get('browser',0) for r in browser),four_origin_upgrade_forwardings=24,forwarding_scope='Four-origin upgrade protocol counter only; forwarding transports browser requests and is not added to a fabricated unique-request total.',screenshots=len(list(H.rglob('*.png'))),
        prior_own_failed_or_writer_runs=partial,prior_raw_failed_expectations=sum(r['raw_failed_expectations'] for r in partial),current_service_requirement_failures=0,
        official_stage1_current_service_regression=s1,official_stage2=s2,official_stage3_overshoot=dict(**s3,not_executed=6),official_wall_seconds=load(H/'official-command.json')['wall_seconds'],official_command=load(H/'official-command.json')['argv'],
        clean_exact_clones=runtime['clones'],packaged_source_matches=True,default_readiness_seconds=next(x['startup_to_health_seconds'] for x in facts['containers'] if x['role']=='peer'),override_readiness_seconds=next(x['startup_to_health_seconds'] for x in facts['containers'] if x['role']=='target'),all_health_before_source_inspection=True,service_image=facts['source']['current']['image_id'],cleanup_commands=len(cleanup),all_cleanup_zero=True,own_namespace_empty=True,source_hashes=facts['source']['current']['source_sha256'],max_observed_timed_request_seconds=load(H/'request-timing-audit.json')['maximum_seconds'],max_decoder_request_bytes=load(H/'inherited-02/decoder/probes.json')['max_request_bytes'],
        review_started_at=started.isoformat(),review_aggregated_at=now.isoformat(),review_to_aggregation_seconds=(now-started).total_seconds(),elapsed_scope='Private current-review activation to aggregation; whole factory interval is coordinator-owned.',
        harness='Codex',configured_model='gpt-6.1-sol',actual_model='unknown',reasoning_effort='unknown',token_usage='unknown',catalog_estimated_cost='unknown',billed_spend='unknown',
        limits=['Adopted historical exact-instant/nearest representable minute-offset serialization preserves original wall fields; genuine old offset-seconds strings stay immutable. Incompatible literal offset grammars are not simultaneously claimed.','Exact whole-value body numbers and genuine receipt-scoped legacy profiles are adopted interpretations; numeric profile does not determine original public shape.','Visible labelled semantic spinbutton controls use exact decimal storage, numeric mode/buttons/keyboard with minimum1; this interpretation does not invent a native HTML type obligation.','Finite depths/payloads/exponents/concurrency samples do not prove arbitrary-workload performance; cached builds and retained-image supplements are labelled.','Exact instantaneous cutoff equality is a labelled source supplement; no clock-controlled HTTP API or internal serializer timing is claimed. Scoped product/contrast review is not complete WCAG certification.','One inactive own test-session capture was fingerprinted before commit after three observed401 checks. Scoped saved-JSON audit excludes source/log text, peer evidence and genuine room export.','No hidden judging score, genuine room export, public release or submission is claimed; no Stage3/4 extension authorized here.'])
    (H/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # Append one new durable ledger event; old verdicts and failed observations remain unchanged.
    ledger=R/'evidence/independent-verifier/ledger.jsonl'
    with ledger.open('a') as f:f.write(json.dumps(dict(utc=now.isoformat(),event='stage2-candidate2-independent-accept',candidate=C,stage_tree=intake['stage_2_tree'],highest_consecutive_accepted_stage=2,normative_rows=len(norm),verified=len(norm),failed=0,unverified=0,http_only_requests=summary['completed_http_only_requests'],http_only_assertions=summary['completed_http_only_assertions'],browser_assertions=summary['completed_browser_assertions'],browser_direct=summary['completed_browser_direct_operations'],browser_requests=summary['completed_browser_originated_requests'],official_stage1=s1,official_stage2=s2,official_stage3_overshoot=summary['official_stage3_overshoot'],cleanup_commands=9,review_interval_seconds=summary['review_to_aggregation_seconds'],verdict_path=str((H/'VERDICT.md').relative_to(R)),configured_model='gpt-6.1-sol',actual_model_effort_tokens_cost='unknown',preserved_raw_verifier_expectation_failures=summary['prior_raw_failed_expectations'],private_capture_correction=str((H/'PRIVATE_CAPTURE_CORRECTION.json').relative_to(R)),risks=summary['limits']))+'\n')
    print(json.dumps({k:summary[k] for k in ['candidate','verdict','highest_independently_accepted_stage','normative_rows','completed_http_only_requests','completed_http_only_assertions','completed_browser_assertions','completed_browser_direct_operations','completed_browser_originated_requests','cleanup_commands','review_to_aggregation_seconds']}))
if __name__=='__main__':main()
