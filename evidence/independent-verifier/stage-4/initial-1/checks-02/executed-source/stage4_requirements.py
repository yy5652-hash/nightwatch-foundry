"""Prospective Stage4 obligations; decomposition is not a judging-test count."""
from itertools import product

S1='75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
S2='4dba10246b07b2dda19de260d529f9d94ba0a1ed'
S3='91e2c471acded1b861b3fec725f202297b1c6740'
PACKAGE='TK-20261004-S4-independent-verifier-INITIAL-1'
SEED=202610064

# Each sentence is a separate observable obligation, not a family-level verdict.
GROUPS={
 'preview':(13,'Seating changes after a table closure',[
  ('manager','Fixture manager can preview.'),('anonymous','No bearer receives 401 unauthenticated.'),
  ('nonmanager','Authenticated nonmanager receives 403 forbidden.'),('restaurant-manager','Manager permission is restaurant scoped.'),
  ('unknown-restaurant','Unknown restaurant receives 404 not_found.'),('unknown-table','Unknown table receives 404 not_found.'),
  ('table-other-restaurant','A table outside this restaurant receives 404 not_found.'),('interval-order','Require from strictly before to as exact absolute instants.'),
  ('interval-offset','Input instants must have explicit offsets.'),('half-open','Proposed closure is half open.'),
  ('all-confirmed','Consider every overlapping confirmed booking, including a booking not seated on the closing table.'),
  ('exclude-cancelled','Cancelled bookings are not considered.'),('exclude-other-restaurant','Other restaurants are excluded.'),
  ('exclude-before','An end equal to closure start is excluded.'),('exclude-after','A start equal to closure end is excluded.'),
  ('fixed-unchanged','Nonconsidered bookings keep their assignments.'),('capacity-own','Each option uses that booking own accepted capacities.'),
  ('not-latest','Latest publication cannot replace a booking accepted capacities.'),('singles-pairs','Options are singles and declared pairs only.'),
  ('not-transitive','Undeclared or transitive pairs are never assigned.'),('fixed-conflict','Options cannot conflict with fixed bookings.'),
  ('result-conflict','Options cannot conflict with another resulting assignment.'),('old-closure','Options cannot intersect earlier applied closures.'),
  ('proposed-closure','Options cannot intersect the proposed closure.'),('absolute-overlap','All conflicts use half-open absolute instants.'),
  ('cutoff-repair','Diner cutoff does not prohibit a manager repair.'),('identity-reference','Every reference remains.'),
  ('identity-owner','Every owner remains.'),('identity-party','Every party size remains.'),('identity-start','Every start remains.'),
  ('identity-end','Every end remains.'),('identity-terms','Every complete accepted snapshot remains.'),
  ('no-disappearance','No booking disappears.'),('no-cancel','No confirmed booking becomes cancelled.'),
  ('objective-changes','First minimize table-set changes.'),('set-equality','Pair input order cannot count as a seating change.'),
  ('objective-unused','Then minimize unused seats over ALL considered bookings, including unmoved ones.'),
  ('objective-ranks','Then minimize rank vector in ascending reference order.'),('rank-singles','Singles rank first in fixture order starting zero.'),
  ('rank-pairs','Pairs rank next in declaration order.'),('pair-canonical','Returned pair members use declaration order.'),
  ('status','First preview succeeds with 201.'),('plan-id','Plan ID obeys opaque ID contract.'),('response-closure','Returned closure represents submitted exact interval.'),
  ('response-revision','Returned restaurant revision is the current revision.'),('response-all','Assignments include every considered booking once.'),
  ('response-order','Assignments are in reference order.'),('response-changed','Each changed flag equals set inequality.'),
  ('response-moved','moved_count equals changed assignments.'),('response-unused','unused_seats equals accepted-capacity sum minus party over all considered bookings.'),
  ('stores-plan','Successful preview stores a replayable/applicable plan.'),('no-closure-write','Preview publishes no closure.'),
  ('no-occupancy-write','Preview alters no occupancy.'),('no-booking-write','Preview alters no reservation.'),('no-history-write','Preview writes no history.'),
  ('no-booking-revision','Preview changes no reservation revision.'),('no-restaurant-revision','Preview changes no restaurant revision.'),
  ('no-series-revision','Preview changes no series revision.'),('infeasible-code','No feasible assignment returns 409 no_feasible_plan.'),
  ('infeasible-state','Infeasible preview changes no state or receipts.'),('empty-considered','A valid interval without considered bookings supports an empty plan.'),
  ('bound-tables','Support six tables.'),('bound-pairs','Support four declared pairs.'),('bound-bookings','Support six considered bookings.'),
  ('bound-all','Support six tables, four pairs and six bookings together with fixed bookings and old closures.'),
  ('larger-choice','Larger inputs may succeed correctly or return 422 planning_limit; an in-bound infeasible problem must not be labelled planning_limit.'),
  ('unknown-ignored','Unknown fields do not invalidate preview but remain part of complete retry identity.')]),
 'apply':(53,'Seating changes after a table closure',[
  ('manager','Fixture manager can apply.'),('anonymous','No bearer receives 401 unauthenticated.'),('nonmanager','Nonmanager receives 403 forbidden.'),
  ('unknown-plan','Unknown plan receives 404 not_found.'),('wrong-restaurant','Plan at another restaurant receives 404 not_found.'),
  ('different-manager','A second legitimate manager of the same restaurant can apply a shared restaurant plan.'),
  ('stale','Intervening same-restaurant revision returns 409 stale_plan.'),('stale-atomic','Stale failure changes no state or key claim.'),
  ('applied-different-key','Applied plan under a different key returns 409 plan_already_applied.'),
  ('already-before-stale','An applied plan remains plan_already_applied under a fresh key after later restaurant revisions.'),
  ('status','First successful application returns 201.'),('response-id','Application returns original plan_id.'),
  ('response-all','Reservations include all considered bookings, including unmoved ones.'),('response-order','Reservations are in reference order.'),
  ('closure-commit','Closure and all assignments commit together.'),('moved-revision','Each moved reservation revision increments once.'),
  ('moved-event','Each moved reservation records exactly one reassigned event.'),('event-field','Reassigned uses complete before/after table_ids even for singles.'),
  ('event-plan','Reassigned records actual plan_id.'),('event-terms','Reassigned stores unchanged complete accepted_terms.'),
  ('event-seq','Reassigned sequence follows the previous history contiguously.'),('unmoved-revision','Unmoved reservation revision is unchanged.'),
  ('unmoved-history','Unmoved history is unchanged.'),('restaurant-once','Restaurant increments once for the whole application.'),
  ('identity','IDs, references, owners, party, times and creation timestamps remain exact.'),('terms','Accepted terms do not adopt newer policies.'),
  ('other-restaurant','Writes/closures at another restaurant do not invalidate this plan.'),('repeat-original','Original successful application retry remains immutable after changes/import.'),
  ('failed-key','A refused application key remains reusable.'),('unknown-ignored','Unknown body fields are ignored and retain full retry identity.')]),
 'closure':(64,'Seating changes after a table closure',[
  ('single-availability','Applied closure excludes overlapping singles.'),('pair-availability','Applied closure excludes pairs with any closed member.'),
  ('unaffected-availability','Other members and adjacent intervals remain available according to capacity/occupancy.'),
  ('create','Create intersecting a closure returns 409 table_unavailable.'),('pair-create','Pair create intersecting any closed member is refused.'),
  ('patch','Real amendment intersecting a closure returns 409 table_unavailable without mutation.'),('batch','Collective moves obey closures atomically.'),
  ('adoption','Generated series occurrences obey closures atomically.'),('series-amend','Series amendment obeys closures atomically.'),
  ('explain-no-overlap','Closure makes no_overlap false.'),('explain-capacity','Capacity remains independently evaluated when a closure also excludes the table.'),
  ('explain-both','A capacity and closure refusal reports both false.'),('without-explain','No explanation appears when omitted.'),
  ('source-immutable','Original successful receipts are unchanged by a closure.'),('export','Closures and saved plans survive unchanged export/import.')]),
 'revision':(47,'Seating changes after a table closure; Amend recurring reservations',[
  ('reset-zero','Reset starts restaurant revision at zero.'),('seed-zero','Seeded bookings do not represent new operations after reset.'),
  ('create-once','Each successful new booking increments once.'),('amend-once','Each real individual amendment increments once.'),
  ('cancel-once','First cancellation increments once.'),('policy-once','First successful policy publication increments once.'),
  ('batch-once','A real collective batch increments once regardless of member count.'),('adopt-once','Series adoption increments once including all generated bookings.'),
  ('series-amend-once','Real series amendment increments once.'),('apply-once','Application increments once even with zero moved bookings.'),
  ('noop-patch','No-op PATCH does not increment.'),('noop-batch','All-no-op batch does not increment.'),('repeat-cancel','Repeated cancel does not increment.'),
  ('noop-series','All-no-op amendment does not increment.'),('empty-series','Empty eligible amendment does not increment.'),
  ('preview-zero','Preview does not increment.'),('failure-zero','Every refused write does not increment.'),('replay-zero','Every successful replay does not increment.')]),
 'amend':(73,'Amend recurring reservations',[
  ('owner','Owner can amend series.'),('anonymous','No bearer receives 401 unauthenticated.'),('unknown','Unknown series receives 404 not_found.'),
  ('other-owner','Other owner receives 404 not_found.'),('manager-private','Manager receives no private access to another diner series.'),
  ('expected-required','expected_revision is required.'),('index-required','from_index is required.'),('time-required','local_time is required.'),
  ('stale-first','Positive mismatch returns stale_revision before member cutoff/booking validation.'),('unknown-ignored','Unknown fields ignored for validation.'),
  ('eligible-index','Only indices at or after from_index are considered.'),('skip-cancelled','Cancelled occurrences are excluded.'),
  ('skip-exception','Permanent exceptions are excluded.'),('skip-both','Cancelled exceptional members remain excluded.'),
  ('schedule-original','Use original scheduled local dates after previous time/table changes.'),('retain-reference','Every reference remains.'),
  ('retain-owner','Every owner remains.'),('retain-party','Every party size remains.'),('retain-seating','Current table selection remains including manager repairs.'),
  ('noop-fields','Identical resulting fields are a no-op.'),('noop-terms','No-op retains old terms even when new policies apply.'),
  ('real-old-cutoff','Real change checks old accepted cutoff first.'),('real-policy','Real change adopts the resulting scheduled date policy.'),
  ('real-all-fields','Real change validates all resulting fields including retained tables/party under new terms.'),
  ('absolute-duration','Real change recalculates absolute end using new duration.'),('unchanged-conflict','Result cannot conflict with unchanged members.'),
  ('outside-conflict','Result cannot conflict with other bookings.'),('closure-conflict','Result cannot conflict with applied closures.'),
  ('nonoccupancy-order','First nonoccupancy error in eligible index order wins before overlap.'),('occupancy-last','Otherwise any overlap is table_unavailable.'),
  ('failed-records','Failure preserves all reservation records.'),('failed-history','Failure preserves all histories.'),('failed-counters','Failure preserves every revision.'),
  ('failed-receipt','Failure leaves key reusable and existing successful receipts unchanged.'),('status','First successful amendment returns 201.'),
  ('response-current','Successful response is the complete current series shape.'),('member-revision','Each changed member gains one revision.'),
  ('member-history','Each changed member records one ordinary changed event with exact ordered fields.'),('series-once','Series increments once if any member changed.'),
  ('restaurant-once','Restaurant increments once if any member changed.'),('no-exceptions','Series amendment never marks an exception.'),
  ('noop-success','All-no-op succeeds with unchanged revisions/history/terms.'),('empty-success','Empty eligible succeeds with unchanged revisions/history/terms.'),
  ('replay-original','Successful retry returns original response after later edits/cancels.'),('dst-gap','Nonexistent resulting local time rejects whole transaction.'),
  ('dst-fold','Repeated resulting local time uses first occurrence.'),('calendar-boundary','Valid original dates across month/year/leap boundaries remain exact.')]),
 'series-repair':(102,'Amend recurring reservations',[
  ('flags','Repair preserves every existing exception flag.'),('schedule','Repair preserves every original scheduled date.'),
  ('identity','Repair preserves occurrence references/indices/reservation identities.'),('terms','Repair preserves complete accepted terms and times.'),
  ('series-once','Each affected series increments once per plan regardless of moved member count.'),
  ('unmoved-series','A series with no moved member does not increment.'),('multiple-series','Each of several affected series increments once.'),
  ('subsequent-amend','Subsequent collective amendment uses repaired current seats and original schedule while skipping exceptions/cancelled.')]),
 'concurrency':(68,'Seating changes after a table closure; Amend recurring reservations',[
  ('apply-identical50','Fifty identical applies yield one 201 and 49 original 200 receipts.'),
  ('preview-identical50','Fifty identical previews yield one 201 and 49 original 200 receipts with one plan identity.'),
  ('amend-identical50','Fifty identical amendments yield one 201 and 49 original 200 receipts.'),
  ('apply-distinct','Concurrent different plans based on same restaurant revision cannot partially commit both.'),
  ('amend-expected','Concurrent real amendments using one expected series revision cannot both change.'),
  ('apply-create','Concurrent plan application and create admit a serial ordering with occupancy/revisions intact.'),
  ('apply-amend','Concurrent plan application and individual/series amendment admit complete serial states.'),
  ('policy-apply','Concurrent policy publication and apply observe stale-plan serialization.'),
  ('reads','Concurrent lookup/list/series/explain observations are complete valid states.'),
  ('exports','Atomic exports captured during changes represent complete pre/post generations and receipts.'),
  ('peer-import','Unchanged captured exports import to independent peers and preserve entire generations.'),
  ('failure-keys','Competing failures retain key reusability.')]),
 'upgrade':(107,'Stage1 export/import; Stage4 Amend recurring reservations',[
  ('accepted-s1','Accept genuine accepted Stage1 unchanged exports.'),('accepted-s2','Accept genuine accepted Stage2 unchanged exports.'),
  ('accepted-s3','Accept genuine accepted Stage3 unchanged exports with actual populated policies/history/series.'),
  ('legacy-s1','Preserve genuine legacy Stage1 receipt numeric meanings and strings.'),('legacy-s2','Preserve genuine legacy Stage2 pair/single receipt shape independently of profile.'),
  ('accounts','Preserve hashes and password login.'),('tokens','Existing source tokens remain usable.'),('replace','Destination data/credentials removed rather than merged.'),
  ('identity','Identities/references/status/timestamps remain exact.'),('create-receipts','Original earlier booking receipts stay unchanged.'),
  ('move-receipts','Original earlier move receipts stay unchanged.'),('series-receipts','Original Stage3 adoption receipts stay unchanged.'),
  ('terms-history','Actual existing immutable terms/history retained.'),('exception-cancel','Moved/exception/cancelled imported occurrences retain flags and history.'),
  ('imported-amend','Amend genuinely imported populated series.'),('imported-repair','Repair genuinely imported bookings/series.'),
  ('mixed-second','Old/current/profile-mixed receipts and new histories survive second independent replacement.'),
  ('plans-transfer','Prepared and applied current plans/closures and original preview/apply/amend receipts survive second replacement.'),
  ('source-mutation','Writes after capture do not alter captured replacement.'),('repeat-import','Repeated replacement restores without duplication.'),
  ('invalid-atomic','Invalid new private-state plan/closure/series relationships reject atomically.'),('reset','Reset clears all imported state and credentials.')]),
 'product':(10,'Stage2 product requirements; Stage4 seating changes; supplementary product brief',[
  ('manager-real','Actual fixture manager can preview/apply through visible controls.'),('nonmanager-refused','Actual nonmanager is refused without fabricated capability.'),
  ('preview-proposed','Preview displays proposed assignments separately from committed reservations.'),('preview-readonly','Diner current lookup remains unchanged before application.'),
  ('apply-authoritative','Successful application displays actual authoritative current assignments.'),('stale-unapplied','Stale refusal remains visibly unapplied.'),
  ('infeasible-unapplied','Infeasible refusal remains visibly unapplied.'),('no-false-success','No optimistic success is shown before server evidence.'),
  ('confirmation-current','Current diner confirmation uses current view separately from immutable successful create receipt.'),
  ('lookup-current','Owned lookup reflects applied seating and reassigned history with unchanged terms.'),('closure-explanation','Refusal wording is truthful for both closures and bookings.'),
  ('amend-real','Actual owner submits expected_revision/from_index/local_time through visible controls.'),
  ('amend-states','Result distinguishes changed/unchanged/cancelled/exception members with stable references.'),
  ('amend-failure','Failure never implies partial commit.'),('lost-apply','Commit-then-drop apply stays uncertain and unchanged retry recovers actual receipt.'),
  ('lost-amend','Commit-then-drop series amend stays uncertain and unchanged retry recovers actual receipt.'),
  ('malformed','Malformed committed response cannot manufacture success.'),('edited-identity','Real field edit changes request identity.'),
  ('unchanged-identity','Unchanged retry retains exact body/key.'),('plan-race','Delayed earlier preview cannot replace a newer preview/selection.'),
  ('agreement-race','Delayed series state cannot replace newer agreement/result.'),('mobile','Required real flows usable at 375 CSS pixels without horizontal scroll.'),
  ('desktop','Required real flows usable at conventional desktop width.'),('keyboard','Actual Tab/Enter/focus flows complete preview/apply/amend/recovery.'),
  ('labels','Human restaurant/table labels remain prominent including combinations.'),('contrast','Text/control contrast and visible focus remain sufficient.'),
  ('logout','Logout clears private manager/diner history/series views.'),('private','Manager cannot reveal another diner terms/history/series.'),
  ('offline','All assets/routes/scripts/styles work without outbound services.'),('upgrade-browser','Same document/form/user/body/key survives genuine earlier-source import and lost-response retry.')])}

TOKENS=[('null','null'),('boolean-true','true'),('boolean-false','false'),('string','"1"'),('array','[]'),('object','{}'),
        ('negative','-1'),('zero','0'),('fraction','1.5'),('tiny-fraction','1e-100000'),('large','1e100000'),('integral-decimal','1.0'),('integral-exponent','1e0')]

def cases():
    rows=[]
    def add(family,slug,text,line,params=None):
        rows.append(dict(requirement_id='TK4-'+family+'-'+slug,family=family,case=slug,requirement_text=text,
            source_section=GROUPS[family][1] if family in GROUPS else 'Stage1 §§5,7; Stage4 seating changes/recurring amendments',
            source_line=line,source_file='stage-4.md',introduced_stage=4,applicable_stages='4',
            implementation_owner='interface-engineer' if family=='product' else 'systems-engineer',
            verification_owner='independent-verifier',normative=True,parameters=params or {}))
    for family,(line,_,atoms) in GROUPS.items():
        for slug,text in atoms:add(family,slug,text,line)
    for field,line in [('expected_revision',80),('from_index',80)]:
        for name,literal in TOKENS:
            add('numeric',field+'-'+name,'Check exact JSON value/type and field-specific integer range: '+field+'='+literal,line,{'field':field,'literal':literal})
    for field,numbers in [('expected_revision',['9007199254740993.0','9007199254740993e0']),('from_index',['11','12','11.0','12.0'])]:
        for i,literal in enumerate(numbers):add('numeric',field+'-boundary-'+str(i),'Exact numeric boundary for '+field+'='+literal,80,{'field':field,'literal':literal})
    for i,value in enumerate(['00:00','23:59','24:00','1:00','01:0','01:00:00','01:00Z','01:00+00:00',' 01:00','01:00 ','02:60','-1:00','abc','']):
        add('time','clock-'+str(i),'Exactly bounded HH:MM local_time validation for '+repr(value),80,{'local_time':value})
    for endpoint in ['preview','apply','amend']:
        for slug in ['missing-key','empty-key','one-char','255-char','256-char','user-scope','path-scope','same-json',
          'numeric-alias','boolean-distinct','ignored-equality','different-before-validation','different-before-resource',
          'different-before-permission','array-order','object-order','failed-reusable','original-after-mutation','original-after-import']:
            # Different-body conflict precedes endpoint permission only AFTER successful authentication.
            add('retry',endpoint+'-'+slug,'Stage1 parsed-body user/method/path key semantics on '+endpoint+': '+slug,13 if endpoint=='preview' else 53 if endpoint=='apply' else 73,{'endpoint':endpoint,'rule':slug})
        for shape in ['array','object','alternating']:
            for depth in [1100,5000,10000,20000]:
                add('deep',endpoint+'-'+shape+'-'+str(depth),'Balanced ignored '+shape+' depth '+str(depth)+' accepted; exact full identity/replay/raw transfer retained.',13 if endpoint=='preview' else 53 if endpoint=='apply' else 73,{'endpoint':endpoint,'shape':shape,'depth':depth})
    for direction,side,digits in product(['from','to'],['before','equal','after'],[1,6,7,18,64]):
        add('instants',direction+'-'+side+'-'+str(digits),'Compare exact closure '+direction+' at '+side+' integer booking endpoint with '+str(digits)+' fractional digits; no rounding/truncation.',20,dict(field=direction,side=side,digits=digits))
    for event in ['create','patch','cancel','policy','batch','adopt','series-amend','apply','noop-patch','noop-batch','repeat-cancel','noop-series','empty-series','preview','failed-write','replay','other-restaurant']:
        add('staleness',event,'Saved preview stale status reflects exactly the specified restaurant counter effect of '+event,47,{'event':event})
    for dimension in ['tables','pairs','bookings']:
        for n in range(0,8):add('bounds',dimension+'-'+str(n),'Observe supported or explicitly permitted larger-input planning semantics for '+dimension+'='+str(n),24,{'dimension':dimension,'count':n})
    for constraint in ['closure-interval','closure-table','plan-restaurant','plan-assignment-reference','plan-rank','plan-applied-flag','plan-revision','series-schedule','series-exception','receipt-original']:
        add('private-state','invalid-'+constraint,'Independently derive invalid '+constraint+' state after genuine export; reject atomically without publishing raw private state.',107,{'constraint':constraint})
    return rows
