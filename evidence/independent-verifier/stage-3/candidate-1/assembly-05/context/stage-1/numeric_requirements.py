"""Explicit JSON numeric-form obligations; source questions remain visible."""
import copy
from decimal_requirements import ROWS as DECIMAL_ROWS

NUMERIC={"control-reset":"The ordinary control fixture resets with204 before numeric-form interactions."}
QUESTION_IDS={"TK1-decimal-"+f+"-fraction" for f in ["slot_minutes","reservation_duration_minutes","cancellation_cutoff_minutes","capacity"]}
for f in ["slot_minutes","reservation_duration_minutes","cancellation_cutoff_minutes","capacity"]:
    for literal in ["1.0","1e0"]:
        key=f+"-"+literal
        NUMERIC[key]=f"A positive integral JSON number value1 written as {literal} remains a valid {f} fixture value; no body integer-notation rule is stated."
        QUESTION_IDS.add("TK1-numeric-"+key)
for literal in ["1.0","1e0"]:
    key="party-"+literal
    NUMERIC[key]=f"Integral party JSON number value1 written as {literal} is not refused as a noninteger; the plain-digit lexical restriction applies explicitly to queries."
    QUESTION_IDS.add("TK1-numeric-"+key)
NUMERIC.update({
    "unknown-exponent-create":"Create ignores an unknown field containing the syntactically valid, mathematically finite JSON number1e4300, without an unpublished floating conversion ceiling.",
    "unknown-exponent-signup":"Signup ignores that same valid unknown finite numeric field.",
    "unknown-exponent-reset":"Reset ignores that same valid unknown finite numeric field.",
    "unknown-failed-key-control":"A refused unknown-field create request consumes no idempotency key; ordinary integer-body control remains reusable.",
})
ROWS=copy.deepcopy(DECIMAL_ROWS)
for key,text in NUMERIC.items():
    row=copy.deepcopy(ROWS[0])
    row.update(requirement_id="TK1-numeric-"+key,source_section="3.4 Conventions / 4. Model / 5. Errors / 7. Idempotency / 8. API",source_line=86,
               owner="systems-engineer / interface-engineer" if "unknown-exponent" in key else "systems-engineer",
               implementation_owner="systems-engineer / interface-engineer" if "unknown-exponent" in key else "systems-engineer",
               requirement_text=text,case="numeric-forms",verification_method="independent raw JSON HTTP; source applicability review",
               candidate_full_revision="UNASSIGNED",executable_command_or_interaction="python numeric_forms_run.py --repo RESULT --workspace WORKSPACE --candidate FULL_REVISION --out NEW_DIRECTORY",
               evidence_path="UNVERIFIED",verdict="unverified",interpretation_note="Integral/fractional base-number error semantics are explicitly pending source adjudication, never established by the production parser's Python types." if "TK1-numeric-"+key in QUESTION_IDS else "The unknown value is finite mathematically and valid JSON grammar; it is not NaN/Infinity and no endpoint capacity rule applies to an ignored field.")
    ROWS.append(row)
assert len(ROWS)==932 and len({r["requirement_id"] for r in ROWS})==len(ROWS)
