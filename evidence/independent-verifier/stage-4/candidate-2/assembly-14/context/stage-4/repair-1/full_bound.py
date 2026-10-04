"""Independent seeded full-bound constructions and future raw HTTP oracle.

Only run main after a new acknowledged source-bound execution release. Local
construct()/control() use hypothetical reference identities, never service state.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from stage4_probe import Client, fixture, DAY, closure, integer, same, raw
from stage4_oracle import instant, booking, seating_plan, cartesian_control, Refusal
from release_guard import validate

SEED = 2026100641
PAIRS = [['b', 'a'], ['c', 'b'], ['d', 'e'], ['f', 'e']]


def construct(index):
    rng = random.Random(SEED + index)
    base = {'a': 3, 'b': 4, 'c': 5, 'd': 2, 'e': rng.choice([2, 3, 4]), 'f': 4}
    later = {'a': 4, 'b': 4, 'c': 6, 'd': rng.choice([2, 3, 4]), 'e': 2, 'f': 5}
    if index % 4 == 0:
        base['e'] = 2
    old = closure('f', DAY + 'T18:00:00+00:00', DAY + 'T19:30:00+00:00')
    proposed = closure('a', DAY + 'T18:30:00+00:00', DAY + 'T20:30:00+00:00')
    specs = [('fixed-early', 'd', '17:00', 1, base)]
    specs += [('early-' + t, t, '18:00', party, base) for t, party in [('a', 3), ('b', 4), ('c', 5)]]
    specs += [('late-' + t, t, '19:30', party, later) for t, party in [('a', 3), ('b', 4), ('c', 6)]]
    specs += [('fixed-late', 'e', '20:30', 1, later)]
    records = []
    for name, table, clock, party, capacities in specs:
        start = instant(DAY + 'T' + clock + ':00+00:00')
        records.append(booking('MODEL-' + name, [table], start, start + 90 * 60, capacities, party))
    old_model = dict(table_id=old['table_id'], start=instant(old['from']), end=instant(old['to']))
    proposed_model = dict(table_id=proposed['table_id'], start=instant(proposed['from']), end=instant(proposed['to']))
    try:
        expected = seating_plan(tuple('abcdef'), PAIRS, records, [old_model], proposed_model)
    except Refusal as error:
        expected = dict(error=error.code)
    return dict(index=index, seed=SEED + index, original_capacities=base, later_capacities=later,
                latest_capacities={t: 1 for t in 'abcdef'}, old_closure=old, proposed_closure=proposed,
                booking_constructions=[dict(name=name, table=table, clock=clock, party=party,
                    accepted_capacities=capacities) for name, table, clock, party, capacities in specs],
                records=records, old_model=old_model, proposed_model=proposed_model,
                expected=expected, scope='Hypothetical reference construction; not actual candidate operations')


def control(index):
    """Unpruned small control includes a fixed booking and old/proposed closures."""
    rng = random.Random(SEED + 1000 + index)
    capacities = {'a': rng.randint(2, 4), 'b': rng.randint(3, 5), 'c': rng.randint(2, 5)}
    records = [booking('MODEL-Z', ['a'], 10, 30, capacities, 2),
               booking('MODEL-A', ['b'], 20, 40, capacities, rng.randint(1, 3)),
               booking('MODEL-FIXED', ['c'], 0, 15, capacities, 1)]
    closures = [dict(table_id='c', start=rng.randint(31, 45), end=50)]
    proposed = dict(table_id='a', start=15, end=35)
    full = cartesian_control(tuple('abc'), [['b', 'a']], records, closures, proposed)
    try:
        pruned = seating_plan(tuple('abc'), [['b', 'a']], records, closures, proposed)
        score = (pruned['moved_count'], pruned['unused_seats'], tuple(pruned['rank_vector']))
        assert score == full
    except Refusal as error:
        assert error.code == 'no_feasible_plan' and full is None
    return dict(index=index, seed=SEED + 1000 + index, capacities=capacities,
                unpruned_score=full, unpruned_matches=True,
                scope='Small exhaustive reference-model control only')


def policy(restaurant, capacities):
    body = {k: deepcopy(restaurant[k]) for k in ['slot_minutes', 'reservation_duration_minutes',
                                               'cancellation_cutoff_minutes', 'opening_hours']}
    return dict(effective_from=DAY, capacities=capacities, **body)


def execute_case(c, index):
    trace_start = len(c.trace)
    construction = construct(index)
    fixture_value = fixture()
    restaurant = fixture_value['restaurants'][0]
    restaurant.update(slot_minutes=30, reservation_duration_minutes=90,
                      cancellation_cutoff_minutes=0, combinable=deepcopy(PAIRS))
    for table in restaurant['tables']:
        table['capacity'] = construction['original_capacities'][table['id']]
    c.setup(fixture_value)
    old = c.preview(construction['old_closure'], key='old-preview')
    c.check('repair-bound-old-empty', not old['assignments'])
    c.response('repair-bound-old-apply', c.apply(old, key='old-apply'), 201)
    issued = []
    for item in construction['booking_constructions']:
        if item['name'] == 'late-a':
            c.response('repair-bound-publication', c.call('POST', '/restaurants/r/policies',
                policy(restaurant, construction['later_capacities']), token=c.tokens['m'], key='later-policy'), 201)
        issued.append(c.make([item['table']], DAY + 'T' + item['clock'], item['party'], key=item['name']))
    c.response('repair-bound-latest-policy', c.call('POST', '/restaurants/r/policies',
        policy(restaurant, construction['latest_capacities']), token=c.tokens['m'], key='latest-policy'), 201)
    models = [booking(b['reference'], b['table_ids'], instant(b['starts_at']), instant(b['ends_at']),
        {k: integer(v) for k, v in b['accepted_terms']['capacities'].items()}, integer(b['party_size'])) for b in issued]
    try:
        expected = seating_plan(tuple('abcdef'), PAIRS, models, [construction['old_model']], construction['proposed_model'])
    except Refusal as error:
        expected = dict(error=error.code)
    public_before = c.public_state()
    raw_before = c.export()
    response = c.call('POST', '/restaurants/r/replans', construction['proposed_closure'],
                      token=c.tokens['m'], key='full-preview')
    if 'error' in expected:
        c.response('repair-bound-infeasible', response, 409, expected['error'])
        c.check('repair-bound-infeasible-atomic', raw_before == c.export())
        return dict(index=index, seed=construction['seed'], actual_references=[r['reference'] for r in issued],
                    expected=expected, observed_status=response[0], request_trace=deepcopy(c.trace[trace_start:]),
                    operation_construction={k: v for k, v in construction.items() if k not in ['records', 'old_model', 'proposed_model', 'expected']},
                    scope='Actual current source-bound HTTP construction')
    plan = c.response('repair-bound-preview', response, 201)
    for field in ['assignments', 'moved_count', 'unused_seats']:
        c.check('repair-bound-objective-' + field, same(plan[field], expected[field]))
    c.check('repair-bound-six-considered', len(plan['assignments']) == 6)
    fixed = {issued[0]['reference'], issued[-1]['reference']}
    c.check('repair-bound-fixed-excluded', not fixed.intersection(a['reference'] for a in plan['assignments']))
    c.check('repair-bound-preview-readonly', same(public_before, c.public_state()))
    applied = c.response('repair-bound-apply', c.apply(plan, key='full-apply'), 201)
    c.check('repair-bound-reference-order', [b['reference'] for b in applied['reservations']] == sorted(a['reference'] for a in plan['assignments']))
    for before in issued:
        after = c.lookup(before['reference'])
        c.check('repair-bound-identity-terms', all(same(before[k], after[k]) for k in
            ['reservation_id', 'reference', 'starts_at', 'ends_at', 'starts_at_local', 'party_size', 'accepted_terms', 'created_at']))
        if before['reference'] in fixed:
            c.check('repair-bound-fixed-unchanged', same(before, after))
        else:
            assignment = next(a for a in expected['assignments'] if a['reference'] == before['reference'])
            c.check('repair-bound-assignments', same(after['table_ids'], assignment['table_ids']))
            c.check('repair-bound-moved-revision', integer(after['revision']) == integer(before['revision']) + int(assignment['changed']))
    return dict(index=index, seed=construction['seed'], actual_references=[r['reference'] for r in issued],
                expected=expected, observed_plan=plan, observed_apply=applied,
                request_trace=deepcopy(c.trace[trace_start:]),
                operation_construction={k: v for k, v in construction.items() if k not in ['records', 'old_model', 'proposed_model', 'expected']},
                scope='Actual current source-bound HTTP construction; tokens and raw exports remain in memory')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cases', type=int, default=160)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit('Repaired candidate execution held')
    release = validate(json.loads(args.release.read_text()))
    assert 1 <= args.cases <= 160
    args.out.mkdir(parents=True, exist_ok=False)
    c = Client(release['urls']['target'], args.out / 'api', release['candidate'])
    observed = []
    error = None
    try:
        for index in range(args.cases):
            observed.append(execute_case(c, index))
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        c.save(error)
        (args.out / 'actual-operation-traces.json').write_bytes(raw(observed))
        (args.out / 'summary.json').write_text(json.dumps(dict(candidate=release['candidate'],
            constructions_completed=len(observed), requested=args.cases, error=error,
            actual_http_requests=c.count, actual_assertions=len(c.assertions),
            failed=sum(not a['passed'] for a in c.assertions), seed=SEED,
            finished_at=datetime.now(timezone.utc).isoformat()), indent=2) + '\n')


if __name__ == '__main__':
    main()
