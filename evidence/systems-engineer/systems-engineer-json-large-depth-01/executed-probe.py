"""One isolated deep operation; imports only the packaged codec, inside image."""
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import json_codec as codec

depth, shape, operation = int(sys.argv[1]), sys.argv[2], sys.argv[3]
leaf_wire = b'{"value":0.100000000000000005,"huge":1e4300,"flag":true}'
opening, closing = (b'{"unused":', b'}') if shape == "object" else (b'[', b']')
wire = opening * depth + leaf_wire + closing * depth
meta = {"depth": depth, "shape": shape, "operation": operation, "payload_bytes": len(wire),
        "payload_sha256": hashlib.sha256(wire).hexdigest(),
        "grammar": "Valid scalar-number leaf in exactly balanced same-kind containers, by construction",
        "recursion_limit_unchanged": sys.getrecursionlimit(), "python_version": sys.version,
        "codec_sha256": hashlib.sha256(Path('/app/json_codec.py').read_bytes()).hexdigest()}
print(json.dumps({"starting": meta}), flush=True)
checks = []


def check(label, passed):
    checks.append({"label": label, "passed": bool(passed)})


def constructed(alias=False):
    leaf = {"value": codec.JsonNumber("100000000000000005e-18" if alias else "0.100000000000000005"),
            "huge": codec.JsonNumber("10e4299" if alias else "1e4300"), "flag": True}
    result = leaf
    for _ in range(depth):
        result = {"unused": result} if shape == "object" else [result]
    return result, leaf


def inspect_depth(tree):
    for _ in range(depth):
        if shape == "object":
            if type(tree) is not dict or set(tree) != {"unused"}:
                return False
            tree = tree["unused"]
        else:
            if type(tree) is not list or len(tree) != 1:
                return False
            tree = tree[0]
    return type(tree) is dict and set(tree) == {"value", "huge", "flag"} and tree["flag"] is True


started = time.monotonic()
exception = None
try:
    if operation == "decoder":
        decoded = codec.loads(wire)
        check("decoder retains complete independently inspected depth", inspect_depth(decoded))
    else:
        tree, original_leaf = constructed()
        if operation == "validation":
            check("direct constructed traversal validates", codec.validate_json(tree) is None)
        elif operation == "equality":
            other, other_leaf = constructed(True)
            check("direct constructed aliases equal", codec.same_value(tree, other))
            other_leaf["value"] = codec.JsonNumber("0.1")
            check("deep numeric difference detected", not codec.same_value(tree, other))
        elif operation == "encoder":
            check("direct constructed encoder equals valid grammar bytes", codec.dumps(tree) == wire)
        elif operation == "copy":
            copied = codec.copy_json(tree)
            a, b = tree, copied
            detached = True
            for _ in range(depth):
                detached = detached and a is not b
                a, b = (a["unused"], b["unused"]) if shape == "object" else (a[0], b[0])
            check("every mutable wrapper and leaf detached", detached and a is not b)
            check("copy encoder equals independent input bytes", codec.dumps(copied) == wire)
            b["value"] = 0
            check("copy mutation leaves original numeric leaf unchanged", original_leaf["value"].token == "0.100000000000000005")
        elif operation == "roundtrip":
            encoded = codec.dumps(tree)
            print(json.dumps({"stage": "encoder finished; entering decoder", "bytes": len(encoded)}), flush=True)
            check("serialization roundtrip depth retained", inspect_depth(codec.loads(encoded)))
        else:
            raise ValueError("Unknown own diagnostic operation")
except Exception as error:
    exception = {"type": type(error).__name__, "message": str(error)}
    check("operation completed without exception", False)
result = {"meta": meta, "assertions": checks, "exception": exception, "seconds": time.monotonic() - started,
          "maximum_rss_linux_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "failed": sum(not c["passed"] for c in checks)}
print(json.dumps({"result": result}), flush=True)
sys.exit(bool(result["failed"]))
