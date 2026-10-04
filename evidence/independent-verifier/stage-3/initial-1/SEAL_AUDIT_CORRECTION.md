# Preserved preparation seal audit correction

The first scoped seal invocation returned **1**, before staging or committing:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-3/seal_initial1.py --out evidence/independent-verifier/stage-3/initial-1/seal-01 --commit
```

Observed exception: `AssertionError` at `assert not findings and not whitespace`. Command wall time reported by the execution tool was **0.278468166 seconds**. [Failure record](seal-01/FAILED_AUDIT.json) and [exact original audit source](seal-01/source-preservation/seal_initial1.py) remain unchanged. No Git stage/commit, HTTP, browser, image, production or credential operation occurred before the stop.

A narrow diagnostic found **220 fields**, all under `/by_id/TK3-…/parameters/token` in the two prepared `cases.json` files. These hold declared JSON number/type boundary literals such as `-1`, `0`, `1.5`, `true` and `{}`. The original scanner treated their key name `token` as sufficient evidence of a session credential. **No unexpected raw credential was observed.** Authored whitespace findings were zero.

The new scanner classifies only those exact case-file locations whose literal values equal the independently declared case inventory. It records their fingerprints and classification separately. Any other unexpected private field still fails. No test vector or original result is rewritten. A new unique seal run must establish the correction; the original stopped audit remains a failed verifier audit, not a service failure or a pass.
