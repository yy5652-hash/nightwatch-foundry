# Stage 2 candidate 2 — concrete visual evidence links

Independent verdict **accept** remains against exact full candidate `4dba10246b07b2dda19de260d529f9d94ba0a1ed`, Stage 2 tree `422380c814043021c2df2daad8edbbb34d5b5887`. This prospective addendum completes five file-link metadata findings in the existing review. Coordinator promotion/freeze and Stage 3 copy remain separate gates pending the concrete file-link audit; this document does not authorize later-stage work.

The [updated complete matrix](coverage.csv) replaces only `evidence_path` in `TK2-visual-coherent`, `TK2-visual-human-labels`, `TK2-visual-actions`, `TK2-visual-navigation` and `TK2-visual-no-invented-facts`. All 6,571 records and every other field are unchanged: **6,549 normative rows verified**, zero failed/unverified, and 22 separate diagnostics. The original [matrix](../coverage.csv), [verdict](../VERDICT.md), [summary](../summary.json), original binding/review/metadata/audit files and coordinator rejection audit remain byte-identical to their seals. [Preservation and metadata proof](metadata-self-check.json) supplies hashes and the exact five field differences.

The coordinator's preserved `evidence/coordinator/stage-2-candidate-2-metadata-audit.json` correctly records `fail` for five directory-only links. My previous exact-tree check accepted the directory prefix, which did not satisfy the required concrete file-link standard. Its original failure and the original sealed matrices remain inspectable; neither is rewritten into a pass. The new complete matrix checks every current evidence path with `is_file()` and has zero missing or directory-only paths.

| Observation | Concrete current screenshot evidence |
| --- | --- |
| Coherent warm presentation and hierarchy | [Selected desktop flow](../browser-01/visual/states-1280-selected.png), [successful desktop flow](../browser-01/visual/states-1280-successful.png), [mobile search](../browser-01/visual/visual-375-search.png) |
| Human labels and intentional combined seating | [Selected Garden Bench + Window Alcove](../browser-01/visual/states-1280-selected.png), [both labels in confirmation](../browser-01/visual/states-1280-successful.png), [mobile Together options](../browser-01/visual/visual-375-search.png) |
| Clear primary actions | [Find/Confirm booking](../browser-01/visual/states-1280-selected.png), [Create account](../browser-01/visual/visual-1280-signup.png), [Sign in](../browser-01/visual/visual-1280-login.png), [Find reservation](../browser-01/visual/visual-1280-lookup.png) |
| Consistent navigation across all four routes | [Search](../browser-01/visual/states-1280-selected.png), [signup](../browser-01/visual/visual-1280-signup.png), [login](../browser-01/visual/visual-1280-login.png), [lookup](../browser-01/visual/visual-1280-lookup.png) |
| No invented establishment facts in the reviewed product | [Mobile search](../browser-01/visual/visual-375-search.png), [signup](../browser-01/visual/visual-1280-signup.png), [login](../browser-01/visual/visual-1280-login.png), [lookup](../browser-01/visual/visual-1280-lookup.png), [actual successful booking](../browser-01/visual/states-1280-successful.png) |

Every repaired row additionally names the concrete [original review records](../review-checks.json), [actual visual-run report](../browser-01/visual/summary.json) and [row-specific observations](visual-observations.json). The screenshots were reinspected during this correction. Cream/green/clay styling, labelled Together seating, prominent green actions and consistent route navigation match the original observations. The reviewed pages contain fixture and reservation information rather than fabricated reviews, ratings, restaurant photos, usage metrics or real-establishment claims. This remains a scoped product observation, not an arbitrary-content or full accessibility certification.

No uncovered behavior was found. **Service/browser reruns: zero. Production edits: zero.** Existing current HTTP/browser/official counts, timing, genuine upgrades, screenshots, all four adopted interpretations and limitations remain unchanged. [File proof](file-proof.json) binds concrete existing evidence bytes; no screenshot was reconstructed or replaced. The new metadata run reports five repaired rows, no other field changes, complete required metadata, all current links resolving to files and zero errors.

Executed from the result repository with the workspace Python:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-2/candidate2_file_links.py
```

[Command proof](command-proof.json) records the actual invocation and successful output. The original verifier verdict commit is `efd23ed509e039ca285012c0c1b23a952e8d92a0`; its inspection seal is `cc271a32cfadec85a8deb578041c87ef099c9cfa`. The new evidence revision is supplied after exact owned-commit inspection in the room report, avoiding a circular self-commit identifier here. Configured harness/model remain Codex/gpt-6.1-sol; actual model override, effort, usage and cost remain unknown.
