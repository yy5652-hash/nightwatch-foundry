"""Own raw-wire deep decoder integration; no production/peer oracle imports.

JSON wrappers are valid inductively. Deep private exports remain raw bytes in
memory and are forwarded unchanged; only shallow public responses are decoded.
--self-check constructs diagnostics without contacting any service.
"""
import argparse
import concurrent.futures
import hashlib
import http.client
import json
import re
import sys
import threading
import time
from urllib.parse import urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--self-check', action='store_true')
parser.add_argument('urls', nargs='*')
args = parser.parse_args()
URLS = [urlsplit(url) for url in args.urls]
CHECKS, TRACE, BLOCKED = [], [], []
START = time.monotonic()
LEAF = b'{"exact":0.100000000000000005,"alias":1.0,"zero":-0.0,"truth":true,"text":"[]{}:comma,\\\"\\\\\\n\\u96ea"}'
FIXTURE = {
    'users': [{'id': 'decoder-diner', 'email': 'decoder@example.test',
               'password': 'correct horse', 'display_name': 'Decoder'}],
    'restaurants': [{'id': 'decoder-room', 'name': 'Calm Room', 'timezone': 'UTC',
        'slot_minutes': 30, 'reservation_duration_minutes': 60, 'cancellation_cutoff_minutes': 0,
        'opening_hours': [{'weekday': day, 'opens': '18:00', 'closes': '23:30'}
                          for day in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')],
        'tables': [{'id': 't'+str(i), 'label': 'Table '+str(i), 'capacity': 4} for i in range(1, 4)]}],
    'reservations': []}


def check(name, condition):
    CHECKS.append({'name': name, 'passed': bool(condition)})


def nested(depth, shape, leaf=LEAF):
    # Prefixes/suffixes retain lexical depth without recursive construction.
    if shape == 'array':
        return b'['*depth + leaf + b']'*depth
    if shape == 'object':
        return b'{"v":'*depth + leaf + b'}'*depth
    prefixes, suffixes = [], []
    for i in range(depth):
        prefixes.append(b'{"v":' if i % 2 else b'[')
        suffixes.append(b'}' if i % 2 else b']')
    return b''.join(prefixes) + leaf + b''.join(reversed(suffixes))


def envelope(value, deep):
    shallow = json.dumps(value, separators=(',', ':')).encode()
    return shallow[:-1] + b',"ignored":' + deep + b'}'


def call(index, method, path, value=None, *, raw=None, token=None, key=None):
    body = raw if raw is not None else (json.dumps(value, separators=(',', ':')).encode() if value is not None else None)
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    if token:
        headers['Authorization'] = 'Bearer '+token
    if key is not None:
        headers['Idempotency-Key'] = key
    limit = 10 if path.startswith('/_test/') else 5
    connection = http.client.HTTPConnection(URLS[index].hostname, URLS[index].port, timeout=limit)
    begin = time.monotonic()
    try:
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        wire = response.read()
        seconds = time.monotonic()-begin
        exported = path == '/_test/export' and response.status == 200
        parsed = None if not wire or exported else json.loads(wire)
        check('JSON UTF-8 media type', response.getheader('Content-Type') == 'application/json; charset=utf-8')
        check('Exact response byte length', response.getheader('Content-Length') == str(len(wire)))
        check('Applicable request deadline', seconds < limit)
        TRACE.append({'process': index, 'method': method,
            'path': re.sub(r'/reservations/[^/]+', '/reservations/<reference>', path),
            'status': response.status, 'code': parsed.get('error', {}).get('code') if isinstance(parsed, dict) else None,
            'seconds': seconds, 'request_bytes': len(body or b''), 'response_bytes': len(wire),
            'request_sha256': hashlib.sha256(body or b'').hexdigest(),
            'response_sha256': hashlib.sha256(wire).hexdigest(), 'deep_export_decoded': False if exported else None})
        return response.status, parsed, wire
    finally:
        connection.close()


def expect(name, response, status, code=None):
    check(name, response[0] == status and (code is None or (response[1] or {}).get('error', {}).get('code') == code))
    if status == 204:
        check('204 carries no bytes', response[2] == b'')
    return response


def current(index, token):
    response = expect('Current private records available', call(index, 'GET', '/reservations', token=token), 200)
    return response[1]


def malformed_controls(depth, shape, token):
    valid = envelope(FIXTURE, nested(depth, shape))
    variants = {
        'missing close': valid[:-1],
        'extra document': valid+b'{}',
        'trailing array comma': envelope(FIXTURE, nested(depth, shape, b'[1,]')),
        'missing object colon': envelope(FIXTURE, nested(depth, shape, b'{"x" 1}')),
        'mismatched closer': envelope(FIXTURE, nested(depth, shape, b'[1}')),
        'leading zero': envelope(FIXTURE, nested(depth, shape, b'01')),
        'unfinished exponent': envelope(FIXTURE, nested(depth, shape, b'1e+')),
        'literal constant': envelope(FIXTURE, nested(depth, shape, b'NaN')),
        'invalid escape': envelope(FIXTURE, nested(depth, shape, b'"\\q"')),
        'literal string control': envelope(FIXTURE, nested(depth, shape, b'"line\nend"')),
        'invalid UTF-8': envelope(FIXTURE, nested(depth, shape, b'"\xff"')),
    }
    for name, raw in variants.items():
        expect('Deep malformed '+name+' reset', call(0, 'POST', '/_test/reset', raw=raw), 400, 'malformed_request')
    # Failed resets must not replace credentials or records.
    check('All malformed deep resets preserve token/empty records', current(0, token) == {'reservations': []})
    expect('Healthy after deep malformed controls', call(0, 'GET', '/health'), 200)


def case(depth, shape):
    label = str(depth)+'-'+shape
    deep = nested(depth, shape)
    reset = expect('Valid deep ignored reset '+label, call(0, 'POST', '/_test/reset', raw=envelope(FIXTURE, deep)), 204)
    if reset[0] != 204:
        BLOCKED.append({'case': label, 'paths': ['deep signup/create/move/aliases/receipts/raw replacement'], 'cause': 'valid reset refused'})
        return
    expect('Peer ordinary reset', call(1, 'POST', '/_test/reset', FIXTURE), 204)
    token = expect('Real diner login', call(0, 'POST', '/auth/login', {'email': 'decoder@example.test', 'password': 'correct horse'}), 200)[1]['token']
    displaced = expect('Peer session before replacement', call(1, 'POST', '/auth/login', {'email': 'decoder@example.test', 'password': 'correct horse'}), 200)[1]['token']
    signup = envelope({'email': label+'@example.test', 'password': 'correct horse', 'display_name': 'Wire'}, deep)
    expect('Valid deep ignored signup '+label, call(0, 'POST', '/auth/signup', raw=signup), 201)
    malformed_controls(depth, shape, token)
    fields = {'restaurant_id': 'decoder-room', 'table_id': 't1', 'starts_at_local': '2099-06-01T18:00', 'party_size': 2}
    raw = envelope(fields, deep)
    first = expect('Valid deep create '+label, call(0, 'POST', '/reservations', raw=raw, token=token, key='create'), 201)
    if first[0] != 201:
        BLOCKED.append({'case': label, 'paths': ['deep create/move original receipts/raw replacement'], 'cause': 'valid create refused'})
        expect('Failed deep key stays reusable', call(0, 'POST', '/reservations', fields, token=token, key='create'), 201)
        return
    original = first[1]
    alias = raw.replace(b'"party_size":2', b'"party_size":2e0').replace(b'"alias":1.0', b'"alias":1e0').replace(b'"zero":-0.0', b'"zero":0')
    check('Full deep numerical aliases replay', expect('Alias create retry', call(0, 'POST', '/reservations', raw=alias, token=token, key='create'), 200)[1] == original)
    unequal = raw.replace(b'0.100000000000000005', b'0.100000000000000006').replace(b'"party_size":2', b'"party_size":false')
    expect('Deep different body conflicts before invalid party', call(0, 'POST', '/reservations', raw=unequal, token=token, key='create'), 409, 'idempotency_key_reuse')
    expect('Deep bool/number distinction', call(0, 'POST', '/reservations', raw=raw.replace(b'"truth":true', b'"truth":1'), token=token, key='create'), 409, 'idempotency_key_reuse')
    expect('Deep missing key precedence', call(0, 'POST', '/reservations', raw=raw, token=token), 400, 'missing_idempotency_key')
    invalid = envelope({**fields, 'table_id': 't2', 'party_size': 1.5}, deep)
    expect('Invalid party in valid deep JSON', call(0, 'POST', '/reservations', raw=invalid, token=token, key='failed'), 422, 'validation_failed')
    second = expect('Failed key reused for valid deep create', call(0, 'POST', '/reservations', raw=envelope({**fields, 'table_id': 't2'}, deep), token=token, key='failed'), 201)
    if second[0] != 201:
        BLOCKED.append({'case': label, 'paths': ['atomic deep swap'], 'cause': 'second create refused'})
        return
    moves = {'moves': [{'reference': original['reference'], 'table_id': 't2'}, {'reference': second[1]['reference'], 'table_id': 't1'}]}
    move = envelope(moves, deep)
    receipt = expect('Actual atomic swap with deep body', call(0, 'POST', '/reservation-moves', raw=move, token=token, key='move'), 201)
    if receipt[0] != 201:
        BLOCKED.append({'case': label, 'paths': ['deep move original receipt/replacement'], 'cause': 'move refused'})
        return
    expect('Move different valid body conflicts before missing reference', call(0, 'POST', '/reservation-moves', raw=move.replace(b'0.100000000000000005', b'0.100000000000000006').replace(original['reference'].encode(), b'UNKNOWN'), token=token, key='move'), 409, 'idempotency_key_reuse')
    expect('Deep move missing key', call(0, 'POST', '/reservation-moves', raw=move, token=token), 400, 'missing_idempotency_key')
    expect('Amend after deep original receipt', call(0, 'PATCH', '/reservations/'+original['reference'], {'party_size': 1}, token=token), 200)
    expect('Cancel after deep original receipt', call(0, 'POST', '/reservations/'+second[1]['reference']+'/cancel', token=token), 200)
    before = current(0, token)
    captured = expect('Real raw deep export', call(0, 'GET', '/_test/export'), 200)[2]
    expect('Raw unchanged deep export to independent process', call(1, 'POST', '/_test/import', raw=captured), 204)
    expect('Import replaces old destination session', call(1, 'GET', '/reservations', token=displaced), 401, 'unauthenticated')
    check('References/identities/current status preserved', current(1, token) == before)
    forwarded = expect('Second independent raw export', call(1, 'GET', '/_test/export'), 200)[2]
    expect('Second raw replacement preserves complete receipts', call(0, 'POST', '/_test/import', raw=forwarded), 204)
    for index in range(2):
        check('Original create JSON value immutable after edit/cancel/import', expect('Original create deep retry after transfer', call(index, 'POST', '/reservations', raw=raw, token=token, key='create'), 200)[1] == original)
        check('Original move JSON value immutable after edit/cancel/import', expect('Original move deep retry after transfer', call(index, 'POST', '/reservation-moves', raw=move, token=token, key='move'), 200)[1] == receipt[1])
        expect('Unequal deep value remains conflict after transfer', call(index, 'POST', '/reservations', raw=unequal, token=token, key='create'), 409, 'idempotency_key_reuse')
        check('Original deep retries do not mutate current state', current(index, token) == before)
    invalid_profile = re.sub(rb'"numeric_profile"\s*:\s*"exact-v1"', b'"numeric_profile":"unsupported"', forwarded, count=1)
    check('Invalid profile changes actual captured raw export', invalid_profile != forwarded)
    expect('Valid grammar invalid deep profile', call(1, 'POST', '/_test/import', raw=invalid_profile), 422, 'validation_failed')
    expect('Malformed deep import', call(1, 'POST', '/_test/import', raw=forwarded[:-1]), 400, 'malformed_request')
    check('Refused deep imports are atomic', current(1, token) == before)
    if depth == 20000 and shape == 'array':
        competing = envelope({**fields, 'table_id': 't3'}, deep)
        barrier = threading.Barrier(50)
        def request(_):
            barrier.wait(timeout=5)
            return call(0, 'POST', '/reservations', raw=competing, token=token, key='fifty')
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
            responses = list(pool.map(request, range(50)))
        statuses = [r[0] for r in responses]
        check('50 deep requests yield exactly one201 and49replays', statuses.count(201) == 1 and statuses.count(200) == 49)
        successful = next((r[1] for r in responses if r[0] == 201), None)
        check('All50 receipts are identical original responses', successful is not None and all(r[1] == successful for r in responses))
        latest = expect('Concurrent deep receipt raw export', call(0, 'GET', '/_test/export'), 200)[2]
        expect('Concurrent receipt raw replacement', call(1, 'POST', '/_test/import', raw=latest), 204)
        check('Concurrent original receipt survives import', expect('Deep fifty retry after transfer', call(1, 'POST', '/reservations', raw=competing, token=token, key='fifty'), 200)[1] == successful)
        check('No concurrent duplicate booking', len(current(1, token)['reservations']) == 3)
    expect('Default service stays healthy', call(0, 'GET', '/health'), 200)
    expect('Override service stays healthy', call(1, 'GET', '/health'), 200)


def self_check():
    leaf = json.loads(LEAF)
    check('Shallow independent leaf grammar', leaf['truth'] is True and isinstance(leaf['text'], str))
    for depth in (10000, 20000):
        for shape in ('array', 'object', 'alternating'):
            raw = nested(depth, shape)
            sample = nested(3, shape)
            json.loads(sample)  # Only a shallow representative is decoded.
            check('Inductive balanced wrapper '+str(depth)+' '+shape, raw.count(LEAF) == 1 and len(raw) > 2*depth)
            check('Leaf replacement retains deep lexical value', raw.replace(b'"alias":1.0', b'"alias":1e0') != raw)
    check('No client recursion-limit mutation', sys.getrecursionlimit() == 1000)


try:
    if args.self_check:
        self_check()
    else:
        assert len(URLS) == 2
        for depth in (10000, 20000):
            for shape in ('array', 'object', 'alternating'):
                case(depth, shape)
except Exception as exc:
    check('Client/flow completes without exception', False)
    TRACE.append({'client_exception': type(exc).__name__, 'message': str(exc)[:160]})
summary = {'scope': 'Own decoder wire construction only' if args.self_check else 'Actual deep HTTP receipts/raw replacement; independently authored Interface evidence',
    'depths': [10000, 20000], 'shapes': ['array', 'object', 'alternating'], 'client_recursion_limit': sys.getrecursionlimit(),
    'operations': sum('method' in row for row in TRACE), 'assertions': len(CHECKS),
    'passed': sum(row['passed'] for row in CHECKS), 'failed': sum(not row['passed'] for row in CHECKS),
    'seconds': time.monotonic()-START, 'max_request_seconds': max((row.get('seconds', 0) for row in TRACE), default=0),
    'max_body_bytes': max((row.get('request_bytes', 0) for row in TRACE), default=0),
    'blocked': BLOCKED, 'checks': CHECKS, 'trace': TRACE}
print(json.dumps(summary, indent=2))
sys.exit(1 if summary['failed'] else 0)
