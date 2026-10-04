"""Additional Stage 1 decimal obligations, prepared independently of builders."""
import copy
from requirements import ROWS as BASE_ROWS

DECIMAL = {}
def add(key, text, section="4. Model / 5. Errors / 8. API / 10. Export and import"):
    DECIMAL[key] = (text, section)

FIELDS = ["slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "capacity"]
for field in FIELDS:
    for suffix, text in {
        "detail": "Restaurant detail serializes the exact 4301-digit value",
        "export": "Export is a read-only exact snapshot of the valid decimal configuration",
        "import": "Independent-process replacement/import retains the exact decimal configuration",
    }.items():
        add(f"decimal-{field}-{suffix}", f"{text} for {field}.")
    for label, text in {"boolean":"boolean", "string":"numeric string", "fraction":"fractional number", "negative":"negative integer", "zero":"zero"}.items():
        if field == "cancellation_cutoff_minutes" and label == "zero":
            continue
        add(f"decimal-{field}-{label}", f"{field} refuses a {text} with the existing type/value error distinction.")
        add(f"decimal-{field}-{label}-atomic", f"Refused {text} {field} reset leaves the entire prior state unchanged.")

for label in ["exponent", "fraction", "plus", "negative", "zero", "spaces"]:
    add("decimal-query-"+label, f"A {label} party query is refused with 422 validation_failed despite decimal conversion being enabled.", "5. Errors / 8. GET availability")
for label in ["boolean", "string", "fraction", "zero", "negative"]:
    add("decimal-party-"+label, f"Invalid {label} party_size retains 422 validation_failed and consumes no retry key.", "5. Errors / 7. Idempotency / 8. POST reservations")
    add("decimal-party-"+label+"-atomic", "The refused party-size request leaves configuration, reservations and receipts unchanged.")
for label in ["truncated", "leading-zero", "nan", "nonobject"]:
    add("decimal-json-"+label, f"The {label} raw JSON body gives 400 malformed_request.", "5. Errors")
    add("decimal-json-"+label+"-atomic", "Malformed raw JSON cannot replace current state.")

for key, text in {
    "query-empty": "A 4301-digit positive party query returns every fitting slot with empty singleton availability when capacity is smaller.",
    "grid-opening": "A huge positive grid yields only the fitting opening slot.",
    "grid-create": "A fitting opening-slot booking succeeds with a huge grid.",
    "grid-off": "Another local start outside the huge grid gives 422 not_on_slot_grid.",
    "grid-failed-key": "A refused huge-grid request's key remains usable for a valid booking.",
    "duration-empty": "A huge duration gives 200 with no fitting slots in the bounded local opening window.",
    "duration-create": "A create with non-fitting huge duration gives 422 outside_opening_hours.",
    "duration-atomic": "The huge-duration refusal leaves records and receipts unchanged.",
    "cutoff-create": "A future ordinary-duration booking can be created under a huge cutoff.",
    "cutoff-cancel": "Cancelling within a huge cutoff gives 409 cutoff_passed.",
    "cutoff-patch": "Amending within a huge current-start cutoff gives 409 cutoff_passed before invalid changes.",
    "cutoff-moves": "Batch validation gives 409 cutoff_passed before invalid changes for that member.",
    "cutoff-atomic": "Huge-cutoff refusals leave the whole state, occupancy and keys unchanged.",
    "cutoff-failed-key": "A failed huge-cutoff batch key remains usable for a legal batch in another restaurant.",
    "capacity-create": "A fitting 4301-digit integer party is accepted and returned exactly as a JSON number.",
    "capacity-query": "Availability uses exact integer capacity comparison at the 4301-digit boundary.",
    "capacity-over": "Capacity plus one gives 422 party_exceeds_capacity.",
    "capacity-over-atomic": "The capacity refusal leaves all state unchanged.",
    "patch-exact": "PATCH preserves an exact giant party value and booking identity.",
    "moves-exact": "An atomic two-member table swap returns exact giant party values in input order.",
    "moves-identity": "The giant-party swap retains both identities, ownership and creation timestamps.",
    "moves-rollback": "An invalid second giant-party move rolls back all listed bookings and receipts.",
    "moves-failed-key": "A failed giant-party move key can be reused for a valid move.",
    "ignored": "An unknown giant integer field is ignored by create validation.",
    "ignored-binding": "The complete parsed giant unknown field still participates in successful retry identity before invalid party validation.",
    "reordered-replay": "JSON key order/whitespace changes preserve successful giant-body replay.",
    "create-original": "Giant-party create replay after amendment/cancellation returns its exact original JSON receipt.",
    "batch-original": "Giant-party batch replay after amendment/cancellation returns its exact original JSON receipt.",
    "replacement": "Importing a giant populated snapshot removes destination credentials and data.",
    "tokens": "Original source session tokens remain valid after independent-process import.",
    "password-login": "Imported hashed credentials still authenticate with the original synthetic password.",
    "records": "Giant-valued records, identities, statuses and timestamps survive replacement exactly.",
    "import-create-original": "Imported giant-party create receipt replays unchanged with 200.",
    "import-batch-original": "Imported giant-party batch receipt replays unchanged with 200.",
    "repeat-import": "Repeated import restores the exact giant snapshot without duplicating state.",
    "invalid-import": "Invalid giant populated state import gives 422 validation_failed without changing destination.",
    "reset-clears": "Reset removes imported sessions, records and receipts.",
}.items():
    add("decimal-"+key, text)

ROWS = copy.deepcopy(BASE_ROWS)
for key, (text, section) in DECIMAL.items():
    row = copy.deepcopy(BASE_ROWS[-1])
    row.update(requirement_id="TK1-"+key, source_section=section, source_line=102,
               requirement_text=text, case="decimal-exact", verification_method="independent exact-integer black-box HTTP",
               interpretation_note="No base-field digit cap is stated; this probe is a modest 4301-digit value, not arbitrary-payload performance proof.",
               executable_command_or_interaction="python decimal_probe.py --base SOURCE --peer DESTINATION --candidate FULL_REVISION --out NEW_DIRECTORY")
    ROWS.append(row)
assert len({r["requirement_id"] for r in ROWS}) == len(ROWS)
