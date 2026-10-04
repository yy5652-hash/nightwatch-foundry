# Stage 1 exact JSON adapter/image intermediate handoff

Package `TK-20261004-S1-interface-engineer-JSON-REPAIR-1`, shared card 11.
Coordinator adapter release: `86cee961-f5e4-4f48-9704-e4acd2d339e0`.
Highest independently accepted consecutive stage remains **0**. This handoff
is the adapter/image step; core exact-number field validation, receipt profiles
and state compatibility remain a separate Systems step. No complete repaired
HTTP candidate, official check result or renewed acceptance is claimed here.
The exact original-module wiring repeat passes: **577/577 real Engine inherited
assertions**, **83 synthetic adapter HTTP operations / 292/292 assertions**, and
**15/15 runtime/aggregate checks**. Assertion totals are not normative row counts.

## Owned production change and callable boundary

Wiring revision: `3dae12788ff59dce8c4ce8a6faa71394f140e3d2`.
Only Interface-owned graded paths change in this commit:

- `stage-1/server.py` imports `loads`/`dumps` from the committed shared codec,
  gives `loads` raw Content-Length-framed bytes, and writes `dumps` bytes
  directly. It calculates encoding before status/headers and byte Content-Length.
  Empty 204 responses bypass encoding and have zero bytes. Existing object-only
  checks, malformed UTF-8/JSON/constants-to-400 mapping, request target/header
  preservation, concurrent listener and Engine responsibility split remain.
- `stage-1/Dockerfile` explicitly copies `json_codec.py` beside core/server.
- `stage-1/.dockerignore` admits that exact module to the build context.
- `stage-1/RUN.md` describes packaged codec/UTF-8 integration and keeps numeric
  endpoint/receipt policy with Engine.

The callable is the agreed bytes API: `loads(bytes | str) -> tree`, strict UTF-8;
`dumps(tree) -> UTF-8 bytes`, with no second encoding. Codec errors inherit
ValueError. Interface implements no numeric field validation, canonical equality,
historical float projection or receipt schema policy. No core/module/Stage 2 file
was edited or staged by Interface. The wiring commit contains Systems module
`00940d4777c316c1369e744109885d58c85373ec`, SHA-256
`913800d80172392e6357b4a9c6d2b5a80d47859779e4b0c7024b5e6e61a71078`.
Core and all Stage 2 files match rejected frozen candidate
`f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250` in that exact wiring revision.

Own evidence code adds an exact-commit image driver and synthetic adapter probe.
The latter uses the packaged `Server` with an explicitly named
`BoundaryFixtureEngine` echo fixture. This is a decoder/encoder/framing probe,
not a Tablekeeper booking or transaction implementation. Its expected values
come from the separately authored lexical-number client; it imports no Systems
or verifier test/oracle implementation. Actual Engine inherited probes run
separately and have separately reported counts.

## Preserved failures, repair and attribution corrections

The first working-tree preflight AST/core/Stage 2 checks reached an assertion
failure on the released module hash: actual shared uncommitted codec SHA-256
was `771cd5c2ccd4e11bb74808998de65605845576d0bc6172fb2d428421bc83895c`,
not the original released `913800d8...`. The shell command sequence did not
stop on that assertion failure, and the owned wiring commit still executed.
An explicit subsequent committed-context check passed AST/core/Stage 2/module
identity for `3dae127...`; no uncommitted module was built in that first run.
The failed preflight is not reported as a pass or a production codec defect.

First exact wiring run:
`interface-engineer-json-adapter-20261004t033721843244z/`.
Real Engine inherited assertions **577/577 passed**, 0 failures, 0.1218 s.
The synthetic fixture then hit an own runner exception: a function named
`concurrent` shadowed the imported module, so the 50-call pool could not start.
`synthetic-adapter.log` preserves `AttributeError: 'function' object has no
attribute 'futures'`. The driver subsequently could not find a structured
summary and reported `ValueError: substring not found`. No final synthetic
assertion count is available for this partial run. Thirteen runtime/aggregate
checks passed before that exception; total command time 42.143436417 s.
Default/override health from launch: 3.283303958 / 3.254216084 s. All three own
cleanup commands returned 0. The intentional synthetic unsupported output also
logs `Engine/response failure: JsonCodecError`; that exercises serialization
before success headers and is separate from the runner exception.

Own repair renamed the helper to `send_parallel`. Its history is preserved in
`182582c41d21a23d8ccd95688fa7f1afa0437460`. A shared-index race in that commit
included 32 concurrently staged verifier evidence/preparation paths alongside
the one owned helper change: Interface used an explicit `git add` but failed to
include a final pathspec in `git commit`. That was an Interface commit-command
error, not verifier authorship by Interface. No verifier code was read, copied,
edited or executed by Interface. Verifier evidence remains verifier-authored;
history was not rewritten. Later Interface commits use final explicit pathspecs.
The room was notified in `5e82917d-6099-41fd-8545-c80bb8fd0ab4`.

An intervening Systems-owned module repair
`c2fcedc853e0fe33e96f9d3f39c0c807b4e08d9f` is the parent of `182582c...`.
It changes module bytes to `771cd5c2...`. Interface initially inferred from a
multi-commit diff that this module also entered its race commit, which was wrong.
Exact parent/changed-path inspection corrected that attribution in room message
`fc5e94dd-bd71-4e44-b647-c484dea7325b`; the incorrect preceding report
`56a18863-6f39-438f-a825-96eae1b24196` remains preserved. There are no graded
changed paths in the Interface helper-repair commit itself.

The next exact run used full revision `182582c...` and therefore Systems' newer
module, with untouched Interface wiring:
`interface-engineer-json-adapter-20261004t033825025000z/`.
Real Engine inherited assertions **577/577**, 0 failures, 0.1209 s.
Synthetic adapter: **83 HTTP operations / 292 assertions / 292 passed / 0
failed**, 0.536367958 s. The overall driver still failed its one identity check
against originally released module 009, correctly disclosing that newer source.
Total command time 41.058413708 s. No result is relabelled as original-module
identity. Core/Stage 2 remain frozen. The full source proof names the actual
Stage 1 tree `e358e87edb0958d52d061eaf4a699eccc9d3520a` and packaged hashes.

Own driver commit `7b7c2edcd4071f50008392be5976bc855e51c0a4` permits a separately
named own probe revision. This binds corrected evidence to original exact service
bytes without editing another participant's newer module or rebuilding a mutable
working tree. The final original-module repeat follows below.

Final exact original-module repeat:
`interface-engineer-json-adapter-20261004t033925189730z/`.
Named service `3dae12788ff59dce8c4ce8a6faa71394f140e3d2`, Stage 1 tree
`22d8e6b475ce737f6df00a7b421c01d358101e31`; separate own probe/driver source
`7b7c2edcd4071f50008392be5976bc855e51c0a4`. Clean clone remained clean.
Real Engine inherited **577/577 assertions / 0 failures**, 0.1225 s.
Synthetic adapter **83 HTTP operations / 292 assertions / 292 passed / 0
failures**, 0.541297333 s. All **15/15 runtime/aggregate checks** pass,
including exact originally released module/core/server identity. Total measured
build/start/probes/cleanup time: **40.227588000 s**.

Default 8080 and overridden 9090 actual service listeners were observed on
0.0.0.0; health from docker-run start measured 3.270898042 / 3.254652709 s.
Both actual service containers have 2 CPU, 2 GiB, no mounts and the driver's
internal offline network. The synthetic fixture runs in a separate exec
interpreter inside the override container; its body echoes are never live Engine
operations. All two own services and own network removed with exit 0; image and
clean clone retained. Image ID:
`sha256:76565a8183898863365ca7f80c16c8d4f32ccebe448e2cee9db581493bccd1b9`.
Packaged core/server/codec hashes match the source proof; server SHA-256 is
`fb8d9e41eb13c3a736d49573903253a6cb98284790cf5edc9caeb352f0e0946c`.

At handoff time the shared result tree also contains Systems' separately
committed c2fcedc module repair. That later full tree is identical to the second
executed 182582c service tree, which passed both HTTP scopes but failed the
original-module identity comparison. It is not labelled the original 009-module
tree or a promoted candidate. The original Interface-owned four runtime files
remain identical across all three executions; module/core ownership stays with
Systems. The report's evidence successor hash is supplied in the room, avoiding
a self-referential hash inside this document.

## Executed commands and durable results

From the result root, the three image driver invocations are:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-1-json-adapter-container-check.py --revision 3dae12788ff59dce8c4ce8a6faa71394f140e3d2
../../.venv/bin/python -B evidence/interface-engineer/stage-1-json-adapter-container-check.py --revision 182582c41d21a23d8ccd95688fa7f1afa0437460
../../.venv/bin/python -B evidence/interface-engineer/stage-1-json-adapter-container-check.py --revision 3dae12788ff59dce8c4ce8a6faa71394f140e3d2 --probe-revision 7b7c2edcd4071f50008392be5976bc855e51c0a4
```

Every actual Docker/clone/health/hash/listener/probe/cleanup argv, elapsed time,
result and stdin digest is in each unique `run.json`. Source/probe hashes and
named revision/tree are in `source-proof.json`. Build logs, real inherited JSON,
synthetic adapter logs, service logs and cleanup outputs remain separate.
Build cache was available; no uncached-build claim is made.

## Remaining integration and review

The module-to-adapter-to-core sequence remains required. The original released
module and newer Systems module both have separately identified observations;
coordinator must bind the exact module revision in subsequent core routing.
The unchanged old core still lacks the adopted JsonNumber field predicates,
value-based body integral aliases, exact recursive receipt identity, schema 2
receipt.numeric_profile and genuine schema 1 legacy import semantics. No claim
is made that synthetic echo establishes those service behaviors.

The prepared full repair driver intentionally requires both server and core codec
imports before execution. It remains pending until the complete core is committed.
It will build a named full service plus separately running genuine 49287b4/f5
sources and two repaired destinations, probing exact finite fractions/exponents,
aliases/types, precedence, rollback, original old receipts and mixed second import.
No official harness or renewed verifier acceptance was run in this intermediate
step. Stage 2 source stays frozen; no Stage 3 work was started.

Content-Length framing remains required; unsupported transfer encoding is refused.
Modest 4,301-digit/compact-exponent probes are scoped timing evidence, not arbitrary
size/depth performance proof. Historical exact-instant minute-offset representation,
immutable original strings and original receipt interpretations remain disclosed.
Exports/credentials remain private; traces contain outcome/hash metadata only.
A recursive check of **2,773 saved JSON object records** across the three own
runtime directories found zero raw fields named password/password_hash/token/
tokens/state/authorization. The 65-file hash/byte manifest and scoped check are
in `stage-1-json-adapter-evidence-proof.json`; this is not a secret review of peer
evidence or the genuine final room export. Original preflight shell output exists
in the room tool trace; the narrative above records it and does not pretend to
be a separately captured raw shell log. Two failed document patch attempts left
files unchanged; subsequent exact-context patches succeeded. No test observations
were affected by those authoring errors.
Harness Codex; configured gpt-6.1-sol; actual override, effort, usage, estimated or
billed spend unknown. Scoped command times do not establish whole-factory elapsed.
