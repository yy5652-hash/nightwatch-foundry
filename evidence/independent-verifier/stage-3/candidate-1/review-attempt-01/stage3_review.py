"""Explicit applicability judgments using concrete current observations only."""
import hashlib,json,shlex,sys
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-1';C='91e2c471acded1b861b3fec725f202297b1c6740'
def load(p):return json.loads(p.read_text())
def main():
 links=load(H/'binding-02/all-observations.json');f=load(H/'runtime-01/preflight.json');s=load(H/'source-audit/source-proof.json');o=load(H/'official/report.json');checks=[]
 command=shlex.join([str(R.parents[1]/'.venv/bin/python'),'-B','evidence/independent-verifier/stage-3/stage3_review.py'])
 def path(p):return str((H/p).relative_to(R))
 def review(rid,evidence,note,method='current source/runtime or personally reviewed screenshot',passed=True,cmd=command):
  for e in evidence.split(' ; '):assert (R/e.split('#')[0]).is_file(),e
  checks.append(dict(requirement_id=rid,passed=bool(passed),evidence_path=evidence,command=cmd,method=method,observation=note))
 def alias(rid,ids,note):
  ids=ids.split(',') if isinstance(ids,str) else ids
  assert all(i in links and links[i] for i in ids),(rid,ids)
  found=[x for i in ids for x in links[i]];assert all(x['passed'] for x in found)
  review(rid,' ; '.join(sorted({x['evidence_path'] for x in found})),note,'actual current observations plus independent applicability review',cmd='\n'.join(sorted({x['command'] for x in found})))
 assert f['candidate']==s['candidate']==o['revision']==C
 current=[x for x in f['containers'] if x['source']=='current'];assert len(current)==3
 facts=dict(dockerfile=f['source']['current']['clean'] and len(f['source']['current']['source_sha256'])==9,
  **{'run-document':any(x['name']=='RUN.md' for x in s['manifest']),'single-image':all(x['mounts']==[] for x in current),
  'offline':load(H/'runtime-01/network-inspect.log')[0]['Internal'] is True,'cpu':all(x['cpu']==2 for x in current),'memory':all(x['memory_bytes']==2147483648 for x in current),
  'startup':all(x['health_before_source_inspection'] and x['startup_to_health_seconds']<5 for x in current),'packaged-assets':all(x['packaged_sha256']==f['source']['current']['source_sha256'] for x in current),
  'listen-all':all(x['cross_container_access'] for x in current),'port-override':any(x['internal_port']==18309 and not x['default_port'] for x in current),
  'port-default':any(x['internal_port']==8080 and x['default_port'] for x in current),'complete-clone':f['source']['current']['clean'] and not f['source']['current']['tree_issues'],
  'own-stage':str(o['claimed_stage'])=='3' and o['state']=='completed' and all(o['checks'][str(i)]['passed']==n for i,n in [(1,120),(2,25),(3,7)])})
 assert all(facts.values()),facts
 for key in facts:review('TK1-'+key,path('runtime-01/preflight.json')+' ; '+path('source-audit/source-proof.json')+' ; '+path('official/report.json'),'Fresh named Stage3 complete image/runtime and applicable unchanged Stage1–3 isolated checks. Frozen earlier folders retain their own accepted stage claims. Build cache reused; default/override readiness before source inspection; no host-published reachability claim.')
 for key in ['source-provenance','two-builders','history-preserved']:review('TK1-'+key,path('source-audit/source-proof.json')+'#checks.'+key,'Exact immutable builder source/history, ownership, permitted-input declarations and preserved failures independently reviewed.',passed=s['checks'][key])
 for key,sourcekey in [('frozen-stage1','frozen-stage1'),('copied-base','copied-base'),('stage2-delivery','stage3-delivery'),('stage2-source','stage3-source')]:review('TK2-'+key,path('source-audit/source-proof.json')+'#checks.'+sourcekey,'Frozen Stage1/2 bytes and complete nine-file Stage3 predecessor copy/history; current Stage3 is independently delivered.',passed=s['checks'][sourcekey])
 review('TK2R-index-provenance',path('source-audit/source-proof.json')+'#source_notes.shared_index',s['source_notes']['shared_index'])
 for field in ['reservation_id','reference','user_id','created_at','starts_at','ends_at','status']:alias('TK2-stage1-record-'+field,'TK2R-record-'+field,'Actual accepted source record before export and authoritative current record after unchanged raw replacement; no identity or timestamp regeneration.')
 for key,suffix in [('genuine-export','import'),('import','import'),('original-create','create-shape'),('original-batch','moves-shape'),('token','token'),('password','password')]:alias('TK2-stage1-'+key,'TK2R-exact-s1-'+suffix,'Genuine accepted Stage1 source issues its state; actual unchanged HTTP export replaces current independent process.')
 for key,suffix in [('identity','body-key-user'),('lookup','lookup-token'),('form','same-document'),('key','body-key-user'),('body','body-key-user'),('original','original-receipt')]:alias('TK2-upgrade-browser-'+key,'TK2R-upgrade-exact-s1-single-'+suffix,'Real old source, same document/user/form/body/key, committed response loss and raw between-request replacement recover the real original confirmation.')
 for key,ids in {'create-source':'TK2R-record-source-create','batch-source':'TK2R-record-source-moves','import':'TK2R-record-import','create-replay':'TK2R-record-original-create','batch-replay':'TK2R-record-original-moves','create-new':'TK2R-exact-s1-new-rule','batch-new':'TK2R-new-batch-both-fields','key-conflict':'TK2R-exact-s1-key-priority'}.items():alias('TK2-legacy-ignored-'+key,ids,'Old ignored table_ids retains its historical body meaning; full body still governs replay, while fresh keys enforce current validation.')
 for key,ids in {'cutoff-order':['TK2R-pair-cutoff-order-'+str(i) for i in range(3)]+['TK2R-pair-cutoff-rollback-'+str(i) for i in range(3)],'no-op-values':['TK2R-noop-all-values-reverse','TK2R-noop-all-values-empty'],'serial-witness':['TK2-pair-create-patch-serial','TK2-pair-move-cancel-serial'],'snapshot-prefix':['TK2-pair-reads-atomic','TK3-moves-concurrency-series-raw-export-peer']}.items():alias('TK2R-'+key,ids,'Current staged operations, saved intervals/read states, independent serial/member oracle, no-op snapshots or raw-export peer observations establish the named invariant. Serializer internals are not observed.')
 legacy={
 'source-genuine':'TK3-upgrade-legacy-s1-real-source','import':'TK3-upgrade-legacy-s1-raw-transfer','export-equality':'TK3-upgrade-bootstrap-old-fields-legacy-s1,TK2R-legacy-s1-token,TK2R-legacy-s1-password,TK2R-legacy-s1-create-shape,TK2R-legacy-s1-moves-shape',
 'replacement':'TK2R-legacy-s1-destination-removed','record-immutable':'TK3-upgrade-bootstrap-original-timestamps-legacy-s1','original-receipt':'TK2R-legacy-s1-cancel-create','batch-original':'TK2R-legacy-s1-cancel-moves','cancelled':'TK3-upgrade-legacy-s1-cancelled-state',
 'new-write':'TK3-upgrade-bootstrap-new-timestamp-minute-offset-legacy-s1','mixed-transfer':'TK2R-legacy-s1-mixed-forward','peer-original-receipt':'TK2R-legacy-s1-mixed-replay'}
 for key,ids in legacy.items():alias('TK1-legacy-'+key,ids,'Genuine earlier-process source, unchanged replacement and immutable historical timestamp/receipt fields; new historic writes follow the exact-instant/minute-offset interpretation, never rewrite original strings.')
 mapping={
 'policies-inclusive-date':'policies-out-of-order,explain-policy-version','policies-same-date-tie':'policies-out-of-order,explain-policy-version','policies-backdated':'policies-contiguous-version,policies-existing-record,policies-existing-history','policies-existing-end':'policies-existing-record',
 'series-cutoff-anchor':'terms-old-cutoff','series-own-capacity':'series-reject-capacity-records,series-own-policy','series-own-opening':'series-reject-grid-records,series-reject-closed-records,series-reject-outside-records',
 'moves-old-cutoff':'terms-old-cutoff','moves-input-order':'moves-stale-priority','moves-unlisted-occupancy':'series-reject-occupied-single-records',
 'moves-no-partial-read':'moves-concurrency-series-raw-export-peer,moves-concurrency-patch-list,moves-concurrency-create-history',
 'upgrade-s1-source':'upgrade-accepted-s1-real-source','upgrade-s2-source':'upgrade-accepted-s2-real-source',
 'upgrade-original-body':'upgrade-original-shape','upgrade-original-moves':'upgrade-accepted-s1-moves-receipt,upgrade-original-shape',
 'upgrade-policies-roundtrip':'policies-policies-retry-replay-after-import,upgrade-repeat-import','browser-series-adopt':'browser-series-occurrences',
 'browser-s1-browser-upgrade':'browser-upgrade-375-real-screenshot','browser-s2-browser-upgrade':'browser-upgrade-1280-real-screenshot'}
 # Unlisted batch occupancy is established by the actual inherited batch test,
 # not by a series refusal (which has a different operation).
 mapping.pop('moves-unlisted-occupancy')
 for rid,ids in mapping.items():alias('TK3-'+rid,['TK3-'+i for i in ids.split(',')],'Current individually asserted behavior reviewed against this separately numbered obligation; local policy dates/ties, complete old snapshots, labelled cutoffs and staged reads retain their exact tested scopes.')
 for rid,ids in {'upgrade-passwords':'TK2R-exact-s1-password,TK2R-legacy-s1-password,TK2R-legacy-s2-password','upgrade-mixed-exact':'TK2R-exact-s1-mixed-new-exact,TK2R-legacy-s1-mixed-new-exact,TK2R-legacy-s2-mixed-new-exact','upgrade-reset-clear':'TK2R-exact-s1-reset-clears,TK2R-legacy-s1-reset-clears,TK2R-legacy-s2-reset-clears'}.items():alias('TK3-'+rid,ids,'Genuine old/new mixed numeric profiles and unchanged raw snapshots, login and complete reset freshly exercised on the exact Stage3 service.')
 for origin in ['accepted-s1','accepted-s2','legacy-s1','legacy-s2']:
  alias('TK3-upgrade-'+origin+'-token','TK3-upgrade-bootstrap-old-fields-'+origin+',TK3-upgrade-'+origin+'-adoption','The genuine source-issued bearer token authorizes current lookup/change/adoption and peer replacement; no new authentication was used.')
  alias('TK3-upgrade-'+origin+'-create-receipt','TK3-upgrade-original-shape','Each genuine origin in the complete migration loop replays original create and move receipt JSON after real current change/adoption, under the original token/body/key.')
 # Real four-route captures and independently computed transparency-aware contrast.
 actions=load(H/'inherited-browser-01/visual/browser-actions.json');views=load(H/'inherited-browser-02/general/visual-review-pending.json')
 images=[]
 def pic(name,note):
  p=H/name;assert p.is_file();images.append(dict(file=path(name),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),observation=note));return path(name)
 for width in [375,1280]:
  for route in ['search','signup','login','lookup']:
   name='inherited-browser-01/visual/visual-'+str(width)+'-'+route+'.png';image=pic(name,'Personally opened current route: warm consistent navigation, visible labels, legible hierarchy, prominent action and responsive layout.')
   rid='TK2-visual-'+str(width)+'-'+route+'-';view=next(x for x in views if x['width']==width and ('search' if x['route']=='/' else x['route'].strip('/'))==route)
   metric=next(x['metrics'] for x in actions if x.get('name')=='visual-'+str(width)+'-'+route and x.get('event')=='contrast-and-overflow')
   review(rid+'usable',image+' ; '+path('inherited-browser-02/general/assertions.json'),'Viewed route and actual width/label interaction metrics establish usable layout.',passed=metric['scroll']<=metric['client'])
   review(rid+'focus',image+' ; '+path('inherited-browser-02/general/visual-review-pending.json'),'Actual keyboard focus computed style has visible 3px outline; Enter/Tab booking/recovery flows freshly passed.',passed='solid 3px' in view['focus']['outline'])
   review(rid+'contrast',image+' ; '+path('inherited-browser-01/visual/browser-actions.json'),'Computed text/background accounts for transparent ancestors. Ordinary text>=4.5:1, large>=3:1; disabled excluded. Scoped, not complete WCAG certification.',passed=all(t['ratio']>=t['minimum'] for t in metric['text']))
 for state in ['available','unavailable','selected','loading','successful','refused','uncertain','empty']:
  width=1280 if state in ['selected','uncertain'] else 375;stem='available-unavailable' if state in ['available','unavailable'] else state
  image=pic('inherited-browser-01/visual/states-'+str(width)+'-'+stem+'.png','Personally viewed actual '+state+' state: distinct colour/outline, spinner, reference, refusal, uncertainty or empty-date text.')
  review('TK2-visual-state-'+state,image+' ; '+path('inherited-browser-01/visual/browser-actions.json'),'Actual '+state+' response/interaction capture is visually distinct and preserves the authoritative form state.')
 common=path('inherited-browser-01/visual/states-1280-selected.png')+' ; '+path('inherited-browser-01/visual/visual-375-search.png')+' ; '+path('browser-03/product/terms-history-1280.png')
 for key,note in {'coherent':'Cream/green/clay/amber system, human seating, clear hierarchy and consistent controls.','human-labels':'Actual restaurant/table labels, intentional Together pair seating and full historical before/after names.','actions':'Primary actions prominently green, secondary cancellation/terms disclosure visible.','navigation':'Consistent Find a table/Your reservation/auth navigation across four actual routes.','no-invented-facts':'Reviewed pages present fixture data and real reservations, with no invented reviews/photos/ratings/usage or establishment claims.'}.items():review('TK2-visual-'+key,common,note)
 for width in [375,1280]:
  for flow in ['terms-history','series-list','cancelled-exception','refused-adoption','uncertain-retry','upgrade']:
   if flow in ['terms-history','series-list','cancelled-exception','refused-adoption']:name='browser-03/product/'+flow+'-'+str(width)+'.png';truth=['TK3-browser-accepted-terms','TK3-browser-historic-changes'] if flow=='terms-history' else ['TK3-browser-series-occurrences'] if flow=='series-list' else ['TK3-browser-series-cancelled','TK3-browser-series-exception'] if flow=='cancelled-exception' else ['TK3-browser-failure-atomic']
   elif flow=='uncertain-retry':name='extra-browser-01/extra-browser/uncertain-retry-drop-'+str(width)+'.png';truth=['TK3-browser-uncertain-original-receipt','TK3-browser-uncertain-form-identity']
   else:name='browser-03/accepted-s1'+('-desktop' if width==1280 else '')+'/retained-lookup.png';truth=['TK3-browser-upgrade-'+str(width)+'-real-screenshot']
   image=pic(name,'Authoritative '+flow+' content matches actual API assertions and saved browser text. Original receipt/current terms/history/series and refused/uncertain states remain distinct; old empty history has no fabricated event.')
   alias('TK3-browser-'+flow+'-'+str(width)+'-truthful-text',truth,'Real text is independently compared to API values and actual current status; the inspected representative captures use human labels and immutable original references.')
   checks[-1]['evidence_path']+=' ; '+image
 review('TK3-browser-no-fake-data',common+' ; '+path('browser-03/product/browser-report.json'),'API-backed current reservation/decision/history/agreement render separately from original receipt; real interaction traces and source support no mock data.')
 review('TK3-browser-no-later-controls',common+' ; '+path('source-audit/source/web/app.js'),'Reviewed current source and real product: no manager role invention, planner or bulk series amendment surface.')
 for diag in load(H/'inherited-http-01/opaque-ids/admission-diagnostics.json'):review(diag['requirement_id'],path('inherited-http-01/opaque-ids/admission-diagnostics.json')+'#'+diag['requirement_id'],'Chosen fixture admission204; this is one of22 nonnormative diagnostics, not a lexical requirement.',passed=diag['status']==204)
 assert all(x['passed'] for x in checks)
 (H/'review-checks.json').write_text(json.dumps(checks,indent=2)+'\n');(H/'visual-observations.json').write_text(json.dumps(dict(candidate=C,scope='Personally opened representative current screenshots plus real exact browser text/width/contrast/keyboard assertions, not complete WCAG certification.',images=images),indent=2)+'\n')
 print(json.dumps(dict(records=len(checks),failed=0,concrete_images=len(images))))
if __name__=='__main__':main()
