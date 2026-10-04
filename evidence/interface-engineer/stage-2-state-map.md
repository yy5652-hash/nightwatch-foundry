# Stage 2 browser state and integration map

Package: TK-20261004-S2-interface-engineer-IMPLEMENT-1, six complete parts and END.
Accepted/frozen Stage 1 source: `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`.
Systems copies the complete folder before any Interface Stage 2 service edit;
coordinator confirmation is required. Core ownership remains with Systems.

## Observable outcomes

| Flow / state | Feedback and invariant | Recovery |
|---|---|---|
| Restaurant loading | Labelled controls and visible loading status; no invented restaurants | Explicit retry after load failure |
| No restaurants | Considered empty state; browse remains public | Reload list explicitly |
| Search normal | Snapshot restaurant/date/party; matching labels and grid from one winning generation | Select an available single or declared pair |
| Search loading | Busy state; new manual search clears prior booking context | Monotonic generation ignores obsolete success/error/detail responses |
| Closed/no slots | `no-slots` replaces grid | Choose another day |
| Slots, no available single | Every single cell retains truthful data-available=false | Unavailable click does nothing; never manufactures capacity/occupancy success |
| Combined seating | Available declared pairs only, canonical API order, both human labels | Both members remain one request/selection |
| Signed-out selection | Auth error with login/signup route; no successful booking | Sign in using real API; preserve same-page selection where useful |
| Auth validation/refusal | `auth-error` exists only for the actual error | Correct input/retry; every signed-in route shows real accepted display name |
| Booking selected | Labelled party input and complete local time/table summary | Actual field change rotates parsed-body request identity |
| Booking submitting | One disabled submit while awaiting response; no optimistic confirmation | Wait for authoritative response |
| Booking success/replay | Form stays; exact reference from real response; errors/uncertainty absent | Unchanged submit retains key and body, even after success |
| Occupancy 409 | `booking-error`; selected form/inputs retained; availability refreshed | Change choice or retry as appropriate; no confirmation |
| Confirmed refusal | Nonempty booking-error; no new confirmation | Correct inputs; meaningful real changes get a new key |
| Lost/invalid/5xx response | Nonempty booking-uncertain only; body/key retained; no refusal/success claim | Exact unchanged retry recovers original reference |
| Changed uncertain form | New request identity; preserve honest notice about the prior uncertain attempt | New submission is a distinct booking request |
| Lookup loading | Reference stays visible; stale lookup responses ignored | Latest requested reference wins |
| Lookup found | Exact confirmed/cancelled status; complete table labels | Cancel uses authoritative server state |
| Lookup unavailable/refused | `reservation-error`, including owner-protected 404 | Correct reference or authentication |
| Cancel pending/failure | No optimistic cancelled state; current detail remains | Retry stable cancel; cutoff refusal remains visible |
| Cancel success | Exact cancelled status; cancel button absent | Next explicit availability search sees actual release |
| Imported upgrade | Existing token, retained form and original pending body/key survive between requests | Genuine Stage 1 export/import; no reload or regenerated receipt |

## Client and transport boundaries

- Same-origin packaged HTML/CSS/JS; direct `/`, `/signup`, `/login`, `/lookup`
  return HTML. JSON API adapter and one Engine remain intact.
- Session-scoped identity supports route navigation. Form/request state remains
  in the current browser runtime; no cross-tab synchronization or polling.
- Singles keep the supported legacy `table_id` body. Declared combinations use
  `table_ids`. Old successful receipts retain `table_id` fallback in presentation;
  the client does not rewrite original request bodies or successful JSON receipts.
- Pending request stores a parsed-value fingerprint, exact body and stable key.
  A real data change rotates identity; an unchanged retry never regenerates it.
- UI text comes from actual fixture/API data, inserted safely. No fake restaurant
  reviews, images, demand metrics, manager access or later-stage controls.
- Visible focus, labelled native controls, restrained warm neutral/green/clay
  hierarchy, complete keyboard flow, desktop and 375px without page overflow.

## Evidence strategy

Own deterministic black-box browser scenarios will delay search A, finish B,
then release A; race a booking against another client; commit a request then drop
its response; record unchanged/changed request identities; exercise declared pairs,
signup/login/logout, lookup/cancel and genuine accepted Stage 1 migration while
the same page remains open. Screenshot and keyboard evidence will cover desktop
and 375px. Source hashes and exact committed service revisions identify each build.
Independent acceptance remains separate from builder integration evidence.
