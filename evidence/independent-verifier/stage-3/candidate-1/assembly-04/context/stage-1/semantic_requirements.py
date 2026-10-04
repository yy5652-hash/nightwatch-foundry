"""Atomic prospective obligations from Stage 1 and the recorded number decision."""
CASES={}
def add(key,text,section="3.4 / 5 / 7 / 8",line=172,owner="systems-engineer"):
    assert key not in CASES,key
    CASES[key]=dict(requirement_id="TK1-semantic-"+key,source_section=section,source_line=line,
                    requirement_text=text,owner=owner)

FIELDS=["slot_minutes","reservation_duration_minutes","cancellation_cutoff_minutes","capacity","party_size"]
ALIASES=["integer","decimal","exponent","trailing-zero","giant-decimal","compact-exponent"]
FRACTIONS=["ordinary","giant","tiny-exponent"]
WRONG_TYPES=["boolean","string","null","array","object"]
BAD_JSON={
    "utf8":b'{"n":"\xff"}',"utf16":'{"n":1}'.encode("utf-16"),"utf32":'{"n":1}'.encode("utf-32"),
    "nan":b'{"n":NaN}',"infinity":b'{"n":Infinity}',"negative-infinity":b'{"n":-Infinity}',
    "leading-zero":b'{"n":01}',"plus":b'{"n":+1}',"leading-dot":b'{"n":.5}',
    "trailing-dot":b'{"n":1.}',"exponent-empty":b'{"n":1e}',"exponent-sign":b'{"n":1e+}',
    "hex":b'{"n":0x1}',"trailing-data":b'{"n":1}{}',"invalid-escape":b'{"n":"\\q"}',
    "raw-newline":b'{"n":"a\nb"}',"nonobject-null":b'null',"nonobject-array":b'[]',
    "nonobject-boolean":b'true',"nonobject-number":b'1.0',"nonobject-string":b'"hello"',
}
for label in BAD_JSON:
    add("syntax-"+label,"Malformed encoding/JSON or nonobject body "+label+" gives400 malformed_request before authentication.","3.4 / 5",160,"interface-engineer")
for key,text in {
    "charset":"Every observed JSON response has application/json;charset=utf-8.",
    "byte-length":"Response Content-Length equals the actual UTF-8 byte length.",
    "bare-numbers":"Successful count/configuration/receipt values remain bare JSON number tokens.",
    "finite-response-json":"Every nonempty response is valid JSON with no nonfinite constants.",
    "empty-204":"Every204 reset/import response has no payload.",
    "request-duration":"Measured ordinary/control requests remain within their respective5/10second limits.",
    "no-5xx":"Numeric boundary requests never produce5xx.",
    "public-no-profile":"Ordinary public receipts/details do not expose private numeric_profile metadata.",
}.items(): add(key,text,"2. Resource limits / 3.4 / 10",86,"interface-engineer")
for field in FIELDS:
    for alias in ALIASES:
        add("count-"+field+"-"+alias,"The exact positive whole "+field+" value using "+alias+" JSON spelling is accepted under the adopted interpretation.","4 / 5 / 8; numeric decision5e7bd528",100)
        add("count-"+field+"-"+alias+"-wire","The accepted "+field+" exact value is preserved as a numeric wire token.","3.4 / 4 / 8 / 10",86,"interface-engineer")
    for fraction in FRACTIONS:
        add("fraction-"+field+"-"+fraction,"A finite "+fraction+" fractional "+field+" gives422 validation_failed, independent of magnitude.","4 / 5 / 8; numeric decision5e7bd528",172)
        add("fraction-"+field+"-"+fraction+"-atomic","A refused fractional "+field+" leaves whole state unchanged.","1 / 10",18)
    for kind in WRONG_TYPES:
        code="422 validation_failed" if field=="party_size" else "400 malformed_request"
        add("wrong-"+field+"-"+kind,kind+" "+field+" gives"+code+"; booleans do not acquire numeric meaning.","5 / 8",172)
        add("wrong-"+field+"-"+kind+"-atomic","A wrong-type "+field+" refusal leaves state unchanged.","1 / 10",18)
    for sign in ["zero","negative"]:
        add("minimum-"+field+"-"+sign,"An exact "+sign+" count obeys this field's minimum; only cutoff permits zero.","4 / 5 / 8",100)
for field in FIELDS:
    add("missing-"+field,"Missing required "+field+" gives422 validation_failed.","5 / 8",166)
for family,text in {
    "grid":"A compact immense positive grid gives only the opening candidate when duration fits.",
    "duration":"A compact immense duration gives no fitting starts and outside_opening_hours without constructing a huge endpoint.",
    "cutoff":"A compact immense cutoff refuses a future cancellation/amendment/batch with cutoff_passed before invalid changes.",
    "capacity":"A compact immense capacity admits fitting huge integral party values and preserves exact values.",
}.items(): add("bounded-"+family,text,"4 / 8; numeric decision5e7bd528",305)
for label in ["fraction","plus","negative","exponent","spaces","zero"]:
    add("query-"+label,"The recognized integer query with "+label+" spelling remains422 validation_failed.","5 / 8",175)
for path in ["reset","signup","login","create","patch","moves","import"]:
    add("ignored-"+path,"Nested ignored finite huge/tiny/fractional numbers never make a valid "+path+" request malformed.","3.4 / 7",88)
add("escaped-string","Ignored escaped strings retain their actual JSON values without confusing numeric token processing.","3.4 / 7",88,"interface-engineer")
add("valid-utf8","A valid UTF-8 body containing non-ASCII text is decoded and returned faithfully.","3.4 / 6",86,"interface-engineer")

CURRENT_EQ=["original","numeric-alias","zero-alias","object-order","tiny-difference","large-rounded-difference", "boolean-difference","string-difference","array-order","missing-ignored","invalid-party-difference","unknown-resource-difference"]
for endpoint in ["create","moves"]:
    for variant in CURRENT_EQ:
        add("identity-"+endpoint+"-"+variant,"Current "+endpoint+" key comparison for "+variant+" follows complete recursive exact JSON value before resource/field checks.","7; numeric decision5e7bd528",243)
    for variant in ["missing-key","missing-auth","fraction","failed-key-reuse","immutable","import-original"]:
        add("precedence-"+endpoint+"-"+variant,endpoint+": "+variant+" obeys authentication/key/value ordering, failure rollback and original receipt requirements.","5 / 6 / 7 / 8 / 11",243)
    add("profile-new-"+endpoint,"New successful "+endpoint+" receipt has private exact-v1 semantics.","7 / 10; agreed receipt contract",435)
    add("identity-"+endpoint+"-atomic","All same-key replays/refusals preserve the entire current state.","1 / 7 / 10",18)
for endpoint in ["patch","moves"]:
    for reason in ["cutoff","cancelled"]:
        add("ordering-"+endpoint+"-"+reason,"The current "+reason+" refusal precedes a proposed finite fractional party value for "+endpoint+".","8 / 11",387 if endpoint=="patch" else 459)
LEGACY_EQ=["original","rounded-alias","underflow-alias","same-integer","different-integer","boolean","string","overflow"]
for phase in ["source","base","peer","third"]:
    for endpoint in ["create","moves"]:
        for alias in LEGACY_EQ:
            add("legacy-"+phase+"-"+endpoint+"-"+alias,"Genuine old "+endpoint+" receipt in "+phase+" preserves source parser meaning for "+alias+"; current destinations give409 for different valid overflow bodies.","7 / 10; adopted historical numeric decision",435)
for phase in ["base","peer","third"]:
    for obligation in ["unchanged-import","token","second-token","password","reference","old-response","profile","snapshot-readonly","archived-numbers"]:
        add("legacy-"+phase+"-"+obligation,"Genuine old unchanged export in "+phase+" preserves "+obligation+", independent of source process.","10",435)
    for obligation in ["profiles","exact-alias","exact-rounded-conflict","exact-underflow-conflict","exact-integer-conflict","exact-move-alias","exact-move-rounded-conflict","exact-move-underflow-conflict","exact-move-integer-conflict","repeat-import","replaced-token"]:
        add("mixed-"+phase+"-"+obligation,"Mixed legacy/current state in "+phase+" preserves receipt-scoped semantics and "+obligation+" through independent replacement.","7 / 10; numeric decision5e7bd528",435)
for endpoint in ["create","moves"]:
    add("archived-exact-"+endpoint,"Current "+endpoint+" receipt archives preserve exact ignored numbers without rounding or string substitution.","7 / 10; numeric decision5e7bd528",435)
for profile in ["exact-v1","python-json-v1"]:
    for error in ["missing","unknown","wrong-type"]:
        add("invalid-profile-"+profile+"-"+error,"Removing or invalidating a "+profile+" schema2 receipt profile gives422 validation_failed.","10; agreed private-format contract",427)
        add("invalid-profile-"+profile+"-"+error+"-atomic","Invalid "+profile+" receipt-profile import leaves all destination state unchanged.","10",427)

def row_list():
    return [dict(introduced_stage=1,applicable_stages="1,2,3,4",implementation_owner=case["owner"],
                 verification_owner="independent-verifier",interpretation_note="Prospective adopted numeric decision; no prior observation reclassified.",
                 candidate_full_revision="PENDING_NAMED_CANDIDATE",verification_method="independent raw HTTP + separate exact numeric/source-projection oracle",
                 case="semantic-current-and-legacy",executable_command_or_interaction="python semantic_probe.py --base CURRENT --peer PEER --third THIRD --legacy GENUINE_49287b4 --candidate FULL_REVISION --out NEW_DIRECTORY",
                 evidence_path="UNVERIFIED",verdict="unverified",**case) for case in CASES.values()]
