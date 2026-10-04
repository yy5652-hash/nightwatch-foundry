"""Audit a prospective ownership correction without touching sealed observations."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from coverage_metadata import REQUIRED, responsible_owner, validate

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
C6_SEAL = "7db8085f06bd6aa53443f5cf647ff4111bbaa771"
PREP_SEAL = "8b87ccdf5160d4e3e1dd1a40c5ca7b4495a98420"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    assert out.is_relative_to(HERE) and out.name.startswith("ownership-correction-")
    out.mkdir(parents=True, exist_ok=False)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    began = time.monotonic()
    commands = []
    checks = []

    def check(label, condition):
        assert condition, label
        checks.append(dict(label=label, passed=True))

    def git(argv):
        result = subprocess.run(["git"]+argv, cwd=REPO, capture_output=True)
        commands.append(dict(argv=["git"]+argv, returncode=result.returncode,
            stdout_sha256=digest(result.stdout), stderr_sha256=digest(result.stderr)))
        assert result.returncode == 0, argv
        return result.stdout

    prep = HERE / "candidate-7-preparation"
    c6_path = HERE / "candidate-6/coverage.csv"
    before_path = prep / "checks-03/coverage-cumulative-prepared.csv"
    after_path = prep / "checks-04/coverage-cumulative-prepared.csv"
    c6 = read_csv(c6_path)
    before = read_csv(before_path)
    after = read_csv(after_path)
    check("candidate6-sealed-csv-exact-bytes", git(["show", C6_SEAL+":"+str(c6_path.relative_to(REPO))]) == c6_path.read_bytes())
    git(["diff", "--exit-code", C6_SEAL, "--", str((HERE/"candidate-6").relative_to(REPO))])
    check("candidate6-entire-sealed-directory-unchanged", True)
    old_paths = git(["ls-tree", "-r", "--name-only", PREP_SEAL, "--", str(prep.relative_to(REPO))]).decode().splitlines()
    git(["diff", "--exit-code", PREP_SEAL, "--"]+old_paths)
    check("all-previously-sealed-preparation-files-unchanged", True)
    check("previous-prospective-csv-exact-sealed-bytes", git(["show", PREP_SEAL+":"+str(before_path.relative_to(REPO))]) == before_path.read_bytes())
    check("candidate6-row-count-and-separate-diagnostics", len(c6)==2679 and sum(r["normative"].lower()=="true" for r in c6)==2657)
    missing = [r for r in c6 if not r["owner"].strip()]
    check("coordinator-empty-owner-observation-reproduced", len(missing)==1273 and sum(r["normative"].lower()=="true" for r in missing)==1251)
    check("all-sealed-identifiers-and-candidate-binding", len({r["requirement_id"] for r in c6})==2679 and all(r["candidate_full_revision"]=="ab0cf79767b6768153a73894bf5768bf3328491a" for r in c6))
    check("explicit-historical-implementation-and-verification-owners", all(r["implementation_owner"].strip() and r["verification_owner"]=="independent-verifier" for r in c6))
    check("prospective-row-count-and-separate-diagnostics", len(before)==len(after)==4237 and sum(r["normative"].lower()=="true" for r in after)==4215)
    before_by_id = {r["requirement_id"]: r for r in before}
    check("prospective-identifiers-preserved", set(before_by_id)=={r["requirement_id"] for r in after})
    corrected = []
    for row in after:
        prior = before_by_id[row["requirement_id"]]
        old_values = {k:v for k,v in prior.items() if k not in ("owner", "ownership_metadata_basis")}
        new_values = {k:v for k,v in row.items() if k not in ("owner", "ownership_metadata_basis")}
        assert old_values == new_values, row["requirement_id"]
        if prior["owner"]:
            assert row["owner"] == prior["owner"]
        else:
            assert row["owner"] == prior["implementation_owner"] and row["ownership_metadata_basis"]
            corrected.append(dict(requirement_id=row["requirement_id"], normative=row["normative"],
                original_owner="", owner=row["owner"], implementation_owner=row["implementation_owner"],
                verification_owner=row["verification_owner"], basis=row["ownership_metadata_basis"]))
    check("only-owner-and-explicit-correction-basis-changed", len(corrected)==1273)
    check("joint-ownership-preserved", sum(r["owner"]=="systems-engineer / interface-engineer" for r in after)==57)
    metadata = validate(after)
    check("every-required-field-and-unique-owner-complete", metadata["empty_required_fields"]==0)
    check("all-prospective-evidence-still-unverified", all(r["candidate_full_revision"]=="PENDING_NAMED_CANDIDATE" and r["verdict"]=="unverified" and r["evidence_path"]=="UNVERIFIED" for r in after))

    def refused(label, operation):
        try:
            operation()
        except ValueError:
            check(label, True)
        else:
            raise AssertionError("Metadata gate unexpectedly accepted "+label)

    sample = dict(after[0])
    for field in REQUIRED:
        for value in ("", None):
            broken = dict(sample, **{field:value})
            refused("required-field-refusal-"+field+("-null" if value is None else "-empty"), lambda broken=broken: validate([broken]))
    refused("duplicate-identifier-refusal", lambda: validate([sample, sample]))
    refused("missing-implementation-not-defaulted", lambda: responsible_owner(dict(sample, owner="", implementation_owner="")))
    refused("unknown-implementation-not-defaulted", lambda: responsible_owner(dict(sample, owner="", implementation_owner="unassigned")))
    refused("wrong-verification-owner-refusal", lambda: responsible_owner(dict(sample, verification_owner="systems-engineer")))
    refused("owner-responsibility-mismatch-refusal", lambda: responsible_owner(dict(sample, owner="foundry-coordinator")))
    check("normalization-does-not-mutate-input", responsible_owner(dict(sample, owner=""))["owner"]==sample["implementation_owner"] and sample==after[0])
    current = json.loads((prep/"checks-04/preparation-summary.json").read_text())
    check("integrated-preparation-gates-440-pass-no-service-execution", current["local_checks"]==current["local_checks_passed"]==440 and all(current[k]==0 for k in ["service_requests","official_checks","images_built","containers_started"]))
    result = dict(scope="Coverage ownership metadata only; no new HTTP observation or acceptance", source_notice="39649b8c-8cdb-447b-9838-31e2f93f6333",
        candidate6_evidence_revision=C6_SEAL, previous_preparation_evidence_revision=PREP_SEAL,
        input_files=[dict(path=str(p.relative_to(REPO)),bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in [c6_path,before_path,after_path]],
        candidate6_rows=2679,candidate6_normative_rows=2657,candidate6_diagnostic_rows=22,missing_owner_rows=1273,
        missing_normative_owner_rows=1251,missing_diagnostic_owner_rows=22,
        corrected_ownership_counts=dict(Counter(r["owner"] for r in corrected)), prospective_ownership_counts=dict(Counter(r["owner"] for r in after)),
        prospective_rows=4237,prospective_normative_rows=4215,prospective_diagnostic_rows=22,prospective_verified=0,prospective_unverified=4237,
        metadata_validation=metadata,checks=len(checks),checks_passed=len(checks),checks_failed=0,
        checks_detail=checks,changed_rows=corrected,commands=commands,
        started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),audit_seconds=time.monotonic()-began,
        source_sha256=digest(Path(__file__).read_bytes()),service_requests=0,official_checks=0,resources_started=0,
        candidate6_behavioral_counts_unchanged=True,prior_sealed_bytes_unchanged=True,highest_accepted_stage=0,
        configured_model="gpt-6.1-sol",actual_model_effort_usage_spend="unknown")
    (out/"audit.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["checks","checks_passed","checks_failed","missing_owner_rows","prospective_rows","prospective_ownership_counts","audit_seconds","service_requests"]}))

if __name__ == "__main__":
    main()
