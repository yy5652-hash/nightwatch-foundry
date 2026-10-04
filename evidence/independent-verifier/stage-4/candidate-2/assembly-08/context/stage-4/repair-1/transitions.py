"""Future independent whole-series/history/error-order/atomic-read protocols."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from stage4_probe import Client, fixture, DAY, closure, integer, same, raw
from release_guard import validate


def policy_value(day, capacities):
    r = fixture()['restaurants'][0]
    return dict(effective_from=day, capacities=capacities, **{k: deepcopy(r[k]) for k in
        ['slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'opening_hours']})


def two_series(c):
    c.seed()
    first = c.adopt(c.make(local=DAY + 'T18:00', key='anchor-1'), count=3, key='series-1')
    second = c.adopt(c.make(local=DAY + 'T19:00', key='anchor-2'), count=3, key='series-2')
    exception = first['occurrences'][1]['reference']
    c.response('repair-series-exception', c.call('PATCH', '/reservations/' + exception,
        dict(party_size=2), token=c.tokens['u']), 200)
    originals = [c.current_series(s) for s in [first, second]]
    histories = {o['reference']: c.history(o['reference']) for s in originals for o in s['occurrences']}
    end = (date.fromisoformat(DAY) + timedelta(days=14)).isoformat() + 'T20:00:00+00:00'
    p = c.preview(closure(start=DAY + 'T17:00:00+00:00', end=end))
    c.check('repair-series-six-members', len(p['assignments']) == 6)
    applied = c.response('repair-series-apply', c.apply(p), 201)
    c.check('repair-series-restaurant-once', integer(applied['restaurant_revision']) == integer(p['restaurant_revision']) + 1)
    for series_index, before in enumerate(originals):
        after = c.current_series(before)
        c.check('repair-series-each-once', integer(after['revision']) == integer(before['revision']) + 1)
        for old, new in zip(before['occurrences'], after['occurrences']):
            c.check('repair-series-flags-indices', old['reference'] == new['reference'] and same(old['index'], new['index']) and old['exception'] is new['exception'])
            b, n = old['reservation'], new['reservation']
            c.check('repair-series-immutable', all(same(b[k], n[k]) for k in
                ['reservation_id', 'reference', 'party_size', 'starts_at_local', 'starts_at', 'ends_at', 'created_at', 'accepted_terms']))
            history = c.history(old['reference'])
            c.check('repair-series-history-once', len(history['entries']) == len(histories[old['reference']]['entries']) + 1)
            event = history['entries'][-1]
            c.check('repair-series-reassigned', event['event'] == 'reassigned' and event['plan_id'] == p['plan_id'] and
                same(event['changes'], [dict(field='table_ids', **{'from': b['table_ids']}, to=n['table_ids'])]) and same(event['accepted_terms'], b['accepted_terms']))
        target_clock = '21:00' if series_index == 0 else '22:00'
        changed = c.response('repair-series-later-amend', c.amend(after, time=target_clock, key='amend-' + after['series_id']), 201)
        for old, new in zip(after['occurrences'], changed['occurrences']):
            c.check('repair-series-repaired-seating', same(old['reservation']['table_ids'], new['reservation']['table_ids']))
            if old['exception']:
                c.check('repair-series-permanent-exception', same(old, new))
            else:
                c.check('repair-series-original-date', new['reservation']['starts_at_local'] == old['reservation']['starts_at_local'][:10] + 'T' + target_clock)


def empty(c):
    c.seed()
    s = c.adopt(c.make(), count=4)
    for i, occurrence in enumerate(s['occurrences']):
        if i % 2:
            c.response('repair-empty-cancel', c.call('POST', '/reservations/' + occurrence['reference'] + '/cancel', {}, token=c.tokens['u']), 200)
        else:
            c.response('repair-empty-exception', c.call('PATCH', '/reservations/' + occurrence['reference'], dict(party_size=2), token=c.tokens['u']), 200)
    current = c.current_series(s)
    before = c.public_state()
    p = c.preview(closure(start=DAY + 'T22:00:00+00:00', end=DAY + 'T23:00:00+00:00'), key='counter-before')
    result = c.response('repair-empty-success', c.amend(current, time='21:00', key='empty'), 201)
    c.check('repair-empty-identical-series', same(current, result))
    c.check('repair-empty-public-unchanged', same(before, c.public_state()))
    after = c.preview(closure(start=DAY + 'T22:00:00+00:00', end=DAY + 'T23:00:00+00:00'), key='counter-after')
    c.check('repair-empty-restaurant-unchanged', same(p['restaurant_revision'], after['restaurant_revision']))


def ordering(c):
    c.seed()
    s = c.adopt(c.make(party=2), count=3)
    obstruction = c.make(local=DAY + 'T19:00', party=1, key='obstruction')
    second_date = s['occurrences'][1]['reservation']['starts_at_local'][:10]
    caps = {t['id']: t['capacity'] for t in fixture()['restaurants'][0]['tables']}
    bad = {**caps, 'a': 1}
    c.response('repair-order-policy', c.call('POST', '/restaurants/r/policies', policy_value(second_date, bad), token=c.tokens['m'], key='bad-policy'), 201)
    before = c.export()
    c.response('repair-order-stale-first', c.amend(s, time='19:00', revision=999, key='stale'), 409, 'stale_revision')
    c.check('repair-order-stale-atomic', before == c.export())
    c.response('repair-order-nonoccupancy-first', c.amend(s, time='19:00', key='ordered'), 422, 'party_exceeds_capacity')
    c.check('repair-order-all-rollback', before == c.export())
    c.response('repair-order-fix-policy', c.call('POST', '/restaurants/r/policies', policy_value(second_date, caps), token=c.tokens['m'], key='good-policy'), 201)
    before = c.export()
    c.response('repair-order-final-occupancy', c.amend(s, time='19:00', key='ordered'), 409, 'table_unavailable')
    c.check('repair-order-occupancy-rollback', before == c.export())
    c.response('repair-order-remove-obstruction', c.call('POST', '/reservations/' + obstruction['reference'] + '/cancel', {}, token=c.tokens['u']), 200)
    c.response('repair-order-failed-key-reuse', c.amend(s, time='19:00', key='ordered'), 201)


def distinct(c):
    c.seed()
    s = c.adopt(c.make(), count=3)
    with ThreadPoolExecutor(max_workers=50) as pool:
        responses = list(pool.map(lambda i: c.amend(s, time='20:00', key='distinct-' + str(i)), range(50)))
    c.check('repair-distinct-one-real', sorted(r[0] for r in responses) == [201] + [409] * 49)
    winner = next(i for i, r in enumerate(responses) if r[0] == 201)
    failed = next(i for i, r in enumerate(responses) if r[0] == 409)
    for response in responses:
        if response[0] == 409:
            c.check('repair-distinct-stale-code', response[1]['error']['code'] == 'stale_revision')
    now = c.current_series(s)
    c.check('repair-distinct-series-once', integer(now['revision']) == integer(s['revision']) + 1)
    c.response('repair-distinct-reuse-failed-key', c.amend(now, time='21:00', key='distinct-' + str(failed)), 201)
    c.check('repair-distinct-original-replay', same(responses[winner][1], c.response('repair-distinct-original-replay', c.amend(s, time='20:00', key='distinct-' + str(winner)), 200)))


def atomic_reads(c):
    for wave in range(5):
        c.seed()
        a = c.make(local=DAY + 'T18:00', key='a')
        b = c.make(local=DAY + 'T19:00', key='b')
        s = c.adopt(a, count=3, key='series-a')
        t = c.adopt(b, count=3, key='series-b')
        end = (date.fromisoformat(DAY) + timedelta(days=14)).isoformat() + 'T20:00:00+00:00'
        p = c.preview(closure(start=DAY + 'T17:00:00+00:00', end=end))
        original = {o['reference']: tuple(o['reservation']['table_ids']) for series in [s, t] for o in series['occurrences']}
        final = {a['reference']: tuple(a['table_ids']) for a in p['assignments']}
        barrier = threading.Barrier(50)
        def operation(i):
            barrier.wait()
            if i == 0:
                return c.apply(p, key='atomic-' + str(wave))
            return c.call('GET', '/reservations', token=c.tokens['u'])
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(operation, range(50)))
        c.response('repair-atomic-write', results[0], 201)
        for result in results[1:]:
            value = c.response('repair-atomic-read', result, 200)
            snapshot = {r['reference']: tuple(r['table_ids']) for r in value['reservations']}
            c.check('repair-atomic-complete-prefix', snapshot in [original, final])


FAMILIES = {'two-series': two_series, 'empty': empty, 'ordering': ordering,
            'distinct': distinct, 'atomic-reads': atomic_reads}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--family', choices=FAMILIES, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit('Repaired candidate execution held')
    release = validate(json.loads(args.release.read_text()))
    c = Client(release['urls']['target'], args.out, release['candidate'])
    error = None
    try:
        FAMILIES[args.family](c)
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        c.save(error)


if __name__ == '__main__':
    main()
