# Historic timestamp verification preparation

This preparation responds to the coordinator's published Stage 1 timestamp decision. It is not a new production verdict and calls no service. Candidate-2 failures in `candidate-2/` remain unchanged.

The independent `wire_oracle.py` searches every RFC3339 minute offset from -23:59 through +23:59, discards clocks outside the supported calendar, and selects by distance to the exact IANA offset then numerical offset. It uses ordinal seconds rather than Python UTC conversion. Five explicit oracle examples passed: Berlin midnight/afternoon year 1, New York afternoon year 1, a historical Monrovia half-minute tie, and New York late year 9999. Each preserves the exact represented instant. The code imports no product code or shipped tests.

`calendar_edges.py` checks the six date/zone combinations, availability wire timestamps, exact start/end instants, unchanged original local fields, RFC3339 grammar, deterministic offsets, minimum-calendar clock adjustment and a genuine IANA tie. Historic create receipts must replay unchanged and survive export/import into a second process with the original token. `probe.py --case calendar-edges` now runs this case; the complete suite includes it automatically. Run against the named committed candidate only after the full numbered handoff arrives, with new output directories.

The prepared matrix contains 765 atomic rows, all unverified. Each calendar row carries an explicit interpretation note. The recorded exception concerns literal historical wire offsets; neither original instants nor local booking fields may be rounded or changed. Modern minute-aligned offsets remain unchanged. New production execution and a named revision are required before a verified claim.

The coordinator decision is preserved in `timestamp-interpretation-input.md`; its recorded source path and SHA256 are appended to the independent ledger. The genuine final room export remains operator-controlled. Harness Codex, configured model gpt-6.1-sol; actual override, effort, usage and spend unknown.
