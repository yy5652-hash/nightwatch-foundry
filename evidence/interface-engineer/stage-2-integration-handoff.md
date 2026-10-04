# Stage 2 Interface implementation and integration handoff

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
