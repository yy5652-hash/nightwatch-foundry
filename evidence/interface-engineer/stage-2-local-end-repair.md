# Stage 2 restaurant-local end-time repair

Builder diagnostics within the complete active Stage 2 package, not independent
acceptance. The separate 4301-digit boundary awaits Systems' committed startup
repair and must not be inferred passing from the tested 401-digit cases.

## Preserved observations and changes

Input: verifier room message `fb310a7a-3ab1-4ac8-9371-ee23fd7884db`. No verifier
probe code was read. An original browser probe compared real HTTP lookup records
and visible text against a separate Python zoneinfo instant-to-local oracle. Its
browser timezone was Pacific/Honolulu, detecting accidental browser-local conversion.

Reproduction revision `a6a513969077269aa50cbe1c973c485a6a0dd6c0` passed 27/29
scenarios, no skips, with 457 assertions attempted in 21.342 seconds. Berlin and
Brussels year 0001 showed wire-clock 19:29 rather than restaurant-local 19:30.
New York historical, both named zones' spring/fall transitions and the last
calendar date passed. Output remains in `interface-engineer-s2-20261004t022440093346z/`.

Production repair `9445466c94423891832ae7a02eaa173b6ce3c870` changes only
stage-2/web/app.js. Lookup parses the exact RFC3339 instant, including immutable
older offset-seconds strings, and formats in the explicit restaurant IANA zone.
UTC calendar construction avoids JavaScript's two-digit-year constructor rule.
Original starts_at_local, raw ends_at in the time element, API records, receipts,
body/key identities and frozen Stage 1 remain unchanged. An unavailable conversion
shows a truthful unavailable label rather than labelling the wire clock local.

After adding three real historical-source imports, revision
`947d449c3fb9b5184d7cc6ae438b0f76dfe237aa` passed 29/32 scenarios, 483 assertions
attempted, 22.044 seconds. The three failures were a probe bug: following a
successful 200 original-receipt replay, it checked that variable against reset's
204 status. The preceding real token/create/export/import/replay checks passed.
This diagnostic error is preserved in `interface-engineer-s2-20261004t022648176418z/`.
Probe-only repair `87b816c63b59032e2bea6130a0b0308c47e9f6b0` separates the reset
assertion from the legacy branch; no production edit followed it.

## Final exact-image result

Tested full candidate: `87b816c63b59032e2bea6130a0b0308c47e9f6b0`.
Command from the result repository:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-2-container-check.py
```

**32/32 scenarios PASS, no skips, 510 assertions, 23.213 seconds.** Final artifacts
are in `interface-engineer-s2-20261004t022744592128z/`: 69 real screenshots, source/
probe/image hashes, full revision, traces, commands, health, limits and cleanup.
Current Brussels mobile and legacy Berlin desktop screenshots were inspected.

| Preserved API timestamp | Restaurant zone | Displayed end |
|---|---|---|
| 0001-01-01T19:29:32+00:53 | Europe/Berlin | 19:30 |
| 0001-01-01T19:29:30+00:17 | Europe/Brussels | 19:30 |
| 0001-01-01T19:30:02-04:56 | America/New_York | 19:30 |
| 2026-10-25T03:00:00+01:00 | Europe/Berlin | 03:00 |
| 2026-11-01T02:00:00-05:00 | America/New_York | 02:00 |
| 2026-03-29T04:00:00+02:00 | Europe/Berlin | 04:00 |
| 2026-03-08T04:00:00-04:00 | America/New_York | 04:00 |
| 9999-12-31T19:30:00+00:00 | UTC | 19:30 |

A genuine separately built Stage 1 at
`49287b4a5a1481f995c470ccae31776f03d4b863` issued three real tokens/bookings
and original +00:53:28, +00:17:30 and -04:56:02 timestamp strings. Unchanged HTTP
exports imported into Stage 2; original tokens and successful receipts replayed
exactly. Actual lookup retained those strings and displayed 19:30 in all three
zones. Nothing was mocked; exports stayed in memory. Old core/server hashes
matched the named source; the temporary historical context was removed.

All previous 21 scenarios passed again: strict transport, exact status, counts
through 401 digits, malformed-response uncertainty, genuine accepted Stage 1
browser upgrade, conflicts/search race, keyboard/mobile and 50-request pair races.
Four service processes plus browser each used 2 CPU/2 GiB on an Interface-owned
internal offline network. Host mappings remained 18210/18211. Default 8080 and
override 9090 health passed; override measured 3.589 seconds including four starts.
All owned containers/network/context were removed; images remain. No host installs
or outside-workspace access. Frozen Stage 1 matched its accepted bytes before build.

## Review boundary

Interface Stage 2 production edits are frozen pending independent review.
Systems' separate 4301-digit core change is not part of the tested source and
requires a new committed integrated run. The numeric-control interpretation and
independent verdict remain promotion gates. Historical transport-offset and
immutable old-string exceptions remain explicit; this UI correction does not alter
the API decision. No Stage 2 acceptance or Stage 3 work is claimed.

All outcomes and the probe mistake/repair are append-only in ledger.jsonl/Git.
Harness Codex; configured gpt-6.1-sol; actual override/effort/usage/spend unknown.
Fresh-clone and official isolated/inherited checks remain independently required.
