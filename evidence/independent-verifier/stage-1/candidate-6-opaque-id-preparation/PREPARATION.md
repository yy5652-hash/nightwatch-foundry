# Opaque ID and encoded route preparation

Source note `45bfa6ba-4d7c-4789-abf3-e9a21d1fec87` is incorporated under the
complete candidate-6 preparation assignment and shared card 12. This supplement
adds **308 conditional normative checks** and **22 separate fixture-admission
diagnostics**. All service rows remain unverified. The cumulative preparation
view contains **1,660 normative rows plus 22 diagnostics: 1,682 records**, all
unverified for the pending candidate. The previously sealed 1,352-row preparation
matrix and all earlier service observations remain unchanged.

Actual local checks: four Python files parsed with AST, and 22 fixture/URI
round-trip cases passed. The pending-handoff guard rejects the new runner family
before Docker or output creation. **Zero HTTP requests, official checks, images
or service containers** were executed by this supplement. These are client input
checks, not a service verdict, clean-clone check or resource observation.

## Source applicability

Stage 1 §3.4 lines 90–91 says IDs are opaque strings of at most 64 characters,
"Their format is yours," and applies the length limit to reset fixture IDs.
Section 4 supplies fixture restaurant/table IDs. Section 8 specifies restaurant
detail at GET /restaurants/{id}, availability using restaurant_id, and table IDs
inside booking/amendment bodies. Section 10 preserves configuration, reservation
identities and receipts through unchanged replacement import.

The source grants format freedom but does not state an ASCII alphabet or a URI
character blacklist. Arbitrary reserved/Unicode fixture **admission** is therefore
recorded separately for source review against the final candidate's chosen format;
this preparation asserts neither a lexical restriction nor an admission defect.
The source interpretation was reported to the coordinator in message
93702729-daaa-4918-a180-b9100bbe0a94. A refusal alone will remain a source question
until that applicability is justified. There is no service observation here.

Once reset returns 204 for an ID, the subsequent correctly encoded API must use
and preserve that accepted opaque identity. This conditional obligation can be
tested independently of the admission interpretation. A successful reset followed
by an unknown-resource refusal on the correctly encoded same ID would require
current-candidate investigation. It would not establish a new lexical rule.
If reset refuses, the dependent checks remain unverified; the client does not
fabricate records or turn skipped paths into passes.

There is no specified Stage 1 GET /tables/{id} endpoint. This client tests table
IDs through restaurant detail, availability, create, PATCH and reservation-moves
bodies and current/original responses. Generated confirmation references retain
their separate specified A-Z0-9, 6–12-character contract.

## Prepared protocol

Eleven ID forms run separately on restaurant and table fixture fields: ordinary,
slash, question/fragment, literal percent escape, plus/semicolon, space, Unicode,
astral Unicode, mixed reserved characters, 64 ASCII characters and 64 CJK
characters. Other fixture identifiers stay ordinary. All inputs have 1–64 Unicode
code points; the 64-CJK control has 192 UTF-8 bytes. This distinguishes characters
from a guessed byte limit without claiming that §3.4 explicitly specifies a
Unicode segmentation algorithm. Null/control characters and malformed URI spellings
are not introduced as unstated normative acceptance obligations.

Restaurant route segments use quote(value, safe='') with strict UTF-8. Query
values use urlencode with quote rather than handwritten concatenation. Each
prepared URI decodes to the original ID, with no unintended query or fragment.
A literal room%2Ffloor ID is transmitted as room%252Ffloor: exactly one decode
must retain the literal percent escape rather than convert it into a slash.

For an accepted fixture the client checks public IDs and fixture order, detail
status/identity, exact availability, create status/identity, original key replay,
owner lookup, amendment, atomic move identity, unchanged export into an independent
destination with the original token, immutable original create replay after import,
cancel release and an unknown correctly encoded route control. It saves real raw
HTTP metadata with the verifier's existing transport recorder. Passwords, bearer
tokens and opaque export payloads remain in memory or are fingerprinted.

The prepared runtime now supports --probe-family opaque-ids. That family builds
the complete named current Stage 1 folder from a clean detached clone and starts
two independently running current processes, default 8080 and override 18335,
with host mappings 18336/18335. Both run with 2 CPU, 2 GiB, internal offline
networking and no service mounts. Cross-container health, exact source/image
hashes, commands, durations and own cleanup are recorded. Unlike the semantic
family it does not start an unused legacy process. The original semantic family
still prepares its three current destinations and genuine legacy source.

## Commands and provenance

Executed preparation command from the result repository:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-1/opaque_id_prepare.py
```

Only after the explicit complete final named candidate and both complete builder
handoffs, execute the guarded runtime with the same required repo/workspace/
candidate/handoff/new-output arguments as the numeric preparation and add:

```sh
--probe-family opaque-ids
```

This extends the verifier's own runtime driver and adds OpaqueId.Probe.Dockerfile,
opaque_id_requirements.py, opaque_id_probe.py and opaque_id_prepare.py. No graded
source or peer probe/oracle was read or edited. source-proof.json binds the
current client hashes; prior source hashes remain historical snapshots at their
named commits rather than being rewritten. coverage-prepared.csv separates
normative rows from diagnostics with an explicit normative column;
coverage-cumulative-prepared.csv provides the cumulative view. Diagnostics must
not be silently counted as failed requirements, passes or promotion evidence.

Preparation-summary.json and input-uri-validation.json contain actual local
checks. The measured supplement wall time and scoped private-artifact scan appear
in preparation-seal.json. Highest accepted consecutive stage remains 0, Stage 2
is frozen, and final full source/coverage/startup/official/regression verification
still waits for the complete named candidate. Historical timestamp, original
receipt and exact/legacy numeric interpretations remain as previously recorded.
Finite sample probes do not establish arbitrary-payload resource performance.

Harness Codex; configured model gpt-6.1-sol. Actual override, reasoning effort,
usage and estimated/billed spend are unknown. This report does not claim a new
candidate defect or acceptance.
