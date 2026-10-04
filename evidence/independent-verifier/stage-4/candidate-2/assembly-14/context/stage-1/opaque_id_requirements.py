"""Accepted opaque-ID usability obligations; fixture admission stays separate."""
from urllib.parse import quote,urlencode

VARIANTS={
    "ordinary":"ordinary_id",
    "slash":"room/floor",
    "question-fragment":"room?query#fragment",
    "literal-percent":"room%2Ffloor",
    "plus-semicolon":"room+floor;section",
    "space":"room floor",
    "unicode":"餐厅é",
    "astral":"room🍽",
    "mixed-reserved":"room/?#%+; é汉",
    "ascii64":"a"*64,
    "unicode64":"界"*64,
}
OBLIGATIONS={
    "list":"Public restaurant listing retains the accepted restaurant ID exactly.",
    "detail-status":"The correctly percent-encoded accepted restaurant detail route returns200.",
    "detail-identity":"Restaurant detail preserves accepted restaurant/table IDs in fixture order.",
    "availability":"Correctly encoded restaurant_id query returns exact IDs and the fitting fixture table order.",
    "create-status":"Create with exact accepted restaurant/table IDs succeeds201.",
    "create-identity":"Create response retains exact accepted IDs and a valid stable reference.",
    "create-replay":"An unchanged successful create body/key replays its original response200.",
    "lookup":"Owner lookup returns the same accepted IDs and reservation identity.",
    "amend":"Amendment to the second accepted table retains identity and returns that exact table ID.",
    "moves":"A batch move back to the first accepted table succeeds and preserves exact IDs/identity.",
    "import-current":"Unchanged export into an independent destination preserves token/current IDs/reference.",
    "import-original":"The original create receipt replays unchanged after independent replacement.",
    "cancel-release":"Cancel releases the exact accepted table ID in correctly encoded availability.",
    "unknown-route":"A correctly encoded unknown ordinary restaurant ID gives404 not_found.",
}
CASES={}
for surface in ["restaurant","table"]:
    for label,value in VARIANTS.items():
        stem=surface+"-"+label
        CASES[stem+"-admission"]=dict(requirement_id="TK1-opaque-"+stem+"-admission",requirement_text="Observe fixture admission for "+surface+" ID "+label+" before source applicability is adjudicated; no lexical defect inferred from refusal.",normative=False,source_section="3.4 / 4",source_line=90,implementation_owner="systems-engineer",verification_method="independent raw fixture admission diagnostic")
        for obligation,text in OBLIGATIONS.items():
            CASES[stem+"-"+obligation]=dict(requirement_id="TK1-opaque-"+stem+"-"+obligation,requirement_text=text+" Fixture scenario: "+surface+"/"+label+".",normative=True,source_section="3.3 / 3.4 / 4 / 7 / 8 / 10 / 11",source_line=90,implementation_owner="interface-engineer" if obligation.startswith("detail") else "systems-engineer",verification_method="independent raw HTTP conditional on accepted fixture")

def fixture(surface,value):
    from semantic_probe import fixture as base_fixture
    result=base_fixture();restaurant=result["restaurants"][0]
    restaurant["id"]=value if surface=="restaurant" else "ordinary-restaurant"
    restaurant["tables"]=restaurant["tables"][:2]
    restaurant["tables"][0]["id"]=value if surface=="table" else "ordinary-table"
    restaurant["tables"][1]["id"]="second-table"
    return result

def detail_path(value):return "/restaurants/"+quote(value,safe="",encoding="utf-8",errors="strict")
def availability_path(value):return "/availability?"+urlencode({"restaurant_id":value,"date":"2035-06-04","party_size":"2"},quote_via=quote,safe="",encoding="utf-8",errors="strict")

def rows():
    return [dict(introduced_stage=1,applicable_stages="1,2,3,4",verification_owner="independent-verifier",candidate_full_revision="PENDING_NAMED_CANDIDATE",evidence_path="UNVERIFIED",verdict="unverified",
                 interpretation_note="Fixture admission diagnostic is nonnormative pending chosen-format/source review; accepted-ID usability is conditional on reset204. No table-detail endpoint is invented.",
                 executable_command_or_interaction="python opaque_id_probe.py --base CURRENT_URL --peer INDEPENDENT_PEER_URL --candidate FULL_NAMED_CANDIDATE --out NEW_UNIQUE_DIRECTORY",**case) for case in CASES.values()]
