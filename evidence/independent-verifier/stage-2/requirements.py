"""Atomic Stage 2 ledger, derived from complete specs before product/test review."""
import copy
import csv
import importlib.util
from pathlib import Path

source = Path(__file__).resolve().parents[1]/"stage-1/requirements.py"
spec = importlib.util.spec_from_file_location("independent_stage1_requirements", source)
stage1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage1)
RESPONSE_FIELDS = stage1.RESPONSE_FIELDS
ROWS = copy.deepcopy(stage1.ROWS)
for row in ROWS:
    row.update(applicable_stages="2,3,4", candidate_full_revision="UNASSIGNED", verdict="unverified", evidence_path="UNVERIFIED")
    row["source_file"] = "stage-1.md"
    row["inherited"] = "yes"
    row["executable_command_or_interaction"] = "Run the original independent Stage 1 probe on the named Stage 2 service; no earlier pass substitutes for current evidence."


def add(section, line, case, entries, owner="systems-engineer", method="black-box HTTP"):
    for key, text in entries.items():
        ROWS.append(dict(requirement_id="TK2-"+key, source_section=section, source_line=line, introduced_stage=2,
                         applicable_stages="2,3,4", owner=owner, implementation_owner=owner, verification_owner="independent-verifier",
                         interpretation_note="", requirement_text=text, candidate_full_revision="UNASSIGNED", verification_method=method,
                         case=case, executable_command_or_interaction=f"python3 evidence/independent-verifier/stage-2/{'browser.py' if method.startswith('browser') else 'api.py'} --case {case} --candidate FULL_REVISION --out NEW_DIRECTORY",
                         evidence_path="UNVERIFIED", verdict="unverified", source_file="stage-2.md", inherited="no"))


add("Inheritance and sequential delivery", 3, "runtime", {
    "frozen-stage1": "Accepted Stage 1 remains byte-identical to the published freeze manifest.",
    "copied-base": "Stage 2 extends a complete accepted Stage 1 copy, with preserved source history.",
    "stage2-delivery": "Stage 2 has its own complete independent service, Dockerfile and reviewed RUN.md.",
    "stage2-source": "Current-stage authored history and source-input declarations support permitted source provenance.",
}, owner="interface-engineer", method="fresh-clone/history/source audit plus constrained HTTP")
for route, key in [("/", "search"), ("/signup", "signup"), ("/login", "login"), ("/lookup", "lookup")]:
    add("Required routes", 9, "routes", {
        "route-"+key: f"{route} loads its specified screen directly by URL.",
        "route-html-"+key: f"{route} returns HTML rather than the API JSON envelope.",
        "current-user-"+key: f"Signed-in display name is visibly present on {route}.",
    }, owner="interface-engineer", method="browser navigation/DOM")
for seating in ["single", "pair"]:
    add("Competing clients and uncertain outcomes", 26, "race-"+seating, {
        seating+"-stale-grid": "Delayed search A completing after B cannot replace B's grid.",
        seating+"-stale-labels": "Delayed A cannot replace the current restaurant/table labels from B.",
        seating+"-stale-form": "Delayed A cannot replace the selected B form or its local time/party values.",
        seating+"-race-error": "A competing client's occupancy refusal displays booking-error.",
        seating+"-race-refresh": "A confirmed occupancy refusal refreshes authoritative availability.",
        seating+"-race-form": "A confirmed occupancy refusal retains the selected booking form.",
        seating+"-race-inputs": "A confirmed occupancy refusal retains the form inputs.",
        seating+"-race-no-confirmation": "A refused attempt never displays a new confirmation.",
        seating+"-race-change-choice": "After a refusal the diner can select a different available option.",
    }, owner="interface-engineer", method="browser with actual API delivery gates and a competing HTTP client")
    for phase in ["precommit", "postcommit"]:
        add("Competing clients and uncertain outcomes", 31, "lost-"+seating, {
            seating+"-"+phase+"-uncertain": f"A {phase} lost response displays nonempty booking-uncertain text.",
            seating+"-"+phase+"-no-error": "A lost response shows no confirmed booking-error.",
            seating+"-"+phase+"-no-confirmation": "A lost response shows no new success confirmation.",
            seating+"-"+phase+"-same-key": "An unchanged uncertain form retries with the exact original Idempotency-Key.",
            seating+"-"+phase+"-same-body": "An unchanged uncertain form retries with the same parsed JSON body.",
            seating+"-"+phase+"-retry-reference": "Successful retry displays the actual successful original reference.",
            seating+"-"+phase+"-clear-uncertainty": "Successful retry removes the uncertainty element.",
            seating+"-"+phase+"-clear-error": "Successful retry has no booking-error element.",
            seating+"-"+phase+"-one-record": "A lost-response retry creates exactly one confirmed reservation.",
        }, owner="interface-engineer", method="browser request fault plus authoritative HTTP state")
    add("Booking form / confirmation", 95, "booking-"+seating, {
        seating+"-form-summary": "Booking summary contains every selected human table label and local start.",
        seating+"-form-party": "Booking party input is prefilled from the searched party size.",
        seating+"-form-retained": "The booking form remains visible after successful submission.",
        seating+"-repeat-reference": "Unchanged resubmission returns the same confirmation reference.",
        seating+"-repeat-no-error": "Unchanged successful resubmission has no booking-error.",
        seating+"-repeat-one-record": "Unchanged successful resubmission does not create a duplicate.",
        seating+"-edited-request": "A real field-value change produces a new request identity.",
        seating+"-same-value-request": "An unchanged value retains the retry identity despite an input event.",
        seating+"-confirmation": "A successful server response displays the confirmation container.",
        seating+"-reference-exact": "confirmation-reference text is exactly the actual reference.",
        seating+"-confirmation-details": "Confirmation details contain restaurant, human table labels and local start.",
    }, owner="interface-engineer", method="browser DOM/request identity plus HTTP state")
for identifier in ["signup-email", "signup-password", "signup-display-name", "signup-submit", "login-email", "login-password", "login-submit",
                   "logout-button", "restaurant-select", "date-input", "party-size-input", "search-button", "availability-grid", "booking-form",
                   "booking-summary", "booking-party-size", "booking-submit", "confirmation", "confirmation-reference", "confirmation-details",
                   "lookup-reference-input", "lookup-submit", "reservation-detail", "reservation-status"]:
    add("UI data-testid contract", 65, "contract", {"testid-"+identifier: f"The specified {identifier} element exposes its exact data-testid."}, owner="interface-engineer", method="browser DOM")
add("Signup and login", 65, "auth", {
    "signup-flow": "Signup through the actual UI creates an account and displays signed-in identity.",
    "login-flow": "Login through the actual UI authenticates the account and displays identity.",
    "auth-error-present": "A confirmed authentication refusal displays auth-error.",
    "auth-error-absent": "auth-error is absent when there is no authentication error.",
    "logout-state": "Logout returns the browser to signed-out identity and booking requires authentication again.",
}, owner="interface-engineer", method="browser with actual authentication API")
add("Search and availability", 80, "grid", {
    "restaurant-values": "Restaurant select option values are the actual restaurant IDs.",
    "date-value": "The date input value is a bare YYYY-MM-DD calendar date.",
    "party-input": "Search party size uses a number input.",
    "search-runs": "Search triggers availability for the actual selected restaurant/date/party.",
    "single-cells": "The grid has one correctly named cell per table per slot.",
    "cell-true": "A single cell has data-available=true exactly when its table is in available_table_ids.",
    "cell-false": "A single cell outside available_table_ids has data-available=false.",
    "available-click": "An available single cell opens the matching booking form.",
    "unavailable-click": "Clicking an unavailable cell does nothing.",
    "signed-out-click": "Signed-out available-cell selection shows auth-error or navigates to login.",
    "no-slots": "A day without slots shows no-slots instead of the availability grid.",
}, owner="interface-engineer", method="browser versus independently fetched API")
add("Lookup", 119, "lookup", {
    "lookup-found": "An owned reference displays reservation-detail.",
    "lookup-confirmed-exact": "An active reservation's status text is exactly confirmed.",
    "lookup-cancelled-exact": "A cancelled reservation's status text is exactly cancelled.",
    "lookup-cancel-button": "An active booking exposes reservation-cancel-button.",
    "lookup-cancel": "The actual lookup cancellation releases occupancy and displays cancellation.",
    "lookup-cancel-absent": "The cancellation button is absent once the booking is cancelled.",
    "lookup-not-found": "Unknown/other-owner lookup displays reservation-error without leaking details.",
    "lookup-cutoff": "A confirmed cutoff refusal displays reservation-error and retains current reservation truth.",
}, owner="interface-engineer", method="browser and authoritative HTTP state")
for width in [375, 1280]:
    for route in ["search", "signup", "login", "lookup"]:
        add("Product and visual direction", 45, "visual", {
            f"visual-{width}-{route}-usable": f"The required {route} flow is clear and usable at {width} CSS pixels.",
            f"visual-{width}-{route}-no-scroll": f"The {route} page has no horizontal page scrolling at {width} CSS pixels.",
            f"visual-{width}-{route}-labels": f"{route} inputs have visible labels at {width} CSS pixels.",
            f"visual-{width}-{route}-focus": f"Keyboard focus is apparent in the {route} flow at {width} CSS pixels.",
            f"visual-{width}-{route}-contrast": f"{route} text and controls have sufficient contrast at {width} CSS pixels.",
        }, owner="interface-engineer", method="browser screenshot/keyboard/computed-style review")
for state in ["available", "unavailable", "selected", "loading", "successful", "refused", "uncertain", "empty"]:
    add("Product and visual direction", 53, "visual", {"visual-state-"+state: f"The actual {state} state has distinct considered visual feedback."}, owner="interface-engineer", method="browser screenshots and observed DOM states")
add("Product and visual direction", 47, "visual", {
    "visual-coherent": "Warm hospitality presentation, hierarchy and typography/spacing/colour/control/feedback form a coherent product.",
    "visual-human-labels": "Human restaurant/table labels are prominent and combined options read as intentional seating.",
    "visual-actions": "Primary actions are easy to identify.",
    "visual-navigation": "Navigation is consistent across required routes.",
    "visual-no-invented-facts": "Product does not invent reviews, ratings, restaurant photos, usage counts or unsupported establishment claims.",
    "visual-offline-assets": "All browser fonts/assets/scripts/styles work from packaged runtime resources.",
}, owner="interface-engineer", method="browser screenshots/network and content review")
add("Existing clients after an upgrade", 129, "upgrade", {
    "stage1-genuine-export": "The frozen accepted Stage 1 process independently produces the imported export.",
    "stage1-import": "Stage 2 accepts the genuine earlier-service state.",
    "stage1-original-create": "Imported Stage 1 successful create receipts retain original JSON on replay.",
    "stage1-original-batch": "Imported Stage 1 successful batch receipts retain original JSON on replay.",
    "upgrade-browser-identity": "The already signed-in browser remains signed in through import.",
    "upgrade-browser-lookup": "The retained original reference still works in the lookup screen.",
    "upgrade-browser-form": "The open form and values survive import without reload.",
    "upgrade-browser-key": "The pending request retains its original key through import.",
    "upgrade-browser-body": "The pending request retains its original parsed body through import.",
    "upgrade-browser-original": "The uncertain retry recovers the original server confirmation after import.",
}, owner="interface-engineer", method="browser plus actual frozen/current HTTP processes and in-memory exports")
add("Combined tables / Model", 139, "model", {
    "fixture-combinable": "Restaurant configuration preserves declared combinable pairs in fixture order.",
    "fixture-absent-combinable": "Inherited fixtures without combinable retain supported single-table behavior.",
    "pair-unordered": "Reversed input order identifies the same declared pair.",
    "pair-capacity": "Pair capacity is the sum of both member capacities.",
    "pair-no-transitive": "Transitive undeclared pairs cannot be booked even when their capacities fit.",
    "pair-full-duration": "A confirmed pair occupies both members for the full absolute duration.",
    "seed-single-legacy": "Seeded legacy table_id bookings remain accepted.",
    "seed-single-array": "Seeded one-member table_ids bookings remain accepted.",
    "seed-pair": "Seeded table_ids pair bookings occupy both members.",
    "seed-default-status": "A seeded booking without status is confirmed.",
    "seed-cancelled-status": "A seeded cancelled booking is retained and does not occupy tables.",
})
add("GET /availability", 170, "availability", {
    "available-options": "Every slot includes available_options.",
    "available-options-table-ids": "Each option carries its canonical table_ids.",
    "available-options-capacity": "Each option carries its actual single/summed capacity.",
    "available-options-singles": "available_table_ids retains its original single-table-only meaning.",
    "available-options-capacity-filter": "Every available option has capacity at least the searched party size.",
    "available-options-member-filter": "Any occupied member excludes the entire pair option.",
    "available-options-complete": "Every qualifying free single and declared pair appears.",
    "available-options-single-order": "Singles appear first in fixture order.",
    "available-options-pair-order": "Pairs then appear in combinable declaration order.",
    "available-options-member-order": "Pair members appear in their declaration order.",
    "available-options-empty": "A slot with no qualifying/free options still exists with an empty options list.",
    "pair-half-open": "Pair occupancy ending exactly at a later start does not exclude that later option.",
})
for endpoint in ["create", "patch", "moves"]:
    add("POST /reservations / PATCH / Atomic moves", 203, "validation", {
        endpoint+"-legacy-single": "Legacy table_id means a one-member set and remains accepted.",
        endpoint+"-array-single": "A one-member table_ids set is accepted.",
        endpoint+"-array-pair": "A declared two-member table_ids set is accepted.",
        endpoint+"-both-fields": "Supplying table_id and table_ids together gives 422 validation_failed.",
        endpoint+"-unlisted-pair": "An undeclared two-member pair gives 422 combination_not_allowed.",
        endpoint+"-transitive-pair": "A transitive but undeclared pair gives 422 combination_not_allowed.",
        endpoint+"-too-many": "More than two table IDs gives 422 combination_not_allowed.",
        endpoint+"-duplicate": "Repeated table IDs give 422 validation_failed.",
        endpoint+"-taken-first": "An occupied first pair member gives 409 table_unavailable.",
        endpoint+"-taken-second": "An occupied second pair member gives 409 table_unavailable.",
        endpoint+"-capacity": "Party size above the summed pair capacity gives 422 party_exceeds_capacity.",
        endpoint+"-wrong-array-type": "A non-array table_ids field is 400 malformed_request under inherited type rules.",
        endpoint+"-wrong-member-type": "A non-string table ID is 400 malformed_request under inherited type rules.",
        endpoint+"-empty-array": "An empty table_ids set violates the required selection and gives 422 validation_failed.",
        endpoint+"-unknown-table": "An unknown table ID retains inherited 404 not_found behavior.",
        endpoint+"-foreign-table": "A table from another restaurant retains inherited 404 not_found behavior.",
        endpoint+"-rollback": "An invalid pair operation leaves records and occupancy unchanged.",
    })
for endpoint in ["create", "lookup", "list", "cancel", "patch", "moves"]:
    add("Response shapes", 205, "responses", {
        endpoint+"-single-table-ids": "Current singleton responses carry table_ids with their sole member.",
        endpoint+"-single-table-id": "Current singleton responses also carry the legacy table_id.",
        endpoint+"-pair-table-ids": "Current pair responses carry canonical table_ids in declared order.",
        endpoint+"-pair-no-table-id": "Current pair responses omit table_id.",
    })
add("PATCH / cancel / Atomic moves", 216, "transactions", {
    "patch-single-to-pair": "An amendment atomically switches a single to a declared pair.",
    "patch-pair-to-single": "An amendment atomically switches a pair to a single.",
    "patch-pair-to-pair": "An amendment atomically moves a pair to another pair with a shared member.",
    "cancel-pair-all-members": "Cancellation immediately releases every pair member.",
    "moves-pair-swap": "Several occupied pair/single assignments can swap atomically.",
    "moves-result-overlap": "Overlapping resulting pair/single assignments give table_unavailable.",
    "moves-unlisted-overlap": "A resulting pair overlapping an unlisted booking gives table_unavailable.",
    "moves-unchanged-occupancy": "An unchanged listed pair still occupies both members during transaction validation.",
    "moves-pair-order-errors": "Pair batch non-occupancy errors retain inherited input-order and cutoff precedence.",
    "pair-create-receipt": "Pair create replays return the exact original receipt after amendments/cancellation/import.",
    "pair-move-receipt": "Pair batch replays return the exact original receipt after amendments/cancellation/import.",
    "pair-reversed-key-conflict": "Reversed member-array JSON is a different parsed body for an already successful key.",
    "pair-key-validation-priority": "A used pair key with a different invalid body conflicts before pair/resource validation.",
    "pair-failed-key-reusable": "Rejected pair create/batch keys remain reusable.",
})
add("Combined table UI", 219, "pairs-ui", {
    "pair-cell-testid": "Available pair cells use slot-ta+tb-HH:MM in declaration order.",
    "pair-cell-availability": "Pair cells' availability agrees with authoritative available_options.",
    "pair-cell-opens": "An available pair cell opens the corresponding pair booking form.",
    "pair-summary-labels": "Pair booking-summary names every selected human table label.",
    "pair-confirmation-labels": "confirmation-tables contains every booked human table label.",
    "pair-lookup-labels": "reservation-tables contains every pair member's human table label.",
    "single-ui-unchanged": "Single cell IDs, confirmation and lookup retain the inherited required behavior.",
}, owner="interface-engineer", method="browser DOM against actual API")
add("Concurrent bookings and amendments", 237, "concurrency", {
    "pair-race-50": "Fifty competing pair/single creates sharing a member yield one occupant and no partial booking.",
    "pair-retry-50": "Fifty identical unused pair-key requests yield exactly one 201 and forty-nine identical 200 receipts.",
    "pair-create-patch-serial": "Concurrent pair create/amend/read observations admit a serial order respecting real-time completion.",
    "pair-move-cancel-serial": "Concurrent pair moves/cancel/read observations admit a serial order respecting real-time completion.",
    "pair-reads-atomic": "Every availability/list/export read observes intact pair occupancy without partial transitions.",
    "pair-random-oracle": "Deterministic saved mixed single/pair operation traces agree with an independent occupancy oracle.",
})
for field in ["reservation_id", "reference", "user_id", "created_at", "starts_at", "ends_at", "status"]:
    add("Existing clients after an upgrade / inherited export/import", 131, "upgrade", {
        "stage1-record-"+field: f"An imported genuine Stage 1 reservation retains its original {field}.",
    })
add("Existing clients after an upgrade", 131, "upgrade", {
    "stage1-token": "Genuine Stage 1 bearer tokens remain valid after Stage 2 import.",
    "stage1-password": "Imported Stage 1 hashed-password accounts remain able to log in.",
})
for field in ["reservation_id", "reference", "user_id", "created_at"]:
    add("PATCH / inherited amendment identity", 216, "transactions", {"patch-retained-"+field: f"Pair amendments retain original {field}."})
for aspect in ["occupancy", "configuration", "records", "tokens", "original-receipts"]:
    add("Inherited export/import of combined records", 233, "transactions", {"pair-import-"+aspect: f"Independent-process export/import preserves pair {aspect}."})
for zone, spring, fall in [("berlin", "2026-03-29", "2026-10-25"), ("new-york", "2026-03-08", "2026-11-01")]:
    add("Combined duration / inherited Time and DST", 141, "dst", {
        f"pair-{zone}-gap-availability": f"Skipped-hour starts are absent from {zone} pair availability on {spring}.",
        f"pair-{zone}-gap-create": f"Pair create for a nonexistent {zone} local time gives 422 invalid_local_time.",
        f"pair-{zone}-repeat-first": f"Pair starts in the {zone} repeated hour resolve to the first occurrence on {fall}.",
        f"pair-{zone}-repeat-once": f"Repeated local slots appear only once in {zone} availability.",
        f"pair-{zone}-absolute-duration": f"Pair duration is absolute time across the {zone} fall-back transition.",
    })
for field, value in [("outer-string", "a string combinable field"), ("entry-string", "a string pair entry"), ("member-number", "a nonstring pair member")]:
    add("Combinable fixture model / inherited type rules", 157, "fixture", {"fixture-pair-"+field: f"Reset rejects {value} with 400 malformed_request."})
for name in ["one-member", "three-members", "same-member-twice", "unknown-member", "foreign-member"]:
    add("Combinable fixture model / inherited value rules", 157, "fixture", {"fixture-pair-"+name: f"Reset rejects a {name} combinable entry violating an in-restaurant two-member pair with 422 validation_failed."})
for row in ROWS:
    if row["requirement_id"] in ["TK2-stage1-original-create", "TK2-stage1-original-batch"]:
        row["interpretation_note"] = "Pending coordinator receipt-shape interpretation: preserve successful original Stage 1 JSON even when it predates table_ids. This row is unverified until decision and actual replay evidence exist."

for seating in ["single","pair"]:
    for value in ["unsafe","scientific"]:
        prefix="integer-"+seating+"-"+value+"-"
        add("Inherited Stage 1 §§4,5,8 / Search, Booking form and Combined tables",95,"integer-boundary",{
            prefix+"reset":"A fitting base fixture with a positive integer capacity beyond 2^53 is accepted without an unstated numeric ceiling.",
            prefix+"api-control":"The exact plain-digit party-size API control offers the fitting singleton or declared pair.",
            prefix+"search-input":"The actual browser search input retains the entered plain-digit positive integer.",
            prefix+"query":"The actual browser emits that exact value as plain decimal query digits, without rounding or exponent notation.",
            prefix+"grid":"The fitting singleton/pair cell is available for the exact searched party size.",
            prefix+"prefill":"The booking party input is prefilled with the exact searched integer, without Number rounding.",
            prefix+"body":"The emitted request party_size is a JSON numeric value equal to the exact entered integer, not a rounded value or string.",
            prefix+"success":"The valid fitting exact-party request receives successful authoritative confirmation.",
            prefix+"stored":"The server's reservation lookup preserves the exact integer party_size.",
            prefix+"repeat-identity":"Unchanged large-integer resubmission retains the exact parsed JSON value and idempotency key; key order and whitespace remain immaterial.",
            prefix+"repeat-reference":"Unchanged large-integer resubmission recovers the same original reference with 200.",
            prefix+"one-record":"An unchanged large-integer resubmission leaves exactly one owned reservation.",
        },owner="interface-engineer",method="browser raw wire capture plus exact Python/Decimal HTTP oracle")
        for row in ROWS[-12:]:
            row["interpretation_note"]="Stage 1 fixture capacity and positive party_size have no stated maximum. Later policy limits do not restrict the base fixture. Query decimal spelling is mandatory; JSON body evidence is checked by exact numeric value, not host floating point."


def write_matrix(path):
    assert len({row["requirement_id"] for row in ROWS}) == len(ROWS)
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ROWS[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)


if __name__ == "__main__":
    write_matrix(Path(__file__).with_name("coverage-prepared.csv"))
    print(f"Prepared {len(ROWS)} atomic rows; {len(stage1.ROWS)} inherited; all unverified.")
