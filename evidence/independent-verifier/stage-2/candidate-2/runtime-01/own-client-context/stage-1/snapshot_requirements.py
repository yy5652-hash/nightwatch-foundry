"""Stage1 snapshot lifetime obligations; no assumption about private state shape."""
from snapshot_oracle import MODES,WAVES,STEPS
CASES={}
def add(key,text,section="10 / 11",owner="systems-engineer"):
    CASES[key]=dict(requirement_id="TK1-snapshot-"+key,requirement_text=text,source_section=section,source_line=417,implementation_owner=owner)
for mode in MODES:
    for generation in range(1,WAVES*STEPS+1):
        stem=mode+"-write-"+str(generation)
        add(stem+"-status","Atomic eight-record move first use succeeds201.","7 / 11")
        add(stem+"-order","Successful move receipt retains input order and exact complete generation state.","11")
    for wave in range(WAVES):
        stem=mode+"-"+str(wave)
        for route in ["export","list","availability"]:
            for key,text in {"status":"Concurrent read returns200.","json":"Entire captured response is valid JSON.","framing":"Response charset and byte-accurate length remain correct during concurrent writes."}.items():
                add(stem+"-"+route+"-"+key,route+": "+text,"2 / 3.4 / 5 / 10", "interface-engineer")
        add(stem+"-list-coherent","Read list is one complete legal atomic generation within the concurrent interval.","1 / 8 / 11")
        add(stem+"-list-identities","Read list retains all eight identities/timestamps while moves commit.","8 / 11")
        add(stem+"-availability-coherent","Availability respects the full unchanged occupancy and fixture order during atomic cyclic moves.","1 / 8 / 11")
        add(stem+"-export-envelope","Captured export retains track/version/state envelope.","10")
        add(stem+"-source-readonly","After writers settle, repeated reads/exports and receipt replays leave complete source state unchanged.","7 / 10")
        for destination in ["peer","third"]:
            prefix=stem+"-"+destination
            for key,text in {"import":"Unchanged captured raw export replaces an independent destination204.",
                "valid-token":"Real source bearer token remains valid after replacement.",
                "generation":"Imported private records form one complete legal generation.",
                "identities":"All imported source identities/statuses/timestamps remain unchanged.",
                "old-token-removed":"Replacement removes the destination's previous session.",
                "old-records-removed":"Replacement removes previous destination records.",
                "create-receipts":"Every successful original create receipt replays200 with its exact original response.",
                "move-receipts":"Every move committed in the captured generation's prefix replays200 with its exact original response.",
                "future-keys-absent":"Moves after the captured generation have no successful retry receipt; a changed invalid body gets422 rather than used-key409.",
                "replay-readonly":"All original replays leave the entire imported snapshot unchanged.",
                "repeat-import":"Repeating unchanged replacement204 preserves full exact snapshot without duplication.",
                "captured-unchanged":"Destination export remains the exact captured snapshot after later source writes and replays."}.items():
                add(prefix+"-"+key,text,"6 / 7 / 10 / 11")
for key,text in {"no-5xx":"No observed bounded concurrent request yields5xx.","ordinary-duration":"Non-held ordinary write/read requests finish within5seconds.","control-duration":"Non-held reset/import/export controls finish within10seconds."}.items():
    add(key,text,"2 / 5", "interface-engineer")

def rows():
    return [dict(introduced_stage=1,applicable_stages="1,2,3,4",normative=True,verification_owner="independent-verifier",
        candidate_full_revision="PENDING_NAMED_CANDIDATE",verification_method="independent deterministic raw HTTP race captures, observable generation oracle and unchanged independent-process replacement",
        executable_command_or_interaction="python snapshot_probe.py --base CURRENT_URL --peer INDEPENDENT_DESTINATION_1 --third INDEPENDENT_DESTINATION_2 --candidate FULL_NAMED_CANDIDATE --out NEW_UNIQUE_DIRECTORY",
        evidence_path="UNVERIFIED",verdict="unverified",interpretation_note="Client events expose HTTP response lifetime; server-internal serialization interleaving is not inferred. Private state stays opaque; bounded schedule only.",**case) for case in CASES.values()]
