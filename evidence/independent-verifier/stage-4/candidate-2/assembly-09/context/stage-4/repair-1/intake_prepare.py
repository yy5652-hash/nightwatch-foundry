"""Read-only historic preservation audit and prospective coverage reset.

No production module, service, container, browser or official checker is executed.
Every output directory is new; preserved historical inputs are never rewritten.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
STAGE = ROOT.parent
SEAL = 'a744fd0cbe3fa24399088d3e4dc8db960bf5c9f3'
ACCEPTED = '91e2c471acded1b861b3fec725f202297b1c6740'
OLD = '261e4d9456a04a8b57ed46db71a09ac267ff15a9'
csv.field_size_limit(sys.maxsize)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*argv):
    return subprocess.check_output(['git', *argv], cwd=REPO)


def preserve(revision, paths):
    tree = git('ls-tree', '-r', '-z', revision, '--', *paths)
    entries = []
    for item in tree.split(b'\0'):
        if not item:
            continue
        meta, name = item.split(b'\t', 1)
        mode, kind, blob = meta.decode().split()
        assert kind == 'blob'
        entries.append((mode, blob, name.decode()))
    process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=REPO,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    records = []
    try:
        for mode, blob, name in entries:
            process.stdin.write((blob + '\n').encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().split()
            assert header[0] == blob and header[1] == 'blob'
            content = process.stdout.read(int(header[2]))
            assert process.stdout.read(1) == b'\n'
            path = REPO / name
            assert path.is_file() and not path.is_symlink(), name
            current = path.read_bytes()
            executable = bool(path.stat().st_mode & 0o111)
            assert content == current and executable == (mode == '100755'), name
            records.append(dict(path=name, git_blob=blob, git_mode=mode,
                                sha256=sha(current), bytes=len(current), identical=True))
    finally:
        process.stdin.close()
        assert process.wait() == 0
    return dict(revision=revision, files=len(records), records=records,
                compared='Named Git blobs/modes against current bytes; not shared HEAD')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    old_path = STAGE / 'candidate-1' / 'coverage.csv'
    rows = list(csv.DictReader(old_path.open()))
    assert len(rows) == 7862 and len({r['requirement_id'] for r in rows}) == 7862
    normative = [r for r in rows if r['normative'].lower() == 'true']
    assert len(normative) == 7840
    counts = {v: sum(r['verdict'] == v for r in normative) for v in ['verified', 'failed', 'unverified']}
    assert counts == dict(verified=54, failed=12, unverified=7774)
    historical_columns = ['historical_candidate1_revision', 'historical_candidate1_verdict',
                          'historical_candidate1_evidence', 'historical_candidate1_command']
    columns = list(rows[0]) + historical_columns
    for row in rows:
        row.update(dict(zip(historical_columns, [row['candidate_full_revision'], row['verdict'],
                                                row['evidence_path'], row['executable_command_or_interaction']])))
        row.update(candidate_full_revision='PENDING: new repaired full candidate execution package',
                   verdict='unverified', verification_method='Prospective requirement; no repaired candidate execution',
                   executable_command_or_interaction='UNEXECUTED current scope: see repair-1/PROTOCOL_BINDING.md; actual argv and assertion binding required after release',
                   evidence_path='evidence/independent-verifier/stage-4/repair-1/PROTOCOL_BINDING.md',
                   preparation_status='Prepared obligation only; prior passes and failures stay historical')
        row['interpretation_note'] += ' REPAIR-1 resets current evidence; candidate1 observations remain immutable.'
        if row['requirement_id'].startswith('TK4-closure-type-'):
            row.update(source_section='Stage1 section5 wrong JSON field type (lines160/177), inherited by Stage4 Seating changes after a table closure (line20)',
                       source_file='stage-1.md; stage-4.md', source_line='160; 177; 20')
    with (args.out / 'coverage.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    # A byte copy retains the complete historical CSV, including original fields.
    (args.out / 'historical-candidate1-coverage.csv').write_bytes(old_path.read_bytes())
    prior = STAGE / 'initial-1' / 'checks-04' / 'source-inputs' / 'accepted-stage3-coverage.csv'
    assert prior.is_file()
    (args.out / 'historical-accepted-stage3-coverage.csv').write_bytes(prior.read_bytes())
    preserved = preserve(SEAL, ['evidence/independent-verifier/stage-4'])
    frozen = preserve(ACCEPTED, ['stage-1', 'stage-2', 'stage-3'])
    assert frozen['files'] == 24
    (args.out / 'rejected-preservation.json').write_text(json.dumps(preserved, indent=2) + '\n')
    (args.out / 'frozen-preservation.json').write_text(json.dumps(frozen, indent=2) + '\n')
    result = dict(scope='Preparation only', historical_candidate=OLD, historical_counts=counts,
        records=len(rows), normative=7840, diagnostics=22, repaired_verified=0, repaired_failed=0,
        repaired_unverified=7840, preserved_files=preserved['files'], frozen_files=frozen['files'],
        original_csv_sha256=sha(old_path.read_bytes()),
        preparation_csv_sha256=sha((args.out / 'coverage.csv').read_bytes()),
        candidate_http_requests=0, candidate_browser_operations=0, official_runs=0)
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(result))


if __name__ == '__main__':
    main()
