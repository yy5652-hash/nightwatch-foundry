"""Own syntax/scalar differential reference and valid-by-composition deep cases."""
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("--module", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
module_path, out = Path(args.module).resolve(), Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=False)
spec = importlib.util.spec_from_file_location("json_codec", module_path)
codec = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = codec
spec.loader.exec_module(codec)
events, traces = [], []
started = time.monotonic()
seed = 2026100402
rng = random.Random(seed)


def check(label, condition, **details):
    events.append({"label": label, "passed": bool(condition), **details})


def signature(value):
    result, pending = [], [((), value)]
    while pending:
        path, item = pending.pop()
        if isinstance(item, dict):
            result.append((path, "object", tuple(sorted(item))))
            pending.extend((path + (key,), item[key]) for key in sorted(item))
        elif isinstance(item, list):
            result.append((path, "array", len(item)))
            pending.extend((path + (index,), child) for index, child in enumerate(item))
        elif type(item) in (bool, str) or item is None:
            result.append((path, type(item).__name__, item))
        elif type(item) is codec.JsonNumber:
            result.append((path, "number", Decimal(item.token)))
        else:
            result.append((path, "number", Decimal(item)))
    return result


def constant(_text):
    raise ValueError("non-JSON constant")


def differential(label, text):
    try:
        expected = json.loads(text, parse_float=Decimal, parse_constant=constant)
        reference_valid = True
    except (ValueError, UnicodeError):
        expected, reference_valid = None, False
    try:
        actual = codec.loads(text)
    except codec.JsonCodecError:
        check(label + " rejection", not reference_valid)
    except Exception as error:
        check(label + " ValueError-compatible result", False, exception=type(error).__name__)
    else:
        check(label + " admission/value", reference_valid and signature(actual) == signature(expected))
        if reference_valid:
            emitted = codec.dumps(actual)
            returned = json.loads(emitted, parse_float=Decimal, parse_constant=constant)
            check(label + " independent wire value", signature(returned) == signature(expected))
    raw = text.encode("utf-8") if isinstance(text, str) else text
    traces.append({"label": label, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "reference_valid": reference_valid})


valid = ['null', 'true', 'false', '0', '-0', '1.0', '1e0', '0.100000000000000005', '1e4300', '1e-4300',
         '[]', '{}', ' \t\r\n [ 1 , {"a": false}, null ] \r\n', '{"a":1,"a":2.0}', '{"x":0,"x":[{"x":true}]}',
         '"\\uD834\\uDD1E"', '"\\ud800"', '"rain 雨"', '"\\b\\f\\n\\r\\t\\\\\\/\\\""',
         '{"\\u0061":1,"a":3}', '[true,1,"1",null,[false],{}]', '{"":[],"a:b,c":[-3e+20]}']
invalid = ['', ' ', '[', '{', '[,]', '[1,]', '{,}', '{"a":1,}', '[1 2]', '{"a" 1}', '{"a":}',
           '{1:2}', '{true:3}', '{"a",2}', '{"a":1 "b":2}', '[]{}', '{}x', 'null true',
           '[}', '{]', '[1}}', '"unterminated', '"bad\\x"', '"bad\\u123x"', '"bad\nline"',
           '+1', '.1', '-.1', '01', '-01', '1.', '1e', '1e+', '--1', '1E--2', 'NaN', 'Infinity', '-Infinity',
           'nan', 'True', 'undefined', '\ufeff{}', '\u00a0{}', '{"a":NaN}', '[Infinity]',
           b'{"bad":"\xff"}', b'\xff{}', b'\xff\xfe{\x00}\x00']
for index, text in enumerate(valid + invalid):
    differential("corpus-%03d" % index, text)


def tree(depth):
    if depth == 0 or rng.randrange(3) == 0:
        return rng.choice([None, True, False, "rain 雨", "\\\"\n", rng.randrange(-200, 201)])
    if rng.randrange(2):
        return [tree(depth - 1) for _ in range(rng.randrange(4))]
    return {"key" + str(i): tree(depth - 1) for i in range(rng.randrange(4))}


for index in range(180):
    original = json.dumps(tree(5), ensure_ascii=rng.choice([True, False]), separators=rng.choice([(": ", ": "), (",", ":")]))
    # The first separator tuple may intentionally create invalid multi-item syntax;
    # the independent decoder determines each mutant's actual validity.
    differential("seed-%03d-original" % index, original)
    position = rng.randrange(len(original) + 1)
    mutated = original[:position] + rng.choice([",", "]", "}", ":", "\n", "x", '"']) + original[position:]
    differential("seed-%03d-mutant" % index, mutated)

for token, expected_type in (("2", int), ("2.0", codec.JsonNumber), ("2e0", codec.JsonNumber), ("true", bool)):
    check("token provenance " + token, type(codec.loads(token)) is expected_type)
check("duplicate key last value preserves boolean", codec.loads('{"a":1,"a":true}') == {"a": True})
check("duplicate escaped key last value", codec.loads('{"\\u0061":1,"a":2}') == {"a": 2})

for depth in (10000, 20000):
    for shape in ("array", "object", "alternating"):
        opening, closing = [], []
        for index in range(depth):
            is_array = shape == "array" or (shape == "alternating" and index % 2 == 0)
            opening.append("[" if is_array else '{"x":')
            closing.append("]" if is_array else "}")
        leaf = '{"value":0.100000000000000005,"large":1e4300,"bool":true}'
        text = "".join(opening) + leaf + "".join(reversed(closing))
        beginning = time.monotonic()
        value = codec.loads(text)
        current = value
        for _ in range(depth):
            current = current[0] if isinstance(current, list) else current["x"]
        check("%s-%d deep exact leaf" % (shape, depth), type(current["bool"]) is bool and current["value"].token == "0.100000000000000005" and current["large"].token == "1e4300")
        check("%s-%d deep wire roundtrip" % (shape, depth), codec.dumps(value) == text.encode())
        for kind, malformed in (("missing closing", text[:-1]), ("trailing", text + "x"),
                                ("wrong closing", text[:-1] + ("}" if text[-1] == "]" else "]")),
                                ("trailing comma", text[:-1] + "," + text[-1])):
            try:
                codec.loads(malformed)
            except codec.JsonCodecError:
                check("%s-%d %s refusal" % (shape, depth, kind), True)
            else:
                check("%s-%d %s refusal" % (shape, depth, kind), False)
        traces.append({"label": "%s-%d" % (shape, depth), "bytes": len(text.encode()),
                       "sha256": hashlib.sha256(text.encode()).hexdigest(), "grammar": "inductively balanced JSON containers and valid scalar leaf", "seconds": time.monotonic() - beginning})

summary = {"assertions": len(events), "passed": sum(x["passed"] for x in events), "failed": sum(not x["passed"] for x in events),
           "seconds": time.monotonic() - started, "seed": seed, "default_recursion_limit": sys.getrecursionlimit(),
           "module_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(), "scope": "codec diagnostics, not HTTP"}
(out / "assertions.json").write_text(json.dumps(events, indent=2) + "\n")
(out / "trace.json").write_text(json.dumps(traces, indent=2) + "\n")
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
raise SystemExit(bool(summary["failed"]))
