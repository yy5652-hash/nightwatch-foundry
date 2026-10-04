"""Audit current rejected-candidate evidence; no production execution or mutation."""
import argparse
import ast
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

csv.field_size_limit(sys.maxsize)
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CANDIDATE = '261e4d9456a04a8b57ed46db71a09ac267ff15a9'
TREE = '501d27abab7226546da42edb1131ef8aa037deaf'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def audit(out):
    home = ROOT / 'candidate-1'
    assert out.parent == home and not out.exists()
    out.mkdir()
    start = datetime.now(timezone.utc)
    tick = time.monotonic()
    commands = []
    try:
        manifest, classified, findings = [], [], []
        objects = embedded = 0

        def scan(value, path, location=''):
            nonlocal objects, embedded
            if isinstance(value, dict):
                objects += 1
                for key, item in value.items():
                    here = location + '/' + key
                    if key.lower() in {'password', 'password_hash', 'token', 'tokens', 'authorization', 'state'}:
                        record = dict(path=str(path.relative_to(REPO)), location=here,
                                      sha256=digest(json.dumps(item, sort_keys=True).encode()))
                        if path == home / 'official/report.json' and here == '/state' and item == 'completed':
                            record['classification'] = 'Official execution status; not private service state'
                            classified.append(record)
                        else:
                            findings.append(record)
                    scan(item, path, here)
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    scan(item, path, location + '/' + str(index))
            elif isinstance(value, str) and value[:1] in {'{', '['}:
                try:
                    item = json.loads(value)
                except (ValueError, RecursionError):
                    return
                embedded += 1
                scan(item, path, location + '/embedded')

        paths = sorted(p for p in home.rglob('*') if p.is_file() and out not in p.parents)
        paths += sorted(ROOT.glob('*.py')) + [ROOT / 'ledger.jsonl']
        for path in paths:
            data = path.read_bytes()
            manifest.append(dict(path=str(path.relative_to(REPO)), bytes=len(data), sha256=digest(data)))
            if path.suffix == '.json':
                scan(json.loads(data), path)
            if path.parent == ROOT and path.suffix == '.py':
                ast.parse(data, filename=str(path))
        assert not findings, findings

        rows = list(csv.DictReader((home / 'coverage.csv').open()))
        metadata = json.loads((home / 'metadata-self-check.json').read_text())
        normative = [r for r in rows if r['normative'].lower() == 'true']
        counts = dict(Counter(r['verdict'] for r in normative))
        assert len(rows) == 7862 and len(normative) == 7840
        assert counts == {'unverified': 7774, 'verified': 54, 'failed': 12}
        assert len({r['requirement_id'] for r in rows}) == len(rows)
        for row in rows:
            assert all(row[k] for k in metadata['required_fields'])
            assert row['candidate_full_revision'] == CANDIDATE
            assert row['verification_owner'] == 'independent-verifier'
            assert (REPO / row['evidence_path']).is_file()
        bindings = json.loads((home / 'coverage-bindings.json').read_text())
        assert len(bindings) == 66
        for row in rows:
            if row['verdict'] == 'unverified':
                assert row['requirement_id'] not in bindings
                continue
            observations = bindings[row['requirement_id']]
            assert observations
            for observation in observations:
                actual = json.loads((REPO / observation['file']).read_text())[observation['index']]
                assert actual == observation['record']
                assert bool(actual['passed']) == (row['verdict'] == 'verified')
        verdict = json.loads((home / 'verdict.json').read_text())
        assert verdict['candidate'] == CANDIDATE and verdict['verdict'] == 'reject'
        assert verdict['verdict_counts'] == counts and verdict['production_edits'] == 0
        summaries = [json.loads(p.read_text()) for p in (home / 'current-http-01').glob('*/summary.json')]
        assert len(summaries) == 7
        assert sum(s['requests'] for s in summaries) == 448
        assert sum(s['assertions'] for s in summaries) == 335
        assert sum(s['failed'] for s in summaries) == 12
        official = json.loads((home / 'official/report.json').read_text())
        assert official['revision'] == CANDIDATE
        for stage, expected in [(1, 120), (2, 25), (3, 7), (4, 6)]:
            check = official['checks'][str(stage)]
            assert check['collected'] == check['passed'] == expected
            assert all(check[k] == 0 for k in ['failed', 'errors', 'skipped', 'deselected', 'xfailed'])
        original = Path(json.loads((home / 'official-command.json').read_text())['output'])
        original_paths = sorted(p for p in original.rglob('*') if p.is_file())
        for path in original_paths:
            assert path.read_bytes() == (home / 'official' / path.relative_to(original)).read_bytes()
        cleanup = json.loads((home / 'cleanup-01/proof.json').read_text())
        assert cleanup['removals'] == 9 and cleanup['all_removal_codes_zero']
        assert cleanup['empty_own_namespace'] and cleanup['graded_diff_empty']
        assert len(cleanup['clones']) == 6 and all(c['clean'] for c in cleanup['clones'])
        for argv in [['git', 'diff', '--quiet', CANDIDATE, '--', 'stage-1', 'stage-2', 'stage-3', 'stage-4'],
                     ['git', 'rev-parse', CANDIDATE + ':stage-4']]:
            proc = subprocess.run(argv, cwd=REPO, capture_output=True)
            commands.append(dict(argv=argv, returncode=proc.returncode,
                                 stdout_sha256=digest(proc.stdout), stderr_sha256=digest(proc.stderr)))
            assert proc.returncode == 0
            if argv[1] == 'rev-parse':
                assert proc.stdout.decode().strip() == TREE
        save(out / 'artifact-audit.json', dict(files=len(manifest), saved_json_object_records=objects,
             embedded_json_strings=embedded, classified_metadata=classified,
             unclassified_private_payload_findings=findings, manifest=manifest,
             scope='Current candidate-1 saved JSON and valid embedded JSON strings only. Source/log/handoff/CSV/JSONL text, prior preparation/stage evidence, peer artifacts and genuine room export are excluded. Hash manifest is broader than the privacy scan.'))
        save(out / 'proof.json', dict(candidate=CANDIDATE, stage_4_tree=TREE, verdict='reject',
             coverage_records=len(rows), normative=len(normative), verdict_counts=counts,
             separate_diagnostics=22, assertion_bindings=66, metadata_and_file_links_valid=True,
             official_copy_byte_identical=True, official_checks=158, production_edits=0,
             cleanup_removals=9, cleanup_exit_codes_zero=True, all_graded_diff_empty=True,
             configured_harness='Codex', configured_model='gpt-6.1-sol',
             actual_model=None, actual_effort=None, usage=None, estimated_cost=None, billed_spend=None,
             start=start.isoformat(), end=datetime.now(timezone.utc).isoformat(),
             seconds=time.monotonic() - tick))
        save(out / 'commands.json', commands)
        (out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
        print(json.dumps(dict(verdict='reject', files=len(manifest), saved_json_objects=objects,
                              embedded_json_strings=embedded, private_findings=len(findings), counts=counts)))
    except Exception as error:
        save(out / 'FAILED_AUDIT.json', dict(error=repr(error), commands=commands,
                                           start=start.isoformat(), end=datetime.now(timezone.utc).isoformat()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    audit(parser.parse_args().out.resolve())
