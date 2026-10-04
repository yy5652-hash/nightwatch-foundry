@yy5652/foundry-coordinator You are the lead seat for the scored factory run. Target all
four fully specification-complete consecutive Tablekeeper stages, with strong
product quality and independent verification, not merely the public minimum.
Use the other seats for substantive implementation and independent review.
Report partial completion honestly if genuinely blocked.

Workspace root: `/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory`

Kickoff repository: `/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/kickoff`

Result repository: `/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-result`

Check outputs: `/Users/hudsonyu/Documents/Codex/2026-09-28/referenced-chatgpt-conversation-this-is-an-4/work/dark-factory/band-work/final-checks`

Track: `tablekeeper`

Execution environment (task context, not a mandate): all four seats run on the
same macOS host and share the one result working tree above, so only one seat
edits or commits a given path at a time and the coordinator sequences overlapping
work. The official harness Python is `<workspace root>/.venv/bin/python`; run it
from the kickoff directory, e.g.
`<workspace root>/.venv/bin/python -m harness run --track tablekeeper --repo <result repository> --stage N --mode isolated --out <check outputs>/<new-unique-name>`.
A Docker daemon is running on the host; the first isolated run builds the unchanged
official runner image. Use a new `--out` directory for every run and never delete
earlier outputs. Dependencies an implementation needs belong in its own buildable
image, not on the host. The official kickoff revision is
`803560d2a678ace1414465c098eb0ab5380ffade`. Each seat is configured as Codex with
model `gpt-6.1-sol`; record the model and effort your own runtime actually reports.
When a seat runs a service or container directly it uses its own host port range:
coordinator 18000-18099, systems 18100-18199, interface 18200-18299, verifier
18300-18399.
Commit with your own seat identity, for example
`git -c user.name="<Seat Name>" -c user.email="<seat-slug>@nightwatch-foundry.invalid" commit ...`.
Stay strictly inside the workspace root: do not read, write or execute anything
outside it, do not inspect credentials or other projects on this machine, do not
change system, Docker or network settings, and do not stop containers or processes
you did not start.

Seats and literal handles:

- coordinator: `@yy5652/foundry-coordinator`
- systems builder: `@yy5652/systems-engineer`
- interface builder: `@yy5652/interface-engineer`
- independent verifier: `@yy5652/independent-verifier`

Authoritative instructions:

1. Read the complete participant guide at
   `kickoff/docs/participant-guide.md` under the absolute workspace root before assigning work.
2. Process stages 1 through 4 strictly in order. The complete stage specifications
   are `kickoff/tablekeeper/spec/stage-1.md` through
   `stage-4.md`. Stage N must extend the accepted Stage N-1 folder while remaining
   a complete, independent service.
3. For every delegated assignment, include the complete applicable task and full
   specification text in the direct handoff. A file path or room-message pointer
   alone is not a complete handoff.
   The participant guide explicitly allows long handoffs as numbered direct
   messages. Use a single package identifier and `part i/N`, at most 12,000
   characters per message including routing and context, with a final completion
   marker. Preserve the full applicable specs across parts. The receiver must
   confirm all parts arrived before working; an earlier part is not a new task.
   If transport rejects a part, split and resend that missing part transparently
   without dropping requirements or asking the human.
4. The result must be created by the seats in this room. Human-authored stage
   code is forbidden. Preserve all commits and room evidence; never amend,
   rebase, squash, or rewrite history.
5. Build to the specification, not the visible tests. The verifier must create a
   requirement coverage matrix and probe untested boundaries, concurrency,
   idempotency, recovery, upgrade, historical-truth, and deterministic planning
   behavior using black-box evidence derived from the specification.
   Number every normative requirement from the full specs. Each ledger row must
   carry the source section, applicable stage, owner, candidate full revision,
   verification method, executable command or observed browser interaction,
   evidence path and verdict. Split bundled obligations so a passing happy path
   cannot conceal an untested error, ordering, atomicity or recovery rule.
   Track inherited requirements explicitly; unsupported claims stay unverified.
   Use deterministic seeds and saved operation traces for randomized invariant
   checks, and a separately derived small reference oracle where appropriate.
   Do not copy another entry's implementation, tests or claimed coverage counts.
6. The systems builder owns integrity-critical service behavior. The interface
   builder owns interface/integration behavior and presentation quality. Both
   must contribute substantive committed work. The verifier reviews candidates
   independently and may reject promotion. The coordinator may not silently do
   all implementation itself.
7. A stage is accepted only after clean startup, applicable official harness
   checks, earlier-stage regression checks, specification coverage review, and
   an independent verifier verdict against a named full commit revision.
8. Run final checks in isolated mode. The judged service has no outbound network,
   2 vCPU and 2 GiB. Preserve every failure and repair in the room and Git history.
9. Maintain an append-only evidence ledger with wall time, model, usage/cost
   estimate, commits, checks, rejected candidates, repairs, and remaining risk.
   Keep ledgers, coverage matrices, probes and other evidence outside the graded
   `stage-N/` folders (for example under `evidence/` in the result repository).
10. Prepare measured facts for the operator-authored `README.md` and `FACTORY.md`,
    copy the four generic files in `factory/mandates-final/` into `mandates/` unchanged, and write one
    `RUN.md` per completed stage and all evidence needed for a fresh-clone review.
    Do not fabricate `room.json`; it is downloaded from Band after the run.
11. During this run, this dispatch is the only human input. Do not ask the human
    for clarification, approval, debugging hints, or a go-ahead between stages.
    Resolve choices from the published requirements and communicate within the
    band. If truly blocked, report the blocker and evidence as the outcome.
12. Finish with a final report stating the highest consecutive accepted stage,
    exact revisions, exact observed check counts, clean-clone status, known
    limitations, elapsed time, and measured or explicitly unknown model spend.
13. Read `factory/PRODUCT_ACCEPTANCE.md` under the absolute workspace root as a supplementary
    task-specific acceptance brief, never as a replacement for the complete specs.
    Do not copy its track-specific content into mandates. Derive independent tests
    from the specs, including the behaviors absent from shipped checks.
14. Aim for full specification coverage at every stage, not merely the minimum
    public claim threshold. Freeze each accepted stage before extending its copy.
    Do not sabotage a correct earlier requirement to fail an overshoot probe.
15. Preserve genuine task ownership: substantial implementation by both builders,
    independent verifier execution against exact revisions, coordinator integration.
    Never fabricate disagreements, test counts, model costs, screenshots or handoffs.
16. Keep the room economical: post decisions, handoffs, revisions, verdicts and
    evidence paths, not long raw logs. Store bulky output in files under the check
    outputs or `evidence/` and cite the path.
17. Time budget: aim to finish all four stages within about 16 hours of this
    dispatch. At 22 hours stop extending, make sure every accepted stage and the
    evidence are committed, and post the final report for the highest consecutive
    accepted stage. An honest partial result is better than an unfinished run.

Begin by confirming all four configured seats already in this room, obtaining
reciprocal literal `@handle` messages, publishing the requirements ledger, and
assigning Stage 1 work. Work only with these seats in this room. Do not contact
other agents, inspect credentials, or access other competitions. Do not reuse toy
solution code, the abandoned `band-work/result` repository, or replay their history
into the fresh scored result. Public publishing, final room export and competition
submission remain operator-controlled steps.
