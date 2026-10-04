"""Own cumulative-spec closure type regression. HTTP only; no service helpers.

Stage 1 section 5 assigns wrong JSON types 400 and missing/value errors 422.
Stage 4's invalid interval rule retains that distinction. Original exports and
tokens stay in memory; saved observations contain fingerprints only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
from pathlib import Path
import time
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8080')
    parser.add_argument('--out')
    args = parser.parse_args()
    target = urlsplit(args.url)
    calls, assertions = [], []
    started = datetime.now(timezone.utc).isoformat()
    began = time.monotonic()
    sha = lambda raw: hashlib.sha256(raw).hexdigest()

    def call(method, path, body=None, *, raw=None, token=None, key=None):
        data = raw if raw is not None else (json.dumps(body, separators=(',', ':')).encode() if body is not None else None)
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        if token is not None:
            headers['Authorization'] = 'Bearer ' + token
        if key is not None:
            headers['Idempotency-Key'] = key
        connection = http.client.HTTPConnection(target.hostname, target.port, timeout=10 if path.startswith('/_test/') else 5)
        start = time.monotonic()
        connection.request(method, path, data, headers)
        response = connection.getresponse()
        content = response.read()
        elapsed = time.monotonic() - start
        connection.close()
        value = None if path == '/_test/export' or not content else json.loads(content)
        code = value.get('error', {}).get('code') if isinstance(value, dict) else None
        calls.append({'index': len(calls), 'method': method, 'path': path, 'status': response.status,
                      'code': code, 'request_sha256': sha(data or b''), 'response_sha256': sha(content),
                      'request_bytes': len(data or b''), 'response_bytes': len(content), 'seconds': elapsed})
        return response.status, value, content

    def check(label, actual, expected):
        assertions.append({'label': label, 'actual': actual, 'expected': expected,
                           'passed': actual == expected, 'request_index': len(calls) - 1})

    def expect(label, result, status, code=None):
        check(label + '-status', result[0], status)
        if code is not None:
            check(label + '-code', result[1].get('error', {}).get('code'), code)
        return result[1]

    fixture = {'users': [{'id': name, 'email': name + '@systems.test', 'password': 'systems fixture', 'display_name': name}
                         for name in ('manager', 'diner')],
               'restaurants': [{'id': 'room', 'name': 'Systems Garden', 'timezone': 'UTC', 'slot_minutes': 30,
                                'reservation_duration_minutes': 60, 'cancellation_cutoff_minutes': 0,
                                'manager_user_ids': ['manager'], 'combinable': [['window', 'garden']],
                                'tables': [{'id': 'window', 'label': 'Window', 'capacity': 2},
                                           {'id': 'garden', 'label': 'Garden', 'capacity': 4}],
                                'opening_hours': [{'weekday': day, 'opens': '17:00', 'closes': '23:00'}
                                                  for day in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')]}],
               'reservations': []}
    expect('reset', call('POST', '/_test/reset', fixture), 204)
    tokens = {}
    for name in ('manager', 'diner'):
        tokens[name] = expect('login-' + name, call('POST', '/auth/login', {'email': name + '@systems.test',
                                    'password': 'systems fixture'}), 200)['token']
    endpoint = '/restaurants/room/replans'
    base = {'table_id': 'window', 'from': '2099-06-04T18:00:00Z', 'to': '2099-06-04T19:00:00Z'}
    cases = []
    for field in ('from', 'to'):
        for name, value in [('null', None), ('true', True), ('false', False), ('number', 7), ('array', []), ('object', {})]:
            cases.append((field + '-' + name, {**base, field: value}, 400, 'malformed_request'))
        cases.append((field + '-missing', {k: v for k, v in base.items() if k != field}, 422, 'validation_failed'))
        for name, value in [('empty', ''), ('bad-date', '2099-02-30T18:00:00Z'), ('bare-local', '2099-06-04T18:00:00'),
                            ('bad-clock', '2099-06-04T24:00:00Z'), ('bad-offset', '2099-06-04T18:00:00+24:00')]:
            cases.append((field + '-' + name, {**base, field: value}, 422, 'validation_failed'))
    cases.extend([('equal', {**base, 'to': base['from']}, 422, 'validation_failed'),
                  ('reverse', {**base, 'from': base['to'], 'to': base['from']}, 422, 'validation_failed'),
                  ('table-type', {**base, 'table_id': []}, 400, 'malformed_request')])
    for index, (label, body, status, code) in enumerate(cases):
        snapshot = call('GET', '/_test/export')[2]
        key = 'systems-refusal-' + str(index)
        expect(label, call('POST', endpoint, body, token=tokens['manager'], key=key), status, code)
        check(label + '-atomic', sha(call('GET', '/_test/export')[2]), sha(snapshot))
        expect(label + '-failed-key-reuse', call('POST', endpoint, base, token=tokens['manager'], key=key), 201)
    for index, payload in enumerate([b'null', b'[]', b'false', b'7', b'{', b'{"from":Infinity}']):
        snapshot = call('GET', '/_test/export')[2]
        key = 'systems-whole-' + str(index)
        expect('whole-' + str(index), call('POST', endpoint, raw=payload, token=tokens['manager'], key=key), 400, 'malformed_request')
        check('whole-atomic-' + str(index), sha(call('GET', '/_test/export')[2]), sha(snapshot))
        expect('whole-key-reuse-' + str(index), call('POST', endpoint, base, token=tokens['manager'], key=key), 201)
    receipt = expect('first-preview', call('POST', endpoint, base, token=tokens['manager'], key='systems-used'), 201)
    for field in ('from', 'to'):
        for value in (None, True, False, 7, [], {}):
            snapshot = call('GET', '/_test/export')[2]
            expect('used-priority-' + field, call('POST', endpoint, {**base, field: value},
                                               token=tokens['manager'], key='systems-used'), 409, 'idempotency_key_reuse')
            check('used-priority-atomic-' + field, sha(call('GET', '/_test/export')[2]), sha(snapshot))
    replay = expect('original-preview', call('POST', endpoint, dict(reversed(list(base.items()))),
                                             token=tokens['manager'], key='systems-used'), 200)
    check('immutable-preview', replay, receipt)
    for label, token, status, code in [('anonymous', None, 401, 'unauthenticated'), ('nonmanager', tokens['diner'], 403, 'forbidden')]:
        snapshot = call('GET', '/_test/export')[2]
        expect(label + '-before-type', call('POST', endpoint, {**base, 'from': None}, token=token, key=label), status, code)
        check(label + '-atomic', sha(call('GET', '/_test/export')[2]), sha(snapshot))
    expect('missing-key', call('POST', endpoint, {**base, 'from': None}, token=tokens['manager']), 400, 'missing_idempotency_key')
    booking = expect('boundary-booking', call('POST', '/reservations', {'restaurant_id': 'room', 'table_id': 'window',
                           'starts_at_local': '2099-06-04T18:00', 'party_size': 2}, token=tokens['diner'], key='boundary'), 201)
    boundaries = [('before', '2099-06-04T17:59:00Z', '2099-06-04T18:00:00Z', 0),
                  ('before-fraction', '2099-06-04T17:59:00Z', '2099-06-04T18:00:00.000000000000000001Z', 1),
                  ('after', '2099-06-04T19:00:00Z', '2099-06-04T19:01:00Z', 0),
                  ('after-fraction', '2099-06-04T18:59:59.999999999999999999Z', '2099-06-04T19:01:00Z', 1)]
    for label, start, end, count in boundaries:
        proposal = expect('precision-' + label, call('POST', endpoint, {**base, 'from': start, 'to': end},
                          token=tokens['manager'], key='precision-' + label), 201)
        check(label + '-considered', len(proposal['assignments']), count)
        check(label + '-strings', proposal['closure'], {'table_id': 'window', 'from': start, 'to': end})
        if count:
            check(label + '-identity', proposal['assignments'][0]['reference'], booking['reference'])
    summary = {'method': 'HTTP', 'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
               'requests': len(calls), 'assertions': len(assertions), 'failed': sum(not row['passed'] for row in assertions),
               'wrong_type_cases': 12, 'interval_cases': len(cases), 'seconds': time.monotonic() - began,
               'maximum_request_seconds': max(row['seconds'] for row in calls), 'private_exports_saved': False}
    report = {'summary': summary, 'requests': calls, 'assertions': assertions}
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=False)
        (out / 'trace.json').write_text(json.dumps(report, indent=2) + '\n')
        (out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
        print(json.dumps(summary))
    else:
        print(json.dumps(report))
    raise SystemExit(bool(summary['failed']))


if __name__ == '__main__':
    main()
