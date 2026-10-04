"""Stage 3 atomic obligations derived from the complete published specifications.

Case records are prospective requirements, never an executed candidate result.
Owners reflect the direct assignment. No builder or shipped-test source is used.
"""
S1 = '75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
S2 = '4dba10246b07b2dda19de260d529f9d94ba0a1ed'
FREEZE = 'a7ef75573233fbf4652b56d6609e14d82d21594c'
PACKAGE = 'TK-20261004-S3-independent-verifier-INITIAL-1'
SEED = 202610063

# A family identifies a prepared protocol. Source line names the first normative
# sentence; clauses and independently chosen parameter cases stay separate.
ATOMS = {
 'explain': (9, 'Availability explanations', [
  ('omitted','Without explain, no slot explanation fields are present; inherited Stage 2 options remain.'),
  ('true','Literal explain=true adds explanations to every returned slot.'),
  ('closed','A closed day returns slots=[] with explain=true.'),
  ('empty-slot','An open slot with no available single remains with complete explanations.'),
  ('table-completeness','Every restaurant table occurs exactly once in each explanation.'),
  ('table-order','Explanation tables occur in fixture order.'),
  ('rule-completeness','Both capacity and no_overlap rules occur for every table.'),
  ('rule-order','Rules occur in capacity then no_overlap order.'),
  ('boolean-types','available and holds are JSON booleans.'),
  ('conjunction','available equals the conjunction of the independently evaluated rules.'),
  ('ids-order','The available explanation IDs equal available_table_ids in order.'),
  ('policy-version','Every explanation identifies the policy selected for that local date.'),
  ('new-grid','Published selected policy supplies the slot grid.'),
  ('new-duration','Published selected policy supplies slot duration and overlap interval.'),
  ('pair-members','Occupancy from a pair causes no_overlap=false for each occupied member.'),
  ('cancel-frees','Cancellation restores no_overlap for all members.'),
  ('half-open','Adjacent absolute intervals do not report overlap.'),
 ]),
 'policies': (94, 'Policies and accepted terms', [
  ('manager-allowed','Only a fixture manager can publish a complete policy.'),
  ('non-manager','An authenticated non-manager receives 403 forbidden.'),
  ('default-managers','Omitting manager_user_ids grants no publishing permission.'),
  ('unknown-restaurant','A manager requesting an unknown restaurant receives 404 not_found.'),
  ('no-token','Policy publication without authentication receives 401 unauthenticated.'),
  ('role-ignored','An ignored signup/body role cannot grant policy permission.'),
  ('restaurant-scoped','Managing one restaurant grants no publishing right at another.'),
  ('first-version','The first accepted policy has integer policy_version=1.'),
  ('contiguous-version','Each later accepted publication increases its restaurant version by one.'),
  ('independent-version','Versions are allocated independently for each restaurant.'),
  ('complete-not-patch','Every required complete-policy field is necessary.'),
  ('supplied-response','Publication returns supplied policy fields plus policy_version.'),
  ('public-list','GET policies works without a token.'),
  ('list-order','GET policies returns publication order, independent of effective dates.'),
  ('omit-zero','GET policies omits policy 0.'),
  ('unknown-list','Public policy list for an unknown restaurant gives 404 not_found.'),
  ('original-detail','Ordinary restaurant detail retains the original fixture configuration.'),
  ('immutable-policy','Subsequent publication or booking mutation cannot change older policies.'),
  ('unknown-fields','Unknown policy body fields are ignored for validation.'),
  ('fixed-labels','Unknown policy label changes do not modify restaurant labels.'),
  ('fixed-tables','Policies cannot modify existing table IDs.'),
  ('fixed-zone','Unknown policy timezone does not modify the restaurant timezone.'),
  ('fixed-pairs','Unknown combinable field does not modify declared pairs.'),
  ('policy-zero','Before all applicable effective dates, use original fixture policy 0.'),
  ('inclusive-date','A policy is eligible on its effective_from local date.'),
  ('out-of-order','Select greatest eligible effective_from despite publication order.'),
  ('same-date-tie','Select greatest policy_version among policies with the selected effective date.'),
  ('future-ineligible','A policy effective after the local booking date cannot be selected.'),
  ('backdated','A valid backdated publication succeeds without changing accepted bookings.'),
  ('local-not-utc','Selection uses the restaurant local booking date rather than the UTC date.'),
  ('existing-record','Publication leaves existing reservation values unchanged.'),
  ('existing-end','Publication leaves existing absolute end times unchanged.'),
  ('existing-history','Publication leaves every existing history entry unchanged.'),
  ('failed-version','An invalid policy allocates no version.'),
  ('failed-state','An invalid policy changes no observable state.'),
 ]),
 'history': (53, 'Reservation history; Policies and accepted terms; Combined-table history', [
  ('created-event','New creation has one created event.'),
  ('seq-start','The first history seq is 1.'),
  ('seq-contiguous','History seq increments exactly one per real event.'),
  ('seq-order','Entries are returned in seq order.'),
  ('at-order','History timestamps are nondecreasing, including same-second writes.'),
  ('at-format','Every history at is RFC3339 with an explicit numeric offset.'),
  ('created-fields','A singleton created event contains table_id, starts_at_local, party_size in that order.'),
  ('created-from','Every created change has from=null.'),
  ('created-values','Created to values equal the reservation accepted at creation.'),
  ('changed-only','A changed event contains only fields that actually changed.'),
  ('changed-order','Changed fields are ordered seating, starts_at_local, party_size.'),
  ('old-from','Changed from values equal the preceding reservation state.'),
  ('new-to','Changed to values equal the resulting reservation state.'),
  ('no-op-entry','No-op PATCH succeeds without a history event.'),
  ('failure-entry','A failed amendment produces no event.'),
  ('replay-entry','A successful create replay produces no event.'),
  ('cancel-empty','The cancelled event has an empty changes array.'),
  ('cancel-terminal','No history event follows cancellation.'),
  ('repeat-cancel','Repeated cancel creates no event.'),
  ('cancel-retained','Cancelled reservation history remains readable by its owner.'),
  ('revision-event','Every entry carries its resulting reservation revision.'),
  ('terms-event','Every entry carries complete resulting accepted_terms.'),
  ('historic-terms','Older entries retain their original terms after amendments/publications.'),
  ('pair-created','Pair creation uses table_ids from null to the complete canonical pair.'),
  ('single-change','Single-to-single history retains table_id representation.'),
  ('single-to-pair','Single-to-pair change uses complete before/after table_ids lists.'),
  ('pair-to-single','Pair-to-single change uses complete before/after table_ids lists.'),
  ('pair-to-pair','Pair-to-pair change uses complete before/after canonical table_ids lists.'),
  ('reversed-noop','Reversing a declared pair alone changes no history.'),
 ]),
 'terms': (136, 'Policies and accepted terms', [
  ('create-revision','New reservations have revision=1.'),
  ('seed-revision','Seeded reservations have revision=1.'),
  ('seed-zero','Seeded reservations accept policy 0.'),
  ('terms-complete','Accepted terms contain the entire selected policy rules and all capacities.'),
  ('terms-no-date','Accepted terms exclude effective_from.'),
  ('lookup-current','Current owned lookup includes revision and accepted_terms.'),
  ('list-current','Current owned reservation list includes revision and accepted_terms.'),
  ('cancel-current','Cancellation responses include current revision and accepted_terms.'),
  ('patch-current','Amendment responses include current revision and accepted_terms.'),
  ('moves-current','Every current batch response member includes revision and accepted_terms.'),
  ('pair-capacity','A combination uses selected policy capacities, not original/latest unrelated capacities.'),
  ('decision-current','Decision returns reference, current revision and accepted_terms.'),
  ('decision-cancelled','Decision remains readable after cancellation.'),
  ('old-cutoff','Cancel checks accepted cutoff against the current reservation start.'),
  ('amend-old-first','A real amendment checks old accepted cutoff before new-field validation.'),
  ('amend-all-fields','A real amendment validates all resulting fields against the resulting date policy.'),
  ('amend-new-terms','A real amendment replaces accepted terms with the resulting date policy.'),
  ('amend-new-end','A real amendment recalculates absolute end from new accepted duration.'),
  ('amend-revision-once','A real multi-field amendment increments revision once.'),
  ('amend-atomic','Failure preserves record, terms, end, history and occupancy.'),
  ('noop-terms','No-op retains accepted terms even if newer policies apply.'),
  ('noop-end','No-op retains end time.'),
  ('noop-revision','No-op retains revision.'),
  ('noop-editable','No-op still requires confirmed status and old cutoff editability.'),
  ('cancel-once','First cancellation increments reservation revision once.'),
  ('cancel-repeat-revision','Repeated cancellation retains revision and current state.'),
  ('expected-optional','Omitting expected_revision retains ordinary amendment semantics.'),
  ('expected-match','A matching positive expected_revision permits ordinary validation.'),
  ('expected-stale','A positive mismatching expected_revision gives 409 stale_revision.'),
  ('stale-before-cutoff','Stale revision takes precedence over cutoff_passed.'),
  ('stale-before-fields','Stale revision takes precedence over invalid resulting fields.'),
  ('expected-noop','No-op with matching revision succeeds without increments.'),
  ('expected-noop-stale','No-op with stale revision is refused before cutoff/field validation.'),
  ('concurrent-revision','Two concurrent changes with one revision allow at most one real success.'),
  ('unknown-patch','Unknown PATCH fields remain ignored and do not turn a no-op into a real change.'),
 ]),
 'series': (168, 'Recurring reservations', [
  ('adopts-anchor','POST series adopts an existing anchor rather than creating a replacement.'),
  ('owned-confirmed','A confirmed owned editable anchor can be adopted.'),
  ('unknown-anchor','An unknown anchor gives 404 not_found.'),
  ('other-owner','Another owner anchor gives 404 not_found.'),
  ('cancelled-anchor','A cancelled anchor gives 409 reservation_cancelled.'),
  ('already-adopted','An already adopted anchor gives 409 already_in_series.'),
  ('cutoff-anchor','The accepted anchor cutoff applies before adoption.'),
  ('no-token','POST series without authentication gives 401 unauthenticated.'),
  ('anchor-ref','Occurrence zero retains anchor reference.'),
  ('anchor-id','Occurrence zero retains anchor reservation identity.'),
  ('anchor-revision','Adoption retains anchor revision.'),
  ('anchor-terms','Adoption retains anchor accepted terms.'),
  ('anchor-history','Adoption retains anchor history.'),
  ('anchor-times','Adoption retains anchor start, end and created timestamps.'),
  ('anchor-receipt','Adoption retains the immutable original anchor receipt.'),
  ('calendar-dates','Generated dates use local date plus i*interval_weeks*7 calendar days.'),
  ('same-clock','Every generated occurrence retains the anchor local clock time.'),
  ('own-policy','Each generated occurrence selects its own local date policy.'),
  ('own-duration','Each generated occurrence has its selected absolute duration.'),
  ('own-capacity','Each generated occurrence obeys its selected capacity.'),
  ('own-opening','Each generated occurrence obeys its selected opening/grid rules.'),
  ('own-party','Generated occurrences retain anchor party size.'),
  ('own-seating','Generated occurrences retain anchor declared canonical seating.'),
  ('dst-gap','A nonexistent generated local time rejects the entire adoption.'),
  ('dst-fold','Repeated generated local time uses the first occurrence.'),
  ('absolute-duration','Generated duration is absolute across DST transitions.'),
  ('first-failure','The first failing occurrence in index order determines the ordinary booking error.'),
  ('rollback-reservations','Failed adoption leaves all reservations unchanged.'),
  ('rollback-histories','Failed adoption creates no history.'),
  ('rollback-series','Failed adoption creates no partial series.'),
  ('rollback-counters','Failed adoption increments no restaurant or series counter.'),
  ('rollback-key','Failed adoption leaves its key reusable.'),
  ('response-status','First successful adoption returns 201.'),
  ('response-id','Series ID is an opaque nonempty string within inherited ID length.'),
  ('response-revision','New series revision is 1.'),
  ('response-interval','Series response retains interval_weeks.'),
  ('response-count','Occurrences includes all count members.'),
  ('response-order','Occurrence indices are 0..count-1 in order.'),
  ('distinct-reference','All occurrences have distinct ordinary valid references.'),
  ('initial-exceptions','Every newly adopted occurrence has exception=false.'),
  ('ordinary-list','Occurrences appear in the ordinary owned reservation list.'),
  ('ordinary-occupancy','All confirmed occurrence members occupy their tables.'),
  ('ordinary-history','Every generated occurrence has ordinary creation history.'),
  ('get-current','Owned series GET returns current reservation states.'),
  ('stable-references','Individual date/table edits preserve occurrence references and indices.'),
  ('patch-exception','A real individual amendment marks that occurrence exception=true.'),
  ('permanent-exception','Changing an occurrence back never removes its exception flag.'),
  ('patch-series-once','A real individual amendment increments series revision once.'),
  ('noop-series','A no-op amendment changes no exception or series revision.'),
  ('failed-series','A failed amendment changes no exception or series revision.'),
  ('cancel-series-once','First cancellation increments series revision once.'),
  ('cancel-keeps-member','Cancellation retains the occurrence with cancelled current state.'),
  ('cancel-no-exception','Cancellation of a nonexception occurrence does not mark an exception.'),
  ('cancel-keeps-exception','Cancellation cannot erase an already permanent exception.'),
  ('repeat-cancel-series','Repeated cancellation changes no series revision.'),
  ('anchor-cancel-siblings','Cancelling the anchor leaves all siblings confirmed and occupied.'),
  ('adopt-restaurant-once','Successful adoption increments restaurant revision once for the whole operation.'),
  ('unknown-fields','Unknown series fields are ignored for validation.'),
 ]),
 'moves': (230, 'Collective moves under policies and agreements', [
  ('old-cutoff','Each real move checks the booking old accepted cutoff.'),
  ('new-policy','Each real move adopts its resulting local date policy.'),
  ('all-fields','Each real move validates all resulting fields under that policy.'),
  ('optional-revision','Omitted per-move expected_revision retains ordinary semantics.'),
  ('stale-priority','Per-move stale revision precedes that member cutoff and change validation.'),
  ('input-order','Nonoccupancy errors are resolved in move input order.'),
  ('noop-retains','Unchanged member retains terms, history, revision and occupancy.'),
  ('changed-revision','Each really changed member gains exactly one revision.'),
  ('changed-event','Each really changed member gains exactly one changed history event.'),
  ('restaurant-once','A successful real multi-member batch increments restaurant revision once.'),
  ('series-once','Several changed members of one series increment that series revision once.'),
  ('multiple-series','A batch increments each affected series once, unrelated series none.'),
  ('exception-changed','Each changed series occurrence becomes a permanent exception.'),
  ('exception-noop','An unchanged series member retains its exception flag.'),
  ('failure-records','Any batch failure leaves every reservation record and occupancy unchanged.'),
  ('failure-terms','Any batch failure leaves accepted terms and end times unchanged.'),
  ('failure-histories','Any batch failure leaves every history unchanged.'),
  ('failure-revisions','Any batch failure increments no booking, restaurant or series revision.'),
  ('failure-exceptions','Any batch failure changes no exception flag.'),
  ('failure-key','A rejected batch leaves its key reusable.'),
  ('replay-counters','Batch replay changes no revisions, history or exceptions.'),
  ('swap-atomic','Pair/single swaps validate all resulting occupancy together.'),
  ('unlisted-occupancy','An overlapping unlisted booking still prevents a batch.'),
  ('no-partial-read','Concurrent readers observe complete states consistent with a serial ordering.'),
 ]),
 'upgrade': (216, 'Recurring reservations; Stage1 §10; Stage2 Existing clients after an upgrade', [
  ('s1-source','Genuine accepted Stage 1 independently issues accounts, sessions, references and original receipts.'),
  ('s2-source','Genuine accepted Stage 2 independently issues single/pair and batch receipts.'),
  ('raw-transfer','Unchanged source HTTP export replaces a separate Stage 3 process.'),
  ('replacement','Import removes previous destination credentials and data rather than merging.'),
  ('sessions','Existing multiple bearer tokens remain valid.'),
  ('passwords','Imported password hashes still permit real login.'),
  ('references','Imported confirmed/cancelled references and identities survive.'),
  ('adoption','Imported confirmed owned reservations can be adopted as series anchors.'),
  ('original-body','Imported original complete parsed body retains source validation meaning.'),
  ('original-shape','Earlier successful receipts retain their original response schema.'),
  ('original-create','Original create retries still return the unchanged receipt after adoption/edit/cancel.'),
  ('original-moves','Original batch retries still return the unchanged receipt after later mutations.'),
  ('mixed-exact','New Stage 3 exact-profile receipts coexist with genuine imported old receipts.'),
  ('second-transfer','A real mixed Stage 3 export replaces another independent process unchanged.'),
  ('second-replay','Original and new receipts retain profiles and values after second replacement.'),
  ('history-roundtrip','Stage 3 histories, accepted terms, revisions and exceptions survive replacement.'),
  ('policies-roundtrip','Published immutable policies and their order survive replacement.'),
  ('series-roundtrip','Series identity, indices, cancelled members and permanent exceptions survive replacement.'),
  ('repeat-import','Repeating unchanged import restores the snapshot without duplicate records.'),
  ('invalid-atomic','Invalid import refuses without changing all current state.'),
  ('reset-clear','Reset removes imported policies, series, receipts, sessions and reservations.'),
 ]),
 'browser': (89, 'Existing screens; supplementary PRODUCT_ACCEPTANCE Stage3 and App-score interaction ownership', [
  ('inherited-grid','Actual availability grid continues inherited Stage 2 truthful selection/recovery behavior.'),
  ('accepted-terms','Own confirmation/lookup displays actual accepted booking terms clearly.'),
  ('historic-changes','Own lookup renders actual historical changes and older accepted terms truthfully.'),
  ('cancelled-history','Cancelled owned booking still displays actual history/terms.'),
  ('series-adopt','Existing owned booking can be adopted by the real recurring-booking UI.'),
  ('series-occurrences','A legible occurrence list preserves actual original references and order.'),
  ('series-cancelled','Occurrence view distinguishes cancelled members.'),
  ('series-exception','Occurrence view distinguishes permanent exceptions.'),
  ('manager-privacy','Manager UI cannot display another diner private booking/history/decision/series.'),
  ('no-fake-data','Terms, history and agreement displays use actual API responses, with no mocked facts.'),
  ('no-later-controls','Stage 3 UI offers only declared Stage 3 capabilities.'),
  ('failure-atomic','A failed adoption or amendment never implies partial success in the view.'),
  ('uncertain-recovery','Real committed-drop/malformed response recovery remains truthful for bookings in the enhanced UI.'),
  ('s1-browser-upgrade','Real Stage 1 API/current assets bridge imports between unchanged browser requests.'),
  ('s2-browser-upgrade','Real Stage 2 browser login/form/reference/retry survives upgrade without reload.'),
 ])
}

def cases():
    records=[]
    def add(family,name,text,line=None,parameters=None,owner='systems-engineer',source=None):
        base_line,section,_=ATOMS[family]
        records.append(dict(id='TK3-'+family+'-'+name,family=family,name=name,text=text,
            line=line or base_line,section=source or section,parameters=parameters or {},owner=owner))
    for family,(line,section,atoms) in ATOMS.items():
        for name,text in atoms:
            add(family,name,text,owner='interface-engineer' if family=='browser' else 'systems-engineer')
    for value in ['false','1','','TRUE','True','0','yes','true ',' true','null','true,false']:
        add('explain','invalid-'+str(len(records)), 'explain='+repr(value)+' gives 422 validation_failed.',24,{'explain':value})
    for cap,overlap in [(True,True),(True,False),(False,True),(False,False)]:
        add('explain','truth-'+str(int(cap))+str(int(overlap)),
            'Both rules independently report capacity='+str(cap)+' and no_overlap='+str(overlap)+'.',44,{'capacity':cap,'no_overlap':overlap})
    # Exact value-based boundaries. The token is saved as a string in the test
    # description; the later request inserts it as a JSON NUMBER, never a string.
    boundaries={
      'slot_minutes':(1,1440),'reservation_duration_minutes':(1,1440),
      'cancellation_cutoff_minutes':(0,10080),'capacity':(1,100),
      'count':(2,12),'interval_weeks':(1,4),'expected_revision':(1,None)}
    wrong=[('boolean','true'),('string','"1"'),('null','null'),('array','[]'),('object','{}'),('fraction','1.5')]
    for field,(low,high) in boundaries.items():
        fam='policies' if field in ('slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','capacity') else ('series' if field in ('count','interval_weeks') else 'terms')
        for label,token in [('minimum',str(low)),('minimum-decimal',str(low)+'.0'),('minimum-exponent',str(low)+'e0')]+([('maximum',str(high)),('maximum-decimal',str(high)+'.0')] if high is not None else []):
            add(fam,field+'-'+label,'Integral '+field+'='+token+' is type/range-valid (other constraints still apply).',124 if fam=='policies' else 180 if fam=='series' else 157,
                {'field':field,'token':token,'value_valid':True})
        invalid=wrong+[('below-minimum',str(low-1)),('negative','-1')]+([('above-maximum',str(high+1)),('huge','1e100000')] if high is not None else [('zero','0')])
        for label,token in invalid:
            add(fam,field+'-'+label,field+'='+token+' gives 422 validation_failed with no state/counter change.',124 if fam=='policies' else 180 if fam=='series' else 157,
                {'field':field,'token':token,'value_valid':False})
    for field in ['effective_from','slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','opening_hours','capacities']:
        add('policies','missing-'+field,'Missing '+field+' gives 422 with no policy/version/state change.',124,{'missing':field})
    for date in ['2035-02-29','2035-13-01','2035-00-01','2035-06-31','35-06-01','2035-6-01','2035-06-01T00:00','2035-06-01Z','0000-01-01','10000-01-01','']:
        add('policies','date-'+str(len(records)),'Invalid effective_from '+repr(date)+' gives 422 validation_failed.',124,{'date':date})
    for label,change in [
      ('missing-table',{'capacities_mode':'missing'}),('extra-table',{'capacities_mode':'extra'}),
      ('wrong-id',{'capacities_mode':'replace'}),('duplicate-weekday',{'opening_mode':'duplicate'}),
      ('unknown-weekday',{'opening_mode':'unknown'}),('overnight',{'opening_mode':'overnight'}),
      ('equal-clock',{'opening_mode':'equal'}),('clock-format',{'opening_mode':'format'}),
      ('hours-object',{'opening_mode':'object'}),('capacities-array',{'capacities_mode':'array'})]:
        add('policies','shape-'+label,'Invalid complete policy '+label+' is 422 with no mutation.',124,change)
    for endpoint in ['history','decision','series']:
        for caller in ['owner','other-diner','manager','no-token','malformed-token','unknown-token']:
            add('history' if endpoint=='history' else 'terms' if endpoint=='decision' else 'series',
                'privacy-'+endpoint+'-'+caller,
                endpoint+' for '+caller+' gives '+('200 for owned existing record.' if caller=='owner' else '404 not_found, revealing no existence.'),
                59 if endpoint=='history' else 162 if endpoint=='decision' else 204,{'endpoint':endpoint,'caller':caller})
    for path in ['policies','series']:
        for label in ['missing-key','empty-key','key-256','same-body-order','same-body-numeric-alias','different-body-priority','failure-key-reuse','scoped-user','scoped-path','concurrent50','replay-after-mutation','replay-after-import']:
            add(path,path+'-retry-'+label,'Inherited Stage1 §7 retry rule '+label+' applies to the new '+path+' write path.',101 if path=='policies' else 170,
                {'retry_case':label},source='Stage1 §7; '+ATOMS[path][1])
    for field in ['expected_revision']:
        for label,token in wrong+[('zero','0'),('negative','-1')]:
            add('moves','per-move-'+field+'-'+label,'Invalid per-move expected_revision='+token+' gives 422 before mutation.',232,{'field':field,'token':token,'value_valid':False})
    for scenario in ['capacity','grid','closed','outside','gap','occupied-single','occupied-pair','first-capacity-second-gap','first-gap-second-occupied']:
        for rollback in ['records','history','series','versions','key']:
            add('series','reject-'+scenario+'-'+rollback,'Failed '+scenario+' occurrence chooses first indexed error and preserves '+rollback+'.',183,
                {'scenario':scenario,'rollback':rollback})
    for zone,day,clock in [('Europe/Berlin','2026-03-29','02:30'),('Europe/Berlin','2026-10-25','02:30'),
        ('America/New_York','2026-03-08','02:30'),('America/New_York','2026-11-01','01:30')]:
        for property_name in ['local-calendar','policy-date','first-fold-or-gap','absolute-end','rollback-or-commit']:
            add('series','calendar-'+zone.replace('/','-')+'-'+day+'-'+property_name,'Generated '+zone+' '+day+'T'+clock+' obeys '+property_name+'.',183,
                {'zone':zone,'date':day,'clock':clock,'property':property_name})
    for event in ['create','patch','cancel','moves','policy','series']:
        for observable in ['lookup','list','history','decision','availability','raw-export']:
            add('moves','concurrency-'+event+'-'+observable,'Concurrent '+event+' and '+observable+' produce a complete legal serial observation.',230,
                {'operation':event,'read':observable},source='Stage2 Concurrent bookings and amendments; Stage3 history/policies/series/collective moves')
    for scenario in ['terms-history','series-list','cancelled-exception','refused-adoption','uncertain-retry','upgrade']:
        for width in [375,1280]:
            for criterion in ['truthful-text','keyboard-focus','visible-labels','no-page-scroll','contrast','real-screenshot']:
                add('browser',scenario+'-'+str(width)+'-'+criterion,'Real '+scenario+' at '+str(width)+' CSS px satisfies '+criterion+'.',89,
                    {'scenario':scenario,'width':width,'criterion':criterion},owner='interface-engineer')
    for origin in ['accepted-s1','accepted-s2','legacy-s1','legacy-s2']:
        for criterion in ['real-source','token','create-receipt','moves-receipt','numeric-profile','public-shape','adoption','second-import','cancelled-state','failed-key']:
            add('upgrade',origin+'-'+criterion,'Genuine '+origin+' upgrade preserves '+criterion+' with unchanged raw snapshots.',216,{'origin':origin,'criterion':criterion})
    for path in ['policies','series']:
        for shape in ['array','object','alternating']:
            for depth in [1100,5000,10000,20000]:
                for criterion in ['strict-grammar','numeric-alias','typed-difference','original-replay','raw-import']:
                    add(path,'deep-'+shape+'-'+str(depth)+'-'+criterion,'New '+path+' receipt with ignored balanced '+shape+' depth '+str(depth)+' preserves '+criterion+'.',101 if path=='policies' else 170,
                        {'shape':shape,'depth':depth,'criterion':criterion},source='Stage1 §§3.4,5,7,10; Stage3 '+ATOMS[path][1])
    return records
