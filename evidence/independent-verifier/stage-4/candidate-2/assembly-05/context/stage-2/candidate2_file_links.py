"""Prospective concrete-file binding repair; preserves sealed C2 observations."""
import csv
import datetime as dt
import hashlib
import io
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parents[2]
H = HERE / 'candidate-2'
OUT = H / 'file-link-addendum-01'
CANDIDATE = '4dba10246b07b2dda19de260d529f9d94ba0a1ed'
SEAL = 'cc271a32cfadec85a8deb578041c87ef099c9cfa'
PREFIX = str(H.relative_to(R)) + '/'
REQUIRED = ['requirement_id', 'requirement_text', 'source_section', 'source_line',
            'introduced_stage', 'applicable_stages', 'owner',
            'candidate_full_revision', 'verification_method',
            'executable_command_or_interaction', 'evidence_path', 'verdict',
            'implementation_owner', 'verification_owner']

SCREENSHOTS = {
    'TK2-visual-coherent': ['states-1280-selected.png', 'states-1280-successful.png',
                            'visual-375-search.png'],
    'TK2-visual-human-labels': ['states-1280-selected.png', 'states-1280-successful.png',
                              'visual-375-search.png'],
    'TK2-visual-actions': ['states-1280-selected.png', 'visual-1280-signup.png',
                          'visual-1280-login.png', 'visual-1280-lookup.png'],
    'TK2-visual-navigation': ['states-1280-selected.png', 'visual-1280-signup.png',
                             'visual-1280-login.png', 'visual-1280-lookup.png'],
    'TK2-visual-no-invented-facts': ['visual-375-search.png', 'visual-1280-signup.png',
                                   'visual-1280-login.png', 'visual-1280-lookup.png',
                                   'states-1280-successful.png'],
}
OBSERVATIONS = {
    'TK2-visual-coherent': 'The desktop selected/successful flow and mobile search show cream surfaces, green primary actions, clay accents, consistent serif headings and spacing, and distinct selected/confirmed presentation.',
    'TK2-visual-human-labels': 'Verifier Kitchen and Window Alcove, Garden Bench, Cedar Booth and Kitchen Nook are visible human labels. Together cards name both members; selection and confirmation name Garden Bench + Window Alcove.',
    'TK2-visual-actions': 'Find a table, Confirm booking, Create account, Sign in and Find reservation are prominent green primary buttons in the respective actual captures.',
    'TK2-visual-navigation': 'All four route captures retain the Tablekeeper brand and Find a table / Your reservation navigation. Signed-out auth links and signed-in Diner A / Sign out reflect actual session state.',
    'TK2-visual-no-invented-facts': 'The actual required-route and successful-flow captures show fixture names, availability, booking details and functional hospitality copy. They contain no reviews, ratings, restaurant photos, usage metrics or claims about real establishments. This remains a scoped reviewed-product observation.',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    protected = {}
    for name in ['coverage.csv', 'VERDICT.md', 'summary.json', 'coverage-bindings.json',
                 'review-checks.json', 'metadata-self-check.json', 'artifact-audit.json']:
        p = H / name
        blob = subprocess.check_output(['git', 'show', SEAL + ':' + str(p.relative_to(R))], cwd=R)
        assert p.read_bytes() == blob, name
        protected[name] = sha(blob)
    coordinator = R / 'evidence/coordinator/stage-2-candidate-2-metadata-audit.json'
    audit_raw = coordinator.read_bytes()
    audit = json.loads(audit_raw)
    assert audit['candidate_full_revision'] == CANDIDATE and audit['status'] == 'fail'
    assert len(audit['errors']) == 5
    original_raw = (H / 'coverage.csv').read_bytes()
    reader = csv.DictReader(io.StringIO(original_raw.decode()))
    fields = reader.fieldnames
    before = list(reader)
    after = [dict(row) for row in before]
    reviews = {x['requirement_id']: x for x in json.loads((H / 'review-checks.json').read_text())}
    replacements = []
    for row in after:
        rid = row['requirement_id']
        if rid not in SCREENSHOTS:
            continue
        screenshots = [PREFIX + 'browser-01/visual/' + name for name in SCREENSHOTS[rid]]
        evidence = screenshots + [PREFIX + 'review-checks.json',
                                  PREFIX + 'browser-01/visual/summary.json',
                                  PREFIX + 'file-link-addendum-01/visual-observations.json']
        old = row['evidence_path']
        row['evidence_path'] = ' ; '.join(evidence)
        assert reviews[rid]['passed']
        replacements.append(dict(requirement_id=rid, candidate=CANDIDATE,
                                 original_evidence_path=old, evidence_files=evidence,
                                 observation=OBSERVATIONS[rid], original_review=reviews[rid],
                                 screenshots_reinspected=True,
                                 basis='Existing genuine current-candidate captures and original review records; no service or browser rerun.',
                                 verdict='verified'))
    assert len(replacements) == 5
    (OUT / 'visual-observations.json').write_text(json.dumps(replacements, indent=2) + '\n')
    newline = '\r\n' if b'\r\n' in original_raw else '\n'
    with (OUT / 'coverage.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator=newline)
        writer.writeheader()
        writer.writerows(after)
    differences = []
    for old, new in zip(before, after):
        changes = [key for key in fields if old[key] != new[key]]
        if changes:
            assert old['requirement_id'] in SCREENSHOTS and changes == ['evidence_path']
            differences.append(dict(requirement_id=new['requirement_id'], fields=changes))
    assert len(differences) == 5 and len(after) == 6571
    errors = []
    evidence_files = set()
    for row in after:
        for field in REQUIRED:
            if not row[field].strip():
                errors.append(row['requirement_id'] + ': empty ' + field)
        assert row['candidate_full_revision'] == CANDIDATE and row['verdict'] == 'verified'
        for link in row['evidence_path'].split(';'):
            path = link.strip().split('#')[0]
            if not path or not (R / path).is_file():
                errors.append(row['requirement_id'] + ': not a concrete file ' + path)
            evidence_files.add(path)
    assert len({r['requirement_id'] for r in after}) == 6571
    assert sum(r['normative'] == 'True' for r in after) == 6549
    assert not errors, errors
    for name, digest in protected.items():
        assert sha((H / name).read_bytes()) == digest
    assert coordinator.read_bytes() == audit_raw
    record = dict(candidate_full_revision=CANDIDATE, original_evidence_seal=SEAL,
                  original_matrix_sha256=sha(original_raw), updated_matrix_sha256=sha((OUT / 'coverage.csv').read_bytes()),
                  protected_originals=protected, original_coordinator_audit=str(coordinator.relative_to(R)),
                  original_coordinator_audit_sha256=sha(audit_raw), original_coordinator_audit_status='fail',
                  rows=6571, normative_verified=6549, diagnostics_verified=22,
                  failed=0, unverified=0, required_metadata_fields=REQUIRED,
                  changed_rows=differences, all_other_fields_unchanged=True,
                  concrete_file_links_checked=len(evidence_files), errors=errors, status='pass',
                  no_service_rerun=True, production_changes=0,
                  checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                  scope='Independent prospective file-link metadata repair only; coordinator promotion/freeze remains a separate gate.')
    (OUT / 'metadata-self-check.json').write_text(json.dumps(record, indent=2) + '\n')
    unique_screens = sorted({PREFIX + 'browser-01/visual/' + name for names in SCREENSHOTS.values() for name in names})
    files = sorted(set(unique_screens + [PREFIX + 'review-checks.json', PREFIX + 'browser-01/visual/summary.json',
                                       str((OUT / 'coverage.csv').relative_to(R)),
                                       str((OUT / 'visual-observations.json').relative_to(R)),
                                       str((OUT / 'metadata-self-check.json').relative_to(R))]))
    manifest = [dict(path=p, bytes=(R / p).stat().st_size, sha256=sha((R / p).read_bytes())) for p in files]
    (OUT / 'file-proof.json').write_text(json.dumps(dict(candidate=CANDIDATE, manifest=manifest,
        source='Previously sealed genuine captures, freshly checked byte hashes; no reconstructed images.',
        self_reference='This manifest omits itself and the later addendum/commit seal.'), indent=2) + '\n')
    print(json.dumps(dict(status='pass', changed_rows=5, changed_fields=['evidence_path'],
                          all_concrete_files=True, matrix_rows=6571, normative_verified=6549,
                          protected_originals_unchanged=True, original_rejection_audit_unchanged=True,
                          service_reruns=0, errors=[])))


if __name__ == '__main__':
    main()
