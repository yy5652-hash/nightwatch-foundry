# Stage 4 closure error source question for independent review

Recorded 2026-10-04 08:46:00 UTC. Current Systems handoff ce078a87f81904195e2484c213bc5582e838f91a explicitly flags this interpretation. This is a source question, not an executed coordinator failure, an adopted decision, a repair instruction or an independent verdict.

The full cumulative Stage1 §5 states: 400 malformed_request for an unparseable body or a field of the wrong JSON type; 422 validation_failed for a missing required field or a stated rule with no more specific code. Correct JSON types with invalid format/range give422. It additionally says endpoint-specific field rules take precedence, and to reserve400 for a nonparsing body or wrong-type field.

Stage4 “Seating changes after a table closure” states that the instants have explicit offsets and from<to; an invalid interval gives422 validation_failed and unknown table404. It does not separately enumerate the timestamp fields' wrong-type error. Systems currently treats missing/nonstring/bad-format from/to as422 under its interval-specific reading, and table_id wrong type as inherited400. Its handoff expressly says this is not a new coordinator-adopted decision.

Independent review must reconcile the full published texts and split malformed whole body, missing endpoints, wrong-JSON-type endpoint values, correct-type bad formats, absent offsets, invalid dates and nonpositive intervals into separate current executable obligations. Preserve any observed divergences, actual source interpretation and unsupported question status; do not silently transfer a builder expectation into a passing normative claim. No default precedence resolution, defect or acceptance is asserted here. All four existing adopted decisions stay unchanged. The complete current execution package will include the FULL Stage1–4 source and full owning reports so the verifier can assess this independently.

