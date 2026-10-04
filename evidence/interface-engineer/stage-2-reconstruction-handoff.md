# Stage 2 reconstruction — Interface base copy

**Phase A is complete locally; Stage 2 is unpromoted.** Highest independently accepted consecutive stage is 1. Stage 1 is immutable at `75005d57fe0904753eac4eab5bf4e4c9a78b6d1b`, tree `75f6ece6952c570eedf8a548f4428a5b2c986128`, independently accepted at `a22de6b769c1454c35650377da1251edc99de744`.

All sixteen parts and END of `TK-20261004-S2-interface-engineer-RECONSTRUCT-2` arrived before work. Shared card 17 authorizes this exact base copy only. Interface copied the four owned runtime files from immutable Git blobs, with no byte normalization. Existing Stage 2 web assets, frozen Stage 1 and all prior source/history remain unchanged. Systems owns its separate core/module copy.

| File | Source and target SHA-256 |
| --- | --- |
| server.py | `fb8d9e41eb13c3a736d49573903253a6cb98284790cf5edc9caeb352f0e0946c` |
| Dockerfile | `ee2fbc4476fdac158e83f18ffb254ff14c2643017092c9baf186c03d06bdb528` |
| .dockerignore | `393ca989893a3ceee4e6fe5366f6b7ac019a51900b9dadc08a56787688c1da1c` |
| RUN.md | `ac938287c37b9da1a76e230466362dd1cdf928fadf8676399c7b495aecb7530f` |

Reproduction: for each listed file, read `git show 75005d57fe0904753eac4eab5bf4e4c9a78b6d1b:stage-1/<file>` as bytes and write those identical bytes to `stage-2/<file>`. Exact executed argv, pre-copy hashes, source blob identities, retained web asset hashes and observed comparisons are in `stage-2-reconstruction-base-copy.json`. Four of four copied files compare byte-for-byte equal. Frozen Stage 1 and web assets compare unchanged before/after. The full resulting own commit is reported in the room after `--only` commit and exact changed-path inspection; embedding its own identifier here would be circular.

No application, Docker build, browser or official check was executed for this intermediate step. The copied RUN.md and Dockerfile are intentionally the original Stage 1 bytes; they will be restored for Stage 2 only after the coordinator commits its six-file proof and releases Phase B. Other target files may temporarily be incompatible. No Stage 2 acceptance or runtime behavior is inferred from a copy check.

The next authorized phase restores Interface static routes/image/RUN integration on this stable bytes adapter and extends its exact numeric presentation probes. All prior semantic controls, exact status, restaurant-local end, search-race and uncertain-response repairs must remain. Full genuine old/new Stage 1 and old Stage 2 upgrade flows and complete independent review remain required. Historical timestamp, immutable receipt and semantic numeric-control interpretations remain disclosed.

Authoring inputs: complete current direct package, authoritative room plan, full participant guide, accepted source and own existing source/history. No peer probe/oracle or external domain source was read, copied or executed. Model: configured Codex/gpt-6.1-sol; actual override, effort, usage and spend unknown. Copy/check elapsed is scoped and measured in the manifest, not whole-factory time.
