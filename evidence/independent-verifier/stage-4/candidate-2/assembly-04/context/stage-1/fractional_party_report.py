"""Append supplemental exact-candidate rejection without changing previous evidence."""
import copy
import csv
import datetime as dt
import hashlib
import json
import shlex
import sys
from pathlib import Path
from fractional_party_requirements import CASES, SOURCE_LINES
from requirements import ROWS
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORKSPACE=REPO.parents[1]
TARGET=HERE/"candidate-5-supplemental-fraction"
data=json.loads((TARGET/"runtime-01/probes.json").read_text())
CANDIDATE=data["candidate_full_revision"]
assert CANDIDATE=="f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
argv=[str(WORKSPACE/".venv/bin/python"),"-B","evidence/independent-verifier/stage-1/fractional_party_run.py","--repo",str(REPO),"--workspace",str(WORKSPACE),"--candidate",CANDIDATE,"--out",str(WORKSPACE/"band-work/final-checks/independent-verifier-s1-f5e0a532-fraction-01")]
rows=[]
for key,(section,text) in CASES.items():
    rid="TK1-finite-party-"+key
    observed=[x for x in data["results"] if x["requirement_id"]==rid]
    assert observed,rid
    row=copy.deepcopy(ROWS[0])
    row.update(requirement_id=rid,source_section=section,source_line=SOURCE_LINES[key],
        requirement_text=text,candidate_full_revision=CANDIDATE,owner="interface-engineer" if key.startswith("literal-") else "systems-engineer",
        implementation_owner="interface-engineer" if key.startswith("literal-") else "systems-engineer",verification_owner="independent-verifier",
        verification_method="independent raw JSON HTTP; finite wire token independently classified with Decimal",
        case="finite-fractional-party",executable_command_or_interaction=shlex.join(argv),evidence_path=str((TARGET/"runtime-01/probes.json").relative_to(REPO))+"#"+rid,
        verdict="verified" if all(x["passed"] for x in observed) else "failed",interpretation_note="Explicit fractional party-size422 rule; no base-fixture fractional/integral-type assumption. LiteralNaN/Infinity remain invalid JSON.")
    rows.append(row)
with (TARGET/"coverage.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
commands=json.loads((TARGET/"runtime-01/commands.json").read_text())
identity=json.loads((TARGET/"runtime-01/identity.json").read_text())
assert commands[-1]["argv"][:3]==["docker","rm","-f"] and commands[-1]["returncode"]==0
now=dt.datetime.now(dt.timezone.utc)
start=dt.datetime.fromisoformat("2026-10-04T03:00:23.179+00:00")
summary=dict(candidate=CANDIDATE,verdict="reject",highest_independently_accepted_stage=0,
    rows=len(rows),verified=sum(r["verdict"]=="verified" for r in rows),failed=sum(r["verdict"]=="failed" for r in rows),unverified=0,
    http_requests=data["http_operations"],assertions=data["assertions"],failed_assertions=data["failed_assertions"],probe_seconds=data["duration_seconds"],
    max_ordinary_seconds=max(x["duration_seconds"] for x in data["operations"] if not x["path"].startswith("/_test/")),
    source_identity=identity,failed_ids=[r["requirement_id"] for r in rows if r["verdict"]=="failed"],
    earlier_verdict_evidence="6c01976c7b1b910f748efc97be7cc468b5963b18",earlier_matrix="932rows913verified5failed14unverified, preserved unchanged",
    no_repeat_official_checks="Existing candidate5 official120/120 and startup/complete coverage evidence remain; this is a targeted new boundary confirmation, not a full new candidate review.",
    started_at=start.isoformat(),finished_at=now.isoformat(),elapsed_seconds=(now-start).total_seconds(),
    harness="Codex",configured_model="gpt-6.1-sol",actual_model="unknown",effort="unknown",usage="unknown",catalog_estimated_cost="unknown",billed_spend="unknown",
    reporting_correction="Interim message8c8c66f3 incorrectly said41requests/0.152681s. Message2a4fe7a3 corrected actual38requests/0.0567245s; actual artifacts never changed.",
    limitations="Historical minute-wire/immutable legacy receipts remain as recorded; fourteen unrelated base/integral-number questions remain unresolved. Modest payload scope, not arbitrary-payload performance proof.")
assert summary["rows"]==35 and summary["failed"]==8 and summary["verified"]==27 and summary["http_requests"]==38
(TARGET/"summary.json").write_text(json.dumps(summary,indent=2))
table="\n".join(f"| {r['requirement_id']} | {r['source_section']} |" for r in rows if r["verdict"]=="failed")
(TARGET/"VERDICT.md").write_text(f"""# Stage1 candidate5 supplemental finite fractional party verdict: reject

Exact candidate `{CANDIDATE}` remains **reject**; highest accepted consecutive stage remains **0**. This supplemental independent confirmation adds **35 source-derived rows:27verified,8failed,0unverified**, from **38 HTTP requests/35 assertions/8 failures in{data['duration_seconds']:.9f}s**. The earlier full932-row verdict/matrix and all raw observations at evidence `6c01976c7b1b910f748efc97be7cc468b5963b18` are preserved unchanged. These supplemental counts are not a fabricated rerun or a claimed replacement cumulative count.

The valid raw JSON party token has4,301integer-part digits followed by`.5`. An independent standard-libraryDecimal parser confirms valid JSON grammar, finite mathematical value and nonintegrality; it is not the literalNaN/Infinity. The fixture has exact integer capacityN+1, exceedingN+.5, so capacity is not the trigger. Stage1§5 and§8 explicitly give invalid fractional party values422 `validation_failed`;§11 uses ordinary amendment codes for moves. No unresolved base-field fractional-type assumption is needed.

Create and moves return400 `malformed_request` / `Invalid JSON value`; expected422. The same correctly parsed/authenticated body returns that wrong400 before the required missing-key400 `missing_idempotency_key` and used-different-body409 `idempotency_key_reuse`. A batch involving a genuine API-created past or cancelled member also returns malformed400 rather than the specified cutoff/cancelled409. These are the eight failed requirement cases:

| Requirement | Source |
|---|---|
{table}

PATCH of a future confirmed booking correctly returns422; PATCH cutoff/cancelled precedence passes. Missing auth with the finite body returns401. All nine literalNaN/Infinity/-Infinity controls across create/PATCH/moves return400, and literalNaN before auth returns400. An exactly represented4,301-digit integer party is accepted201 with fitting capacity. Both failed create/move keys remain reusable; refused operations preserve whole exported state. Export bodies and credentials remain fingerprinted in artifacts.

Executed from the result root:

```sh
{shlex.join(argv)}
```

Use a new unique output path for reproduction. The independently authored probe, exact raw bodies, responses, lexical proof, assertions and timings are in `runtime-01/fractional_party_probe.py` and `runtime-01/probes.json`; argv/source hashes/resource inspection/cleanup are in `commands.json`, `client-source-proof.json`, `identity.json`, `image-hashes.json`, `inspect.json` and `cleanup.log`. A fresh detached exact clone built the complete image. Core/server hashes match the named candidate,2CPU/2GiB/networknone/no mounts; the separate HTTP client executes under those same container limits. The service and client are different Python processes; configuring the client cannot configure the service. Own service cleanup returned0; image/clone retained. Build cache was available. Ordinary maximum request duration is{summary['max_ordinary_seconds']:.9f}s.

After the HTTP probe completed and wrote all observations, the host driver's result reader hit its own4,300-digit integer conversion limit. The original driver/source/output and successful cleanup remain preserved; only the future host evidence reader is corrected. That metadata-reader error is not a service failure and does not erase the conclusive HTTP results. No HTTP rerun was made solely to repair a summary reader. An interim room message incorrectly reported41requests/0.152681s; the subsequent explicit correction binds the actual38requests/0.0567245s. Raw artifacts always contained measured values.

Previous official Stage1 checks remain120/120 from the exact candidate; they were not redundantly repeated for this rejecting boundary. This supplement took{summary['elapsed_seconds']:.3f}s from{start.isoformat()} to{now.isoformat()}; whole factory elapsed is coordinator-owned. HarnessCodex/configuredgpt-6.1-sol; actual override/effort/token usage/catalog-estimated cost/billed spend unknown. Historical exact-instant minute-wire offset and immutable original receipt interpretations remain disclosed. No production change or promotion is made. A complete scoped repair/candidate handoff and independent exact-revision execution are required.
""")
with (HERE.parent/"ledger.jsonl").open("a") as f: f.write(json.dumps(dict(utc=now.isoformat(),phase="stage1-candidate5-supplemental-finite-party",**summary))+"\n")
manifest=[dict(path=str(f.relative_to(TARGET)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in TARGET.rglob("*") if f.is_file()]
(TARGET/"artifact-manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:summary[k] for k in ["candidate","rows","verified","failed","unverified","http_requests","assertions","failed_assertions","probe_seconds","elapsed_seconds"]}))
