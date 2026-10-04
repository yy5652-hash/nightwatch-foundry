"""Append one preparation event and commit only explicitly owned paths."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SEAL = 'a744fd0cbe3fa24399088d3e4dc8db960bf5c9f3'
LEDGER = ROOT.parent / 'ledger.jsonl'
OUT = ROOT / 'seal-01'
IDENTITY = ['-c', 'user.name=Independent Verifier', '-c', 'user.email=independent-verifier@nightwatch-foundry.invalid']


def main():
    OUT.mkdir(exist_ok=False)
    commands = []
    def run(argv):
        began = time.monotonic()
        result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
        commands.append(dict(argv=argv, cwd=str(REPO), returncode=result.returncode,
                             seconds=time.monotonic()-began, stdout=result.stdout, stderr=result.stderr))
        if result.returncode:
            raise RuntimeError(str(argv) + ': ' + result.stderr)
        return result.stdout
    historical = subprocess.check_output(['git', 'show', SEAL + ':' + str(LEDGER.relative_to(REPO))], cwd=REPO)
    current = LEDGER.read_bytes()
    assert current == historical, 'Expected untouched original ledger before the new append'
    event = dict(event='stage4-repair1-independent-preparation', logged_at=datetime.now(timezone.utc).isoformat(),
        package='TK-20261004-S4-independent-verifier-REPAIR-1', complete22parts_and_both_markers=True,
        acknowledged_on_inbound='89d7f585-a83a-4240-bf74-ec2c90375242', scope='prospective preparation only',
        new_candidate=None, current_execution_held=True, highest_consecutive_accepted=3,
        historical_rejected_candidate='261e4d9456a04a8b57ed46db71a09ac267ff15a9',
        historical_rejection='16b6955aee3036298aaa81aa3533fe3536d44cff',
        normative_unverified=7840, separate_unverified_diagnostics=22,
        selected_local_self_checks=568, local_passed=568, local_failed=0,
        model_constructions=160, small_unpruned_controls=160,
        candidate_http_requests=0, candidate_browser_operations=0, official_runs=0,
        production_edits=0, new_runtime_resources=0, evidence='repair-1/PREPARATION.md',
        harness='Codex', configured_model='gpt-6.1-sol', actual_model='unknown', effort='unknown',
        tokens='unknown', estimated_cost='unknown', billed_spend='unknown',
        risks='New full candidate/source/runtime/selectors/private state and exact obligation-to-assertion bindings remain future execution work')
    LEDGER.write_bytes(current + (json.dumps(event) + '\n').encode())
    paths = sorted(str(p.relative_to(REPO)) for p in ROOT.rglob('*') if p.is_file() and not p.is_relative_to(OUT) and '__pycache__' not in p.parts)
    paths.append(str(LEDGER.relative_to(REPO)))
    run(['git', 'add', '--', *paths])
    text = run(['git', *IDENTITY, 'commit', '--only', '-m', 'Prepare independent Stage4 repair review without releasing execution', '--', *paths])
    abbreviated = re.search(r'^\[[^\]]+ ([0-9a-f]+)\]', text, re.M).group(1)
    revision = run(['git', 'rev-parse', abbreviated]).strip()
    changed = run(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', revision]).splitlines()
    assert set(changed) == set(paths)
    author = run(['git', 'show', '-s', '--format=%an <%ae>', revision]).strip()
    assert author == 'Independent Verifier <independent-verifier@nightwatch-foundry.invalid>'
    graded_diff = run(['git', 'diff', '--name-only', '--', 'stage-1', 'stage-2', 'stage-3', 'stage-4'])
    assert not graded_diff
    raw = LEDGER.read_bytes()
    assert raw.startswith(historical) and raw[len(historical):] == (json.dumps(event) + '\n').encode()
    inspection = dict(revision=revision, author=author, changed_paths=changed, exclusively_owned=True,
        graded_working_diff=[], original_ledger_prefix_sha256=hashlib.sha256(historical).hexdigest(),
        original_ledger_prefix_preserved=True, new_ledger_events=1, current_execution_held=True)
    (OUT / 'commit-inspection.json').write_text(json.dumps(inspection, indent=2) + '\n')
    (OUT / 'commands-after-commit.json').write_text(json.dumps(commands, indent=2) + '\n')
    print(json.dumps(dict(revision=revision, owned_paths=len(paths), ledger_prefix_preserved=True, current_execution_held=True)))


if __name__ == '__main__':
    main()
