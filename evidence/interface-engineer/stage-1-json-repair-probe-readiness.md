# JSON repair integration probe readiness

This is **prepared builder evidence code, not a service verification result**.
Coordinator message `9c909ac1-51b0-46c0-bbdf-d5a1e496afcb` released Systems for
module-only implementation. Interface's production transport/image paths remain
frozen until the exact committed module/API handoff and explicit adapter release.
Stage 2 remains frozen; highest independently accepted stage remains 0.

Two new Interface-owned evidence scripts preserve all earlier probes/results:

- `stage-1-json-repair-probe.py`: independent raw HTTP client. Numeric JSON leaves
  retain lexical decimal information in the client so a host float/Decimal
  exponent limit cannot be confused with an HTTP result. A separately authored
  coefficient/exponent normalization checks exact response values and numeric
  aliases without importing the service's codec or another seat's oracle.
- `stage-1-json-repair-container-check.py`: adapted from our own committed
  candidate-5 driver. It requires a full named revision and rejects an
  intermediate candidate whose server or core is not wired to the codec. It
  builds the full clean detached Stage 1 context and plans four independently
  running services: two repaired destinations, genuine older `49287b4` and
  genuine frozen candidate-5 `f5e0a532`. It preserves unique outputs/clones and
  removes only resources it creates.

The prepared HTTP scenarios cover adopted whole-count aliases and fraction/type
errors, all four 4,301-digit base boundaries, compact exponent metadata, exact
ignored nested body values, underflow and precision differences, signed zero,
boolean/string/array distinctions, idempotency precedence and failed-key reuse,
reset/import rollback and malformed constants/UTF-8/nonobjects. Genuine old
services must actually issue tokens, references, create and move receipts with
rounded decimal, underflow and integer leaves. Unchanged old exports transfer to
both repaired destinations; new exact create/move receipts are then mixed with
legacy receipts and transferred again. Original responses/profiles, sessions,
credentials, identity, invalid-profile atomicity and repeated replacement are
checked. Existing meaningful transport/concurrency/calendar probes are also
retained and planned for the integrated image.

Prepared runtime constraints are 2 CPU, 2 GiB, internal offline network and no
service mounts, using host ports 18230–18233. The driver records actual argv,
source/image hashes, startup/listener, resource inspections, timings and cleanup.
These are future assertions until actual complete-image execution. No service
image was built or started during preparation.

Measured preparation artifacts are in
`interface-engineer-json-probe-preparation-20261004t032635665098z/`:
both scripts were AST-parsed without executing host service imports. Actual
recorded command:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-1-json-repair-probe.py --self-check
```

Its **17/17 client self-check assertions** passed in **0.026493959 s**, zero
failures. This checks only the evidence client's exact lexical round trips and
value distinctions; it makes **zero HTTP requests** and proves no production
behavior. A preliminary same-client self-check also passed 17 assertions in the
tool trace before the durable preparation capture; the counts are not added
together or described as service coverage. `preparation.json` binds exact
command, script hashes, source-freeze check and measured duration. All five Stage
1 and eight Stage 2 graded files remained unchanged at preparation time.

After the full module → adapter → core sequence commits, execute:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-1-json-repair-container-check.py --revision <full-coherent-commit>
```

Every actual failure and corrected execution must stay in its own output path.
Prepared scenarios and helper self-checks cannot replace official checks or an
independent named verdict. Modest compact/large-number inputs do not establish
arbitrary-payload performance. No verifier probe or shipped test implementation
was read/copied. Harness Codex; configured gpt-6.1-sol; actual runtime override,
effort, usage and estimated/billed spend remain unknown.
