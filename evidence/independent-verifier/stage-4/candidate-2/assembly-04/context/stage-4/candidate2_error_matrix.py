"""Future individually separated invalid writes and permission/key rollback.

No endpoint behavior is counted during preparation. Corrected bodies reuse the
same failed key at the same path and caller, against freshly seeded real state.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from stage4_probe import Client, closure
sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from stage3_probe import parse


def cases(family):
    result = [('whole-null', b'null', 400, 'malformed_request'),
              ('whole-array', b'[]', 400, 'malformed_request'),
              ('whole-number', b'1', 400, 'malformed_request'),
              ('whole-boolean', b'true', 400, 'malformed_request'),
              ('whole-syntax', b'{', 400, 'malformed_request'),
              ('whole-constant', b'{"ignored":NaN}', 400, 'malformed_request'),
              ('whole-utf8', b'{"ignored":"\xff"}', 400, 'malformed_request')]
    if family == 'preview':
        for field in ['table_id', 'from', 'to']:
            result.append((field + '-missing', ('missing', field), 422, 'validation_failed'))
            for name, value in [('null', None), ('true', True), ('false', False), ('number', 7), ('array', []), ('object', {})]:
                result.append((field + '-type-' + name, ('set', field, value), 400, 'malformed_request'))
        result.append(('unknown-table', ('set', 'table_id', 'missing'), 404, 'not_found'))
    elif family == 'amend':
        for field in ['expected_revision', 'from_index', 'local_time']:
            result.append((field + '-missing', ('missing', field), 422, 'validation_failed'))
            values = [('null', None), ('true', True), ('false', False), ('array', []), ('object', {})]
            if field != 'local_time':
                values += [('string', '1'), ('fraction', parse('1.5'))]
            else:
                values += [('number', 7), ('seconds', '19:00:00'), ('padding', ' 19:00'),
                           ('offset', '19:00+00:00'), ('invalid-clock', '24:00')]
            for name, value in values:
                result.append((field + '-invalid-' + name, ('set', field, value), 422, 'validation_failed'))
        result += [('revision-zero', ('set', 'expected_revision', 0), 422, 'validation_failed'),
                   ('revision-negative', ('set', 'expected_revision', -1), 422, 'validation_failed'),
                   ('index-negative', ('set', 'from_index', -1), 422, 'validation_failed'),
                   ('index-count', ('set', 'from_index', 4), 422, 'validation_failed'),
                   ('revision-stale', ('set', 'expected_revision', 999), 409, 'stale_revision')]
    return result


def build(c, family):
    c.seed()
    a = c.make()
    if family == 'preview':
        return '/restaurants/r/replans', closure(), 'm'
    if family == 'apply':
        p = c.preview()
        return '/restaurants/r/replans/' + p['plan_id'] + '/apply', {}, 'm'
    s = c.adopt(a, count=4)
    return '/series/' + s['series_id'] + '/amend', dict(expected_revision=s['revision'], from_index=0, local_time='19:00'), 'u'


def run(c, family):
    for index, (name, mutation, status, code) in enumerate(cases(family)):
        path, good, who = build(c, family)
        before = c.export()
        key = 'invalid-' + str(index)
        if isinstance(mutation, bytes):
            response = c.call('POST', path, body=mutation, token=c.tokens[who], key=key)
        else:
            bad = deepcopy(good)
            if mutation[0] == 'missing':
                bad.pop(mutation[1])
            else:
                bad[mutation[1]] = mutation[2]
            response = c.call('POST', path, bad, token=c.tokens[who], key=key)
        c.response('repair-' + family + '-' + name, response, status, code)
        c.check('repair-' + family + '-' + name + '-atomic', before == c.export())
        c.response('repair-' + family + '-' + name + '-key-reusable',
                   c.call('POST', path, good, token=c.tokens[who], key=key), 201)
    permission_cases = [('no-token', None, 'valid', 401, 'unauthenticated'),
                        ('unknown-token', 'not-a-live-token', 'valid', 401, 'unauthenticated'),
                        ('no-key', 'owner', None, 400, 'missing_idempotency_key'),
                        ('empty-key', 'owner', '', 400, 'missing_idempotency_key'),
                        ('long-key', 'owner', 'x' * 256, 422, 'validation_failed')]
    if family != 'amend':
        permission_cases.append(('non-manager', 'diner', 'valid', 403, 'forbidden'))
    else:
        permission_cases.append(('another-owner', 'other', 'valid', 404, 'not_found'))
    for name, auth, key, status, code in permission_cases:
        path, good, who = build(c, family)
        token = c.tokens[who] if auth == 'owner' else c.tokens['u'] if auth == 'diner' else c.tokens['v'] if auth == 'other' else auth
        before = c.export()
        c.response('repair-' + family + '-' + name,
                   c.call('POST', path, good, token=token, key=key), status, code)
        c.check('repair-' + family + '-' + name + '-atomic', before == c.export())
    path, good, who = build(c, family)
    original = c.response('repair-' + family + '-original', c.call('POST', path, good, token=c.tokens[who], key='used'), 201)
    before = c.export()
    bad = {**good, 'ignored-distinct': True}
    c.response('repair-' + family + '-full-body-priority', c.call('POST', path, bad, token=c.tokens[who], key='used'), 409, 'idempotency_key_reuse')
    c.check('repair-' + family + '-used-key-atomic', before == c.export())
    replay = c.response('repair-' + family + '-original-replay', c.call('POST', path, dict(reversed(list(good.items()))), token=c.tokens[who], key='used'), 200)
    from stage4_probe import same
    c.check('repair-' + family + '-same-original', same(original, replay))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--family', choices=['preview', 'apply', 'amend'], required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit('Repaired candidate execution held')
    release = validate(json.loads(args.release.read_text()))
    c = Client(release['urls']['target'], args.out, release['candidate'])
    error = None
    try:
        run(c, args.family)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        c.save(error)


if __name__ == '__main__':
    main()
