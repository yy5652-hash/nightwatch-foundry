"""Own codec diagnostics; independent Decimal/Fraction reference at modest bounds."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import Decimal
from fractions import Fraction
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
out = Path(args.out)
out.mkdir(parents=True, exist_ok=False)
module_path = Path(args.module).resolve()
spec = importlib.util.spec_from_file_location("json_codec", module_path)
codec = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = codec
spec.loader.exec_module(codec)
events = []
started = time.monotonic()


def check(label, condition, detail=None):
    events.append({"id": len(events) + 1, "label": label, "passed": bool(condition), "detail": detail})


def refuses(label, operation):
    try:
        operation()
    except codec.JsonCodecError as error:
        check(label, isinstance(error, ValueError))
    except Exception as error:
        check(label, False, type(error).__name__)
    else:
        check(label, False, "no refusal")


giant = "1" + "0" * 4299 + "1"
enormous_exponent = "9" * 80
tokens = ["0", "-0", "-0.0", "1", "1.0", "1e0", "1.5", "0.100000000000000005",
          "9007199254740993.0", giant, giant + ".5", "1e4300", "1e-4300",
          "1e" + enormous_exponent, "-7e-" + enormous_exponent,
          "-0e-" + enormous_exponent]
for index, token in enumerate(tokens):
    value = codec.loads(token)
    wire = codec.dumps({"unused": value})
    roundtrip = codec.loads(wire)["unused"]
    detail = {"input_sha256": hashlib.sha256(token.encode()).hexdigest(), "input_bytes": len(token),
              "wire_sha256": hashlib.sha256(wire).hexdigest(), "wire_bytes": len(wire),
              "leaf_type": type(value).__name__}
    check("boundary-%02d bytes encoder" % index, type(wire) is bytes, detail)
    check("boundary-%02d exact roundtrip" % index, codec.same_value(value, roundtrip))
    check("boundary-%02d numeric wire token" % index, not wire.startswith(b'{"unused":"'))
    check("boundary-%02d token kind" % index,
          type(value) is codec.JsonNumber if "." in token or "e" in token else type(value) is int)
    if len(token) < 4400 and len(token.split("e")[-1]) < 20:
        exact = Decimal(token)
        emitted = json.loads(wire, parse_float=Decimal)["unused"]
        check("boundary-%02d independent exact value" % index, emitted == exact)

huge = codec.loads("1e" + enormous_exponent)
huge_alias = codec.loads("10e" + str(int(enormous_exponent) - 1))
check("compact huge exponent equal alias", codec.same_value(huge, huge_alias))
check("compact huge exponent comparison", codec.compare_numbers(huge, codec.loads("9e4300")) == 1)
check("compact tiny exponent comparison", codec.compare_numbers(codec.loads("1e-" + enormous_exponent), 0) == 1)
check("compact huge exponent classification", codec.is_integral(huge))
check("compact tiny exponent classification", not codec.is_integral(codec.loads("1e-" + enormous_exponent)))
check("compact zero integral and no expansion", codec.to_integer(codec.loads("-0e" + enormous_exponent)) == 0)
product = codec.multiply_integer(huge, 60_000_000)
check("compact multiplication", codec.same_value(product, codec.loads("6e" + str(int(enormous_exponent) + 7))))

for left, right, equal in [("1", "1.0", True), ("1.0", "1e0", True), ("-0.0", "0e20", True),
                           ("true", "1", False), ('"1"', "1", False), ("false", "0", False),
                           ("null", "0", False), ("0.1", "0.100000000000000005", False),
                           ("9007199254740993.0", "9007199254740993", True)]:
    check("current alias/type " + left + " / " + right,
          codec.same_value(codec.loads(left), codec.loads(right)) == equal)

legacy_pairs = [("0.1", "0.100000000000000005", True), ("0.1", "0.10000000000000002", False),
                ("9007199254740992.0", "9007199254740993.0", True),
                ("9007199254740992.0", "9007199254740993", False),
                ("9007199254740992.0", "9007199254740992", True),
                ("0.0", "1e-4300", True), ("0", "1e-4300", True),
                ("0.0", "true", False), ("0.0", '"0"', False),
                ("1.0", "1e4300", False), ("1e4300", "1e4300", False)]
for left, right, equal in legacy_pairs:
    check("legacy projection " + left + " / " + right,
          codec.same_value(codec.loads(left), codec.loads(right), profile="python-json-v1") == equal)

original = codec.loads('{"a":[1e0,{"ignored":0.100000000000000005}],"b":true}')
alias = codec.loads('{"b":true,"a":[1.0,{"ignored":0.100000000000000005}]}')
different = codec.loads('{"b":true,"a":[1.0,{"ignored":0.1}]}')
check("nested exact object order", codec.same_value(original, alias))
check("nested ignored distinct fraction", not codec.same_value(original, different))
check("nested ignored legacy source equality", codec.same_value(original, different, profile="python-json-v1"))
check("array order matters", not codec.same_value([1, 2], [2, 1]))
snapshot = deepcopy(original)
original["a"].append(2)
check("copied tree independent", codec.same_value(snapshot, alias))
number = codec.loads("1e4300")
try:
    number.token = "2"
except FrozenInstanceError:
    check("numeric leaf immutable", True)
else:
    check("numeric leaf immutable", False)
check("immutable deepcopy value", codec.same_value(number, deepcopy(number)))

strings = {"quote": '"\\\n\x00', "unicode": "Café 雨", "surrogate": "\ud800",
           "values": [None, True, False, 1, codec.loads("1e4300")]}
wire = codec.dumps(strings)
check("ASCII escaped Unicode/control/surrogate", wire.isascii())
check("Unicode/control/surrogate roundtrip", codec.same_value(strings, codec.loads(wire)))
check("native old diagnostic float emitted value", codec.dumps({"v": 0.1}) == b'{"v":0.1}')
check("native float exact emitted comparison", codec.same_value(0.1, codec.loads("0.1")))
check("native float does not merge higher exact precision", not codec.same_value(0.1, codec.loads("0.100000000000000005")))
check("root arrays remain codec values", codec.same_value(codec.loads("[1,null]"), [1, None]))
check("root scalar remains codec value", codec.loads("true") is True)

invalid = ["NaN", "Infinity", "-Infinity", '{"x":NaN}', '[Infinity]', '{"x":-Infinity}',
           "01", "+1", ".5", "1.", "1e", "1e+", "1e-", "--1", "[1,]", '{"x":1,}',
           "1 true", "", '{"x":1', '"unterminated']
for value in invalid:
    refuses("invalid JSON " + repr(value), lambda value=value: codec.loads(value))
for raw in [b'{"x":"\xff"}', b'\xff', '{"x":1}'.encode("utf-16"), b'\xef\xbb\xbf{}']:
    refuses("invalid/non-UTF8 bytes " + raw.hex(), lambda raw=raw: codec.loads(raw))
for value in [None, 1, [], {}]:
    refuses("nontext decoder input " + type(value).__name__, lambda value=value: codec.loads(value))
for token in ["NaN", "01.0", "+1.0", " 1.0", "1.0 ", "1e", "1e+", "1_0.0"]:
    refuses("invalid numeric leaf " + token, lambda token=token: codec.JsonNumber(token))
for value in [float("inf"), float("-inf"), float("nan"), Decimal("1"), object(), {1: "x"}]:
    refuses("unsupported encoder tree " + type(value).__name__, lambda value=value: codec.dumps(value))
    refuses("unsupported validator tree " + type(value).__name__, lambda value=value: codec.validate_json(value))
refuses("unknown profile", lambda: codec.same_value(1, 1, profile="unknown"))
try:
    codec.same_value(1, 1, "exact-v1")
except TypeError:
    check("profile keyword-only contract", True)
else:
    check("profile keyword-only contract", False)
refuses("true fraction integral conversion", lambda: codec.to_integer(codec.loads("1.5")))
refuses("boolean integral conversion", lambda: codec.to_integer(True))
refuses("boolean integer multiplier", lambda: codec.multiply_integer(1, True))
cyclic = []
cyclic.append(cyclic)
refuses("cyclic validator tree", lambda: codec.validate_json(cyclic))
refuses("cyclic encoder tree", lambda: codec.dumps(cyclic))

rng = random.Random(20261004)
random_trace = []
for index in range(180):
    coefficient = rng.randrange(-10**18, 10**18)
    exponent = rng.randrange(-90, 91)
    left = str(coefficient) + "e" + str(exponent)
    right = (str(coefficient * 10) + "e" + str(exponent - 1)) if index % 3 == 0 else (
        str(rng.randrange(-10**18, 10**18)) + "e" + str(rng.randrange(-90, 91)))
    a, b = codec.loads(left), codec.loads(right)
    da, db = Decimal(left), Decimal(right)
    reference = (da > db) - (da < db)
    actual = codec.compare_numbers(a, b)
    random_trace.append({"left": left, "right": right, "expected_order": reference, "observed_order": actual})
    check("seeded-%03d independent order" % index, actual == reference)
    check("seeded-%03d independent equality" % index, codec.same_value(a, b) == (da == db))
    check("seeded-%03d numeric encoder value" % index, Decimal(codec.dumps(a).decode()) == da)
    check("seeded-%03d value roundtrip" % index, codec.same_value(a, codec.loads(codec.dumps(a))))
    integral = Fraction(da).denominator == 1
    check("seeded-%03d independent integrality" % index, codec.is_integral(a) == integral)
    if integral:
        check("seeded-%03d exact integral conversion" % index, codec.to_integer(a) == Fraction(da).numerator)
    factor = rng.randrange(-7, 8)
    product = codec.multiply_integer(a, factor)
    check("seeded-%03d independent multiplication" % index,
          Fraction(Decimal(codec.dumps(product).decode())) == Fraction(da) * factor)
(out / "random-trace.json").write_text(json.dumps({"seed": 20261004, "operations": random_trace}, indent=2) + "\n")

thread_body = b'{"x":1e4300,"z":0.100000000000000005,"items":[1.0,true,"1"]}'


def worker(_index):
    start = time.monotonic()
    value = codec.loads(thread_body)
    return codec.dumps(value) == thread_body, codec.same_value(value, codec.loads(thread_body)), time.monotonic() - start


with ThreadPoolExecutor(max_workers=50) as executor:
    results = list(executor.map(worker, range(50)))
for index, (encoded, equal, seconds) in enumerate(results):
    check("parallel-%02d exact encoding" % index, encoded)
    check("parallel-%02d exact equality" % index, equal, {"wall_seconds": seconds})
summary = {"assertions": len(events), "passed": sum(e["passed"] for e in events),
           "failed": sum(not e["passed"] for e in events), "seed": 20261004, "random_pairs": 180,
           "parallel_tasks": 50, "parallel_max_seconds": max(r[2] for r in results),
           "wall_seconds": time.monotonic() - started, "module_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest()}
(out / "assertions.json").write_text(json.dumps(events, indent=2) + "\n")
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
sys.exit(bool(summary["failed"]))
