# Stage 4 Interface state map

Complete TK-20261004-S4-interface-engineer-INITIAL-1, all 19 parts and both END markers, was acknowledged before Phase A. Own exact copy ec8de75a0ae6c23bc50e8cf18ed6011072d9aed1 extends accepted Stage3 91e2c471acded1b861b3fec725f202297b1c6740 only after coordinator nine-file proof e11e2de5f7fb6452323d73a611fdd3bae11f4467 and release 4a91cc84-8403-48b7-af5c-39c754714e92. Highest accepted stage3; Stage4 unaccepted. This is implementation design, not an executed behavior claim.

## Real manager closure flow

The manager route is an offline HTML route over the same authenticated session. The restaurant comes from the real public catalogue/detail. Fixture manager_user_ids and actual current user_id determine whether to offer a write form; every submitted write is still server-authoritative. There is no role signup or capability endpoint. Permissions never grant diner lookup/history access.

| State | Product | Protocol and identity |
| --- | --- | --- |
| Signed out / non-manager / empty catalogue | Sign-in guidance, selected-restaurant permission refusal, or empty catalogue; no invented manager access | Public detail only; missing manager list means no declared managers |
| Loading restaurant A then B | Label/table selector reflects only B | Independent generation and auth epoch guard |
| Preview idle | Real table selection plus complete explicit-offset interval strings | Exact original string values; no browser timezone conversion or fractional truncation |
| Preview loading | Form disabled; no proposed or committed move claim | POST replans with retained body/key |
| Preview refused | Explain actual stale/validation/planning-limit/no-feasible/auth/not-found refusal; no apply action | Failed key remains reusable when the unchanged body later succeeds |
| Preview uncertain / malformed response | Nonempty uncertainty; no proposal or apply affordance | Same unchanged body/key retry recovers original plan |
| Preview successful | Clearly proposed, unapplied assignments in server reference order, human labels, moved_count/unused_seats and declared-option ranks | Preserve original preview response; preview creates no UI claim of closure or movement |
| Apply loading / uncertain | Proposal remains visibly unapplied; uncertainty never treated as refusal or success | Same plan path and exact {} body/key retry |
| Apply refused | Proposal visibly unapplied, no committed-reservation panel | stale_plan requires a fresh preview; plan_already_applied never fabricated as own successful receipt |
| Apply success / original replay | Original successful application snapshot separate from fresh current owner views | Original apply receipt immutable; refresh public availability and own current confirmation/lookup/remembered series independently |
| Form genuinely edited | New request identity; warn if previous outcome uncertain | Clear old proposal/action, preserve any original receipt separately in its original attempt object |

No manager request fetches another diner's private history. Actual apply-response reservations may be shown because this is the specified authorized manager response. A no_overlap failure is labelled a generic seating conflict: the API does not distinguish a booking from a closure.

## Real owner recurring amendment

Use the actual GET-series response and server-issued series_id. There is no series-list endpoint and ordinary reservations need not carry series linkage. Keep same-document remembered agreement IDs, stable occurrence references, current cancellation/exception flags and the agreement's own restaurant labels.

| State | Product | Protocol and identity |
| --- | --- | --- |
| Current list ready | Visible current revision, from-index and local HH:MM inputs, original-date guidance | expected_revision captured for this attempt; from_index bounded by actual count |
| Loading / uncertain | Disable current attempt during request; uncertainty says the entire operation may have succeeded | Retain complete expected_revision/from_index/local_time body/key and baseline snapshot |
| Refused | No partial-success claim or success receipt | Actual stale revision before cutoff/booking refusal; explicit load/current-revision action starts a new attempt |
| Success / replay | Original result distinguishes changed, unchanged, before-index, cancelled and permanent-exception members, with stable references | Original POST result immutable; fresh GET list is current, separately labelled |
| No-op / empty eligible set | Successful result honestly says zero changed | No client-invented revision increments |
| A read/write finishes after agreement B | B remains current with its own labels/form | Agreement-read generation, form object identity, reference and auth guards |
| Real field/revision edit | New body/key, uncertain prior-outcome notice when applicable | Server is authoritative; no synthetic partial update |

## Inheritance, runtime and evidence

Preserve every accepted Stage1–3 API/browser contract, strict shared UTF8 bytes adapter, exact mathematical numeric responses/control/query/body values, opaque URI/Unicode IDs, human canonical labels, direct routes, signed-in identity/logout, search/lookup/agreement race suppression, retained booking/retry identities, historical IANA local end presentation, terms/history truth and raw earlier-version migrations. Original booking/series success receipts never acquire later fields or current assignments.

New Stage4 history presents real reassigned entries and actual plan_id without rewriting accepted terms. Current confirmation is loaded separately from its original successful booking receipt. Closure wording remains truthful for both bookings and closures. No mock role, unavailable API, fake historical event or optimistic success is introduced.

Own complete driver will clean-clone a named integrated source, build the entire context, bind packaged hashes, run default/override ports with2CPU/2GiB/no mounts/internal offline network, execute all60 inherited scenarios plus independently authored Stage4 flows at375px/desktop, genuinely export/import earlier Stage1–3 processes during retained sessions/forms/retries, save checkpoints/screenshots/counts and inspect startup/cleanup. Own runtime prefix interface-engineer and ports18200–18299 only. All attempts preserved in unique owned folders; no aggregate claims after a stopped runner.

All four adopted timestamp/receipt/numeric/control interpretations and the truthful empty earlier-history/revision1/policy0/counter0 bootstrap apply. Finite samples/visual checks do not prove arbitrary workload performance/full WCAG/hidden judging. Configured Codex/gpt-6.1-sol; actual override, effort, usage and estimated/billed spend unknown. Complete named independent acceptance remains a separate verifier gate.
