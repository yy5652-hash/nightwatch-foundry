# Stage 1 decoder repair integration — Interface

Package `TK-20261004-S1-interface-engineer-JSON-REPAIR-2`: parts 1–10 and the
END marker were received and acknowledged before work. Shared assignment #14.
This entry prepares diagnostics only. Repaired production execution requires
the coordinator's explicit release of a named complete service revision and
the complete Systems handoff. Highest independently accepted stage remains 0.

Candidate 6 `ab0cf79767b6768153a73894bf5768bf3328491a`, production `debff0bbf2625936d30e1e11066b966a46320137`,
tree `d2905df39546a619afbad3547b10205bb6c01610`, is independently rejected at
`7db8085f06bd6aa53443f5cf647ff4111bbaa771`. Its balanced ignored nested JSON
refusals remain failures. Earlier Interface 577 inherited, 305-operation/1227
numeric and 103-operation/392 depth-1050 observations remain unchanged and
bounded; they neither restore acceptance nor cover the new depths.

## Source and ownership

Stage 1 §§3.4/5 distinguish valid JSON unknown fields from malformed grammar.
Sections 7/10 require complete parsed-body identity and immutable successful
receipts across independent replacement. The adopted value/legacy decision
preserves exact new numeric values and receipt-specific historic comparisons.
No published nesting maximum is introduced by this review.

The transport already invokes `loads(raw bytes)` and uses `dumps(tree)` UTF-8
bytes directly before headers. A stable codec API therefore needs no speculative
adapter change. Systems owns decoder/core repair; Interface owns framing,
object-only bodies, HTTP error mapping, byte lengths, empty 204, launch and image
packaging. A callable change requires reciprocal agreement before wiring.
No core/module, Stage 2 or other-seat evidence path is edited here.

The active room plan was read through the room CLI and its workspace source.
Workspace `plan.md` SHA-256 `4b9dbb35a7298d456e23c5064e81a9e4474fdd42b945c4e40a36bc46e37df5b9`
matches the authoritative immutable snapshot. The participant roster contains
only the four configured seats and the operator. The full participant guide
was read. An attempted `work show` was an unsupported CLI subcommand; no task
mutation followed it. The documented `work take` and `room-status` operations
then joined card 14 and set the actual assignment in progress.

## Executable integration state map

| State/trigger | Required observation and independent method |
| --- | --- |
| Valid unknown nested value | Arrays, objects and alternating wrappers at 10,000/20,000 are composed around an independently shallow-validated leaf; reset/signup/create/move succeed with their specified status. |
| Equal complete parsed value | Party and deep numeric aliases, signed zero and object order preserve the successful original JSON response on retry. |
| Changed complete parsed value | A deep exact fraction or boolean-versus-number difference conflicts with 409 before invalid party/missing resource checks. |
| Invalid endpoint value/missing key | Valid deep JSON follows endpoint/key precedence; failed keys remain reusable for another valid deep request. |
| Malformed grammar/encoding | Truncated/extra documents, malformed leaf arrays/objects/numbers/escapes/constants/control characters and UTF-8 return 400, retain sessions/state and leave health available. |
| Mutation after success | Real amendment/cancellation changes current records; original create/move receipts remain unchanged. |
| Independent replacement | Actual deep exports stay raw bytes in client memory and are sent unchanged to a separately running process, then exported/imported back. Tokens, identities, references, records and original retries survive. |
| Refused import | Malformed deep export or unsupported receipt profile refuses atomically. |
| Concurrent retry | Fifty real simultaneous depth-20,000 writes yield exactly one 201 and 49 identical 200 receipts, one new identity, and an importable original receipt. |
| Blocked deep success | A refused valid reset/create/move records dependent paths as blocked; a shallow recovery never counts as successful deep migration. |
| Inherited/legacy behavior | Re-execute own 577-assertion transport suite and independently authored exact/legacy/mixed suite against the same complete built service. Genuine earlier services actually issue receipts and unchanged exports. |

## Probe construction and execution gate

`stage-1-decoder-repair-probe.py` imports no production module, peer probe or
shipped test. Prefix/suffix construction follows the JSON array/object production;
only the shallow leaf and depth-three representatives use the client decoder.
The default client recursion limit remains 1000. Shallow public responses are
decoded; deep private snapshots are never recursively decoded or persisted.
Saved traces carry byte counts, hashes, statuses, error codes and timings only.

`--self-check` performs construction diagnostics with zero HTTP operations.
It does not establish service acceptance or a deep-decoder oracle. The complete
container driver binds all own probes to committed `--probe-revision` blobs,
clones the released full candidate, builds the entire six-file image, derives
actual candidate hashes, verifies packaged source/listeners/resources, and runs
two current plus two genuinely earlier services. Allocated mappings are
18240–18243; all resources have an Interface prefix and only own resources are
removed. Each execution uses a new output directory and retains the clean clone.

Prospective command, pending release and exact revisions:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-1-decoder-repair-container-check.py --revision <released-full-candidate> --probe-revision <committed-own-probes>
```

Modest sampled depths/payloads do not prove arbitrary-size/depth performance.
Historical exact-instant/minute-offset and immutable older receipt-string
interpretations remain disclosed. Official isolated and complete independent
coverage/acceptance remain coordinator/verifier gates. Stage 2 stays frozen;
no later-stage work is authorized. Harness Codex/configured gpt-6.1-sol; actual
override, effort, usage, estimated and billed spend are unknown.
