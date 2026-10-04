# Response snapshot ownership: source-only audit

Requested in coordinator message `315f458e-2e0a-4488-95b9-ef64ab3f3a8d`, within
the complete JSON-REPAIR-1 assignment. Core remains held. This audit changes only
Systems evidence and records future integration/verification requirements.
No concurrent HTTP failure, race or repaired service result is asserted.

## Current source facts

The audited core is unchanged from production
`78732dde56ba6116d0722136beba74b674811105` and rejected candidate
`f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250`. Its SHA-256 is
`324c6535bb81f13a61244da554b33c385544f13556e5d894ad5ae53578847380`.
Shared HEAD at the audit read was `b9174e1e7f8661dab6147bd662af540197cc12b4`;
that HEAD is not claimed to be a new accepted or complete core candidate.

The private `_dispatch` export branch returns an envelope containing
`self._state`. Restaurant detail and original receipt replay also return internal
objects from that private function. However, the public `Engine.request` wraps
dispatch in `with self._lock` and returns `deepcopy(result[1])` **inside that lock**.
Thus an ordinary successful public response already owns detached containers
before another Engine request can acquire the lock. The internal export reference
does not itself escape the public boundary. `Refusal` errors construct new error
dicts inside the lock; caught value errors likewise return newly constructed
errors. This existing snapshot protection must not be lost during repair.

Write receipts separately archive `deepcopy(data)` and `deepcopy(response)` while
dispatch holds the same RLock. Replay returns the archive internally, then the
public wrapper detaches its outgoing tree. Current reservation `_public` creates
a shallow dict, and availability/auth/list paths generate response containers;
the common final copy protects nested aliases across all successful paths.

Interface's transport receives `(status, result)` only after `request` returns,
then calls codec `dumps(result)` before writing status/headers/bytes. This is a
sound boundary **when the result owns its mutable containers**. Transport must
not access state or repeat business validation. Codec `JsonNumber` leaves are
immutable; sharing such a leaf is safe, unlike sharing a list/dict.

The recursive `deepcopy` mechanism remains unsuitable for the newly observed
deep valid trees. Current full-body validation and equality are recursive too.
These are pending integration boundaries; this audit does not manufacture an
export-during-write failure. Recursive copy failure after a state mutation is
also an ordering risk to inspect: required body/receipt snapshots should be
prepared before commit or be guaranteed by the validated iterative copy path,
so a caught validation refusal cannot follow a partial write.

## Invariant for released core integration

Every successful response crossing `Engine.request` must own all reachable
mutable JSON containers. Capture that tree while the RLock still protects the
same committed state. Export linearizes at this snapshot: later writes,
cancellations, token additions, reset/import replacement or source activity cannot
change its bytes while the transport encoder traverses it. The copy must preserve
exact finite numeric values/provenance, original receipt JSON values, historic
timestamp strings and profile metadata, and use an iterative/depth-safe traversal.

Apply the same ownership rule to fresh write responses, original replays,
restaurant detail, reservation list/detail, availability and auth. Completed
receipts own detached request and original response trees independently of current
records and outgoing results. Imported candidate state must own its mutable
containers independently of the decoded envelope. Validation/construction/copy
and transaction commit stay in core under the existing atomic boundary; transport
only encodes the detached tree. No global transport lock or business policy is
introduced. Capture/serialize work may consume measured time, but no size/depth
ceiling is added.

## Own verification to run after release

1. Build named committed current and peer service processes with 2 CPU/2 GiB,
   offline internal networking, no service mounts and own allocated ports.
   Populate real users/tokens, receipts, references and valid depth-1100 ignored
   object/array bodies through HTTP. Save synthetic payload hashes/byte counts
   and operation traces; keep credentials/export bodies private in memory.
2. Stage export reads concurrently with deterministic sequential writes whose
   cumulative receipts/references supply an independent prefix oracle. Import
   every captured snapshot unchanged into the independent peer. Each state must
   correspond to one complete committed prefix, with consistent records and
   receipts, never partial pairs or mixed versions. Repeat with batch moves,
   amendment/cancellation, reset/import replacement and active tokens.
3. Record one real captured HTTP export, then perform further source writes and
   replacement. Its retained bytes/digest must remain unchanged. Import those
   same bytes repeatedly into the peer; verify old session/reference/login,
   original create/move responses and retry semantics without regenerating state.
4. Check response bodies across concurrent lookup/amend/cancel and identical
   receipt replays. Compare returned bodies against separately captured original
   receipts/current committed states; successful old receipts must never reflect
   later record mutation. Refused operations leave occupancy, records and keys
   unchanged. Peak traffic and timings will be measured, not presumed.
5. Add a deterministic owner diagnostic at the Engine boundary that retains
   returned trees, performs later independent requests and encodes the retained
   responses afterward. It supplements real HTTP concurrency and proves container
   detachment directly; it does not replace the black-box export/import evidence.

All outputs must use unique directories and preserve failures/repairs. These are
planned checks, not executed passes or coverage rows. Current source commands were
bounded `rg`/`sed` reads of owned core and the permitted adapter boundary, plus
hash/frozen-core diff checks. No peer probe or oracle implementation was read,
production path edited or host dependency installed. Highest accepted remains 0.
Historical timestamp/receipt interpretations, full regression/independent review
gates and arbitrary-payload performance limits remain unchanged. Harness Codex;
configured gpt-6.1-sol; actual override, effort, usage and estimated/billed spend
unknown.
