"""Freeze or verify accepted stage trees; acceptance remains a human-readable verdict.

Usage: python3 evidence/coordinator/freeze_stage.py freeze N FULL_REV VERDICT_PATH
       python3 evidence/coordinator/freeze_stage.py revoke N FULL_REV VERDICT_PATH
       python3 evidence/coordinator/freeze_stage.py verify
No implementation files are written. Existing manifests are never overwritten.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from acceptance_state import current_manifests, verify_history

RESULT = Path(__file__).resolve().parents[2]
ACCEPTED = Path(__file__).parent / 'accepted'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=RESULT, text=True).strip()


def tree(stage, revision):
    entries = []
    for line in git('ls-tree', '-r', revision, '--', f'stage-{stage}').splitlines():
        if not line:
            continue
        meta, path = line.split('\t', 1)
        mode, kind, object_id = meta.split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Stage contains a nested repository or symlink: ' + path)
        entries.append({'path': path.split('/', 1)[1], 'mode': mode, 'object_id': object_id})
    if not entries:
        raise ValueError('No committed stage files')
    return entries


def verify():
    verify_history()
    for path, saved in current_manifests():
        stage = saved['stage']
        verdict = RESULT / saved['independent_verdict_path']
        if not verdict.is_file() or hashlib.sha256(verdict.read_bytes()).hexdigest() != saved['independent_verdict_sha256']:
            raise ValueError(f'Accepted Stage {stage} original verdict changed or disappeared')
        if tree(stage, 'HEAD') != saved['tree']:
            raise ValueError(f'Accepted Stage {stage} committed tree changed')
        dirty = git('status', '--porcelain', '--', f'stage-{stage}')
        if dirty:
            raise ValueError(f'Accepted Stage {stage} has uncommitted changes')
        print(f'Stage {stage}: frozen tree unchanged')


if sys.argv[1] == 'verify':
    verify()
elif sys.argv[1] == 'freeze':
    stage = int(sys.argv[2])
    revision = git('rev-parse', sys.argv[3])
    if revision != sys.argv[3] or len(revision) != 40:
        raise ValueError('Provide the full 40-character candidate revision')
    verdict = Path(sys.argv[4]).resolve()
    verdict.relative_to(RESULT)
    if not verdict.is_file():
        raise ValueError('Independent verdict evidence is missing')
    verify()
    current = {d['stage']: d for _, d in current_manifests()}
    if stage in current:
        raise ValueError('Stage already accepted; preserve and explicitly revoke before repair')
    if stage > 1 and any(n not in current for n in range(1, stage)):
        raise ValueError('Earlier consecutive accepted stage is missing')
    if git('status', '--porcelain', '--', f'stage-{stage}'):
        raise ValueError('Candidate stage has uncommitted changes')
    entries = tree(stage, revision)
    if entries != tree(stage, 'HEAD'):
        raise ValueError('Candidate stage differs from HEAD')
    ACCEPTED.mkdir(exist_ok=True)
    destination = ACCEPTED / f'stage-{stage}.json'
    if destination.exists():
        destination = ACCEPTED / f'stage-{stage}-{revision}.json'
    with destination.open('x') as stream:
        json.dump({'stage': stage, 'candidate_full_revision': revision,
                   'freeze_wall_time_utc': datetime.now(timezone.utc).isoformat(),
                   'independent_verdict_path': str(verdict.relative_to(RESULT)),
                   'independent_verdict_sha256': hashlib.sha256(verdict.read_bytes()).hexdigest(),
                   'tree': entries}, stream, indent=2)
        stream.write('\n')
    print(destination)
elif sys.argv[1] == 'revoke':
    stage = int(sys.argv[2])
    revision = git('rev-parse', sys.argv[3])
    if revision != sys.argv[3] or len(revision) != 40:
        raise ValueError('Provide the full 40-character candidate revision')
    verdict = Path(sys.argv[4]).resolve()
    verdict.relative_to(RESULT)
    if not verdict.is_file():
        raise ValueError('Supplemental independent verdict evidence is missing')
    verify_history()
    matches = [(p, d) for p, d in current_manifests()
               if d['stage'] == stage and d['candidate_full_revision'] == revision]
    if len(matches) != 1:
        raise ValueError('Current accepted revision does not match revocation')
    original, _ = matches[0]
    destination = ACCEPTED / f'revoked-stage-{stage}-{revision}.json'
    with destination.open('x') as stream:
        json.dump({'stage': stage, 'candidate_full_revision': revision,
                   'revocation_wall_time_utc': datetime.now(timezone.utc).isoformat(),
                   'original_manifest_path': str(original.relative_to(RESULT)),
                   'original_manifest_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
                   'independent_verdict_path': str(verdict.relative_to(RESULT)),
                   'independent_verdict_sha256': hashlib.sha256(verdict.read_bytes()).hexdigest()}, stream, indent=2)
        stream.write('\n')
    print(destination)
else:
    raise ValueError('Expected freeze, revoke or verify')
