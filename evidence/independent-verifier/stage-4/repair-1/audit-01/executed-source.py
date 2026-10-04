"""Metadata, immutable-history and scoped new saved-JSON preparation audit."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from intake_prepare import REPO, SEAL, ACCEPTED, preserve, sha
csv.field_size_limit(sys.maxsize)

REQUIRED = ['requirement_id', 'requirement_text', 'source_section', 'source_line', 'source_file',
            'introduced_stage', 'applicable_stages', 'owner', 'implementation_owner', 'verification_owner',
            'candidate_full_revision', 'verification_method', 'executable_command_or_interaction', 'evidence_path']
PRIVATE_KEYS = {'token', 'tokens', 'password_hash', 'password_hashes', 'raw_export', 'raw_state',
                'bearer_token', 'session_token', 'credentials'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rows = list(csv.DictReader((ROOT / 'intake-check-01/coverage.csv').open()))
    original = list(csv.DictReader((ROOT.parent / 'candidate-1/coverage.csv').open()))
    lookup = {r['requirement_id']: r for r in original}
    assert len(rows) == len(lookup) == 7862
    historical = dict(historical_candidate1_revision='candidate_full_revision', historical_candidate1_verdict='verdict',
                      historical_candidate1_evidence='evidence_path', historical_candidate1_command='executable_command_or_interaction')
    links = set()
    for row in rows:
        assert all(row[key] for key in REQUIRED) and row['verification_owner'] == 'independent-verifier'
        assert row['verdict'] == 'unverified' and row['candidate_full_revision'].startswith('PENDING:')
        old = lookup[row['requirement_id']]
        assert row['requirement_text'] == old['requirement_text'] and row['normative'] == old['normative']
        assert all(row[new] == old[prior] for new, prior in historical.items())
        assert all(row[key] == old[key] for key in ['previous_candidate', 'previous_verdict', 'previous_evidence', 'previous_command'])
        for value in row['evidence_path'].split(';'):
            path = REPO / value.strip().split('#')[0]
            assert path.is_file()
            links.add(str(path.relative_to(REPO)))
    assert sum(r['normative'].lower() == 'true' for r in rows) == 7840
    assert sum(r['requirement_id'].startswith('TK4-closure-type-') for r in rows) == 12
    assert (ROOT / 'intake-check-01/historical-candidate1-coverage.csv').read_bytes() == (ROOT.parent / 'candidate-1/coverage.csv').read_bytes()
    prior = ROOT.parent / 'initial-1/checks-04/source-inputs/accepted-stage3-coverage.csv'
    assert (ROOT / 'intake-check-01/historical-accepted-stage3-coverage.csv').read_bytes() == prior.read_bytes()
    metadata = dict(records=7862, normative=7840, diagnostics=22, normative_verified=0,
                    normative_failed=0, normative_unverified=7840, required_fields=REQUIRED,
                    exact_original_history_retained=True, current_concrete_preparation_links=sorted(links))
    (args.out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    rejected = preserve(SEAL, ['evidence/independent-verifier/stage-4/candidate-1'])
    frozen = preserve(ACCEPTED, ['stage-1', 'stage-2', 'stage-3'])
    (args.out / 'rejected-preservation.json').write_text(json.dumps(rejected, indent=2) + '\n')
    (args.out / 'frozen-preservation.json').write_text(json.dumps(frozen, indent=2) + '\n')
    manifest, findings = [], []
    objects = embedded = 0
    def visit(value, path, location='$'):
        nonlocal objects, embedded
        if isinstance(value, dict):
            objects += 1
            for key, item in value.items():
                if key.lower() in PRIVATE_KEYS and item not in [None, '', [], {}]:
                    findings.append(dict(path=path, location=location + '.' + key, kind='private payload key'))
                visit(item, path, location + '.' + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, path, location + '[' + str(index) + ']')
        elif isinstance(value, str) and value[:1] in ['{', '[']:
            try:
                parsed = json.loads(value)
            except (ValueError, RecursionError):
                return
            embedded += 1
            visit(parsed, path, location + '<embedded>')
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or path.is_relative_to(args.out) or '__pycache__' in path.parts or any(part.startswith('seal-') or part.startswith('audit-') for part in path.relative_to(ROOT).parts):
            continue
        relative = str(path.relative_to(REPO))
        payload = path.read_bytes()
        manifest.append(dict(path=relative, bytes=len(payload), sha256=sha(payload)))
        if path.suffix == '.json':
            visit(json.loads(payload), relative)
    assert not findings, findings
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    privacy = dict(scope='New REPAIR-1 saved JSON and valid embedded JSON strings only',
        files_hashed=len(manifest), saved_json_objects=objects, embedded_json_strings=embedded,
        unclassified_private_payload_findings=0,
        excluded=['Authored/source/log/handoff text', 'Historical CSV', 'Prior/peer artifacts',
                  'Audit and seal successor files', 'Genuine full room export'],
        model_records='Hypothetical reference constructions explicitly labelled, not private production state',
        candidate_operations=0)
    (args.out / 'artifact-audit.json').write_text(json.dumps(privacy, indent=2) + '\n')
    (args.out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(complete=True, metadata=metadata, preservation=dict(candidate1_files=rejected['files'], frozen_files=frozen['files']), privacy=privacy)
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(complete=True, normative_unverified=7840, candidate1_files=rejected['files'],
                         frozen_files=frozen['files'], hashed_files=len(manifest), saved_json_objects=objects, private_findings=0)))


if __name__ == '__main__':
    main()
