# Stage 1 interface integration handoff

Package: TK-20261004-S1-interface-engineer-A. Shared assignment: board #2.

Transport implementation revision: `9d53de905fdd498ee34dfa7c4d814b13dda7a921`.
Final tested candidate: `a6d90ba140a5f2d6eb926376edc8b4fef07b5f7c`.
The Stage 1 paths were clean at the final build. Container `core.py` and
`server.py` SHA-256 values match their files at that candidate revision.

## Contribution

- `stage-1/server.py`: concurrent standard-library HTTP server, one shared Engine,
  original target/query and case-insensitive headers, unchanged parsed JSON
  objects, strict malformed/nonobject JSON refusal, JSON response framing and
  zero-byte 204 responses. A disconnected response never re-executes a request.
- `stage-1/Dockerfile` and `.dockerignore`: self-contained Python runtime and IANA
  timezone rules, explicit application copy, no host or runtime downloads.
- `stage-1/RUN.md`: single-image build/start, default and custom PORT, bearer and
  retry usage, state lifetime and private test-control snapshot handling.
- `evidence/interface-engineer/`: state map, executable container driver and
  HTTP probe, retained diagnostics, final candidate evidence and append-only ledger.

Systems confirmed the Engine constructor and parsing precedence. Systems owns
application refusals, authentication, field validation, occupancy, transactions,
idempotency and migration. No core or independent-verifier files were edited.

## Commands and observed results

`python3 evidence/interface-engineer/stage-1-container-check.py`

Final evidence directory:
`evidence/interface-engineer/interface-engineer-s1-20261004T002535279440Z/`.
The full Docker commands are preserved in `run.json`:

1. Build a uniquely tagged image from `stage-1/`.
2. Start a uniquely named container with `--network none --cpus 2 --memory 2g
   -e PORT=9090`.
3. Execute the stdlib HTTP probe inside that container against localhost:9090.
4. Record exact image source hashes, configured resource/network limits and logs.
5. Remove only the container created by the invocation.

Observed: **489/489 assertions passed, zero failures**. These include repeated
media-type/length/timing assertions; this is not a normative requirement count.
The API probe took 0.1142 seconds; build/start/probe/evidence/cleanup took 1.2816
seconds. The image build reused available build cache. The listener was observed
on `0.0.0.0:9090`; resource limits and disabled networking were inspected.

Behavior exercised includes malformed UTF-8/JSON/nonobject refusal before auth,
case-insensitive headers, Unicode round trip, public browsing, ignored fields,
field/query validation boundaries, original-body replay, failed-key reuse,
exactly one 201 among 50 identical writes, exactly one successful booking among
50 occupancy competitors, commit-then-drop response recovery, bodyless cancel,
old receipt replay after cancellation, all-or-nothing refused import, reset/token
clearing and import recovery, plus both specified IANA repeated hours and a skipped
hour. Snapshots and session tokens remain in memory and are not emitted to evidence.

AST syntax checks passed without executing host service dependencies. The
earlier diagnostic run is retained in
`interface-engineer-s1-20261004T002131890279Z/`: 489/489 assertions passed in an
uncommitted working-tree build, so it is labeled diagnostic rather than candidate
acceptance. Its total elapsed time was 14.1094 seconds.

## Assumptions and remaining review

Ordinary requests carry Content-Length-framed JSON; the adapter refuses unsupported
transfer-encoding framing. Empty bodies are absent values for Engine, whereas
explicit null/list/scalar JSON is a transport refusal. One shared Engine owns all
atomic application changes; transport has no independent retry cache or state.

This builder evidence establishes the observed integration flows only. Official
isolated harness checks, the independent atomic requirement matrix/verdict and
fresh-clone startup remain separate promotion gates. No browser, policy, series or
planning surfaces were added to Stage 1. No independent acceptance is claimed.

Harness: Codex. Operator-configured model: gpt-6.1-sol. Actual runtime model override,
reasoning effort, token usage, billed spend and catalog-estimated cost are unknown.
