# Stage 4 Systems exact predecessor copy — Phase A

**The two owned files are copied and committed. Phase B remains held.** Highest consecutive independently accepted stage is **3**; Stage 4 is not implemented or accepted. No runtime build, service launch, application import, HTTP probe or official harness execution occurred in this phase.

All nineteen parts and the final END of `TK-20261004-S4-systems-engineer-INITIAL-1` arrived and were acknowledged before work. Shared card 22 is joined. Its detail contains exactly one standalone `Components: integrity, json_codec, planning` line, a textual association only. Final-part delivery ID is `1a48adc4-a904-4e14-b407-79c37d8e412e`; the runtime did not expose a reciprocal acknowledgement message ID, recorded explicitly as unknown.

| Source identity | Full revision |
| --- | --- |
| Frozen accepted Stage 3 | `91e2c471acded1b861b3fec725f202297b1c6740` |
| Frozen Stage 3 tree | `a0f0a4741bb0ab0125856510a000ade385344a04` |
| Stage 3 independent verdict | `315631a0565cbc671ba112842b452eb0b8624313` |
| Systems two-file Stage 4 base commit | `418d2270ec31bbfbb50276f80908d99b38c0a3c7` |

| Copied owned path | SHA-256 | Source and target Git blob |
| --- | --- | --- |
| `stage-4/core.py` | `5ed0a09d1d2230981e0035be6f58c2938a10a15d47476c95296fd2f30f4d8197` | `4ecfbe140dddb4223572fdf15fa9a84fb117cf9d` |
| `stage-4/json_codec.py` | `3bf4c5dd7ccee1c99127d735822331fedb1491af3568d3490a81a092bae49501` | `61625ebeef583c81933e86571c861949d373b84c` |

Both files retain filesystem mode 0644 and Git mode 100644. Source working bytes matched the accepted committed blobs before copying; each target was absent. The copy checker wrote identical bytes, retained modes and committed only the two explicit production paths with Systems Engineer identity. Exact resulting-commit inspection verified both target blobs/modes and the changed-path set.

[Copy record](stage-4-source-copy.json) preserves all actual Git argv/exits, byte counts, source/target hashes, modes, UTC interval and measured copy/check/commit duration **0.525808625 seconds**. All **24** frozen files (6 Stage 1, 9 Stage 2, 9 Stage 3) matched their exact accepted revisions before copying, before commit and after commit. The Stage 3 verdict hash matches its freeze manifest. This is a copy check, not runtime behavior or whole-factory elapsed time. Interface's seven target paths and the coordinator's all-nine-target inheritance proof are separate responsibilities.

The first checker attempt stopped with AssertionError before any target write or commit because it selected historical `accepted/stage-1.json`, whose revoked revision remains preserved. The corrected checker selects the named current Stage 1 manifest. [Original executed checker](stage-4-base-copy-attempt-01.py) and [observed error record](stage-4-base-copy-runner-error-01.json) retain that own metadata error; the original duration is unknown. No source or service failure is inferred, and no historical manifest was changed.

Actual invocation from the absolute result root:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-4-base-copy.py
```

The [executed copy helper](stage-4-base-copy.py) refuses existing targets or output and records its exact source hash. Do not rerun it against the existing preserved outputs. The actual production commit used explicit `git add -- stage-4/core.py stage-4/json_codec.py` and `git -c user.name='Systems Engineer' -c user.email='systems-engineer@nightwatch-foundry.invalid' commit --only ... -- stage-4/core.py stage-4/json_codec.py`; no history was rewritten. The later evidence seal is reported in the room after exact owned-path inspection, avoiding a circular self-commit identifier.

Authoring inputs are the complete current direct cumulative task/specifications/guide/brief, authoritative room plan, accepted freeze manifests/verdict hash and own accepted source bytes. No peer probe/oracle, shipped test implementation, external domain code/schema, memory, toy/abandoned result or host dependency was used. All four adopted numeric/profile, original receipt, semantic numeric-control and historical timestamp decisions remain inherited; this copy introduces no interpretation.

The intermediate Stage 4 folder has no runtime or acceptance claim. Extension and candidate execution wait for the coordinator's complete nine-file predecessor proof and explicit Phase B release. Systems must preserve frozen Stage 1–3 and remain in disjoint core/codec/evidence paths. No Docker/network/runtime resource was created. Configured harness/model: Codex/gpt-6.1-sol; actual model override, effort, tokens, catalog-estimated cost and billed spend are unknown. Whole-factory timing, genuine room export, public release and submission remain coordinator/operator responsibilities.
