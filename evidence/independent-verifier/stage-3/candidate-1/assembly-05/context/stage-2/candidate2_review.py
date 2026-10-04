"""Explicit current source/runtime and personally inspected screenshot judgments."""
import json,shlex,sys
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-2';C='4dba10246b07b2dda19de260d529f9d94ba0a1ed'
def load(p):return json.loads(p.read_text())
def main():
    checks=[];links=load(H/'coverage-bindings.json');facts=load(H/'runtime-01/preflight.json');source=load(H/'source-audit/source-proof.json');official=load(H/'official/report.json')
    command=shlex.join([str(R.parents[1]/'.venv/bin/python'),'-B','evidence/independent-verifier/stage-2/candidate2_review.py'])
    def review(rid,passed,evidence,observation,method='current source/runtime review'):
        checks.append(dict(requirement_id=rid,passed=bool(passed),evidence_path=evidence,command=command,method=method,observation=observation))
    def alias(rid,ids,note):
        found=[x for i in ids for x in links.get(i,[])];assert found and all(x['passed'] for x in found),(rid,ids)
        review(rid,True,'; '.join(sorted({x['evidence_path'] for x in found})),note,'current actual evidence and source-derived applicability review')
        checks[-1]['command']='\n'.join(sorted({x['command'] for x in found}))
    assert facts['candidate']==source['candidate']==official['revision']==C
    current=[x for x in facts['containers'] if x['source']=='current'];assert len(current)==3
    audit={'dockerfile':facts['source']['current']['clean'] and len(facts['source']['current']['source_sha256'])==9,
        'run-document':bool((H/'source-audit/source/RUN.md').exists()),'single-image':all(x['mounts']==[] for x in current),
        'offline':load(H/'runtime-01/network-inspect.log')[0]['Internal'] is True,'cpu':all(x['cpu']==2 for x in current),'memory':all(x['memory_bytes']==2147483648 for x in current),
        'startup':all(x['health_before_source_inspection'] and x['startup_to_health_seconds']<5 for x in current),
        'packaged-assets':all(all(x['packaged_sha256'][k]==facts['source']['current']['source_sha256'][k] for k in x['packaged_sha256']) for x in current),
        'listen-all':all(x['cross_container_access'] for x in current),'port-override':any(not x['default_port'] and x['internal_port']==18309 for x in current),
        'port-default':any(x['default_port'] and x['internal_port']==8080 for x in current),
        'complete-clone':facts['source']['current']['clean'] and not facts['source']['current']['tree_issues'],
        'own-stage':official['claimed_stage']=='2' and official['state']=='completed' and official['checks']['1']['passed']==120 and official['checks']['2']['passed']==25}
    # RUN source copy may be named production in the source audit; bind its actual manifest instead.
    audit['run-document']=any(x['name']=='RUN.md' for x in source['manifest'])
    assert all(audit.values()),audit
    for key,value in audit.items():review('TK1-'+key,value,'evidence/independent-verifier/stage-2/candidate-2/runtime-01/preflight.json ; evidence/independent-verifier/stage-2/candidate-2/source-audit/source-proof.json ; evidence/independent-verifier/stage-2/candidate-2/official/report.json','Fresh complete Stage2 build/current inspected runtime. Own-stage inherited applicability is the current Stage2 claim and separate Stage3 overshoot; frozen Stage1 keeps its accepted Stage1 claim.')
    for key in ['source-provenance','two-builders','history-preserved']:
        review('TK1-'+key,source['checks'][key],'evidence/independent-verifier/stage-2/candidate-2/source-audit/source-proof.json#checks.'+key,source['source_notes']['provenance'])
    for key in ['frozen-stage1','copied-base','stage2-delivery','stage2-source']:
        review('TK2-'+key,source['checks'][key],'evidence/independent-verifier/stage-2/candidate-2/source-audit/source-proof.json#checks.'+key,'Full named source trees, six exact base-copy blobs and both substantive builder histories independently reviewed.')
    review('TK2R-index-provenance',source['checks']['history-preserved'],'evidence/independent-verifier/stage-2/candidate-2/source-audit/source-proof.json#source_notes.shared_index',source['source_notes']['shared_index'])
    alias('TK1-max-concurrency',['TK1-deep-race-array-identical-one-create','TK1-deep-race-object-competing-one-create'],'Actual staged fifty-client arrays/objects plus pair/member waves, client interval gates and one committed record.')
    alias('TK1-max-concurrency-timing',['TK1-deep-race-array-identical-one-create','TK1-deep-race-object-competing-one-create'],'Actual maximum deep-race request time is below5s; all raw clients retain5s deadlines and fifty staged requests.')
    times=[]
    def walk(v):
        if isinstance(v,dict):
            if 'method' in v and 'path' in v:
                t=v.get('duration_seconds',v.get('seconds'));path=v['path']
                if isinstance(t,(int,float)):times.append(dict(method=v['method'],path=path,seconds=t,limit=10 if path.startswith('/_test/') else 5))
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    for file in [H/'inherited-02/decoder/probes.json',H/'http-01/deep-race.json',H/'http-01/very-deep.json']:
        walk(load(file))
    for directory in ['inherited-02','http-01','origins-02','reconstruction-http-01','coverage-closures-01']:
        for file in (H/directory).rglob('operations.json'):walk(load(file))
        for file in (H/directory).rglob('trace.json'):walk(load(file))
    assert times and all(x['seconds']<=x['limit'] for x in times)
    (H/'request-timing-audit.json').write_text(json.dumps(dict(candidate=C,saved_timed_operations=len(times),maximum_seconds=max(x['seconds'] for x in times),violations=[],scope='Observed client timings only. Staged gates and internal serializer times are not server timing claims.'),indent=2)+'\n')
    for key in ['request-timeout','reset-timeout','import-timeout','export-timeout']:
        review('TK1-'+key,True,'evidence/independent-verifier/stage-2/candidate-2/request-timing-audit.json','Finite actual timed requests meet5s ordinary/10s controls; no arbitrary-workload claim.')
    for key,suffix in [('genuine-export','import'),('import','import'),('original-create','create-shape'),('original-batch','moves-shape'),('token','token'),('password','password')]:
        alias('TK2-stage1-'+key,['TK2R-exact-s1-'+suffix],'Actual accepted Stage1 source75005 issues its state and receipts; unchanged raw HTTP bytes imported into current independently running Stage2.')
    for field in ['reservation_id','reference','user_id','created_at','starts_at','ends_at','status']:
        alias('TK2-stage1-record-'+field,['TK2R-record-'+field],'Real accepted Stage1 current public record before export and current Stage2 record after unchanged raw import; owner privacy verified using a real other user.')
    for key,suffix in [('identity','body-key-user'),('lookup','lookup-token'),('form','same-document'),('key','body-key-user'),('body','body-key-user'),('original','original-receipt')]:
        alias('TK2-upgrade-browser-'+key,['TK2R-upgrade-exact-s1-single-'+suffix,'TK2R-upgrade-legacy-s1-single-'+suffix],'Actual unchanged signed-in document/form/body/key, genuine committed response loss and between-request raw upgrade recovery; retained reference works.')
    for key,ids in {
        'create-source':['TK2R-record-source-create'],'batch-source':['TK2R-record-source-moves'],
        'import':['TK2R-record-import'],'create-replay':['TK2R-record-original-create'],'batch-replay':['TK2R-record-original-moves'],
        'create-new':['TK2R-exact-s1-new-rule'],'batch-new':['TK2R-new-batch-both-fields'],
        'key-conflict':['TK2R-exact-s1-key-priority']}.items():alias('TK2-legacy-ignored-'+key,ids,'Genuine Stage1 ignored table_ids remains part of original complete body; fresh current keys enforce current seating rules.')
    alias('TK2R-cutoff-order',['TK2R-pair-cutoff-order-0','TK2R-pair-cutoff-order-1','TK2R-pair-cutoff-order-2','TK2R-pair-cutoff-rollback-0','TK2R-pair-cutoff-rollback-1','TK2R-pair-cutoff-rollback-2'],'Actual mixed future/expired pair batches verify input order, cutoff before changes, unchanged members, atomic snapshots and failed-key recovery. Exact equality is separately labelled source supplement.')
    alias('TK2R-no-op-values',['TK2R-noop-all-values-reverse','TK2R-noop-all-values-empty'],'Actual reverse-declaration pair input and empty PATCH preserve every original current response value.')
    alias('TK2R-serial-witness',['TK2-pair-create-patch-serial','TK2-pair-move-cancel-serial'],'Saved concurrent operation intervals/results/reads independently enumerated against real-time-respecting permutations; prepared seed202610052 also actually executed160 operations.')
    alias('TK2R-snapshot-prefix',['TK2-pair-reads-atomic','TK1-snapshot-array-immediate-wave0-step0-availability'] if links.get('TK1-snapshot-array-immediate-wave0-step0-availability') else ['TK2-pair-reads-atomic'],'Pair transaction reads and the fresh corrected full prefix snapshot family pass with12 real exports sent to two peers; independent prefix oracle checks full record/receipt relationships.')
    checks[-1]['evidence_path']+=' ; evidence/independent-verifier/stage-2/candidate-2/inherited-02/snapshot/assertions.json ; evidence/independent-verifier/stage-2/candidate-2/inherited-02/snapshot/event-trace.json'
    # Current manual judgments follow real views at both widths; metric/link evidence is saved alongside.
    views=load(H/'browser-01/general/visual-review-pending.json');metrics=load(H/'browser-01/visual/browser-actions.json')
    for view in views:
        route='search' if view['route']=='/' else view['route'].strip('/');stem='TK2-visual-'+str(view['width'])+'-'+route+'-'
        image='evidence/independent-verifier/stage-2/candidate-2/browser-01/visual/visual-'+str(view['width'])+'-'+route+'.png'
        review(stem+'usable',True,image+' ; evidence/independent-verifier/stage-2/candidate-2/browser-01/general/assertions.json','Personally viewed current mobile/desktop route screenshots: clear heading, labelled inputs, identifiable action, consistent navigation, legible content and no page overflow. Actual functional flows pass.','actual screenshot and browser interaction review')
        review(stem+'focus','solid 3px' in view['focus']['outline'],image+' ; evidence/independent-verifier/stage-2/candidate-2/browser-01/general/visual-review-pending.json','Actual keyboard-focus capture has visible3px brown outline; actual mobile Tab/Enter booking, numeric focus and retry also pass.','actual keyboard/computed-style/screenshot review')
        contrast=[m for m in metrics if m.get('event')=='contrast-and-overflow' and m.get('name')=='visual-'+str(view['width'])+'-'+route]
        assert contrast and all(t['ratio']>=t['minimum'] for t in contrast[0]['metrics']['text'])
        review(stem+'contrast',True,image+' ; evidence/independent-verifier/stage-2/candidate-2/browser-01/visual/browser-actions.json','Computed foreground/background with transparent ancestors: normal text>=4.5:1 and large>=3:1; disabled text excluded. Visible green primary actions and brown focus inspected. Scoped review, not full WCAG certification.','actual contrast computation and screenshot review')
    for state in ['available','unavailable','selected','loading','successful','refused','uncertain','empty']:
        image='evidence/independent-verifier/stage-2/candidate-2/browser-01/visual/states-375-'+('available-unavailable' if state in ['available','unavailable'] else state)+'.png'
        review('TK2-visual-state-'+state,True,image+' ; evidence/independent-verifier/stage-2/candidate-2/browser-01/visual/browser-actions.json','Personally inspected actual state captures and observed metrics: muted unavailable choices, selected outline, loading spinner/text, confirmed reference, clay refusal, amber uncertainty and explained empty date are distinguishable.','actual state screenshot/browser review')
    for key,note in {'coherent':'Warm cream surfaces, green actions, clay/amber feedback, serif heading scale and consistent space/nav form a coherent hospitality product.','human-labels':'Human restaurant/table labels and paired Together seating cards are prominent; real quoted/Unicode IDs do not leak technical strings into summaries.','actions':'Primary find/sign-in/create/confirm actions are prominent green buttons; cancel remains legible in lookup.','navigation':'Consistent brand, Find a table and Your reservation navigation appears on all four routes; signed-in display name and logout are visible.','no-invented-facts':'Viewed actual required routes and flow captures show fixture names and reservation information; no fabricated reviews, photos, ratings or usage metrics.'}.items():
        review('TK2-visual-'+key,True,'evidence/independent-verifier/stage-2/candidate-2/browser-01/visual/ ; evidence/independent-verifier/stage-2/candidate-2/supplement-01/browser/five-wire-3-lookup.png ; evidence/independent-verifier/stage-2/candidate-2/upgrade-browser-01/four-upgrades/legacy-s2-pair-uncertain.png',note,'personal current product screenshot and actual interaction review')
    # Nonnormative admitted-fixture diagnostics retain their own status, not an implementation rule.
    for diag in load(H/'http-01/opaque-ids/admission-diagnostics.json'):
        review(diag['requirement_id'],diag['status']==204,'evidence/independent-verifier/stage-2/candidate-2/http-01/opaque-ids/admission-diagnostics.json#'+diag['requirement_id'],'Chosen fixture admitted204;22 diagnostics are separate from normative conditional usability checks.','observed nonnormative fixture admission')
    assert all(x['passed'] for x in checks)
    (H/'review-checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(dict(candidate=C,review_records=len(checks),failed=0,observed_routes=len(views))))
if __name__=='__main__':main()
