# Tablekeeper acceptance brief — task-specific, never a seat mandate

Source: official kickoff `803560d2a678ace1414465c098eb0ab5380ffade`,
`docs/participant-guide.md` and all four `tablekeeper/spec/stage-N.md` files.
This is an operator-authored acceptance brief, not implementation or scored evidence.
The complete official specifications prevail over this summary. Seats must derive
their own exhaustive requirement ledger and code in the submitted Band room.

## Target and evidence standard

The target remains four consecutive, fully implemented stages, a polished product,
and a reproducible autonomous factory. The public claim threshold is not our
quality target. Public test percentages or a passing public suite do not establish
hidden-test coverage, a judging score, or a prize.

Every claimed behavior needs a requirement reference, candidate full commit,
independent executable probe or observed UI flow, command, result and artifact path.
Record `unverified` when any link is missing. Never manufacture a rejection.
Tests belong outside graded stage folders unless genuinely needed by the service.
Do not modify the official checker, omit suites, or convert skipped checks to passes.

## Stage 1 — transaction and state foundations

| Requirement family | Independent acceptance evidence beyond a happy path |
|---|---|
| Runtime | Fresh single-image build; nondefault PORT; 0.0.0.0 listener; health within 60 s; 2 CPU/2 GiB; no runtime internet or separate database service. |
| Authentication | Hashed passwords; multiple active tokens; public browsing without token; owner-only reference lookup cannot reveal another account's booking. |
| Validation | Distinguish wrong JSON types from invalid values; reject boolean party sizes; strictly parse decimal query integers and bare local timestamps; ignore unknown fields. |
| Retry semantics | Same user+method+path+parsed JSON replays original response with 200; exactly one concurrent first request returns 201; same key on another path remains independent; different body conflicts before resource validation; failed keys remain reusable. |
| Occupancy | Half-open boundaries; 50 competing requests; no double booking or partial mutation; capacity and grid constraints; closed-day and empty-slot ordering. |
| Time | IANA rules, nonexistent local times, first occurrence in a repeated hour, absolute duration across transitions; do not reject dates merely because they are in the past. |
| Amend/cancel | Cutoff measured against current start; failed amendment leaves old occupancy intact; repeated cancel is stable; reference and identity survive edits. |
| Batch moves | 1..8 distinct references; same owner/restaurant; validate non-occupancy errors in input order before overlap; swap several occupied tables atomically; failed batch leaves receipts and every record unchanged. |
| Export/import | Atomic replacement across independent processes; preserve hashes, tokens, identities, timestamps, successful original receipts and cancelled records; invalid import is all-or-nothing; reset removes all imported state. |

Do not add the later browser or policy/series surfaces to this folder. Copy the
accepted stage forward; never copy a final answer backwards.

## Stage 2 — product experience and uncertain outcomes

Product direction: a warm, calm hospitality product. Use a consistent type scale,
warm neutral surfaces, a restrained accent, clear labels, and human table names.
This is a direction, not a reference design to reproduce. Do not invent reviews,
ratings, restaurant photos, usage counts, or claims about real establishments.
All assets/fonts/scripts must be packaged for offline runtime.

| Required flow | Evidence to capture |
|---|---|
| Browse before login | `/` is useful without authentication; restaurant, date, party size and table choices are legible; booking routes to authentication. |
| Authentication routes | `/signup`, `/login`, `/lookup` load directly; visible labels and focus; signed-in identity visible on all screens; logout state works. |
| Search race | Delay A, complete B, then release A: grid, labels and form remain B, not stale A. |
| Booking conflict | Another client takes the selected option: show refusal, refresh availability, retain form inputs, and never show a false confirmation. |
| Lost response | Commit then drop response: show uncertainty, not refusal/success; retry identical body/key and recover the original reference; another submit after success creates no duplicate. |
| Changed form | A real field change creates a new request identity; an unchanged form retains the same retry identity. |
| Combined seating | Only declared pairs, never transitive combinations; canonical declared order; atomically occupy/release both tables; show both human labels. |
| Upgrade in place | Import a stage-1 export between browser requests: login token, open form, retained reference and uncertain retry still work without a reload. |
| Responsive/accessibility | Real screenshots and keyboard flows at 375 CSS px and desktop; no horizontal page scroll; distinct loading, empty, available, unavailable, selected, success, refusal and uncertainty states. |

Required test IDs are a contract, not a substitute for product-quality review.
Verify text-only constraints (reference and reservation status) precisely.
The Experience Engineer must contribute substantive UI/recovery code and evidence,
not only cosmetic changes after another seat built the entire app.

## Stage 3 — immutable terms, history and recurring agreements

| Risk | Required independent probe |
|---|---|
| Explanation truth | Both capacity and overlap rules reported for each table in fixture order; validate explain=true only; no extra explanation fields when omitted. |
| Policy ordering | Publish effective dates out of order and ties on the same date; select by local booking date then version; preserve existing bookings and immutable historic terms. |
| Manager boundary | Only fixture managers publish; managers do not gain private diner lookup/history access; ordinary restaurant detail remains original fixture configuration. |
| Revision/history | Contiguous seq; exact changed fields/order; no-op/replay/failure creates no event; accepted terms are snapshotted on each historical event; optimistic revision conflicts precede cutoff validation. |
| Receipt longevity | Replay an old create/policy receipt after amendments and cancellation and after import: original body, revision and terms survive. |
| Series adoption | Anchor remains identical; each future occurrence uses its own local date's policy and DST resolution; any failed occurrence rolls back every reservation/history/counter/key. |
| Series exceptions | Real individual change permanently marks exception; cancellation retains occurrence but does not create exception; anchor cancellation does not cancel siblings. |
| Combined history | Pair sets canonicalized; reverse input order alone is a no-op; single/pair transitions use the specified field representation. |
| Batch and series counters | Several changed members in one transaction increment each affected series once and restaurant once; failed batches/replays increment nothing. |
| Cross-version import | Independently export from both earlier stages and adopt imported reservations; preserve sessions and original receipts. |

## Stage 4 — deterministic planning and atomic application

1. Exercise the full supported bound: six tables, four declared pairs, six considered
   bookings, with fixed bookings and existing closures present.
2. Build an independent small exhaustive oracle from the written planning objective:
   minimize changed booking sets, then total unused seats, then the rank vector in
   reference order. Do not use the production solver as its own oracle.
3. Use each booking's accepted capacities, not the latest policy's capacities.
   Preserve its identity, time, party size, owner and accepted terms.
4. Preview must not reserve occupancy, publish closure, increment revision or write
   booking history. Infeasible preview must leave all observable state unchanged.
5. Any intervening revision in that restaurant invalidates a plan; unrelated
   restaurants do not. Replaying a successful apply returns its original receipt;
   a different key for an already applied plan has its specified error.
6. Concurrent applies cannot partially move bookings. Moved records get one revision
   and reassigned event, unmoved records none; restaurant changes once per plan.
7. Bulk series amendments exclude cancelled/exception members and use original
   scheduled dates. Validate the series revision before member cutoff/validation;
   apply occupancy across changed and unchanged members together.
8. Empty eligible/no-op series changes succeed without incrementing revisions.
   A seating repair preserves exception flags and increments each affected series once.
9. Import populated states from every prior stage, including changed/cancelled series
   members, and repeat these operations without losing tokens, receipts or history.

## App-score interaction ownership

The stage-3 and stage-4 specs say no new screens are required. The following are
our product-quality targets, not organizer eligibility requirements. Implement
them only in their applicable stage after core correctness, without changing the
specified API or delaying required regression/upgrade coverage. Experience owns
substantive UI/integration work alongside Systems rather than only a final skin.

- In stage 3, make the existing diner's own confirmation/lookup flow explain
  accepted terms and historical changes clearly. Offer recurring-booking creation
  and a legible occurrence list with cancelled and exception states. Never expose
  another diner's private lookup/history to a manager.
- In stage 4, provide a manager-authorized closure preview/apply workflow showing
  proposed changes separately from committed changes. A stale or infeasible plan
  must remain visibly unapplied; never display optimistic success before evidence.
  Keep diners' lookup/confirmation synchronized with actual applied assignments.
- Make series amendment results distinguish changed, unchanged, cancelled and
  exception occurrences. Preserve original references in the view; show failures
  without implying that a partial operation committed.
- Use actual API responses and declared capabilities only. No mocked manager
  access, fake history, fabricated metrics, or later-stage controls in an earlier
  folder. Capture the real authorized and refused flows in the independent review.

## Promotion and presentation

- Freeze each accepted stage at its full revision before the next copy. Keep every
  applicable public check green as the working target, plus independent spec probes.
- Every stage must claim its own number in isolated mode; the next-suite probe must
  not establish a later stage in an earlier folder. Never intentionally break a
  requirement merely to fail an overshoot probe.
- Use clean clones, no nested Git repositories, submodules, escaping symlinks or
  host-specific runtime dependencies. Preserve failed outputs in unique directories.
- Capture real Band handoffs, a real independent verdict, actual product interactions,
  upgrade/retry recovery and final stage results. Label rehearsal separately.
- Do not publish exported fixture state with tokens/password hashes as a demo asset.
  Inspect the genuine full room export for secrets before public release; follow the
  official rotate-and-redact exception if one is found, never invent room events.
- Include measured elapsed time and catalog-estimated cost only with provenance;
  distinguish estimates from billed spend. Unknown is preferable to an invented value.
