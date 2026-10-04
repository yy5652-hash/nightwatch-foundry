"""Audit frozen-stage matrix metadata and inspectable artifact paths.

This is coordinator bookkeeping, not independent service verification.
Run from any clone: python3 evidence/coordinator/audit_coverage.py
Prints JSON; does not rewrite an existing verdict, matrix or evidence file.
"""
import csv
import hashlib
import json
from pathlib import Path
from acceptance_state import current_manifests, verify_history

RESULT = Path(__file__).resolve().parents[2]
reports = []
verify_history()
for manifest, saved in current_manifests():
    verdict = RESULT / saved['independent_verdict_path']
    matrix = verdict.parent / 'coverage.csv'
    rows = list(csv.DictReader(matrix.open()))
    errors = []
    required = ['requirement_id', 'source_section', 'applicable_stages', 'owner',
                'candidate_full_revision', 'verification_method',
                'executable_command_or_interaction', 'evidence_path', 'verdict']
    seen = set()
    for row in rows:
        label = row.get('requirement_id', '<missing id>')
        if label in seen:
            errors.append(label + ': duplicate requirement id')
        seen.add(label)
        if any(not row.get(key) for key in required):
            errors.append(label + ': missing required metadata')
        if row.get('candidate_full_revision') != saved['candidate_full_revision']:
            errors.append(label + ': candidate revision differs from freeze')
        if row.get('verdict') != 'verified':
            errors.append(label + ': verdict is not verified')
        stages = {s.strip() for s in row.get('applicable_stages', '').split(',')}
        if str(saved['stage']) not in stages:
            errors.append(label + ': current stage applicability absent')
        for evidence in row.get('evidence_path', '').split(';'):
            location = Path(evidence.strip().split('#', 1)[0])
            if not location.is_absolute():
                location = RESULT / location
            try:
                location.resolve().relative_to(RESULT)
            except ValueError:
                errors.append(label + ': artifact is outside result clone')
            if not location.is_file():
                errors.append(label + ': artifact file missing: ' + evidence.strip())
    if hashlib.sha256(verdict.read_bytes()).hexdigest() != saved['independent_verdict_sha256']:
        errors.append('Original accepted verdict hash differs from freeze')
    reports.append({'stage': saved['stage'], 'candidate_full_revision': saved['candidate_full_revision'],
                    'matrix': str(matrix.relative_to(RESULT)), 'rows': len(rows),
                    'errors': errors, 'status': 'pass' if not errors else 'fail'})
print(json.dumps({'scope': 'coordinator artifact metadata audit; independent execution remains in verifier reports',
                  'stages': reports}, indent=2))
raise SystemExit(any(report['errors'] for report in reports))
