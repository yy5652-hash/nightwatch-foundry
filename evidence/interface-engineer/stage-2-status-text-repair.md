# Stage 2 exact visible status repair

This is builder evidence within the complete Stage 2 package, not an independent
verdict or promotion. The coordinator and verifier retain all earlier observations.
Highest consecutive accepted stage remains 1. No Stage 3 work was started.

Input: verifier room message `20f901a8-f8e1-40f9-8485-c912e3037e6b` described an
older candidate's DOM text as `confirmed`/`cancelled`, with CSS displaying title
case. I authored a separate browser probe without reading verifier probe code.
It creates a real booking, opens private lookup, cancels it through the real API,
and captures both states at 1440px and 375px before asserting either text value.

## Preserved reproduction and repair

Reproduction revision: `c4944c0b71bb0b442e067f563e424889c11c9743`.
Its Stage 2 service was unchanged from the preceding repaired large-integer
candidate. The newly committed probe reproduced lowercase textContent but
`Confirmed`/`Cancelled` innerText and computed `text-transform: capitalize` in all
four observations. The complete diagnostic run passed 20/21 scenarios, no skips,
with 372 assertions attempted in 16.977 seconds. The one failing scenario is the
new visible-status check; all original 20 scenarios passed. Four status screenshots
and the complete trace are retained in
`interface-engineer-s2-20261004t021527073226z/`.

Repair and tested full revision: `71de2e326dc3d96c495a8c4df64f0130f13ce95c`.
The sole production change replaces `text-transform: capitalize` with `none` on
the `.status` badge in `stage-2/web/app.css`. It leaves colors, shape, labels,
layout, API, core, timestamps, request identities and all original receipts intact.
No interpretation of invisible versus visible text is needed after this repair.

## Exact-image checks

From the result repository, for both independently built candidates:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-2-container-check.py
```

The fresh repaired run passed **21/21 scenarios, no skips, 379 assertions in
17.340 seconds**. Both textContent and innerText equal `confirmed` or `cancelled`
exactly at both widths, with computed transformation `none`. No horizontal page
scrolling was observed. There are 47 genuine screenshots in the final run; the
confirmed mobile and cancelled desktop status captures were inspected visually.
All prior search-race, single/pair conflict, commit-then-drop retry, original
Stage 1 receipt upgrade, 50-request concurrency, exact large-integer display/body
and malformed-response uncertainty scenarios passed again.

Final artifacts: `interface-engineer-s2-20261004t021620623514z/`.
`runtime-report.json` records the full tested revision, source/probe SHA-256,
image hash matches, every command, resource settings, network, health and cleanup.
`browser-report.json` records all scenario results and the four exact status
observations. Default 8080 and nondefault 9090 health checks passed; the measured
override health time was 3.418 seconds, including three container starts.
Each service and browser used 2 CPU/2 GiB on the seat-owned internal offline
network. No host packages were installed. All owned containers and the network
were removed; build images remain. Browser: Chromium 153.0.8010.12 in the unchanged
official dependency runner. Frozen Stage 1 still matches its accepted revision.

## Remaining gates and provenance

The large-integer representation/control repair remains included unchanged.
The semantic exact-decimal Number-control interpretation still requires the
coordinator's published decision and independent final verification; this report
does not manufacture that approval. The historical timestamp decision and
immutable legacy-string exception remain disclosed in the main handoff.

The complete repaired candidate must receive independent exact-revision review,
official isolated Stage 2 plus inherited regression, and clean-clone acceptance.
Builder pass counts are scenarios/assertions, not normative requirement coverage
or a judging result. Harness: Codex. Operator-configured model: gpt-6.1-sol.
Actual runtime model override, effort, usage and spend are unknown. Wall times,
commands and both genuine outcomes are appended to the evidence ledger.
