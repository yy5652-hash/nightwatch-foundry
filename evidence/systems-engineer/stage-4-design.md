# Stage 4 Systems transaction and planning design

Complete acknowledged package: `TK-20261004-S4-systems-engineer-INITIAL-1`, nineteen parts plus END. Phase A source is frozen Stage 3 `91e2c471acded1b861b3fec725f202297b1c6740`; own copy `418d2270ec31bbfbb50276f80908d99b38c0a3c7`, complete nine-file coordinator proof `e11e2de5f7fb6452323d73a611fdd3bae11f4467`, release message `f38dea86-6a23-4a18-8afb-586744a904b7`. Only current core/codec and owned evidence are Systems paths. All frozen predecessor and Interface paths remain untouched.

## Transaction boundary

The inherited RLock covers authentication, complete parsed-body retry resolution, policy/booking/closure reads, candidate preparation, receipt snapshots and commit. New POST paths join the same user/method/path/key namespace; a successful retry precedes permission/resource/revision/field checks and returns its original JSON. A failed request claims nothing. Prepared responses/history entries detach before mutation. No public counter, role, clock or capability endpoint is added.

## Exact closure intervals

New closure timestamps accept explicit-offset RFC3339 calendar strings, retaining the original strings. Decimal fractional seconds are represented internally by exact integer ratios of microseconds, never binary floats or truncated datetime fractions. Booking instants remain inherited exact integer microseconds and compare directly to those ratios. Half-open intersections apply to the proposed interval, existing closures and booking intervals. Old historical second-offset booking strings remain immutable; their existing interpretation is unchanged.

## Deterministic plans

Consider all confirmed restaurant bookings intersecting the proposed time interval, sorted by reference, including ones not currently using the closing table. Support the published six tables/four pairs/six considered bound. Each candidate option uses the booking's accepted capacity map, canonical member set, original interval and fixed bookings. Reject options intersecting the proposed or prior closure and precompute pairwise incompatibilities. Search all feasible assignments with admissible bounds, minimizing changed member-set count, then exact total unused seats, then the fixture-option rank vector in reference order. Bounds must never prune a possibly better objective.

Preview stores only a detached plan and successful original receipt. It changes no closure, occupancy, booking/series/restaurant revision or history. Infeasible/invalid/limit refusals change nothing. Apply checks manager, restaurant-scoped plan, already-applied before stale status, then the captured restaurant revision. Prepare every resulting record and `reassigned` history before atomically installing assignments and closure. Changed records increment once, unchanged records retain values; restaurant increments once even if nobody moves; each affected agreement increments once without altering exceptions or schedules. Any restaurant write invalidates its previews; unrelated restaurants remain independent.

## Series amendments

Validate owner and complete bounded expected_revision/from_index/local_time, then stale series revision before member cutoff/booking checks. Eligible occurrences are confirmed and not exceptions at or after from_index. Build their requested wall time on each original scheduled date, keeping current table selection, party and reference. Identical resulting fields are no-ops, bypassing real-change cutoff and new-policy adoption. Real changes use inherited old-cutoff then selected-date policy semantics. Validate all non-occupancy errors in index order before one final occupancy check including unchanged occurrences/bookings and closures. Commit all histories/records and one agreement/restaurant counter change; never mark a series amendment as an exception. Empty/no-op operations succeed without counters. Simultaneous expected-revision changes serialize under the same lock.

## Export compatibility

Private schema 4 adds plans/closures to the accepted schema-3 state. Schema 1–3 imports bootstrap these new collections empty while preserving real earlier profiles, original receipt shapes, terms/history, current assignments, cancellations, exceptions and schedules. Earlier missing-history revision-1/policy-0/counter-0 interpretation remains inherited; no past event is fabricated. Schema-4 import validates closure/plan identities and assignments, reassigned histories, new successful receipts and original series schedules atomically. Historical receipts and histories are checked under their original terms, independently of today's occupancy or closures.

Own verification will use a separately derived exhaustive small oracle, full bound and fixed/previous closure cases, fractional endpoint controls, counter/rollback/retry/races, genuine unmodified Stage 1–3 processes and raw unchanged state transfer. All tests/evidence stay outside graded folders. Builder passes do not accept Stage 4. Four adopted decisions remain explicit. Configured Codex/gpt-6.1-sol; actual override, effort, tokens and spend unknown.
