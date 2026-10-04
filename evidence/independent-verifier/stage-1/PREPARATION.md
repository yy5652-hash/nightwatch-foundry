# Stage 1 independent verification preparation

Package: `TK-20261004-S1-independent-verifier-A`, all four parts and final completion marker received. Candidate has not yet been handed off. No candidate verdict is issued here.

Authoritative kickoff revision verified: `803560d2a678ace1414465c098eb0ab5380ffade`. The complete participant guide, complete Stage 1 specification and supplementary acceptance brief were read. Probe requirements were derived before consulting shipped tests or implementation source.

`requirements.py` defines stable atomic IDs and generates `coverage-prepared.csv`. All 389 initial rows remain **unverified**. The count is a decomposition count, not a score, test count, proof of completeness or unseen judging coverage. Every row retains source section/line, applicable stages, owner, candidate slot, method, command, evidence and verdict. Rows inherited by later stages remain explicit.

The coordinator source index includes all Stage 1 sections. It is not an atomic normative matrix: its fixture block (`TK-S1-063`) and auth/response schema blocks bundle multiple fields; prose rows also bundle independent type, error, ordering, atomicity and replay obligations. The independent matrix separates these obligations. No source-section omission was identified in the initial index review. This does not claim its 229 source rows are 229 normative requirements.

`probe.py` is a standard-library black-box runner against two independently started containers. It imports no production module or shipped test. Its saved assertions map to individual IDs; a row receives `verified` only when its mapped executed assertions pass. Missing execution remains `unverified`. Runtime and provenance obligations require separate container/clone/history evidence and will not be marked verified from HTTP source appearance.

Prepared cases cover legal fixtures, public browsing, authentication and concurrent tokens, strict query/body types and values, schema fields, original receipts, cross-user/path key scopes, fifty identical retries and fifty competing occupancy requests, half-open intervals, amendment rollback and current cutoffs, eight-way cyclic swaps and input-order errors, both specified zones' spring/fall transitions, independent-process state replacement and invalid-import rollback. The occupancy property probe uses seed `20261004`, a separately written integer-minute half-open oracle and a saved operation trace. Export snapshots stay in process memory; saved traces replace credentials/tokens/export state with fingerprints.

Candidate execution sequence:

1. Receive and acknowledge the complete candidate/applicable-spec package and full commit.
2. Review committed scope/history and RUN.md before running checks; confirm substantive contributions by both builders and no reliance on uncommitted files.
3. Clone that exact revision into a new `independent-verifier-` directory beside the result repository. Verify no nested repositories, submodules or escaping symlinks.
4. Follow RUN.md, build its single image and start independent containers using verifier host ports 18300–18399, 2 CPU, 2 GiB and a seat-prefixed internal network. Measure readiness and default/nondefault PORT behavior.
5. Run the unchanged official isolated harness from kickoff using workspace `.venv/bin/python`, the clean clone and a fresh final-checks output directory. Preserve exact observed suite counts, overshoot outcome and all failures.
6. Run all independent cases, review every unverified row, add any missing requirement probes and record complete coverage evidence. Preserve smallest failures and send owning builder exact command/expected/observed/requirement/evidence.
7. Independently rerun repaired revisions. Append ledger and issue `accept`, `reject` or `blocked` against a full revision. An official green result alone is insufficient for acceptance.

Environment: same macOS host/shared working tree; harness Codex; operator-configured model `gpt-6.1-sol`; actual runtime override and effort not exposed. Token usage, catalog cost and billed spend are unknown. Preparation syntax checks are verifier-artifact checks, not product acceptance checks.
