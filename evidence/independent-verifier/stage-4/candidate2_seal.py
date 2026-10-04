"""Final owned materials and explicit-path commit; inspect exact resulting revision."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
R = HERE.parents[2]
H = HERE / 'candidate-2'
C = '58270860cb6a762c8a4c2a551672701fb00bd613'
TREE = '00e208c746a488a9b4cb0761efd04b90c4248dd8'


def save(path, value):
    data = json.dumps(value, indent=2) + '\n'
    if path.exists():
        assert path.read_text() == data
    else:
        path.write_text(data)


def materials():
    images = [
        ('product-02/full/full-bound-proposal-desktop.png', 'Complete individual full-bound case in a run whose later separate cases failed; no relabelling of the overall run.', 'Warm cream, green and clay hierarchy; six actual reference-ordered human seating assignments, moved/unused/rank facts, explicit unapplied proposal and distinct Apply action.'),
        ('product-02/members/series-member-states-375.png', 'Complete individual member case in the same preserved overall attempt.', 'Mobile owner lookup shows accepted terms and actual reassignment. Four stable references distinguish the moved-date permanent exception, cancellation, before-index member and changed final member.'),
        ('inherited-browser-01/inherited-browser-01--visual/visual-375-search.png', 'Selected complete inherited visual protocol.', 'Labelled mobile restaurant/date/guest search, visible exact numeric stepping controls and human single/pair seating grid; available and unavailable cells remain distinct.'),
        ('product-03/racesui/current-lookup-reassigned-mobile.png', 'Selected complete current-read race protocol.', 'Actual owner lookup shows Hospitality b, revision 2 and stable reference; creation at Hospitality a precedes the actual a-to-b reassigned event with plan ID and retained accepted terms.'),
        ('recovery-02/apply-lost/apply-lost-uncertain-375.png', 'Selected complete committed-response-loss recovery protocol.', 'Mobile proposal remains visible with unchanged exact closure strings and human seating facts. Amber application uncertainty explains the unconfirmed outcome and offers unchanged retry without manufacturing success.'),
        ('product-04/stale/stale-plan-unapplied-1280.png', 'Selected complete stale-plan UI protocol.', 'Desktop manager form and human seating proposal stay legible beside a red restaurant-changed refusal. Application is visibly unconfirmed; fresh-preview action remains available after real 409 stale_plan and unchanged state.')
    ]
    records = []
    for name, scope, observation in images:
        path = H / name
        data = path.read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n'
        width, height = struct.unpack('>II', data[16:24])
        records.append(dict(path=str(path.relative_to(R)), sha256=hashlib.sha256(data).hexdigest(), width=width, height=height, personally_opened=True, scope=scope, concrete_observation=observation))
    save(H / 'visual-review.json', dict(candidate=C, personally_opened_images=6, images=records, scope='Six actual independently captured PNGs personally opened during this review. Other captures have separately saved layout/text/contrast observations; no claim every PNG was personally opened or full WCAG certification.'))
    summary = json.loads((H / 'summary.json').read_text())
    record = dict(event='stage4-candidate2-independent-acceptance', at=datetime.now(timezone.utc).isoformat(), candidate=C, tree=TREE, verdict='accept', highest_consecutive_accepted=4, coverage=dict(normative=7840, verified=7840, failed=0, unverified=0, separate_diagnostics=22), checks=summary['current_protocols'], official=summary['official'], direct_diagnostic=summary['direct_diagnostic'], cleanup=dict(final_commands=9, final_exit_codes=[0]*9, separate_direct_removal_exit=0, namespace_empty=True, only_own=True), review_timing=summary['timing'], production_edits=0, model_usage=summary['model'], evidence='evidence/independent-verifier/stage-4/candidate-2/VERDICT.md', evidence_seal='Supplied in the final room report after exact owned commit inspection; no circular self-seal', limitations=summary['limits'], adopted_interpretations=summary['known_interpretations'])
    for ledger in [HERE / 'ledger.jsonl', HERE.parent / 'ledger.jsonl']:
        existing = ledger.read_text()
        events = [json.loads(x) for x in existing.splitlines() if x]
        if any(x.get('event') == record['event'] for x in events):
            continue
        with ledger.open('a') as output:
            output.write(json.dumps(record, sort_keys=True) + '\n')
        assert ledger.read_text().startswith(existing)
    print(json.dumps(dict(personally_opened_pngs=6, ledger_event=record['event'], candidate=C)))


def seal():
    out = H / 'seal-01'
    out.mkdir(exist_ok=False)
    commands = []
    started = datetime.now(timezone.utc)

    def run(argv, allow=False):
        begin = time.monotonic()
        proc = subprocess.run(argv, cwd=R, capture_output=True)
        commands.append(dict(argv=argv, cwd=str(R), returncode=proc.returncode, seconds=time.monotonic()-begin, stdout=proc.stdout.decode(), stderr=proc.stderr.decode()))
        assert allow or proc.returncode == 0, argv
        return proc.stdout

    audit = json.loads((H / 'artifact-audit-03.json').read_text())
    assert not audit['unclassified_private_payload_findings'] and not audit['json_read_errors']
    metadata = json.loads((H / 'metadata-self-check.json').read_text())
    assert metadata['normative'] == metadata['verified'] == 7840 and metadata['failed'] == metadata['unverified'] == 0
    assert json.loads((H / 'final-runtime-proof.json').read_text())['namespace_empty']
    assert not run(['git', 'diff', C, '--', 'stage-1', 'stage-2', 'stage-3', 'stage-4'])
    for path in HERE.glob('candidate2_*.py'):
        ast.parse(path.read_bytes(), filename=str(path))
    (out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
    selectors = ['evidence/independent-verifier/stage-4', 'evidence/independent-verifier/ledger.jsonl']
    status = run(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--', *selectors]).decode().split('\0')
    paths = sorted(x[3:] for x in status if x and not x[3:].startswith(str(out.relative_to(R))+'/'))
    assert paths and all(x.startswith('evidence/independent-verifier/stage-4/') or x == 'evidence/independent-verifier/ledger.jsonl' for x in paths)
    assert all((R / x).is_file() for x in paths)
    assert not any('__pycache__' in Path(x).parts for x in paths)
    assert not any((R / x).stat().st_size >= 100_000_000 for x in paths)
    spec = out / 'owned.pathspec'
    paths += [str(spec.relative_to(R)), str((out/'executed-source.py').relative_to(R))]
    paths = sorted(set(paths))
    spec.write_bytes(b''.join((':(literal)'+x).encode()+b'\0' for x in paths))
    for attempt in range(20):
        proc = subprocess.run(['git', 'add', '--pathspec-from-file='+str(spec), '--pathspec-file-nul'], cwd=R, capture_output=True)
        commands.append(dict(argv=['git', 'add', '--pathspec-from-file='+str(spec), '--pathspec-file-nul'], returncode=proc.returncode, stdout=proc.stdout.decode(), stderr=proc.stderr.decode(), index_lock_attempt=attempt))
        if proc.returncode == 0:
            break
        assert b'index.lock' in proc.stderr
        time.sleep(1)
    else:
        raise RuntimeError('Persistent shared Git index lock; no lock removed')
    authored = [x for x in paths if (Path(x).parent == HERE.relative_to(R) and x.endswith('.py')) or (Path(x).parent == H.relative_to(R) and x.endswith('.md'))]
    run(['git', 'diff', '--cached', '--check', '--', *authored])
    result = run(['git', '-c', 'user.name=Independent Verifier', '-c', 'user.email=independent-verifier@nightwatch-foundry.invalid', 'commit', '--only', '--pathspec-from-file='+str(spec), '--pathspec-file-nul', '-m', 'Accept exact Stage 4 candidate with complete independent current evidence'])
    short = re.search(rb'\[[^\]]+ ([0-9a-f]{7,40})\]', result).group(1).decode()
    revision = run(['git', 'rev-parse', short]).decode().strip()
    changed = run(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', revision]).decode().splitlines()
    assert sorted(changed) == paths
    owner = run(['git', 'show', '-s', '--format=%an <%ae>', revision]).decode().strip()
    assert owner == 'Independent Verifier <independent-verifier@nightwatch-foundry.invalid>'
    tree = run(['git', 'rev-parse', revision+':stage-4']).decode().strip()
    assert tree == TREE
    assert not run(['git', 'diff', C, revision, '--', 'stage-1', 'stage-2', 'stage-3', 'stage-4'])
    save(out/'commands.json', commands)
    save(out/'proof.json', dict(verdict_commit=revision, candidate=C, stage_4_tree=tree, changed_paths=changed, changed_path_count=len(changed), exclusively_owned_paths=True, production_changed_paths=0, author=owner, graded_diff_empty=True, started_at=started.isoformat(), finished_at=datetime.now(timezone.utc).isoformat(), separate_inspection_seal='Supplied after fresh-clone artifact inspection and exact commit inspection in final room report'))
    print(json.dumps(dict(verdict_commit=revision, owned_changed_paths=len(changed), stage_4_tree=tree, production_changed_paths=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--materials', action='store_true')
    args = parser.parse_args()
    materials() if args.materials else seal()
