# Tablekeeper scored factory run TK-20261004

Goal: four consecutive specification-complete stages, a polished product, and independently inspectable evidence. Public-check success alone cannot promote a stage.

## Ordered delivery and ownership

1. Intake: read the full guide and four specs; confirm the four seats and reciprocal routing; publish a source-complete requirements ledger, dependencies and risks.
2. Stage 1: Systems owns the atomic service engine. Interface owns substantive HTTP/runtime integration and RUN.md. Verifier independently atomizes every normative requirement and executes boundary, concurrent, retry, move and migration probes plus isolated official checks.
3. Freeze accepted Stage 1. Copy its folder to Stage 2. Systems extends combined seating and cross-version state; Interface builds and validates the complete browser product and uncertain-response recovery. Verifier checks inherited requirements and actual UI interactions.
4. Freeze accepted Stage 2. Copy to Stage 3. Systems implements effective policies, immutable accepted terms, truthful histories and recurrence. Interface adds real diner integration for terms, history and series. Verifier probes ordering, counters, upgrades and races.
5. Freeze accepted Stage 3. Copy to Stage 4. Systems implements atomic recurring amendments and deterministic closure plans. Interface adds truthful manager preview/apply and occurrence results. Verifier derives a separate exhaustive oracle, validates full supported bounds and concurrent applications.
6. Complete fresh-clone isolated runs and startup from RUN.md; retain all failures and repairs. Prepare measured facts for operator-authored README.md and FACTORY.md. Public publication, room export and competition submission remain operator-controlled.

## Dependency map

Intake → Stage 1 candidate → independent acceptance → immutable Stage 1 copy → Stage 2 candidate → independent acceptance → immutable Stage 2 copy → Stage 3 candidate → independent acceptance → immutable Stage 3 copy → Stage 4 candidate → independent acceptance → fresh-clone review.

Within a stage, engine and transport/UI ownership are disjoint. Overlapping edits require explicit serialized handoff. Only committed candidates are reviewed; every review records its full revision. A rejected candidate returns to its owning builder with complete failure evidence and complete applicable specs. Commits are never rewritten.

## Risk register

| Risk | Owner | Gate or mitigation |
|---|---|---|
| Partial public coverage conceals missing rules | Verifier | Exhaustive atomic requirement matrix and saved specification-derived probes |
| Concurrent writes split occupancy or retry claims | Systems | Single transactional serialization boundary, 50-request and interleaving probes |
| DST and half-open comparisons use wall time incorrectly | Systems | Absolute-time interval oracle and both specified zones/transitions |
| Successful receipts mutate with current state | Systems | Immutable deep response snapshots and migration replay probes |
| Lost responses or stale searches mislead diners | Interface | Stable form request identity, race and commit-then-drop browser probes |
| History or policy publication rewrites past truth | Systems | Independent snapshots, old receipt replay and contiguous event checks |
| Closure optimizer chooses feasible but nonoptimal plan | Systems/Verifier | Independent small exhaustive oracle and full supported-bound fixtures |
| Shared-tree commits include another seat's edits | Coordinator/all | Explicit path ownership and pathspec-only staging, no destructive Git operations |
| Runtime needs host dependencies or outbound access | Interface/Verifier | Single-image clean build, isolated 2 vCPU/2 GiB checks and offline UI assets |
| Evidence claims exceed observed state | Coordinator/Verifier | Unverified stays unverified; costs unknown unless measured with provenance |
| Time budget expires | Coordinator | Aim 16 hours; cease extension at 22 hours, commit accepted stages and report honest partial outcome |

## Current promotion gate

Stage 1 is independently accepted and frozen at 2a4b0408a3453bc87d86bca3d0ec571f479e03ca. Verifier evidence commit fcc0974e8cc44f7f3d57891d6b1759b499ede176 reports 801/801 atomic rows verified, no failures/unverified rows, 120/120 isolated official tests and fresh-clone startup. Acceptance follows the historical timestamp interpretation below. Previous rejected candidates and the revoked provisional acceptance remain preserved. Manifest: evidence/coordinator/accepted/stage-1.json. Stage 2 may now extend a copy; Systems performs the one serialized folder copy, then Interface edits its owned transport/runtime/UI paths. Stage 1 files remain frozen. Stage 2 combined seating, complete browser flow, competing clients, uncertain-response recovery and genuine Stage 1 migration are the next independent gate. Shared work cards 4/5/6 and all six parts of each owner's full cumulative task/spec package have been sent successfully; receivers must acknowledge completeness before execution.

## Intake history and timestamp decision

Stage 1 review found a historical-offset grammar conflict. The recorded resolution preserves exact IANA instants and original restaurant wall times while using deterministic RFC3339 minute-aligned transport offsets for historical subminute cases. See evidence/coordinator/timestamp-representation-decision.md. Independent acceptance must disclose this interpretation; prior failures remain intact.

The result repository was empty and clean at intake. Four room identities are present and all three other seats replied with literal coordinator routing. Harness is Codex; model gpt-6.1-sol is operator-configured; actual runtime override and effort are not exposed. Token usage and cost are unknown. No stage was accepted at intake.

The initial ledger lives in evidence/coordinator/requirements-ledger.csv. It deliberately retains nonnormative examples for source completeness. The independent verifier must split bundled obligations and schemas into atomic normative rows before counting coverage.

```arch
{
  "kind": "layered",
  "title": "Tablekeeper cumulative service",
  "layers": [
    {"id": "experience", "title": "Diner and manager experience", "items": [
      {"id": "browser", "label": "Offline browser product", "detail": "Stage 2 onward; authoritative responses and stable retry identity"}
    ]},
    {"id": "service", "title": "Single-container HTTP service", "items": [
      {"id": "transport", "label": "HTTP transport and runtime", "detail": "Interface Engineer owns integration, launch and presentation"},
      {"id": "integrity", "label": "Atomic service engine", "detail": "Systems Engineer owns authentication, transactions and state invariants"},
      {"id": "planning", "label": "Terms, recurrence and deterministic planning", "detail": "Cumulative Stage 3 and Stage 4 behavior only"}
    ]},
    {"id": "evidence", "title": "Independent evidence", "items": [
      {"id": "verification", "label": "Coverage and black-box verification", "detail": "Independent Verifier; exact commits, retained failures and clean clones"},
      {"id": "coordination", "label": "Sequential promotion and run ledger", "detail": "Foundry Coordinator; immutable accepted folders and full handoffs"}
    ]}
  ],
  "flows": [
    {"from": "browser", "to": "transport", "label": "JSON API"},
    {"from": "transport", "to": "integrity", "label": "Engine.request"},
    {"from": "integrity", "to": "planning", "label": "Atomic cumulative rules"},
    {"from": "verification", "to": "coordination", "label": "Accept or reject exact candidate"}
  ]
}
```
