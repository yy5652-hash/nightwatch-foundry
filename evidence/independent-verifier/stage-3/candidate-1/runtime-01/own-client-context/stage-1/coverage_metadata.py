"""Prospective verifier metadata gate; does not establish behavioral coverage."""
REQUIRED = (
    "requirement_id", "requirement_text", "source_section", "source_line",
    "introduced_stage", "applicable_stages", "owner", "candidate_full_revision",
    "verification_method", "executable_command_or_interaction", "evidence_path",
    "verdict", "implementation_owner", "verification_owner",
)
SEATS = {"systems-engineer", "interface-engineer", "independent-verifier", "foundry-coordinator"}
RESPONSIBILITIES = SEATS | {"systems-engineer / interface-engineer"}

def _text(value):
    return "" if value is None else str(value).strip()

def responsible_owner(row):
    """Use existing explicitly assigned implementation responsibility, never a default."""
    result = dict(row)
    implementation = _text(result.get("implementation_owner"))
    verifier = _text(result.get("verification_owner"))
    if implementation not in RESPONSIBILITIES or verifier != "independent-verifier":
        raise ValueError("Missing/unknown implementation or verification ownership: "+result.get("requirement_id", "?"))
    if not _text(result.get("owner")):
        result["owner"] = implementation
        result["ownership_metadata_basis"] = "Filled prospectively from this row's existing explicit implementation_owner; historical matrices unchanged."
    if result["owner"] not in RESPONSIBILITIES or result["owner"] != implementation:
        raise ValueError("Owner/implementation responsibility mismatch: "+result.get("requirement_id", "?"))
    return result

def validate(rows):
    missing = [(r.get("requirement_id", "?"), field) for r in rows for field in REQUIRED if not _text(r.get(field))]
    if missing:
        raise ValueError("Incomplete coverage metadata: "+repr(missing[:10]))
    if len({r["requirement_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate requirement identifiers")
    for r in rows:
        responsible_owner(r)
    return dict(rows=len(rows),required_fields=list(REQUIRED),empty_required_fields=0,unique_identifiers=True,
        responsible_ownership_complete=True,implementation_and_verification_explicit=True)
