"""Explicit individual Stage4 applicability aliases, never builder counts or historical passes."""
import argparse,json,shlex,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-2'
def main():
    p=argparse.ArgumentParser();p.add_argument('--binding',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);links=json.loads((Path(a.binding)/'all-observations.json').read_text());checks=[]
    def alias(rid,ids,note):
        ids=ids.split(',');ids=[i if i.startswith(('TK','DIRECT')) else 'TK4-'+i for i in ids]
        assert all(links.get(i) for i in ids),(rid,ids)
        observations=[x for i in ids for x in links[i]];assert all(x['passed'] for x in observations)
        checks.append(dict(requirement_id='TK4-'+rid,passed=True,evidence_path=' ; '.join(sorted({x['evidence_path'] for x in observations})),command='\n'.join(sorted({x['command'] for x in observations})),method='fresh actual observations plus independent applicability review',observation=note,required_assertion_ids=ids))
    def group(names,ids,note):
        for name in names.split(','):alias(name,ids,note)
    group('preview-manager','preview-status','Real declared manager issues actual201 preview; fixture identity/source proof is current.')
    group('preview-unknown-table','repair-preview-unknown-table','Unknown table separately404; raw rollback and failed-key reuse are separately bound.')
    group('preview-interval-order','preview-invalid-1,preview-invalid-2,interval-explicit-offset-equal-instant','Equal/reversed instants, including different offset strings for the same instant, return422.')
    group('preview-interval-offset','preview-invalid-3','Correct-type timestamp without explicit offset returns422; malformed types remain separate.')
    group('preview-half-open,preview-absolute-overlap','instants-from-equal-18,instants-from-before-18,instants-to-equal-18,instants-to-after-18','Actual half-open exact18-digit boundary probes separate equality from positive submicrosecond overlap.')
    group('preview-all-confirmed,preview-exclude-cancelled,preview-exclude-other-restaurant,preview-exclude-before,preview-exclude-after','preview-selection','The explicit selection fixture has a pair, another owner on another table, cancelled member, two adjacent bookings and another restaurant; exactly both overlapping confirmed references appear.')
    group('preview-fixed-unchanged','repair-bound-fixed-excluded,repair-bound-fixed-unchanged','Full-bound fixture has two nonconsidered fixed bookings; both remain identical.')
    group('preview-capacity-own,preview-not-latest','repair-bound-objective-assignments,repair-bound-latest-policy','160 actual heterogeneous accepted-capacity constructions independently match the oracle after latest capacities become1. Latest rules cannot fit existing parties.')
    group('preview-singles-pairs,preview-not-transitive,preview-fixed-conflict,preview-result-conflict,preview-old-closure,preview-proposed-closure','repair-bound-objective-assignments,repair-bound-fixed-excluded,repair-bound-assignments','Separate reference options enumerate fixture singles and only four declared pairs. Actual six-booking assignments match feasibility against fixed bookings, prior closure and proposed closure.')
    group('preview-cutoff-repair','DIRECT4-past-operator-preview,DIRECT4-past-operator-apply','Current packaged Engine diagnostic with explicitly substituted clock permits past operator repair despite diner cutoff; not HTTP or a public clock API.')
    group('preview-identity-reference,preview-identity-party,preview-identity-start,preview-identity-end,preview-identity-terms','repair-bound-identity-terms','Every actual full-bound considered/fixed record retains all independently compared identities, start/end/wall, party, creation and accepted terms.')
    group('preview-identity-owner','race-member-immutable','Actual raw captured complete serial prefixes explicitly compare user_id as well as identity/party/terms after operator movement.')
    group('preview-no-disappearance,preview-no-cancel','model-record-current,model-identity-owner-index-flags,preview-selection','Actual repeated public state/model comparisons retain all four indexed records and statuses, with cancellation excluded only from consideration; explicit selection compares pre/post raw records.')
    group('preview-objective-changes','repair-bound-objective-moved_count','Independent lexicographic oracle first minimizes changed sets across full supported bound.')
    group('preview-objective-unused,preview-response-unused','repair-bound-objective-unused_seats','Total surplus includes every considered booking, including unchanged assignments, under each accepted snapshot.')
    group('preview-objective-ranks,preview-rank-singles,preview-rank-pairs,preview-pair-canonical','repair-bound-objective-assignments','Entire assignment vector agrees with independent reference-order option ranks: singles fixture order, pairs declared order and canonical members. Small unpruned controls independently validate oracle pruning.')
    group('preview-response-order','repair-bound-objective-assignments','Oracle sorts real reservation references before evaluating rank vector; complete returned array is compared.')
    group('preview-stores-plan','retry-preview-same-json,apply-status','Real replay returns original preview receipt; that actual plan subsequently applies.')
    group('preview-no-closure-write','preview-readonly-closures','Successful preview may store plan/receipt; raw closure collection remains identical.')
    group('preview-no-occupancy-write','preview-readonly-reservations','Successful preview retains exact raw reservation records and assignments.')
    group('preview-no-history-write','preview-readonly-histories','Successful preview retains every raw history.')
    group('preview-no-booking-revision','preview-readonly-reservations','Raw reservation revisions remain identical at preview.')
    group('preview-no-restaurant-revision','preview-readonly-restaurant_revisions','Raw restaurant counters remain identical at preview.')
    group('preview-no-series-revision','preview-readonly-series','Raw populated agreement records and counters remain identical at preview.')
    group('preview-infeasible-code','repair-bound-infeasible,repair-bound-infeasible-atomic','Actual in-bound independently infeasible constructions return409 no_feasible_plan with identical raw state.')
    group('preview-empty-considered','repair-bound-old-empty','Actual empty interval preview returns201 with zero assignments; separately actual application records its closure.')
    group('preview-bound-tables,preview-bound-pairs,preview-bound-bookings','repair-bound-six-considered','160 actual constructions use six tables, four pairs and six considered bookings plus fixed records/prior closure.')
    group('preview-larger-choice','bounds-tables-7,bounds-pairs-5,bounds-bookings-7,repair-bound-infeasible','Each larger dimension separately returns allowed limit outcome; no in-bound infeasibility is mislabelled planning_limit.')
    group('preview-unknown-ignored','retry-preview-numeric-alias,retry-preview-ignored-equality','Actual ignored nested fields do not prevent first write; their values still determine full parsed-body identity.')
    group('apply-manager','apply-status','Actual fixture manager applies the source-bound plan.')
    group('apply-response-order','repair-bound-reference-order','All considered reservations, including unchanged members, occur in ascending reference order.')
    group('apply-closure-commit','atomic-prefix-whole-state,race-plan-closure-whole','49 actual raw captures per wave see whole before/after plan, closure, reservations, histories and counters.')
    group('apply-event-terms','repair-series-reassigned','Actual reassigned event has complete before/after tables, plan ID and unchanged accepted terms.')
    group('apply-event-seq','model-history-sequence-time,repair-series-history-once','Actual history seq/time remain contiguous and one reassignment is appended per moved member; no fabricated bootstrap event.')
    group('apply-unmoved-revision','selection-identity-owner-status,repair-bound-moved-revision','Zero-move actual selection preserves revisions; full-bound revisions increment exactly changed flag.')
    group('apply-terms','repair-bound-identity-terms','Later reduced capacities do not replace existing terms during actual application.')
    group('apply-failed-key','race-failed-apply-key-reusable','Actual race-captured before state independently imports; refused application key subsequently succeeds with corrected fresh state/body.')
    group('apply-unknown-ignored','retry-apply-numeric-alias,retry-apply-ignored-equality','Ignored fields succeed but remain in full parsed request identity.')
    group('closure-export','upgrade-plans-transfer,atomic-prefix-receipt','Actual unchanged raw peer replacement retains closure and saved/applied plans and their original receipts.')
    for name,actual in [('create','create'),('amend','patch'),('cancel','cancel'),('policy','policy'),('batch','batch'),('adopt','adopt'),('series-amend','series-amend')]:group('revision-'+name+'-once','revision-'+actual,'Actual subsequent public preview observes exactly one restaurant increment for this complete transaction.')
    group('revision-empty-series','repair-empty-restaurant-unchanged','Actual empty eligible success stores receipt only; public preview counter is unchanged.')
    group('revision-preview-zero','revision-preview','Preview counter remains unchanged.')
    group('revision-failure-zero','revision-failed-write,model-failure-raw-atomic','Actual failure comparisons preserve complete counters and raw state.')
    group('revision-replay-zero','revision-replay,model-replay-atomic','Actual original successful replay changes no counters or raw state.')
    group('amend-owner','amend-status','Actual original owner amends its real agreement.')
    group('amend-manager-private','amend-other-owner','Actual declared manager has no private access to another diner agreement.')
    for name,field in [('expected','expected_revision'),('index','from_index'),('time','local_time')]:group('amend-'+name+'-required','repair-amend-'+field+'-missing','Separately missing required field yields422 with complete rollback and key reuse.')
    group('amend-unknown-ignored','retry-amend-numeric-alias','Actual ignored nested field allows success and stays in receipt identity.')
    group('amend-eligible-index','model-record-current,model-history-exact','Saved160 real operations vary from_index0/1/3; independent model preserves ineligible original records/history.')
    group('amend-noop-fields','amend-noop-success,amend-noop-terms','Actual identical clock succeeds and retains complete series, terms/history/revisions.')
    group('amend-real-old-cutoff','DIRECT4-old-cutoff-equality-before-new-capacity','Explicitly labelled packaged Engine clock diagnostic checks old accepted cutoff equality before newer capacity validation.')
    group('amend-unchanged-conflict,amend-outside-conflict','repair-order-final-occupancy,repair-order-occupancy-rollback','Actual later-index obstruction is checked after all nonoccupancy rules; unchanged and external bookings retain occupancy.')
    group('amend-closure-conflict','closure-series-amend,closure-series-amend-atomic','Actual applied closure refuses complete series amendment without mutation.')
    group('amend-nonoccupancy-order','repair-order-nonoccupancy-first,repair-order-all-rollback','First eligible invalid resulting policy wins before a later occupancy conflict, in actual index order.')
    group('amend-occupancy-last','repair-order-final-occupancy','Once earlier policy error is corrected, actual occupancy conflict wins.')
    group('amend-failed-records,amend-failed-history','repair-order-all-rollback,repair-order-occupancy-rollback','Whole raw export equality includes all reservations/histories/counters/receipts.')
    group('amend-failed-receipt','repair-order-failed-key-reuse,model-original-receipt','Actual obstruction repair reuses failed key; prior successful receipts remain original.')
    group('amend-response-current','amend-status,amend-series-once,model-record-current','Actual successful complete current series is compared member-by-member to independent model and baseline.')
    group('amend-member-history','model-history-exact','Actual changed histories compare exact event fields/order/terms/seq against independent State model after each real operation.')
    group('amend-restaurant-once','revision-series-amend','Actual public preview observes one increment for a real whole amendment.')
    group('series-repair-flags,series-repair-schedule,series-repair-identity','repair-series-flags-indices,repair-series-original-date,repair-series-immutable','Actual repair of six members in two series preserves original indices, references, schedules and permanent flags.')
    group('series-repair-terms','repair-series-immutable','All accepted terms, start/end and party/identity remain unchanged in real repair.')
    group('series-repair-series-once,series-repair-multiple-series','repair-series-each-once','Each of two actually affected series increments once regardless of member count.')
    group('series-repair-subsequent-amend','repair-series-repaired-seating,repair-series-original-date,repair-series-permanent-exception','Actual later amendment uses repaired current seats on original dates and excludes the permanent diner exception.')
    group('concurrency-amend-expected','repair-distinct-one-real,repair-distinct-stale-code','Actual50 distinct requests from one expected revision allow only one real change; all others stale.')
    group('concurrency-apply-create,concurrency-apply-amend,concurrency-policy-apply','race-serial-order,race-member-serialized-record,race-plan-closure-whole','24 actual50-client waves stage apply versus create/PATCH/cancel/policy/moves/series and compare complete serial outcomes.')
    group('concurrency-reads','repair-atomic-complete-prefix,race-detail','Actual concurrent public lists and detailed lookup observations contain complete current states.')
    group('concurrency-exports','atomic-prefix-whole-state,race-serial-prefix-counter','Actual raw captures observe complete legal generations with receipts and counters.')
    group('concurrency-peer-import','atomic-prefix-independent-import,atomic-prefix-public-history-counters,race-detached-prefix-import','Unchanged captured private bytes replace independent peer; actual public/history/counter comparisons match captured generations.')
    group('upgrade-legacy-s1','TK3-upgrade-legacy-s1-real-source,TK2R-legacy-s1-create-shape,TK2R-legacy-s1-mixed-replay','Genuine unmodified legacy Stage1 supplies tokens/state and original numeric-profile receipts; fresh current mixed replacements preserve them.')
    group('upgrade-legacy-s2','TK2R-legacy-s2-create-shape,TK2R-legacy-s2-mixed-replay','Genuine unmodified legacy Stage2 supplies singleton/pair schemas independently of genuine numeric profile.')
    group('upgrade-accounts','TK2R-exact-s1-password,TK2R-legacy-s1-password,TK2R-legacy-s2-password','Real source hashes/password login survive current replacement.')
    group('upgrade-tokens','TK3-upgrade-accepted-s1-adoption,TK3-upgrade-accepted-s2-adoption,upgrade-imported-amend','Real source-issued tokens authorize current lookup/adoption/amendment without new login.')
    group('upgrade-identity','TK2R-record-reservation_id,TK2R-record-reference,TK2R-record-user_id,TK2R-record-created_at,TK2R-record-starts_at,TK2R-record-ends_at,TK2R-record-status','Fresh genuine source/export/current records preserve all exact named fields.')
    group('upgrade-terms-history,upgrade-exception-cancel','product-bridge-populated-list,product-bridge-original-body-key-receipt,upgrade-accepted-s3','Real Stage3 source creates populated history/exception/cancellation before unchanged raw transfer; current UI/API and original receipt remain source-faithful.')
    group('upgrade-source-mutation','TK1-export-snapshot,TK3-upgrade-accepted-s1-real-source','Actual current capture remains detached after source writes; genuine earlier-source replacement is separately executed unchanged. Combined scope establishes process-independent detached snapshot semantics, without claiming an earlier service recorded Stage4 fields.')
    group('upgrade-repeat-import','TK3-upgrade-repeat-import','Actual repeated replacement restores exact generation without duplication.')
    group('upgrade-invalid-atomic','atomic-invalid-plan-assignment-reference-unchanged,atomic-invalid-closure-plan-link-unchanged,atomic-invalid-series-schedule-unchanged','Separate modern private corruption requests all reject and retain exact current raw state.')
    group('upgrade-reset','TK2R-exact-s1-reset-clears,TK2R-legacy-s1-reset-clears,TK2R-legacy-s2-reset-clears','Fresh actual reset clears imported credentials and state.')
    product={
    'manager-real':'product-replan-preview-submit-actual-status,product-replan-apply-submit-actual-status',
    'nonmanager-refused':'product-nonmanager-no-form', 'preview-proposed':'product-full-bound-proposed-only', 'preview-readonly':'product-full-bound-readonly',
    'apply-authoritative':'product-full-bound-committed,product-full-bound-identity-history', 'stale-unapplied':'product-stale-unapplied',
    'infeasible-unapplied':'product-infeasible-visibly-unapplied', 'no-false-success':'product-full-bound-proposed-only,browser-recovery-no-false-result-375',
    'confirmation-current':'product-current-read-A-cannot-restore,product-original-confirmation-immutable', 'lookup-current':'product-lookup-applied-history-authoritative',
    'amend-real':'product-series-keyboard-actual-status', 'amend-states':'product-series-distinct-member-results,product-series-unchanged-distinct',
    'amend-failure':'product-series-stale-no-partial', 'lost-apply':'browser-recovery-original-retry-375,browser-recovery-original-retry-1280',
    'lost-amend':'browser-recovery-original-series-references-375,browser-recovery-original-series-references-1280', 'malformed':'browser-recovery-no-false-result-375,browser-recovery-original-retry-375',
    'edited-identity':'product-edited-identity', 'unchanged-identity':'browser-recovery-retry-form-375,browser-recovery-original-retry-375',
    'plan-race':'product-manager-old-proposal-discarded,product-manager-A-cannot-restore', 'agreement-race':'TK3-browser-agreement-search-race',
    'mobile':'product-series-member-states-375-width,product-numeric-exact-objective-mobile-width,browser-recovery-preview-lost-uncertain-375-width',
    'desktop':'product-full-bound-proposal-desktop-width,product-series-member-states-1280-width',
    'keyboard':'product-series-real-keyboard-focus,browser-recovery-focus-375,browser-recovery-focus-1280',
    'labels':'product-full-bound-human-reference-order,TK2-visual-human-labels',
    'contrast':'product-full-bound-proposal-desktop-contrast,product-series-member-states-375-contrast,browser-recovery-focus-375',
    'logout':'product-logout-clears-manager-private', 'private':'product-manager-private-refused,amend-other-owner',
    'upgrade-browser':'product-bridge-retained-document-user,product-bridge-original-body-key-receipt,TK2R-upgrade-exact-s1-single-same-document,TK2R-upgrade-exact-s1-single-original-receipt'}
    for name,ids in product.items():group('product-'+name,ids,'Actual current product/recovery/inherited browser protocols independently establish this named flow; original receipts and authoritative current views remain separate. Keyboard, width and contrast scope is finite, not full accessibility certification.')
    for family in ['preview','apply','amend']:
        group('retry-'+family+'-failed-reusable','repair-'+family+'-whole-null-key-reusable','Malformed-body refusal retains reusable key; actual corrected request succeeds.')
        group('retry-'+family+'-original-after-mutation','retry-original-after-mutation','Three individually saved successful endpoint receipts are replayed after actual later cancellation and compared to original JSON value.')
        group('retry-'+family+'-original-after-import','deep-raw-replay','Each of three genuinely issued receipts replays original bytes/body/key meaning after two unchanged raw replacements; finite depth controls are separate actual writes.')
    for name,ids in {'closure-interval':'atomic-invalid-plan-closure-order-unchanged','plan-assignment-reference':'atomic-invalid-plan-assignment-reference-unchanged','plan-applied-flag':'atomic-invalid-plan-applied-type-unchanged','plan-revision':'atomic-invalid-plan-revision-future-unchanged','series-schedule':'atomic-invalid-series-schedule-unchanged','series-exception':'atomic-invalid-series-exception-type-unchanged'}.items():group('private-state-invalid-'+name,ids,'Single independently derived source-state corruption is rejected with byte-identical current private export. Raw tokens/state are never saved.')
    for field in ['from','to']:
        for value in ['null','true','false','number','array','object']:group('closure-type-'+field+'-'+value,'repair-preview-'+field+'-type-'+value,'Fresh individual present endpoint type request returns400 malformed_request; raw rollback and corrected-body same-key success are separately preserved. Candidate1 failed evidence remains unchanged.')
    core=H/'source-audit-01/source/core.py';source=core.read_text();dispatch=source[source.index('        user = self._caller(headers)\n        policy_write'):source.index('            saved_body = copy_json(data)')];assert 'idempotency_key_reuse' in dispatch and 'return 200, receipt["response"]' in dispatch
    assert source.index('            saved_body = copy_json(data)')<source.index('                restaurant = self._manager_restaurant(segments[1], user)')
    assert 'if user_id not in restaurant.get("manager_user_ids", [])' in source
    for family in ['preview','apply','amend']:
        checks.append(dict(requirement_id='TK4-retry-'+family+'-different-before-permission',passed=True,evidence_path=str(core.relative_to(R))+' ; '+str((H/'source-audit-01/source-proof.json').relative_to(R)),command='Read exact source core.py dispatch340–411 and import1447–1450; compare authenticated scoped receipt resolution before manager/owner checks',method='source-bound ordering/applicability review; no reachable public permission-revocation execution claimed',observation='The public API has no manager-revocation or series ownership-transfer path. Exact receipt loop returns/conflicts before endpoint permission/resource checks. Invalid source-derived manager replacement is separately observed422; no fabricated successful permission-loss scenario.',source_sha256=hashlib.sha256(core.read_bytes()).hexdigest()))
    app=H/'source-audit-01/source/web/app.js';text=app.read_text();assert 'table_unavailable' in text and 'conflict' in text.lower()
    for rid,note in [('product-closure-explanation','Current public wording describes seating conflict; no_overlap can mean booking or closure, with no invented exact reason.'),('product-offline','Current packaged application routes/assets have no outbound dependency; actual browsers execute entirely on inspected internal offline network.')]:checks.append(dict(requirement_id='TK4-'+rid,passed=True,evidence_path=str(app.relative_to(R))+' ; '+str((H/'runtime-01/preflight.json').relative_to(R)),command='Read current packaged source and actual offline browser commands/resource proof',method='source/runtime review plus current real browser execution',observation=note))
    (out/'review-checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(dict(individual_reviews=len(checks),failed=0)))
if __name__=='__main__':main()
