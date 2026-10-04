"""Own valid-by-construction deep JSON probes; no recursion-limit adjustment."""
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
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
start = time.monotonic()
leaf_text = '{"finite":1e4300,"flag":true,"text":"雨"}'
independent_leaf = json.loads(leaf_text, parse_float=Decimal)
assert independent_leaf["finite"].is_finite() and independent_leaf["finite"] == Decimal("1e4300")


def observe(label, operation, predicate, detail):
    begin = time.monotonic()
    try:
        answer = operation()
        passed = bool(predicate(answer))
        outcome = {"returned_type": type(answer).__name__}
    except Exception as error:
        passed = False
        outcome = {"exception": type(error).__name__, "message": str(error)}
    events.append({"label": label, "passed": passed, "seconds": time.monotonic() - begin,
                   "construction": detail, "outcome": outcome})


for depth in (750, 1000, 1100, 1200, 1600):
    for shape in ("object", "array", "alternating"):
        prefixes, suffixes = [], []
        value = codec.loads(leaf_text)
        other = codec.loads(leaf_text)
        # Each operation wraps a known valid JSON value. Composition preserves
        # JSON grammar; the separate stdlib Decimal decoder checked the leaf.
        for level in range(depth):
            object_level = shape == "object" or (shape == "alternating" and level % 2 == 0)
            if object_level:
                prefixes.append('{"unused":')
                suffixes.append("}")
                value, other = {"unused": value}, {"unused": other}
            else:
                prefixes.append("[")
                suffixes.append("]")
                value, other = [value], [other]
        wire = ("".join(reversed(prefixes)) + leaf_text + "".join(suffixes)).encode("utf-8")
        label = "%s-%d" % (shape, depth)
        (out / (label + ".json")).write_bytes(wire)
        detail = {"shape": shape, "wrapping_depth": depth, "leaf_container_depth": 1,
                  "grammar_valid_by_composition": True, "leaf_independent_finite_decimal": True,
                  "payload_bytes": len(wire), "payload_sha256": hashlib.sha256(wire).hexdigest()}

        def parsed_roundtrip():
            parsed = codec.loads(wire)
            return codec.same_value(parsed, value) and codec.same_value(parsed, codec.loads(codec.dumps(parsed)))

        observe(label + " decode only", lambda: codec.loads(wire), lambda result: type(result) in (dict, list), detail)
        observe(label + " parse/roundtrip/equality", parsed_roundtrip, lambda result: result, detail)
        observe(label + " direct-tree validation", lambda: codec.validate_json(value), lambda result: result is None, detail)
        observe(label + " direct-tree encode", lambda: codec.dumps(value),
                lambda result: codec.same_value(codec.loads(result), other), detail)
        observe(label + " direct-tree exact equality", lambda: codec.same_value(value, other), lambda result: result, detail)
        observe(label + " direct-tree legacy equality", lambda: codec.same_value(value, other, profile="python-json-v1"),
                # Overflow cannot be present in a real archived successful old
                # receipt. Here it must be a stable false comparison, not error.
                lambda result: result is False, detail)
        leaf = other
        for _level in range(depth):
            leaf = leaf["unused"] if type(leaf) is dict else leaf[0]
        leaf["flag"] = False
        observe(label + " deep changed exact value", lambda: codec.same_value(value, other),
                lambda result: result is False, detail)
        observe(label + " deep changed historical value", lambda: codec.same_value(value, other, profile="python-json-v1"),
                lambda result: result is False, detail)
        leaf["flag"] = True
        leaf["finite"] = codec.loads("10e4299")
        observe(label + " deep equal numeric alias", lambda: codec.same_value(value, other), lambda result: result, detail)

        def malformed_tail():
            try:
                codec.loads(wire[:-1])
            except codec.JsonCodecError:
                return True
            return False

        observe(label + " malformed closing tail refused", malformed_tail, lambda result: result, detail)

        def detached_copy():
            cloned = codec.copy_json(value)
            if not codec.same_value(cloned, value):
                return False
            old, new = value, cloned
            for _level in range(depth):
                if old is new:
                    return False
                old = old["unused"] if type(old) is dict else old[0]
                new = new["unused"] if type(new) is dict else new[0]
            if old is new or old["finite"] is not new["finite"]:
                return False
            new["flag"] = False
            return old["flag"] is True and not codec.same_value(value, cloned)

        observe(label + " depth-safe detached container copy", detached_copy, lambda result: result, detail)

for label, tree in (("empty nested containers", [[], {}, {"empty": []}]),
                    ("punctuation and key order", {"z": [1, 2, 3], "a": {"two": 2, "one": 1}})):
    observe(label, lambda tree=tree: codec.dumps(tree), lambda wire: json.loads(wire) == tree,
            {"independent_reference": "stdlib shallow JSON decoder"})
shared = {"value": [codec.loads("0.100000000000000005")]}
dag = [shared, shared]
observe("repeated subtree remains valid", lambda: codec.validate_json(dag), lambda result: result is None,
        {"shared_subtree": True, "cycle": False})
observe("repeated subtree encodes twice", lambda: codec.dumps(dag),
        lambda wire: codec.same_value(codec.loads(wire), dag), {"shared_subtree": True, "cycle": False})

def cycle_refused():
    cycle = {"self": None}
    cycle["self"] = cycle
    try:
        codec.same_value(cycle, cycle)
    except codec.JsonCodecError:
        return True
    return False

observe("cyclic mapping equality refused", cycle_refused, lambda result: result, {"cycle": True})

def cycle_copy_refused():
    cycle = []
    cycle.append(cycle)
    try:
        codec.copy_json(cycle)
    except codec.JsonCodecError:
        return True
    return False

observe("cyclic copy refused", cycle_copy_refused, lambda result: result, {"cycle": True})

summary = {"module_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
           "assertions": len(events), "passed": sum(e["passed"] for e in events),
           "failed": sum(not e["passed"] for e in events), "wall_seconds": time.monotonic() - start,
           "maximum_payload_bytes": max(e["construction"].get("payload_bytes", 0) for e in events),
           "maximum_wrapping_depth": 1600, "recursion_limit_unchanged": sys.getrecursionlimit()}
(out / "observations.json").write_text(json.dumps(events, indent=2) + "\n")
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
sys.exit(bool(summary["failed"]))
