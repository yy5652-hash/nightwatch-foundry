"""Source obligations for finite giant fractional party and strict JSON controls."""
CASES={}
def add(key,section,text): CASES[key]=(section,text)
add("reset-control","3.3 Reset / 4. Model","A fitting positive integer fixture capacity above the finite fractional party value resets successfully.")
add("signup-control","6. Authentication","Ordinary signup issues a real token before protected fractional-party tests.")
add("create-control","8. POST reservations","Ordinary integral party creates a real booking and successful original key receipt.")
for key,section,text in [
    ("create-value","5. Errors / 8. POST reservations","A mathematically finite 4301-digit integer-part-plus-.5 party value is invalid because it is nonintegral, and gives422 validation_failed, not a JSON grammar refusal."),
    ("create-atomic","1. Scope / 8. POST reservations","A refused finite fractional create leaves all records, occupancy and retry state unchanged."),
    ("missing-key","7. Idempotency","Missing create key gives400 missing_idempotency_key before endpoint validation of a correctly parsed/authenticated finite fractional body."),
    ("reuse-before-value","7. Idempotency","A used create key with a different finite fractional body gives409 idempotency_key_reuse before endpoint field validation."),
    ("key-errors-atomic","1. Scope / 7. Idempotency","Refused create key/mismatch requests leave the complete state unchanged."),
    ("authentication","6. Authentication / 7. Idempotency","A missing caller token with a valid finite fractional JSON body gives401 unauthenticated."),
    ("failed-key-reusable","7. Idempotency","A finite fractional create refusal consumes no retry key; the corrected ordinary create succeeds201."),
    ("patch-value","5. Errors / 8. PATCH reservations","A finite fractional party amendment of a future confirmed booking gives422 validation_failed."),
    ("patch-atomic","8. PATCH reservations","A refused finite fractional amendment leaves the original record/occupancy and other state unchanged."),
    ("moves-value","5. Errors / 11. Atomic reservation moves","A finite fractional party in an otherwise valid future confirmed move uses ordinary amendment422 validation_failed."),
    ("moves-atomic","11. Atomic reservation moves","A refused finite fractional batch leaves all records, occupancy and retry state unchanged."),
    ("moves-missing-key","7. Idempotency / 11. Atomic reservation moves","A missing move key gives400 missing_idempotency_key before member value validation."),
    ("moves-failed-key-reusable","7. Idempotency / 11. Atomic reservation moves","A failed finite fractional batch consumes no key; a corrected move with that key succeeds201."),
    ("moves-reuse-before-value","7. Idempotency / 11. Atomic reservation moves","A successful move key reused with a different finite fractional body gives409 idempotency_key_reuse before member validation."),
    ("huge-integer-control","4. Model / 5. Errors / 8. POST reservations","An exactly represented 4301-digit positive integral party succeeds when the table has fitting exact capacity."),
    ("literal-before-auth","5. Errors / 7. Idempotency","The literalNaN is invalid JSON and gives400 malformed_request before application authentication."),
    ("past-create-control","4. Model / 8. POST reservations","A genuine past booking is created over HTTP and is not refused solely for its past date."),
    ("patch-cutoff-before-value","8. PATCH reservations","A current-start cutoff refusal precedes amendment field validation, even with a finite giant fractional proposed party."),
    ("moves-cutoff-before-value","11. Atomic reservation moves","A listed member's existing cutoff error precedes its finite fractional proposed change validation."),
    ("cutoff-atomic","8. PATCH / 11. Atomic reservation moves","Cutoff refusals leave the complete state unchanged."),
    ("cancel-control","8. Cancel reservations","A future ordinary confirmed booking cancels authoritatively before cancelled-member probes."),
    ("patch-cancelled-before-value","8. PATCH reservations","A cancelled booking amendment returns409 reservation_cancelled for a finite fractional proposed value."),
    ("moves-cancelled-before-value","11. Atomic reservation moves","A cancelled listed member returns409 reservation_cancelled for a finite fractional proposed value."),
]: add(key,section,text)
for literal in ["NaN","Infinity","-Infinity"]:
    for method,path in [("POST","reservations"),("PATCH","reservations"),("POST","reservation-moves")]:
        add("literal-"+literal+"-"+method+"-"+path,"5. Errors",f"{method} /{path}: literal{literal} is not a JSON number and gives400 malformed_request, independent of finite fractional values.")
assert len(CASES)==35

# Exact primary source lines in the unchanged official Stage 1 specification.
SOURCE_LINES={
    "reset-control":80,"signup-control":197,"create-control":329,
    "create-value":172,"create-atomic":18,"missing-key":250,
    "reuse-before-value":243,"key-errors-atomic":18,"authentication":214,
    "failed-key-reusable":254,"patch-value":387,"patch-atomic":390,
    "moves-value":459,"moves-atomic":467,"moves-missing-key":250,
    "moves-failed-key-reusable":254,"moves-reuse-before-value":243,
    "huge-integer-control":352,"literal-before-auth":160,
    "past-create-control":144,"patch-cutoff-before-value":387,
    "moves-cutoff-before-value":462,"cutoff-atomic":467,
    "cancel-control":371,"patch-cancelled-before-value":388,
    "moves-cancelled-before-value":461,
}
SOURCE_LINES.update({key:160 for key in CASES if key.startswith("literal-")})
assert set(SOURCE_LINES)==set(CASES)
