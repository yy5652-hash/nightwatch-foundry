# Stage 2 Interface implementation and integration handoff

**Update 2026-10-04:** the large-integer boundary, exact visible status and
restaurant-local end-time repairs supersede the original candidate/counts below.
Current tested full revision is `87b816c63b59032e2bea6130a0b0308c47e9f6b0`:
**32/32 scenarios, 510 assertions PASS**. Scoped end-time report:
`stage-2-local-end-repair.md`. The separate 4301-digit core boundary is pending
Systems' committed repair and is not claimed verified by this run.
Original results and failures remain preserved. Independent acceptance is pending.

Interface implementation is complete for independent review. This is builder
evidence, not promotion or a hidden judging result. Highest consecutive accepted
stage remains 1 according to the coordinator's frozen manifest.

Final tested full revision: `1067ccd06d86145ca5ac9fcaedb9df3f404a6983`.
Last service change: `93544c6c0ec8ba1424af15a120e51415e49df3c9`.
The diagnostic/evidence revisions after that do not change the Stage 2 service.
The final room handoff supplies the full evidence-successor revision and verifies
the identical service tree. Frozen Stage 1 was compared byte-for-byte with
`2a4b0408a3453bc87d86bca3d0ec571f479e03ca` before every upgrade-source build.

## Authored surface

- `stage-2/server.py`: whitelist HTML routes and local CSS/JS assets, HEAD behavior,
  explicit content types, same-origin CSP and no-sniff response headers, while
  retaining the strict JSON adapter, case-insensitive headers, original target,
  concurrent HTTP server and single shared Engine.
- `stage-2/web/index.html`, `app.css`, `app.js`: original warm neutral/green/clay
  product; public search, declared pair options, signup/login/logout, persistent
  signed-in identity, confirmation, private lookup and authoritative cancellation.
  Visible labels/focus and responsive desktop/375px layouts; no later-stage controls.
- `Dockerfile`, `.dockerignore`, `RUN.md`: packaged offline browser assets and
  IANA data, standard-library service, fresh single-image launch instructions.
- Original probes, state map, provenance declaration, append-only ledger and every
  run artifact are outside graded folders under `evidence/interface-engineer/`.

Only these explicitly owned paths were edited/committed. Systems owns core.py;
its Stage 2 core was consumed through the unchanged Engine contract. Stage 1 was
never modified, copied backwards, or used as a later-stage browser surface.

## Behavior and review evidence

Final run directory:
`evidence/interface-engineer/interface-engineer-s2-20261004t015431148781z/`.
`runtime-report.json` records full candidate, all source and probe SHA-256 values,
container arguments/limits/internal network, image hashes, health checks, logs and
cleanup. `browser-report.json` records assertions, deterministic operation traces,
scenario verdicts and Chromium version. The image's Python/HTML/CSS/JS hashes
matched the committed candidate. Every owned container/network was removed;
seat-prefixed images remain for inspection. No host package was installed.

Observed final result: **15/15 scenarios PASS, no skips; 243 assertions; 13.945 s**.
Both default PORT=8080 and override PORT=9090 answered health. The override health
measurement includes starting three containers; exact timing is in runtime report.
All service and browser containers used 2 CPU/2 GiB and one internal network.

| Written requirement family | Original black-box observation |
|---|---|
| Stage 1 transport/runtime; Stage 2 routes | Direct HTML routes, local asset content types, strict invalid constants/nonobject refusal before auth, empty 204; public grid before login |
| Signup/login/navigation | Real signup refusal and success, login, display name on all four routes, logout; catalogue completion preserves typed credentials |
| Keyboard/mobile/product | Available cell activated with Enter; focus moves to labelled guest input; mobile Tab/Enter submits a real booking; 375/1440px no horizontal page scrolling |
| Competing search responses | A response held after real fetch; B completes and its form opens; A release cannot restore grid, table label, restaurant, party or form |
| Single and pair conflicts | Other user commits first; confirmed 409 shows booking-error, preserves selection/party, refreshes true availability and shows no confirmation/uncertainty |
| Uncertain single and pair writes | Real create commits, route drops response; only nonempty uncertainty appears; unchanged same body/key retry obtains exact original reference; another submit duplicates nothing |
| Changed form identity | Two unchanged dropped requests share body/key; genuine party change gets a different key and body; retry then succeeds authoritatively |
| Combined seating | Canonical declaration order, both labels in summary/confirmation/lookup; no transitive pair; both members atomically occupy and release |
| Lookup and refusal | Actual other-owner reference returns private refusal; delayed old lookup cannot restore detail after input changes; failed cutoff cancellation retains confirmed status/action |
| Genuine accepted Stage 1 upgrade | Browser assets use old Stage 1 API through a controlled routing proxy; old service issues token, retained reference, and lost-response booking. Its real export is imported into Stage 2 between requests; routing switches without reload/login/form edit. Same original table_id body/key recovers real original receipt without table_ids; retained reference works with existing token |
| Concurrent writes through final adapter | 50 identical pair requests: exactly one 201 and 49 identical 200 receipts. 50 competing keys: exactly one 201, 49 table_unavailable refusals; one persisted record and both members occupied at read |

The browser does not invent success from cached state. Its form retains the exact
request body/key; legacy singles use table_id and receipt presentation falls back
to table_id only when table_ids is absent. Search generations cover restaurant
detail and availability together. Failed or lost writes cannot create a cosmetic
confirmation. Friendly date formatting does not modify request timestamps.

## Screenshots reviewed

The final directory contains 35 genuine PNGs from the tested service. Examples:
`single-confirmation-desktop.png`, `mobile-keyboard-confirmed.png`,
`signup-labelled-mobile.png`, `cutoff-refusal-mobile.png`,
`combined-conflict-mobile.png`, `combined-uncertain-mobile.png`,
`legacy-uncertain-desktop.png`, `search-race-desktop.png`,
`closed-day-mobile.png` and `cancelled-lookup-desktop.png`.
Earlier screenshots and outputs remain in their original unique run folders.
Visual review confirmed coherent spacing/type/color, legible human table labels,
separate available/unavailable/selected/success/refusal/uncertainty states and
labelled controls. This is an Interface review; independent review remains separate.

## Exact reproducible commands

From the result repository:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-2-container-check.py
```

The script builds stage-2 and the verified frozen stage-1 source, starts two
nondefault/default API processes plus a default-port Stage 2 process, checks
source hashes/resources and runs the original probe inside the unchanged official
runner image. Every subprocess argv/log is retained in runtime-report.json. If the
official runner image is absent on a fresh review machine, build it from the
unchanged supplied `kickoff/harness/Dockerfile` and `requirements.txt` using tag
`df-harness-runner:latest`; no scored test source is used by these probes.

Python AST syntax checks passed for the adapter and both own probes. Fresh service
builds passed. The runtime driver rejects uncommitted graded source and compares
the accepted Stage 1 source before executing it. Official isolated harness checks,
inherited coverage-matrix review, independent named verdict and clean-clone
acceptance are coordinator/verifier work and remain pending for this handoff.

## Preserved diagnostics and repairs

- First run `interface-engineer-s2-20261004t014738019820z` is an ERROR: its host
  published-port health probe could not reach the service, while retained container
  logs showed listening. No service startup failure is inferred. Later runs use
  container loopback plus real internal-network browser requests. The original
  failure output and cleanup are retained unchanged.
- Catalogue-completion input stability (`be82cfd`) and pending lookup retry
  (`9f26892`) were repaired after code review and then exercised explicitly.
- Product refinements (`f1f348a`, `93544c6`) made dates and confirmed refusals
  readable without changing API bodies, receipt identities or exact status text.
- The first 50-race assertions passed, but the saved trace in
  `interface-engineer-s2-20261004t015346752119z` mislabeled competing counts as
  identical counts. Trace-only commit `1067ccd` separates both actual counters;
  the fresh final run passes and records both. No old output was edited into a pass.
- Earlier 12/12 and 14/14 runs remain recorded in the append-only ledger and Git.

## Assumptions and remaining risks

The complete supplied specification, acceptance brief and recorded historical
timestamp interpretation govern this implementation. Historical wire offsets
retain the coordinator's explicit minute-offset interpretation; exact instants
and original local fields are preserved, but literal historical subminute offsets
cannot be claimed simultaneously with RFC3339 minute grammar. Legacy successful
receipt strings remain immutable. No new interpretation was introduced here.

No reload/cross-tab synchronization/background polling recovery is required or
claimed. Browser memory retains the open form and retry identity through a
between-request upgrade. The migration probe honestly uses the Stage 2 browser
assets against genuine Stage 1 API/state before switching to Stage 2; Stage 1
itself has no browser requirement. There is no public demo/export/submission.

Harness: Codex. Operator-configured model: gpt-6.1-sol. Actual runtime model
override, effort, token usage, catalog estimate and billed spend are unknown.
Wall times, commands and commit provenance are measured in the append-only ledger;
no judging score or independent acceptance is inferred from these diagnostics.

## Large-integer boundary follow-up, 2026-10-04

Input: coordinator source-boundary note `d1526e98-31d9-44b4-953f-fcc84ba8076c`,
within the existing full Stage 2 package. No new external product/source or
verifier probe code was consulted. The original client already retained exact
plain-digit party queries, prefilled strings and emitted JSON numeric tokens.
The new independent builder probes expanded that boundary to fixture capacities,
pair sums, lookup counts, keyboard stepping and values beyond native float range.

Reproduction `e176224a7861f3b1a2396fdc51b559a1e3f40e8d` used the original graded
service tree. It passed 15/19 scenarios but exposed four new failures:
`9007199254740991` had a rounded pair sum; `9007199254740993` and `10^30+1`
had rounded/exponent-form capacity and lookup labels; native Chromium number
input cleared `10^400+1` before submission. For the finite cases the exact query,
prefill, request JSON number and unchanged body/key were already correct.
Preserved artifacts: `interface-engineer-s2-20261004t020049436891z/`.

Repair `496f996af35ec1d2545cc93c3d5dc617f9e815c2` validates response JSON syntax
before scanning tokens, retains unsafe plain integer tokens as exact decimal
strings inside the browser, leaves quoted text untouched, and sums table capacities
with BigInt. This changes neither the API wire value/type nor any submitted
request/receipt. MAX_SAFE_INTEGER selects an internal representation, never a
party-size limit. That image passed 18/19 scenarios; the native input limitation
remained. Its failure is retained in `interface-engineer-s2-20261004t020238327614z/`.

Repair `78ace90ad6022e534f4c78003d883de98d47e883` uses exact-decimal numeric
controls: text storage with numeric input mode, labelled spinbutton semantics,
visible increment/decrement controls, exact arrow-key stepping and a minimum of
one. It adds no upper cap. The published UI calls for Number/Number input without
prescribing an HTML type; Interface explicitly interprets that as a semantic
numeric control rather than an unbounded native float control. This interpretation
was posted to coordinator and remains subject to independent review; no coordinator
approval is invented. The control retains actual DOM input values, not mocked
getters or hidden substitute values. Both required test IDs remain on the real
visible editable numeric field. Server validation/limits remain authoritative.

Final tested full revision `8035394fd718d4a99d7a1b934304e7761304a26f` includes
RUN instructions and stronger accessible-value/keyboard assertions. Stage 2 tree:
`045c05f05e57556048e2c8e2ed4faad6ee748ff5`. No core.py, server.py, Dockerfile,
Stage 1 or other seat's implementation was changed in this follow-up.

Observed final result: **20/20 scenarios PASS, no skips; 359 assertions; 15.964 s**.
All previous 15 scenarios are rerun, including genuine Stage 1 recovery and 50-client
pair races. New cases independently check `9007199254740991`, `9007199254740993`,
`10^30+1` and `10^400+1`: exact plain query, exact prefill, integer JSON body,
unchanged key/body replay, exact single capacity, exact pair sum, exact lookup
guest count, quoted numeric label preservation, spinbutton/input-mode semantics,
accessible value and exact keyboard increments/decrements. A real committed response
is deliberately corrupted with an invalid unquoted numeric key; it remains uncertain
and recovers the original reference on an unchanged retry. Invalid JSON is never
made valid by the exact-integer scanner.

Final directory: `evidence/interface-engineer/interface-engineer-s2-20261004t020650125411z/`.
It retains candidate/probe/source hashes, 43 genuine screenshots, seeded traces,
complete commands and resource/startup/cleanup evidence. Image source hashes match
the committed candidate; default and override PORT succeed, override healthy
measurement is 3.434 s. All service/browser containers run at 2 CPU/2 GiB on an
internal network. Own containers/networks are removed; images retained. Desktop
and 375px large-count views have no horizontal page scrolling. The original
20/20 intermediate run remains in `interface-engineer-s2-20261004t020457946050z/`;
the final run replaces its loosely labelled lookup-element assertion with real
numeric-field role/mode/value/keyboard checks rather than claiming that old
assertion proved those properties.

Reproduce with the unchanged command above. Append-only ledger records every
failure/repair/run separately. Highest accepted stage remains 1; the numeric-control
interpretation, independent named review, official isolated regressions and
clean-clone acceptance remain review gates. Historical timestamp interpretation
and actual model/effort/spend unknowns are unchanged.
