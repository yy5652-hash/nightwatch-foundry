# Stage 3 Systems predecessor copy

Phase A is complete at **`0f9e5b9544ab1d9a80d28fef81c14187768d9d81`**. That commit changes only `stage-3/core.py` and `stage-3/json_codec.py`. Both are byte-for-byte copies from the accepted Stage 2 working folder, with filesystem mode `0644` and committed Git mode `100644` preserved. Stage 3 extension and verification preparation remain held pending the coordinator's complete nine-file inheritance proof and explicit release.

All thirteen parts and both END markers of `TK-20261004-S3-systems-engineer-INITIAL-1` arrived and completeness was acknowledged before work. Final-part receipt ID is `b77a7c04-8ece-40d2-961a-9249f5e0b1b3`; the actual reciprocal acknowledgement message ID is unavailable and recorded as **unknown**, separately from that receipt ID. Shared assignment is card 19.

Accepted predecessor: `4dba10246b07b2dda19de260d529f9d94ba0a1ed`, Stage 2 tree `422380c814043021c2df2daad8edbbb34d5b5887`. Coordinator freeze commit is `a7ef75573233fbf4652b56d6609e14d82d21594c`. Highest independently accepted consecutive stage is **2**. Stage 1 remains immutable at `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b`.

| Copied file | Accepted/source/target SHA-256 | Git blob |
| --- | --- | --- |
| core.py | `c5ddc11f9a7c7b80d7d85dd5f9ba93ff4f236a6bf1ee4f4cfc901efae02c957e` | `0bc8e81f6b9d833f1ac2dcf049e59249df96ff3c` |
| json_codec.py | `3bf4c5dd7ccee1c99127d735822331fedb1491af3568d3490a81a092bae49501` | `61625ebeef583c81933e86571c861949d373b84c` |

The copy check compares all nine Stage 2 working files to the freeze manifest and accepted blobs, and all six accepted Stage 1 working files to their current freeze manifest. It verifies source folders unchanged after copying and again after commit. The two committed Stage 3 blobs and modes equal the accepted Stage 2 blobs and modes. This Systems check covers the source files and its two copied targets; the coordinator's complete nine-target proof is a separate gate.

[Exact copy record](stage-3-source-copy.json) preserves the executed Python source, invocation, actual Git argv, pre-copy target absence, hashes, byte counts, modes, UTC interval and scoped copy duration. The copy script reads the verified accepted Stage 2 working bytes, writes identical bytes, and applies the source filesystem mode. The copy check took **0.198795417 seconds**; this is not whole-factory elapsed time. The append-only Systems ledger records this new event without changing prior entries.

Commit command from the absolute result root:

```sh
git add -- stage-3/core.py stage-3/json_codec.py
git -c user.name='Systems Engineer' -c user.email='systems-engineer@nightwatch-foundry.invalid' commit --only -m 'Copy accepted Stage 2 Systems modules into Stage 3' -- stage-3/core.py stage-3/json_codec.py
git show --format=fuller --stat 0f9e5b9544ab1d9a80d28fef81c14187768d9d81 --
git diff --quiet 4dba10246b07b2dda19de260d529f9d94ba0a1ed -- stage-2
git diff --quiet 75005d57fe0904753eac4eab5bf4e4c9a78b6d1b -- stage-1
```

All copy/commit checks passed. No application import, Docker build, service launch, HTTP probe or official harness check was executed. No container/network/temporary runtime resource was created. The intermediate Stage 3 folder has no independently accepted behavior claim.

The full cumulative specifications and four adopted decisions remain applicable to the next released phase: exact numeric values and genuine per-receipt legacy profiles; immutable original response shape; semantic exact numeric controls; and exact historical IANA instants with the disclosed minute-offset representation and immutable older strings. This copy introduces no new interpretation. Authoring inputs were the complete direct assignment, authoritative room plan, accepted freeze manifests and own previously implemented accepted files; no peer probe implementation, external domain code or host dependency was used.

Harness/configured model: Codex/gpt-6.1-sol. Actual model override, effort, tokens, catalog-estimated cost and billed spend remain unknown. Independent Stage 3 acceptance, whole-factory timing, public release, genuine room export and submission are separate coordinator/operator gates.
