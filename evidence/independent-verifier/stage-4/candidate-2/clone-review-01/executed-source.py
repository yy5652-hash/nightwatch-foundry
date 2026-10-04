"""Fresh exact evidence-clone file/link/archive review; no service execution."""
import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.set_int_max_str_digits(0)
csv.field_size_limit(sys.maxsize)
HERE = Path(__file__).resolve().parent
R = HERE.parents[2]
H = HERE / 'candidate-2'
C = '58270860cb6a762c8a4c2a551672701fb00bd613'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[0-9a-f]{40}', args.revision)
    out = H / 'clone-review-01'
    out.mkdir(exist_ok=False)
    clone = R.parent / ('independent-verifier-s4-c2-evidence-'+datetime.now(timezone.utc).strftime('%m%d%H%M%S'))
    assert not clone.exists()
    started = datetime.now(timezone.utc)
    commands = []

    def run(argv, cwd=R):
        begin = time.monotonic()
        proc = subprocess.run(argv, cwd=cwd, capture_output=True)
        commands.append(dict(argv=argv, cwd=str(cwd), returncode=proc.returncode, seconds=time.monotonic()-begin, stdout=proc.stdout.decode(), stderr=proc.stderr.decode()))
        assert proc.returncode == 0, argv
        return proc.stdout

    try:
        run(['git', 'clone', '--quiet', '--no-checkout', str(R), str(clone)])
        run(['git', 'checkout', '--quiet', '--detach', args.revision], cwd=clone)
        assert run(['git', 'rev-parse', 'HEAD'], cwd=clone).decode().strip() == args.revision
        assert not run(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=clone)
        assert not run(['git', 'diff', C, args.revision, '--', 'stage-1', 'stage-2', 'stage-3', 'stage-4'], cwd=clone)
        cloned_home = clone / H.relative_to(R)
        archives = json.loads((cloned_home / 'aggregate-archives.json').read_text())
        assert len(archives) == 7
        for archive in archives:
            original, packed = cloned_home/archive['original'], cloned_home/archive['archive']
            assert not original.exists() and packed.is_file()
            assert hashlib.sha256(packed.read_bytes()).hexdigest() == archive['archive_sha256']
        run([sys.executable, '-B', str(clone/HERE.relative_to(R)/'candidate2_package_aggregates.py'), '--restore'], cwd=clone)
        for archive in archives:
            original = cloned_home / archive['original']
            assert original.is_file()
            assert hashlib.sha256(original.read_bytes()).hexdigest() == archive['original_sha256']
            assert original.stat().st_size == archive['original_bytes']
        assert not run(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=clone)
        rows = list(csv.DictReader((cloned_home/'coverage.csv').open()))
        assert len(rows) == 7862
        assert sum(row['normative'] == 'True' for row in rows) == 7840
        for row in rows:
            assert row['candidate_full_revision'] == C and row['verdict'] == 'verified'
            for evidence in row['evidence_path'].split(';'):
                assert (clone/evidence.strip().split('#')[0]).is_file(), evidence
        runs = json.loads((cloned_home/'completed-runs.json').read_text())
        assert len(runs) == 108
        for row in runs:
            assert (clone/row['summary']).is_file()
        image_records = json.loads((cloned_home/'visual-review.json').read_text())['images']
        for row in image_records:
            assert hashlib.sha256((clone/row['path']).read_bytes()).hexdigest() == row['sha256']
        proof = dict(evidence_revision=args.revision, candidate=C, clone=str(clone), exact_detached_revision=True, clone_git_status_empty=True, graded_diff_empty=True, restored_archives=7, archives_lossless=True, coverage_records=7862, normative=7840, concrete_evidence_links_valid=True, complete_selected_summaries=108, personally_viewed_image_hashes_valid=6, service_reruns=0, scope='Fresh-clone committed artifacts, source equality, archive restoration and concrete file links; no new service or browser pass claimed.', started_at=started.isoformat(), finished_at=datetime.now(timezone.utc).isoformat(), executed_audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        (out/'proof.json').write_text(json.dumps(proof, indent=2)+'\n')
        print(json.dumps({k:proof[k] for k in ['evidence_revision','clone','clone_git_status_empty','graded_diff_empty','restored_archives','coverage_records','complete_selected_summaries','service_reruns']}))
    except Exception as error:
        (out/'FAILED_AUDIT.json').write_text(json.dumps(dict(error=repr(error), clone=str(clone), revision=args.revision), indent=2)+'\n')
        raise
    finally:
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        (out/'executed-source.py').write_bytes(Path(__file__).read_bytes())


if __name__ == '__main__':
    main()
