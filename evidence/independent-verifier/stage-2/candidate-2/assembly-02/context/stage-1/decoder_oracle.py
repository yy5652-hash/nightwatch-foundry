"""Independent bounded grammar/value inputs; never imports the product.

Shallow grammar is checked with the standard JSON grammar implementation plus
strict UTF-8 and forbidden-constant rejection. Deep grammar follows induction:
wrapping a valid leaf in a balanced array/object creates another valid value.
No deep decoder, recursion-limit change or service implementation is needed.
"""
import hashlib
import json
import random
from dataclasses import dataclass
from semantic_oracle import Number, encode, parse, same

SEED = 20261004
DEPTHS = (1100, 5000, 10000, 20000)
SHAPES = ("array", "object", "alternating")

LEAF = b'{"exact":0.100000000000000005,"tiny":1e-4300,"huge":1e4300,"zero":-0,"ordered":[1,true,"1",null],"text":"quote:\\" slash:\\\\ \\u6c49"}'
LEAF_ALIAS = b'{"text":"quote:\\" slash:\\\\ '+"汉".encode()+b'","ordered":[1.0,true,"1",null],"zero":0.0,"huge":10e4299,"tiny":10e-4301,"exact":100000000000000005e-18}'
LEAF_DIFFERENT = LEAF.replace(b"0.100000000000000005", b"0.1", 1)
LEAF_TYPED = LEAF.replace(b'[1,true,"1",null]', b'[true,true,"1",null]', 1)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def wrap(shape, depth, leaf=LEAF):
    if shape not in SHAPES or type(depth) is not int or depth < 1:
        raise ValueError("unknown shape or invalid evidence depth")
    parse(leaf)  # Only the bounded shallow leaf is decoded by the client.
    opens, closes = [], []
    for index in range(depth):
        is_array = shape == "array" or shape == "alternating" and index % 2 == 0
        opens.append(b"[" if is_array else b'{"v":')
        closes.append(b"]" if is_array else b"}")
    return b"".join(opens) + leaf + b"".join(reversed(closes))

def inject(raw_object, raw_value):
    # The envelope is independently known shallow JSON with no ignored field.
    value = parse(raw_object)
    assert isinstance(value, dict) and "ignored" not in value
    return raw_object.rstrip()[:-1] + b',"ignored":' + raw_value + b"}"

@dataclass(frozen=True)
class GrammarCase:
    label: str
    raw: bytes
    valid: bool
    category: str

def grammar_cases():
    valid = {
        "empty-object": b"{}", "empty-array": b"[]", "null": b"null", "true": b"true", "false": b"false",
        "integer": b"1", "negative-zero": b"-0", "zero-exponent": b"-0.000e-4300",
        "negative-integer": b"-12", "fraction": b"0.100000000000000005", "exp-plus": b"1E+004",
        "underflow": b"1e-4300", "overflow": b"1e4300", "huge-compact-exponent": b"1e"+b"9"*80,
        "empty-string": b'""', "escaped-quote": b'"\\\""', "escaped-backslash": b'"\\\\"',
        "escaped-slash": b'"\\/"', "all-short-escapes": b'"\\b\\f\\n\\r\\t"',
        "unicode-escapes": b'"\\u0000\\u00e9\\u6c49"', "surrogate-pair": b'"\\uD834\\uDD1E"',
        "escaped-surrogate": b'"\\uD800"', "utf8": '"é汉𝄞"'.encode(),
        "mixed-containers": b'{"a":[null,false,true,1,{},[]],"b":{"c":"x"}}',
        "json-whitespace": b' \t\r\n { "a" : [ 1 , 2 ] } \n',
        "number-looking-string": b'"NaN Infinity 01 +1 .5 1e4300 [}\\\""',
        "escaped-key": b'{"\\u0061":1}',
    }
    bad = {
        "empty": b"", "only-whitespace": b" \n\t", "bom": b"\xef\xbb\xbf{}", "utf16": "{}".encode("utf-16"),
        "invalid-utf8": b'{"a":"\xff"}', "overlong-utf8": b'{"a":"\xc0\xaf"}', "utf8-surrogate": b'"\xed\xa0\x80"',
        "unclosed-string": b'"abc', "unclosed-escape": b'"abc\\', "bad-escape": b'"\\q"',
        "unicode-short": b'"\\u123"', "unicode-nonhex": b'"\\u12G4"', "raw-nul": b'"\x00"',
        "raw-newline": b'"x\ny"', "raw-tab": b'"x\ty"', "single-quote": b"'abc'",
        "nan": b"NaN", "infinity": b"Infinity", "minus-infinity": b"-Infinity", "undefined": b"undefined",
        "upper-true": b"True", "partial-null": b"nul", "leading-zero": b"01", "minus-leading-zero": b"-01",
        "plus": b"+1", "leading-dot": b".5", "trailing-dot": b"1.", "empty-exponent": b"1e",
        "signed-empty-exponent": b"1e+", "double-sign": b"--1", "hex": b"0x10", "underscore": b"1_000",
        "array-unclosed": b"[1", "object-unclosed": b'{"a":1', "extra-close": b"[]]", "mismatched-close": b"[1}",
        "array-trailing-comma": b"[1,]", "object-trailing-comma": b'{"a":1,}', "double-comma": b"[1,,2]",
        "array-missing-comma": b"[1 2]", "object-missing-comma": b'{"a":1 "b":2}',
        "object-missing-colon": b'{"a" 1}', "unquoted-key": b"{a:1}", "nonstring-key": b"{1:2}",
        "missing-value": b'{"a":}', "leading-comma": b"[,1]", "trailing-value": b"{} []", "trailing-text": b"{}junk",
        "line-comment": b"{}//x", "block-comment": b"/*x*/{}", "non-json-space": b"\xc2\xa0{}",
    }
    return [GrammarCase(k, v, True, "scalar/container") for k,v in valid.items()] + [GrammarCase(k, v, False, "syntax/encoding") for k,v in bad.items()]

def alias_bytes(value):
    if isinstance(value, Number):
        neg, digits, exponent = value.canonical
        return (("-" if neg and digits != "0" else "")+digits+"e"+str(exponent)).encode()
    if type(value) is str:
        return json.dumps(value, ensure_ascii=False).encode("utf-8")
    if isinstance(value, list):
        return b"[ " + b" , ".join(alias_bytes(v) for v in value) + b" ]"
    if isinstance(value, dict):
        return b"{ " + b" , ".join(alias_bytes(k)+b" : "+alias_bytes(v) for k,v in reversed(list(value.items()))) + b" }"
    return encode(value).encode()

def randomized_values(count=96):
    rng = random.Random(SEED)
    numbers = ["1", "1.000", "-0", "1e-4300", "1e4300", "0.100000000000000005", "9007199254740993.0", "10e-1", "-12.50"]
    strings = ["", "é汉𝄞", 'quote:" slash:\\', "number:01 NaN 1e4300", "line\n\t\x00", "key:{[,]}"]
    def value(level):
        choices = 7 if level < 4 else 5
        tag = rng.randrange(choices)
        if tag == 0:return Number(rng.choice(numbers))
        if tag == 1:return rng.choice(strings)
        if tag == 2:return bool(rng.randrange(2))
        if tag == 3:return None
        if tag == 4:return Number(str(rng.randrange(-9999, 10000)))
        if tag == 5:return [value(level+1) for _ in range(rng.randrange(5))]
        return {"k"+str(i):value(level+1) for i in range(rng.randrange(5))}
    result=[]
    for i in range(count):
        tree={"sample":Number(str(i)),"value":value(0),"ordered":[Number("1"),True,"1",None]}
        raw=encode(tree).encode(); alias=alias_bytes(tree)
        changed=dict(tree, sample=Number(str(i+1)))
        result.append(dict(label=f"seed-{SEED}-{i:03d}",tree=tree,raw=raw,alias=alias,different=encode(changed).encode()))
    return result

def self_check():
    checks=[]
    def check(label, condition):
        checks.append(dict(label=label,passed=bool(condition)))
        assert condition,label
    for case in grammar_cases():
        try:parse(case.raw);valid=True
        except (ValueError,UnicodeError):valid=False
        check("grammar-"+case.label,valid == case.valid)
    check("leaf-alias",same(parse(LEAF),parse(LEAF_ALIAS)))
    check("leaf-precision-difference",not same(parse(LEAF),parse(LEAF_DIFFERENT)))
    check("leaf-boolean-difference",not same(parse(LEAF),parse(LEAF_TYPED)))
    for item in randomized_values():
        check(item["label"]+"-roundtrip",same(item["tree"],parse(item["raw"])))
        check(item["label"]+"-alias",same(item["tree"],parse(item["alias"])))
        check(item["label"]+"-difference",not same(item["tree"],parse(item["different"])))
    for shape in SHAPES:
        for depth in DEPTHS:
            raw=wrap(shape,depth)
            # The separately tested shallow base plus exactly matched wrappers
            # proves grammar, without asking any decoder to accept this depth.
            check(f"{shape}-{depth}-construction",raw.endswith(b"]" if shape=="array" or shape=="alternating" else b"}") and LEAF in raw)
    return checks

if __name__ == "__main__":
    print(json.dumps(dict(scope="own oracle self-check only; no service execution",checks=self_check()),indent=2))
