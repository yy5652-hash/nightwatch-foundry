"""Prospective atomic decoder/deep receipt obligations from Stage1 only."""
from decoder_oracle import DEPTHS, SHAPES, grammar_cases, randomized_values

CASES = {}
def add(key, text, section="3.4 / 5 / 7 / 10", owner="systems-engineer"):
    assert key not in CASES, key
    CASES[key] = dict(requirement_id="TK1-decoder-"+key, source_section=section,
        source_line="see named Stage1 sections", requirement_text=text, owner=owner)

DEEP = {
    "reset":(204,None,"Valid ignored deep reset succeeds without imposing a nesting ceiling."),
    "signup":(201,None,"Valid ignored deep signup succeeds."),
    "login":(200,None,"Valid ignored deep login succeeds and supplies a second active session."),
    "second-token":(200,None,"The original session remains valid after another deep login."),
    "create":(201,None,"Valid ignored deep create issues a real original receipt."),
    "create-alias":(200,None,"An equal complete deep parsed body replays the original create response."),
    "create-precision":(409,"idempotency_key_reuse","A deep exact numeric difference conflicts before current resource checks."),
    "create-type":(409,"idempotency_key_reuse","A nested number/boolean difference conflicts."),
    "create-invalid-difference":(409,"idempotency_key_reuse","Used-key deep differences precede invalid party values."),
    "create-no-auth":(401,"unauthenticated","Valid deep writes still require authentication."),
    "create-no-key":(400,"missing_idempotency_key","Valid deep writes still require a key."),
    "second-create":(201,None,"A second ordinary booking provides a real atomic swap member."),
    "moves":(201,None,"A deep complete body and per-item ignored field preserve an atomic two-member swap."),
    "moves-alias":(200,None,"Deep move aliases replay the real original ordered batch receipt."),
    "moves-precision":(409,"idempotency_key_reuse","A deep exact move body difference conflicts."),
    "moves-type":(409,"idempotency_key_reuse","A nested numeric/type move difference conflicts."),
    "create-fraction":(422,"validation_failed","A valid deep fractional party reaches endpoint validation."),
    "create-fraction-atomic":(None,None,"A refused deep create preserves records and occupancy."),
    "create-failed-key":(201,None,"A deep refused create leaves its key reusable."),
    "move-fraction":(422,"validation_failed","A deep fractional move refuses without consuming the key."),
    "move-fraction-atomic":(None,None,"A refused deep batch preserves every record and occupancy."),
    "move-failed-key":(201,None,"A deep refused move leaves its key reusable."),
    "export":(200,None,"Export captures actual successful deep create and move receipts."),
    "amend":(200,None,"A real amendment changes the current booking after snapshot capture."),
    "cancel":(200,None,"A real cancellation changes current occupancy after snapshot capture."),
    "create-immutable":(200,None,"Original deep create replay remains unchanged after amendment and cancellation."),
    "moves-immutable":(200,None,"Original deep move replay remains unchanged after amendment and cancellation."),
    "bad-import":(400,"malformed_request","Malformed deep private import refuses before replacing state."),
    "bad-import-atomic":(None,None,"Malformed deep import preserves current records, sessions and original receipts."),
    "snapshot-lifetime":(None,None,"Captured immutable bytes remain unchanged through subsequent source writes."),
}
for shape in SHAPES:
    for depth in DEPTHS:
        stem=f"deep-{shape}-{depth}"
        for suffix,(_,_,text) in DEEP.items(): add(stem+"-"+suffix,text)
        for destination in ["peer","third"]:
            for suffix,text in {
                "import":"Unchanged actual deep export replaces an independent destination atomically.",
                "replaced-session":"Old destination sessions are removed by replacement.",
                "replaced-login":"Old destination credentials are removed by replacement.",
                "records":"Imported deep state retains real identities, assignment, timestamps and confirmed status.",
                "create-original":"The transferred deep original create receipt replays identically.",
                "moves-original":"The transferred deep original ordered swap receipt replays identically.",
                "difference":"A valid deep body difference retains used-key refusal after import.",
                "cancel":"An imported booking can be cancelled with its retained token.",
                "replay-cancelled":"A cancelled imported booking still replays its original receipt.",
                "repeat-import":"Repeating the unchanged deep import restores exported state without duplication.",
                "repeat-records":"Repeated replacement restores confirmed status and exactly the exported identities.",
            }.items(): add(stem+"-"+destination+"-"+suffix,text,"7 / 10")
        add(stem+"-peer-export", "A second independent process exports the genuinely imported deep receipts.","10")

for case in grammar_cases():
    if not case.valid and case.label in ["empty","bom"]:
        continue  # Absent HTTP body/BOM admission is not a new lexical mandate.
    if case.valid:
        for suffix in ["create","replay","moves","move-replay","cancel"]:
            add("grammar-"+case.label+"-"+suffix,"Valid ignored "+case.label+" JSON preserves "+suffix+" semantics.")
    else:
        for route in ["reset","signup","login","create","moves","patch","import"]:
            add("grammar-"+case.label+"-"+route,"Malformed "+case.label+" gives400 malformed_request on "+route+" before endpoint/auth checks.","3.4 / 5","interface-engineer")
        add("grammar-"+case.label+"-atomic","Malformed requests preserve all current records, sessions and keys.","1 / 7 / 10")
for label in ["null","array","string","number","boolean"]:
    add("top-level-"+label,"A parsed nonobject "+label+" request body gives400 malformed_request.","5","interface-engineer")
for item in randomized_values():
    for suffix,text in {
        "first":"A independently generated shallow ignored JSON value succeeds.",
        "alias":"Key order, whitespace, escaped strings and exact numeric aliases preserve complete identity.",
        "difference":"A separately generated exact value difference gives409 idempotency_key_reuse.",
        "immutable":"The original response survives a real current-state cancellation.",
    }.items(): add("random-"+item["label"]+"-"+suffix,text,"3.4 / 7; adopted numeric decision")
for key,text in {
    "charset":"Observed JSON responses have application/json;charset=utf-8.",
    "length":"Content-Length equals actual UTF-8 byte length, including exports.",
    "json":"Public/error responses parse as strict JSON without invalid constants.",
    "empty-204":"Every observed204 carries no payload.",
    "duration":"Every measured ordinary/control request respects its5/10second limit.",
    "no-5xx":"No actual decoder probe produces5xx or an unclassified transport failure.",
}.items():add(key,text,"2 / 3.4 / 5","interface-engineer")

def rows():
    return [dict(introduced_stage=1,applicable_stages="1,2,3,4",implementation_owner=v["owner"],
        verification_owner="independent-verifier",candidate_full_revision="PENDING_NAMED_CANDIDATE",
        verification_method="independent raw HTTP, inductive deep grammar and shallow exact-value oracle",
        case="decoder-strictness/deep-real-receipts",executable_command_or_interaction="PENDING explicit candidate7 execution release; prepared decoder_runtime.py",
        evidence_path="UNVERIFIED",verdict="unverified",normative=True,**v) for v in CASES.values()]
