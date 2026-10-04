"""Source-derived obligations for finite bounded nesting samples."""
from nesting_input import DEPTHS,SHAPES
ENDPOINT_OBLIGATIONS={
    "first":"A valid write with an ignored bounded nested JSON value succeeds201.",
    "alias":"Complete-body exact numeric/object-order aliases replay the original receipt200.",
    "number-difference":"A changed precise numeric leaf under the same used key gives409 idempotency_key_reuse.",
    "type-difference":"Changing a numeric leaf to boolean under the used key gives409 idempotency_key_reuse.",
    "missing-auth":"A valid deep body without authentication gives401 unauthenticated.",
    "missing-key":"An authenticated valid deep write without a key gives400 missing_idempotency_key.",
    "failed-value":"A new-key valid deep body with fractional party gives422 validation_failed.",
    "failed-key-reuse":"Correcting the refused party with the same key succeeds201.",
    "atomic":"Replays and refused deep writes leave complete state unchanged before a later successful correction.",
    "immutable":"Original receipt replay remains200 and identical after current record mutation/cancellation.",
    "import-original":"Original deep receipt replays unchanged200 in an independent imported destination.",
    "import-difference":"A changed deep leaf still conflicts409 after independent replacement.",
}
SHARED_OBLIGATIONS={
    "reset":"A valid fixture with an ignored bounded nested value resets204.",
    "signup":"A valid signup with an ignored bounded nested value succeeds201.",
    "login":"A valid login with an ignored bounded nested value succeeds200.",
    "patch":"An ignored bounded nested PATCH value succeeds without changing state.",
    "export":"Export after deep successful writes returns200 valid JSON with the specified track/version/state envelope.",
    "import":"The unchanged opaque export imports204 into a separately running destination.",
    "replacement":"The independently imported full snapshot preserves the complete exact source state.",
    "retained-token":"The real source token and current private records survive independent replacement.",
    "malformed":"A truncated deep body remains400 malformed_request before auth/key processing.",
    "malformed-atomic":"Refusing truncated deep JSON leaves complete source state unchanged.",
}
CASES={}
for shape in SHAPES:
    for depth in DEPTHS:
        stem=shape+"-"+str(depth)
        for endpoint in ["create","moves"]:
            for key,text in ENDPOINT_OBLIGATIONS.items():
                CASES[stem+"-"+endpoint+"-"+key]=dict(requirement_id="TK1-nesting-"+stem+"-"+endpoint+"-"+key,requirement_text=endpoint+": "+text+" Shape/depth "+stem+".",source_section="3.4 / 5 / 6 / 7 / 8 / 10 / 11",source_line=86,implementation_owner="systems-engineer")
        for key,text in SHARED_OBLIGATIONS.items():
            CASES[stem+"-"+key]=dict(requirement_id="TK1-nesting-"+stem+"-"+key,requirement_text=text+" Shape/depth "+stem+".",source_section="3.3 / 3.4 / 5 / 7 / 10",source_line=86,implementation_owner="interface-engineer" if key=="malformed" else "systems-engineer")
for key,text in {"charset":"All observed payloads have application/json;charset=utf-8.","byte-length":"Observed Content-Length equals actual response bytes.","duration":"Measured ordinary/control requests remain below5/10seconds for these bounded samples.","no-5xx":"Bounded nested JSON samples produce no5xx responses."}.items():
    CASES[key]=dict(requirement_id="TK1-nesting-"+key,requirement_text=text,source_section="2 / 3.4 / 5",source_line=48,implementation_owner="interface-engineer")

def rows():
    return [dict(introduced_stage=1,applicable_stages="1,2,3,4",normative=True,verification_owner="independent-verifier",candidate_full_revision="PENDING_NAMED_CANDIDATE",verification_method="independent generated raw HTTP and exact JSON-value oracle",executable_command_or_interaction="python nesting_probe.py --base CURRENT_URL --peer INDEPENDENT_PEER_URL --candidate FULL_NAMED_CANDIDATE --out NEW_UNIQUE_DIRECTORY",evidence_path="UNVERIFIED",verdict="unverified",interpretation_note="No published nesting ceiling; finite bounded samples only, not arbitrary-depth performance.",**case) for case in CASES.values()]
