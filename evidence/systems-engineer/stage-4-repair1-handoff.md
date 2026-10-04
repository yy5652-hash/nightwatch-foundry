# Stage 4 REPAIR-1 — complete Systems builder handoff

**Own complete-image checks pass. Highest consecutive independently accepted stage remains 3; Stage 4 is unaccepted.** Final exact tested candidate and probe revision are **`969ee95ac1a7bb1d28ecf075f256b6eb4c32f6fb`**, Stage 4 tree **`00e208c746a488a9b4cb0761efd04b90c4248dd8`**. Source is held for the coordinator's complete new candidate package and fresh independent review. This report does not transfer observations to a later production tree.

## Intake, rejection, source and ownership

All 22 numbered parts and both END markers of `TK-20261004-S4-systems-engineer-REPAIR-1` were received and acknowledged before any repair work. Final-part inbound ID is `ff568c68-1e53-4c8e-9e9d-0b94e221ddce`; the reciprocal acknowledgement ID is unknown. Shared card 25 covers this assignment. The full task, participant guide, specifications 1–4, supplementary brief, four adopted decisions, historical builder handoffs and complete independent rejection/source reconciliation/failure observations were directly supplied. The authoritative room plan was read before repository inspection. [Repair design](stage-4-repair1-design.md) records the boundary and chronology.

The rejected full candidate is `261e4d9456a04a8b57ed46db71a09ac267ff15a9`, tree `501d27abab7226546da42edb1131ef8aa037deaf`. Independent substantive evidence is `16b6955aee3036298aaa81aa3533fe3536d44cff`, seal `a744fd0cbe3fa24399088d3e4dc8db960bf5c9f3`. Twelve present nonstring closure endpoint cases returned 422 instead of inherited 400. The independent candidate-1 official passes do not override that rejection, and are not observations against this repair.

| Identity | Full revision |
| --- | --- |
| Immutable accepted Stage 1 | `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b` |
| Immutable accepted Stage 2 | `4dba10246b07b2dda19de260d529f9d94ba0a1ed` |
| Immutable accepted Stage 3 | `91e2c471acded1b861b3fec725f202297b1c6740` |
| Independent Stage 3 acceptance | `315631a0565cbc671ba112842b452eb0b8624313` |
| Coordinator nine-file predecessor copy proof | `e11e2de5f7fb6452323d73a611fdd3bae11f4467` |
| Systems substantive Stage 4 implementation | `30e6b6edd6e6e061e5b3ff155b42261c9c97568a` |
| Interface substantive Stage 4 runtime/product | `83dccc909250800384d29d8d05d70a6cee383b6a` |
| Own new specification-derived closure protocol/reproducer | `d85a200927ae7e95ae2cc85a847c1c0d81a1080a` |
| One-line production repair | `6225a0e6f25afd28ceddac472887a77e5941bba5` |
| Exact complete tested candidate/protocol | `969ee95ac1a7bb1d28ecf075f256b6eb4c32f6fb` |

Only `stage-4/core.py` changes in production, one line against the rejected candidate. Codec and all seven Interface files are unchanged. All 24 frozen Stage 1–3 files remain identical. Explicit owned pathspec commits and exact author/path inspection preserve history. New support files and unique run folders are under Systems evidence; all original probes, reports and run folders remain unchanged. The final evidence seal is supplied in the room after inspection, avoiding a circular self-commit claim.

## Concrete repair and preserved failure

The inherited Stage 1 section 5 rule distinguishes wrong JSON types (400 `malformed_request`) from missing fields and correct-type invalid formats/values (422 `validation_failed`). Stage 4's invalid-interval rule supplies no nonstring override. The repair passes closure `from` and `to` through the existing `text_field` before unchanged `explicit_instant` parsing. Missing endpoints retain 422; null, booleans, numbers, arrays and objects now receive 400. Bad date/clock/offset strings, missing offsets, equal and reversed intervals retain 422. The earlier Systems 422 interpretation in [original handoff](stage-4-handoff.md) remains unchanged as an incorrect historical expectation, not a new adopted coordinator decision. The earlier source question is superseded by the explicit repair assignment and cumulative rule.

Idempotency still resolves after object parsing and authentication, before endpoint field/resource checks. Used-key body differences return 409 before field validation; successful replays retain original responses. Manager authentication and permission ordering remain intact. Wrong table types and malformed whole bodies retain 400. Failed keys remain reusable, and every failed request leaves the raw exported state byte-identical. Import's existing refusal boundary still turns invalid private replacements into 422 without committing. Exact rational fractions, closure spelling, parser grammar and occupancy ordering are unchanged.

Before editing production, [own reproduction](systems-engineer-s4-repair1-reproduction-01/runtime.json) executes actual HTTP against the retained rejected Systems image: **185 requests /197 assertions**, **24 failed status/code assertions across the twelve wrong-type cases**, all neighboring assertions passing. Runtime is **1.949479208 seconds**, protocol **0.188174417 seconds**, one own removal exits zero. Actual old packaged core hash matches the rejected commit. Network-none/2 CPU/2 GiB/no mounts are inspected. The HTTP client runs through docker exec inside the service's resource boundary; no separate constrained client or fresh build is claimed for this labelled reproduction. Original observations and executed bytes remain preserved.

## Complete current behavior and actual checks

The inherited RLock remains the read/write/retry/export/import transaction boundary. Planning retains every overlapping confirmed booking, supports six tables/four declared pairs/six considered bookings, and uses each booking's accepted capacities. Fixed bookings, simultaneous assignments, proposed closure and prior closures constrain options. The deterministic objective is changed table sets, exact unused seats, then reference-ordered option ranks. Pair order alone is unchanged. Preview stores a plan and receipt only; infeasibility changes nothing.

Apply retains manager/scoped-plan checks, successful-key replay first, already-applied precedence and restaurant-local stale revision. Closure and assignments commit together. Moved records gain one reassigned history/revision, unmoved records none; accepted identity/time/party/terms remain unchanged. Restaurant and affected series increment once, with original schedules and exceptions preserved. Operator repair ignores diner cutoffs. Closures affect availability/explanation and create/individual/batch/series occupancy. Other restaurants remain independent.

Series amendment retains exact revision/index/HH:MM checks, stale-before-member validation, original scheduled dates and current tables/party/identities. Cancelled and permanent-exception members are excluded. No-ops preserve terms/history/counters; real changes check old accepted cutoff before new policy validation. Index-ordered non-occupancy errors precede final combined occupancy validation. Every real member changes once, restaurant/agreement once, and no exceptions are set. Failure is atomic; empty/no-op success and original receipt replay remain stable. Private schema 4 accepts genuine schemas 1–3, preserving source-faithful missing histories/counters and modern receipts, plans, closures, schedules and histories. The public four-required-argument Engine and codec bytes boundaries, fixture manager declaration and absence of reservation-to-series linkage are unchanged. No public counter, clock, capability, role or list endpoint is invented.

| Fresh exact-current owning scope | Observed result | Seconds |
| --- | --- | ---: |
| New closure type/format/rollback/key/auth/precision HTTP regression | **185 requests /197 assertions, zero failed; all twelve type cases** | 0.199323459 |
| Full Stage 3 plus planning/series transition protocol | **34/34 scenarios, 2,077 operations /2,886 assertions; no failures/errors/skips** | 17.158900133 |
| Inherited combinations/member intervals/atomicity/concurrency | **11/11 scenarios**, 160 saved oracle operations, seed 20261004 | 1.867 |
| Inherited authentication/calendar/occupancy/original receipts | **15/15 scenarios**, no skips | 2.433 |
| Exact finite values/types/identity/ordering/genuine legacy profiles | **373 HTTP requests /1,773 assertions; 7/7 scenarios, zero failed** | 1.293253084 |
| 4,301-digit configuration/query/pair/retry/replacement | **92 operations /148 assertions, zero failed** | 0.551484001 |
| Deep cumulative receipts/raw replacement/races | **192 HTTP requests /821 assertions, zero failed; seven raw transfers** | 8.049363587 |
| Separately labelled packaged Engine with substituted diagnostic clock, **not HTTP** | **19 total Engine calls /30 assertions, passed** | 0.101786125 |
| Complete clone/build/seven-service/eight-client/cleanup driver | **All eight clients exit zero; no exception** | 167.219227042 |

Five counted wire clients total **2,919 requests/operations and 5,825 assertions**. This excludes uncounted inherited unittest traffic, startup/inspection and direct calls. Builder scenarios/assertions are not normative rows, official counts, hidden results or independent acceptance. Systems ran no official harness and observed no browser interaction or screenshot; Interface and verifier own those scopes.

The separate small Cartesian seating oracle freshly executes **45 saved constructions**, seed **202610044**, including full 6/4/6 bounds, fixed bookings and prior applied closures. It independently enumerates fixture options, accepted capacity and interval/set conflicts without production helpers. Accepted versus newer-policy capacities, canonical pair identity, read-only/infeasible preview, stale/already-applied precedence, empty/zero-move applications, affected-series counters, no-op/empty eligibility and nine atomic invalid modern replacements pass. Fifty identical applies produce one 201 and 49 original 200 receipts; competing series amendments permit one real success. Five fifty-client apply/read waves and diner-write/apply races observe complete serial states.

Real accepted Stage 1, 2 and 3 images issue sessions/hashes/references/original receipts. Stage 3 genuinely creates moved-date permanent exceptions and cancelled series members before export. Current amendment/repair and original retries work after unchanged transfer and mixed replacement through a peer. Legacy origins `49287b4a5a1481f995c470ccae31776f03d4b863` and `16aee9f0ea10de5b8fa81a84429cc337c3c4490f` preserve their real rounded numeric profiles and historic strings. There are **70 current transition raw-transfer traces**, plus seven separate deep transfers, with matching lengths/digests and decoded=false. This describes transfer bytes, not all private counter snapshots, which may be decoded only in memory. No old state, token, hash, lost numeric lexeme or receipt is fabricated.

New preview/apply/amend depth-20,000 ignored values, exact numeric aliases/boolean differences and original receipt recovery across replacement pass. The inherited deep scope retains balanced 10,000/20,000-depth receipts and 50-client waves. Largest measured deep request is **338,671 bytes**, maximum measured deep request **2.453612210 seconds**. Transition maximum measured HTTP is **0.074389167 seconds**. Both specified DST zones and first-occurrence/absolute-duration truth are exercised; the past-cutoff/no-op counter supplement is distinctly diagnostic Engine execution, not a public clock or successful past HTTP adoption.

## Runtime/source identity and reproduction

Current image: **`sha256:345ba1df8e7d5051797966564260bdd0da3660b3ffa29343129c21db0f46931d`**.

| Actual packaged module | SHA-256 |
| --- | --- |
| core.py | `9449cf0334c4ace4c688046eb42220e06c4ae9a4312e2b4551d0e6681f7f97d9` |
| json_codec.py | `3bf4c5dd7ccee1c99127d735822331fedb1491af3568d3490a81a092bae49501` |
| server.py | `9cbbb424a2b3207e94f9d7f4a5d19b3f4ea3005ca5842bb8c6ddd715e127884e` |

All nine committed context files build from the fresh clean detached exact clone. Context and actual packaged module hashes, genuine origins, sealed probe bytes and executed driver are recorded. Seven services and eight clients each have inspected **2 CPU/2 GiB/no mounts**, on an inspected internal offline network. Own host mappings are 18180–18186. Default 8080/override 18181 readiness upper bounds are **3.289928125 /3.262471000 seconds**, from launch to health-command return, before source inspection. Cross-container traffic establishes selected-port all-interface listening. Cache was available; uncached build and host-published reachability are not claimed.

All **sixteen fresh own service/client/network removals exit zero**; reproduction's one removal also exits zero: **seventeen repair removals**, separate from the 44 original Stage 4 removals. Own Stage 4 container namespace is empty. Temporary contexts are removed; images and the exact clean clone remain. Only own resources were stopped. Retained clone:

`/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/systems-engineer-s4r1-20261004t092055103743`

[Runtime](systems-engineer-s4-repair1-service-01/runtime.json) preserves all actual Git/build/Docker/client/health/source/cleanup argv, logs, statuses and timings. [Final source proof](stage-4-repair1-final-source-proof.json) binds all nine current bytes/modes/blobs, empty current graded diff, only core differing from the rejected candidate, immutable predecessors, clean retained clone and empty own namespace. Missing-codec lookups on genuinely old sources remain labelled source-absence diagnostics. From the absolute result root with new unique outputs and exact committed driver/probe blobs:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-4-repair1-container-check.py --revision 969ee95ac1a7bb1d28ecf075f256b6eb4c32f6fb --probe-revision 969ee95ac1a7bb1d28ecf075f256b6eb4c32f6fb --out evidence/systems-engineer/<new-owned-run>
../../.venv/bin/python -B evidence/systems-engineer/stage-4-repair1-evidence-audit.py --candidate 969ee95ac1a7bb1d28ecf075f256b6eb4c32f6fb --runs evidence/systems-engineer/systems-engineer-s4-repair1-reproduction-01 evidence/systems-engineer/<new-owned-run> --out evidence/systems-engineer/<new-owned-audit.json>
```

## Audit, preserved evidence and remaining gates

[Scoped repair audit](stage-4-repair1-evidence-audit.json) hashes **249 files**, inspects **8,409 saved JSON object records**, identifies **62 private fingerprints** and finds **zero raw private JSON payload findings**. Live tokens/hashes/exports remain in client memory. Scope is owned run-folder saved JSON only; source/log strings, later root report/ledger/proof files, peer artifacts and genuine room export are excluded. It binds the original failed reproduction separately from the repaired complete pass, resources/cleanup/source/clones/transfers and all 24 frozen files. Synthetic test passwords occur in authored fixture code. Final full-room secret review remains operator-controlled.

The earlier rejected candidate, old incorrect 422 interpretation, original Systems/Interface failures and all Stage 1–3 repairs/runner errors/shared-index attribution remain unchanged history. The repair's expected failing reproduction is not relabelled as a pass; the fresh complete run has different production and separate evidence. One read-only task-history CLI usage error is preserved in room tool history and corrected prospectively; it changed no source or task state.

All four adopted decisions remain explicit: exact IANA instant/original wall fields with nearest representable minute offsets and immutable genuine older seconds-offset strings; immutable original successful schema/body meaning; exact JSON values with genuine receipt-scoped old numeric comparison; semantic visible exact numeric controls. Literal historical offset grammars and native HTML type ambiguity remain disclosed. Empty earlier histories/revision-1/policy-0/private-counter-0 bootstrap is retained. Finite sizes, depths, exponents, histories and concurrency prove no arbitrary-workload fit, huge-output guarantee or complete accessibility certification. The closure type defect is repaired under the existing cumulative rule, with no new adopted interpretation.

Fresh driver UTC interval is **2026-10-04T09:20:55.103940+00:00 to 2026-10-04T09:23:42.323925+00:00**, measured **167.219227042 seconds**. Whole-factory elapsed belongs to the coordinator. Harness/configured model **Codex/gpt-6.1-sol**; actual override, effort, tokens, catalog-estimated cost and billed spend are **unknown**. Inputs were complete direct requirements/decisions/room plan, own accepted source/history and committed Interface runtime/assets. Supplied rejection identifies the defect; no verifier/official executable was copied or executed, and no external domain code/schema, memory, toy/abandoned repository, outside-workspace source or host installation was used.

Complete Interface current integration and a new acknowledged coordinator exact-candidate package/fresh independent review are required. Builder evidence cannot accept Stage 4. Source is held; genuine room export, operator README/FACTORY, public release and submission remain operator-controlled.
