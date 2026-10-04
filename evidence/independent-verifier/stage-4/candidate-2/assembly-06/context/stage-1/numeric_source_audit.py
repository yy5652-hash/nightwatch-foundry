"""Clarify source interpretations using immutable independently executed traces."""
import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORKSPACE=REPO.parents[1]
TARGET=HERE/"candidate-5-numeric-source-audit"
TARGET.mkdir(exist_ok=False)
CANDIDATE="f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
with (HERE/"candidate-5/coverage.csv").open(newline="") as stream:
    rows=list(csv.DictReader(stream))
counts={v:sum(row["verdict"]==v for row in rows) for v in ["verified","failed","unverified"]}
assert len(rows)==932 and counts==dict(verified=913,failed=5,unverified=14)
fields=["slot_minutes","reservation_duration_minutes","cancellation_cutoff_minutes","capacity"]
base_ids=["TK1-decimal-"+field+"-fraction" for field in fields]
base_rows=[row for row in rows if row["requirement_id"] in base_ids]
assert len(base_rows)==4 and all(row["verdict"]=="unverified" for row in base_rows)
base_checks=json.loads((HERE/"candidate-5/decimal-04/probes/assertions.json").read_text())
base_checks=[check for check in base_checks if check["requirement_id"] in base_ids]
assert len(base_checks)==4
for check in base_checks:
    assert not check["passed"] and check["expected"]["status"]==422 and check["observed"]["status"]==400
executed_client=HERE/"candidate-5/decimal-04/helper-source-versions/decimal_probe.py"
client=executed_client.read_text()
assert '("fraction",1.5,422)' in client
# These four tests set the field to ordinary 1.5. Other configuration fields can
# retain the suite's giant integer, but the proposed fractional field is not giant.
baseline_types=[row for row in rows if row["requirement_id"].startswith("TK1-reset-type-")
                and any(field in row["requirement_id"] for field in fields)]
assert len(baseline_types)==20 and all(row["verdict"]=="verified" for row in baseline_types)
assert all(any(row["requirement_id"].endswith("-"+value) for value in ["string","bool","array","object","null"]) for row in baseline_types)
numeric=json.loads((HERE/"candidate-5/numeric-01/probes.json").read_text())
numeric_checks=[check for check in numeric["results"] if check["requirement_id"] in
                ["TK1-numeric-unknown-exponent-create","TK1-numeric-unknown-exponent-reset","TK1-numeric-unknown-exponent-signup"]]
assert len(numeric_checks)==3
assert sum(check["passed"] for check in numeric_checks)==1
fraction=json.loads((HERE/"candidate-5-supplemental-fraction/runtime-01/probes.json").read_text())
fraction_ids=["TK1-finite-party-create-value","TK1-finite-party-moves-value",
              "TK1-finite-party-reuse-before-value","TK1-finite-party-moves-reuse-before-value"]
fraction_checks=[check for check in fraction["results"] if check["requirement_id"] in fraction_ids]
assert len(fraction_checks)==4 and all(not check["passed"] and check["observed"]["status"]==400 for check in fraction_checks)
assert fraction["lexical_proof"]["mathematically_finite"] and fraction["lexical_proof"]["nonintegral"]
for name,value in [("pending-base-rows.json",base_rows),("base-fraction-observations.json",base_checks),
                   ("ordinary-base-type-rows.json",baseline_types),("definite-ignored-field-observations.json",numeric_checks),
                   ("definite-party-retry-observations.json",fraction_checks)]:
    (TARGET/name).write_text(json.dumps(value,indent=2))
source_files=[WORKSPACE/"kickoff/tablekeeper/spec/stage-1.md",HERE/"candidate-5/coverage.csv",
              HERE/"candidate-5/summary.json",HERE/"candidate-5/VERDICT.md",executed_client,
              HERE/"candidate-5/decimal-04/probes/assertions.json",HERE/"candidate-5/numeric-01/probes.json",
              HERE/"candidate-5-supplemental-fraction/runtime-01/probes.json",
              HERE/"candidate-5-supplemental-fraction/coverage.csv"]
proof=[dict(path=str(path.relative_to(WORKSPACE)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in source_files]
(TARGET/"source-proof.json").write_text(json.dumps(proof,indent=2))
start=dt.datetime.fromisoformat("2026-10-04T03:07:14.854+00:00")
now=dt.datetime.now(dt.timezone.utc)
summary=dict(candidate=CANDIDATE,kind="source applicability clarification; no HTTP rerun",new_http_requests=0,
             current_committed_full_matrix=dict(rows=932,**counts),pending_base_fraction_ids=base_ids,
             all_pending_numeric_ids=[row["requirement_id"] for row in rows if row["verdict"]=="unverified"],
             inherited_base_wrong_type_controls=20,observed_fractional_base_field_value="1.5",
             no_magnitude_dependent_type_rule=True,definite_unknown_endpoint_failures=2,
             supplemental_finite_party_matrix=dict(rows=35,verified=27,failed=8,unverified=0),
             previous_evidence_revisions=["6c01976c7b1b910f748efc97be7cc468b5963b18","f371edd40eb4a336b87a3358a6616d6c6dd6aabb"],
             started_at=start.isoformat(),finished_at=now.isoformat(),elapsed_seconds=(now-start).total_seconds(),
             verdict="reject",highest_accepted_stage=0,harness="Codex",configured_model="gpt-6.1-sol",
             actual_model="unknown",effort="unknown",usage="unknown",catalog_estimated_cost="unknown",billed_spend="unknown")
(TARGET/"summary.json").write_text(json.dumps(summary,indent=2))
base_table="\n".join(f"| `{rid}` | `1.5` | 400 | 422 | unverified |" for rid in base_ids)
(TARGET/"SOURCE-CLARIFICATION.md").write_text(f"""# Candidate 5 numeric source clarification

Exact candidate `{CANDIDATE}` remains **reject**, with highest accepted consecutive stage **0**. The current committed full matrix at `6c01976c7b1b910f748efc97be7cc468b5963b18` already has **932 rows: 913 verified, 5 failed, 14 unverified**. The earlier 917-row per-suite summary is a preserved intermediate observation. It does not supersede that full verdict. This audit makes **zero new HTTP requests** and does not change any prior row, assertion, count, raw response or report.

The four disputed reset status expectations are unverified. Their executed probe sets the proposed base field to ordinary `1.5`, rather than a 4,301-digit fractional value. Other fields in the fixture can retain the decimal suite's giant integer. The archived client source and assertion trace establish this distinction.

| Row | Proposed field value | Observed status | Provisional raw expectation | Current verdict |
|---|---|---|---|---|
{base_table}

Stage 1 §4 names the base minute counts and table capacity without an explicit JSON float-versus-integer type definition. Section 5 assigns wrong-type 400 and invalid-value 422, while giving party size an explicit endpoint-specific 422 rule. That does not by itself settle whether a fractional base count is a wrong field type or an invalid value. No magnitude-dependent classification is supported. These four base rows remain unverified for ordinary and large finite values until an applicable interpretation is justified. This audit does not claim execution of giant fractional base-field resets.

The original baseline has 20 verified base wrong-type rows: each of the four fields is exercised as string, boolean, array, object and null, with 400. It has no separately verified ordinary fractional base-field 400 rule. Those ordinary wrong-type controls therefore do not resolve the four fractional status questions. The other ten unresolved numeric-form rows concern eight base `1.0`/`1e0` cases and two party `1.0`/`1e0` cases. Their original responses and provisional assertions also remain unverified. Correct refusal atomicity was independently observed and is separate from the disputed error status.

Definite rejection grounds are independently supported by the written requirements and retained exact-candidate HTTP evidence:

- Stage 1 §§5/8 explicitly give a nonintegral party value 422; §11 uses ordinary amendment codes. The valid finite token with 4,301 integer-part digits plus `.5` instead returns 400 for create and moves. PATCH correctly returns 422. Independent grammar/finite/nonintegral classification uses Decimal only in the separate probe process.
- Stage 1 §3.4 requires unknown request fields to be ignored, never an error. An otherwise valid create body and reset fixture containing unknown `"unused":1e4300` instead return 400, where 201 and 204 are required. That token is valid finite JSON, with no recognized capacity/count constraint. Signup with the same unknown value returns 201. The two endpoint observations account for the full verdict's five failed linked rows; they are not five different HTTP failures.
- Stage 1 §7 resolves a used key and changed parsed body before endpoint validation or current-resource checks. The independently executed successful-create and successful-move keys, reused with valid finite fractional bodies, return 400 rather than the required 409 `idempotency_key_reuse`. Missing-key and batch cutoff/cancelled precedence failures are separately preserved in the same supplement. Literal NaN/Infinity controls correctly return 400 and are not used to justify treating finite numeric tokens as malformed.

The unknown-field evidence is `candidate-5/numeric-01/probes.json`, with complete executed command in `candidate-5/VERDICT.md`. The party and retry evidence is `candidate-5-supplemental-fraction/runtime-01/probes.json`, with full command and constrained source proof in that supplement's `VERDICT.md`. The latter independent supplement at `f371edd40eb4a336b87a3358a6616d6c6dd6aabb` has **35 rows: 27 verified, 8 failed, 0 unverified; 38 HTTP requests, 35 assertions, 8 failed assertions in 0.056724500 seconds**. These separate counts are not combined into a fabricated cumulative matrix or new run.

Run this audit from the result repository with `../../.venv/bin/python -B evidence/independent-verifier/stage-1/numeric_source_audit.py`; its output directory must not already exist. It only reads the specified own prior evidence and official source, verifies the links, and writes an append-only clarification. Source hashes, extracted row links and precise assertions are alongside this report. No builder probe implementation, production edit, new service execution or official test rerun is involved. Elapsed time through report generation: {summary['elapsed_seconds']:.6f} seconds. Actual model override, effort, usage and estimated/billed spend are unknown. Existing historical wire-offset and immutable original receipt interpretations remain unchanged. A complete scoped repair and independently executed new candidate are required before promotion.
""")
with (HERE.parent/"ledger.jsonl").open("a") as stream: stream.write(json.dumps(dict(utc=now.isoformat(),phase="candidate5-numeric-source-clarification",**summary))+"\n")
manifest=[dict(path=str(path.relative_to(TARGET)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
          for path in sorted(TARGET.rglob("*")) if path.is_file()]
(TARGET/"artifact-manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(summary))
