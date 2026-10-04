# Stage 1 Interface Engineer source provenance

This declaration covers the authored `stage-1/server.py`, `Dockerfile`, `RUN.md`
and `.dockerignore`, first committed at
`9d53de905fdd498ee34dfa7c4d814b13dda7a921` (2026-10-04 00:20:34 UTC).
It is an audit declaration, not a new implementation or acceptance verdict.

Workspace root:
`/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory`.
Result repository: `<workspace>/band-work/final-result`.

## Inputs before authoring the service files

1. Complete coordinator package `TK-20261004-S1-interface-engineer-A`, parts
   1/4 through 4/4 and final completion marker. This contained the full official
   Stage 1 specification, complete current factory task, supplementary acceptance
   brief, path ownership, runtime/resource constraints and chosen Engine boundary.
   The specification was read as handoff text. I did not directly open
   `kickoff/tablekeeper/spec/stage-1.md`.
2. `<workspace>/kickoff/docs/participant-guide.md`: opened twice as complete text
   before implementation. Tool output truncation required bounded rereads. The
   12000:26000 character slice was reread before the service files were written;
   the first 12000 characters and remainder after 26000 were explicitly reread
   after the first transport commit to ensure complete untruncated coverage.
   Thus I distinguish opening the complete file before implementation from the
   final complete readable reread later. The guide includes toy workflow examples;
   no toy solution or scaffold implementation file was opened or copied.
3. `<workspace>/factory/PRODUCT_ACCEPTANCE.md`, opened as supplementary context
   before implementation. Stage 1 scope prevailed over its later-stage product
   directions.
4. Result `plan.md` and `architecture.json`, read before implementation for
   ownership, integration and stage boundaries. No implementation code was taken
   from these planning documents.
5. The supplied runtime mandate, shared-tree constraints and user AGENTS
   instructions in this conversation. No additional project AGENTS.md file was
   found by the bounded workspace search.

The adapter was authored from these requirements and prior standard-library
programming knowledge. No external Python/Docker/API documentation or example
implementation was consulted. The used runtime library APIs are Python's
`http.server`, `json`, `os`, `socket`, `sys` and `collections.abc.Mapping`.
The image uses the ordinary `python:3.12-slim-bookworm` runtime image and Debian
`tzdata`, installed during Docker build. Their source was not read or copied;
they are runtime dependencies, not reservation-domain implementation inputs.

## Later diagnostics and integration inputs

- Systems' messages confirmed `from core import Engine`, `Engine()`, one shared
  instance, original target/query, case-insensitive header mapping, unchanged
  parsed objects, absent-body None and parsing precedence. These confirmations
  arrived after the initial transport implementation; the contract did not change.
- I inspected this run's Systems-authored `stage-1/core.py` constructor and
  request/dispatch excerpt (lines 144–226 at the time), plus bounded searches
  for headers, idempotency, body handling and timestamps. This was integration
  diagnosis after the transport files were authored. Docker packages that core
  unchanged as the other builder's contribution; I did not edit core.py.
- I authored `evidence/interface-engineer/stage-1-transport-probe.py` and
  `stage-1-container-check.py` from the supplied specification. They were not
  copied from shipped tests, verifier probes or another submission. Their own
  container output was consulted after implementation: the retained uncommitted
  diagnostic, committed-candidate run and post-repair regression run.
- Systems' later builder/repair summaries described actual test outcomes and
  repaired missing-array/date-boundary behavior. They were received after
  implementation. I did not open the linked builder/repair test source or report
  files to author the service, and the interface service files were unchanged.
- I read my own Git status/log output, image build/service logs, source hashes and
  resource-limit metadata for provenance and runtime checks.

## Tests, products and code not consulted

No shipped Stage 1 or later-stage test source was opened, copied or executed by
this seat. No verifier probe source was opened, copied or executed by this seat.
Independent findings were received as room messages; they did not supply copied
transport code. The official harness was not run by this seat for Stage 1.

No existing reservation-domain product code, API documentation or schema was
accessed or reused. No toy/scaffold solution files, abandoned `band-work/result`
implementation, prior solution history or outside-workspace implementation were
accessed or reused. No web research, browser research or memory-file lookup was
used. Standard runtime tools and dependency binaries are distinguished from
domain source inputs.

Earlier room declaration: message `f8738479-3750-4add-a9d6-2fa7871a98dd`.
This file makes the declaration inspectable and clarifies guide reread timing.
Implementation and evidence commits remain preserved without history rewriting.

## Later TIMESTAMP-3 interpretation and probe extension

After the initial declaration, I read the coordinator's
`evidence/coordinator/timestamp-representation-decision.md` and updated active
plan when message `3b19f2a6-4b23-4528-9643-c4dcbbf202d6` assigned an integration
regression under that decision. I extended only my own HTTP probe, committed at
`94c4d59cffb71c2936434d3379673ad4951753e5`. The reference calculation uses
packaged IANA offsets, ordinal arithmetic and independent exhaustive minute-offset
enumeration from the decision. No production serializer or verifier probe source
was opened or copied. Systems' committed-candidate handoff and my own resulting
container output were later diagnostic inputs. Interface service files remained
unchanged. The resulting integration evidence is in
`stage-1-timestamp-03-check.md`; its interpretation is explicitly disclosed.

## Later candidate 5 serialized decimal integration review

Package `TK-20261004-S1-interface-engineer-CANDIDATE-5` was received in all seven
parts and acknowledged before work. The package included the complete Stage 1
specification, current factory task, supplementary brief, timestamp/receipt
decisions, Systems' repaired-candidate report and the supplied independent
supplemental rejection text. These are later diagnostic inputs, not inputs to the
original Interface runtime implementation. The participant guide and active plan
were reread. The exact candidate `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250` was
built from clean detached own clones; the four Interface runtime files were read
and compared byte-for-byte with original source `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`.
No runtime or Stage 2 source was edited.

I independently authored `stage-1-candidate-5-probe.py` and
`stage-1-candidate-5-container-check.py` from that package and my own existing
transport probe, first committed at `76763bb2cbf54d5da8780768ae89399d3106a8fc`.
The genuine older process uses the committed five-file Stage 1 service at
`49287b4a5a1481f995c470ccae31776f03d4b863`, generated into an owned build context;
it is this run's legitimate earlier implementation, not an abandoned result.
After observing an own runner DNS-label `UnicodeError`, only the runner was repaired
at `74dff654931980cdacbb63dec61a649fa47a9a81`, and both unique outputs were retained.

The corrected run then observed a 400 refusal for a syntactically valid giant
fractional party number where the probe expected 422. Read-only bounded core
searches and `json_value`/write-dispatch excerpts were inspected after that result
to diagnose the adapter's default float overflow and core's finite-value refusal.
This was integration diagnosis, not copying or editing Engine implementation.
The unresolved observation and all passing results are in
`stage-1-candidate-5-integration-handoff.md`. No shipped test source, verifier probe
source, external domain documentation/code/schema, toy/abandoned implementation,
outside-workspace project or memory file was consulted. Own output, Git/Docker
metadata and standard-library programming knowledge are the only additional inputs.
