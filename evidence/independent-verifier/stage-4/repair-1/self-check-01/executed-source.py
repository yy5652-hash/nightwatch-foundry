"""Preparation-only checks; imports own reference tools, never production code."""
import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
sys.path.insert(0, str(ROOT))
from full_bound import construct, control, SEED
from release_guard import validate, REJECTED
from stage4_oracle import instant, overlap, seating_plan, options
from error_matrix import cases


def normalize(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    assertions = []
    def check(name, condition, details=None):
        assertions.append(dict(name=name, passed=bool(condition), details=details,
                               scope='Local preparation/reference self-check, never candidate behavior'))
        if not condition:
            raise AssertionError(name)
    error = None
    try:
        intake = json.loads((ROOT / 'intake.json').read_text())
        check('all-parts-before-preparation', intake['acknowledged_before_preparation'] and intake['all_parts_received'] and
              intake['end_received'] and intake['final_completion_marker_received'] and
              sorted(p['part'] for p in intake['all_parts']) == list(range(1, 23)))
        check('execution-held', intake['execution_authorized'] is False and intake['new_candidate'] is None)
        sources = []
        for source in sorted(ROOT.glob('*.py')):
            ast.parse(source.read_text(), filename=str(source))
            sources.append(dict(path=str(source.relative_to(REPO)), sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
            check('ast-' + source.name, True)
        (args.out / 'source-manifest.json').write_text(json.dumps(sources, indent=2) + '\n')
        constructions, controls = [], []
        for index in range(160):
            value = construct(index)
            check('construction-full-bound-' + str(index), len(value['records']) == 8 and len(options(tuple('abcdef'), [['b', 'a'], ['c', 'b'], ['d', 'e'], ['f', 'e']])) == 10 and
                  sum(overlap(b, value['proposed_model']) for b in value['records']) == 6)
            check('construction-distinct-accepted-' + str(index), value['original_capacities'] != value['later_capacities'] and value['latest_capacities'] not in [value['original_capacities'], value['later_capacities']])
            controls.append(control(index))
            check('small-unpruned-control-' + str(index), controls[-1]['unpruned_matches'])
            constructions.append(normalize(value))
        (args.out / 'model-constructions.json').write_text(json.dumps(dict(seed=SEED, constructions=constructions,
            fractional_value_format='Fraction strings are model notation only, never HTTP values',
            actual_candidate_operations=0), indent=2) + '\n')
        (args.out / 'small-controls.json').write_text(json.dumps(controls, indent=2) + '\n')
        x = instant('2035-06-04T18:00:00+00:00')
        tiny = Fraction(1, 10**18)
        check('fraction-exact-positive', instant('2035-06-04T18:00:00.000000000000000001+00:00') - x == tiny)
        check('fraction-exact-negative', x - instant('2035-06-04T17:59:59.999999999999999999+00:00') == tiny)
        check('offset-exact-alias', x == instant('2035-06-04T20:00:00+02:00'))
        check('half-open-adjacency', not overlap(dict(start=x-60, end=x), dict(start=x, end=x+60)))
        check('half-open-tiny-overlap', overlap(dict(start=x-60, end=x+tiny), dict(start=x, end=x+60)))
        # Pair reversal changes neither the mathematical set nor moved count.
        from stage4_oracle import booking
        b = booking('MODEL-PAIR', ['a', 'b'], 0, 20, {'a': 2, 'b': 2, 'c': 1}, 4)
        proposed = dict(table_id='c', start=0, end=20)
        plan = seating_plan(tuple('abc'), [['b', 'a']], [b], [], proposed)
        check('pair-set-order-no-move', plan['moved_count'] == 0 and plan['assignments'][0]['table_ids'] == ['b', 'a'])
        negative = [dict(candidate=REJECTED), {}, dict(candidate='a'*40, new_complete_execution_package=True),
                    dict(candidate=None, new_complete_execution_package=True, preparation_only=False),
                    dict(candidate='short', new_complete_execution_package=True, preparation_only=False), intake]
        for index, release in enumerate(negative):
            try:
                validate(release)
                raise AssertionError('unexpected execution authorization')
            except (ValueError, TypeError):
                check('release-negative-' + str(index), True)
        commands = []
        for name, extra in [('full_bound.py', []), ('transitions.py', ['--family', 'atomic-reads']),
                            ('error_matrix.py', ['--family', 'preview']),
                            ('browser_recovery.py', ['--family', 'preview', '--mode', 'lost'])]:
            argv = [sys.executable, '-B', str(ROOT / name), '--release', str(ROOT / 'intake.json'),
                    '--out', str(args.out / 'must-not-exist'), *extra]
            before = time.monotonic()
            result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
            commands.append(dict(argv=argv, cwd=str(REPO), returncode=result.returncode,
                seconds=time.monotonic()-before, stdout=result.stdout, stderr=result.stderr))
            check('default-held-' + name, result.returncode != 0 and 'execution held' in result.stderr.lower() and not (args.out / 'must-not-exist').exists())
        (args.out / 'guard-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        check('separate-closure-types', sum('-type-' in case[0] for case in cases('preview')) == 18)
        inherited_path = REPO / 'evidence/independent-verifier/stage-3/candidate-1/completed-runs.json'
        inherited = json.loads(inherited_path.read_text())
        inventory = []
        for prior in inherited:
            argv = shlex.split(prior['command'])
            source_name = next(a.removeprefix('/verifier/') for a in argv if a.startswith('/verifier/') and a.endswith('.py'))
            path = REPO / 'evidence/independent-verifier' / source_name
            check('inherited-source-' + prior['name'], path.is_file())
            inventory.append(dict(scope=prior['name'], kind=prior['kind'], source=str(path.relative_to(REPO)),
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), historical_command=prior['command'],
                historical_summary=prior['summary'], current_verdict='unverified',
                new_argv='PENDING fresh Stage4 candidate/package/assembly/resources; no old receipt or acceptance rebound'))
        check('complete-inherited-inventory', len(inventory) == 61 and sum(i['kind'] == 'http' for i in inventory) == 44 and sum(i['kind'] == 'browser' for i in inventory) == 17)
        (args.out / 'inherited-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        (args.out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
        (args.out / 'assertions.json').write_text(json.dumps(assertions, indent=2) + '\n')
        summary = dict(scope='Preparation/reference checks only', complete=error is None, error=error,
            started_at=started, finished_at=datetime.now(timezone.utc).isoformat(), seconds=time.monotonic()-start,
            checks=len(assertions), passed=sum(a['passed'] for a in assertions), failed=sum(not a['passed'] for a in assertions),
            model_constructions=160 if error is None else None, candidate_http_requests=0, candidate_browser_operations=0,
            official_runs=0, production_imports=0, new_runtime_resources=0)
        (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary))


if __name__ == '__main__':
    main()
