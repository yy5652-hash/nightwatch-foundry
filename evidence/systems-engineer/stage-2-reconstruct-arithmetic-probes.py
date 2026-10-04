"""Owning-builder helper controls; these are explicitly not HTTP evidence."""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import time

p = argparse.ArgumentParser()
p.add_argument('--module', default='stage-2/json_codec.py')
p.add_argument('--out', required=True)
a = p.parse_args()
spec = importlib.util.spec_from_file_location('systems_arithmetic_codec', a.module)
codec = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = codec
spec.loader.exec_module(codec)
began = time.monotonic()
assertions = 0
failures = []
def check(label, actual, expected):
    global assertions
    assertions += 1
    if actual != expected:
        failures.append({'label': label, 'actual': actual, 'expected': expected})

rng = random.Random(2026100403)
for i in range(2000):
    ac, bc, tc = [rng.randrange(0, 10**rng.randrange(1, 25)) for _ in range(3)]
    ae, be, te = [rng.randrange(0, 40) for _ in range(3)]
    left, right, target = [codec.JsonNumber(f'{c}e{e}') for c, e in ((ac, ae), (bc, be), (tc, te))]
    av, bv, tv = ac * 10**ae, bc * 10**be, tc * 10**te
    check(f'sum-{i}', codec.to_integer(codec.add_integers(left, right)), av + bv)
    check(f'fit-{i}', codec.sum_at_least(left, right, target), av + bv >= tv)
    check(f'mixed-{i}', codec.sum_at_least(av, right, target), av + bv >= tv)
for av, bv in ((0, 0), (0, 1), (4, 6), (10**4300+1, 10**4300+2)):
    for tv in (0, av, bv, av+bv, av+bv+1):
        check('integer-boundary', codec.sum_at_least(av, bv, tv), av+bv >= tv)
huge = '9' * 80
left = codec.JsonNumber('4e' + huge)
right = codec.JsonNumber('6e' + huge)
total = codec.add_integers(left, right)
check('compact-sum', codec.compare_numbers(total, codec.JsonNumber('10e' + huge)), 0)
check('compact-fit', codec.sum_at_least(left, right, total), True)
check('compact-refusal', codec.sum_at_least(left, right, codec.JsonNumber('11e'+huge)), False)
check('compact-distant', codec.sum_at_least(1, 2, total), False)
check('compact-small-target', codec.sum_at_least(left, 1, right), False)
for value in (True, '1', None, codec.JsonNumber('0.1'), -1):
    try:
        codec.sum_at_least(value, 1, 1)
    except codec.JsonCodecError:
        check('invalid-helper-operand', True, True)
    else:
        check('invalid-helper-operand', False, True)
result = {'kind': 'helper-only controls; not HTTP', 'seed': 2026100403,
          'assertions': assertions, 'failures': failures, 'seconds': time.monotonic()-began}
Path(a.out).write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'assertions': assertions, 'failed': len(failures), 'seconds': result['seconds']}))
raise SystemExit(bool(failures))
