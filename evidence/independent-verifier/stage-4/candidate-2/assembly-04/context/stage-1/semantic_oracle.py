"""Independent JSON-value oracle for HTTP evidence, never imported by product.

Canonical decimal strings compare without expanding exponents. The historical
oracle uses the published source decoder meaning only for old receipt matching.
"""
import json
import re
import sys
from dataclasses import dataclass

sys.set_int_max_str_digits(0)  # Evidence interpreter only.
NUMBER=re.compile(r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?\Z")

@dataclass(frozen=True)
class Number:
    raw: str

    def __post_init__(self):
        if NUMBER.fullmatch(self.raw) is None:
            raise ValueError("not a JSON numeric token")

    @property
    def canonical(self):
        match=NUMBER.fullmatch(self.raw)
        negative,whole,fraction,exponent=match.groups()
        digits=(whole+(fraction or "")).lstrip("0")
        if not digits:
            return (False,"0",0)
        power=int(exponent or "0")-len(fraction or "")
        without=digits.rstrip("0")
        power+=len(digits)-len(without)
        return (bool(negative),without,power)

    @property
    def integer_token(self):
        return "." not in self.raw and "e" not in self.raw.lower()

    @property
    def integral(self):
        return self.canonical[1]=="0" or self.canonical[2]>=0

    def small_integer(self):
        negative,digits,power=self.canonical
        if not self.integral or power>5000:
            raise ValueError("oracle refuses unnecessary materialization")
        value=int(digits)*(10**power)
        return -value if negative else value

    def source_projection(self):
        # Integer-token values stayed exact in the genuine source decoder.
        return int(self.raw) if self.integer_token else float(self.raw)

def parse(raw):
    if isinstance(raw,bytes): raw=raw.decode("utf-8",errors="strict")
    def invalid(value): raise ValueError("invalid JSON constant: "+value)
    return json.loads(raw,parse_int=Number,parse_float=Number,parse_constant=invalid)

def encode(value):
    if isinstance(value,Number): return value.raw
    if value is None: return "null"
    if type(value) is bool: return "true" if value else "false"
    if type(value) is int: return str(value)
    if type(value) is str: return json.dumps(value,ensure_ascii=True)
    if isinstance(value,list): return "["+",".join(encode(item) for item in value)+"]"
    if isinstance(value,dict):
        if not all(type(key) is str for key in value): raise TypeError("JSON keys must be strings")
        return "{"+",".join(encode(key)+":"+encode(item) for key,item in value.items())+"}"
    raise TypeError("unsupported evidence JSON type")

def same(left,right,legacy=False):
    number_types=(Number,int)
    left_num=type(left) in number_types
    right_num=type(right) in number_types
    if left_num or right_num:
        if not (left_num and right_num): return False
        a=left if isinstance(left,Number) else Number(str(left))
        b=right if isinstance(right,Number) else Number(str(right))
        return a.source_projection()==b.source_projection() if legacy else a.canonical==b.canonical
    if type(left) is not type(right): return False
    if isinstance(left,dict): return left.keys()==right.keys() and all(same(left[key],right[key],legacy) for key in left)
    if isinstance(left,list): return len(left)==len(right) and all(same(a,b,legacy) for a,b in zip(left,right))
    return left==right

def self_check():
    checks=[]
    def check(label,condition):
        checks.append(dict(case=label,passed=bool(condition)))
        if not condition: raise AssertionError(label)
    pairs=[("1","1.0"),("1","1e0"),("-0","0e-999999"),("1000","1e3"),
           ("9007199254740993.0","9007199254740993"),("0.100000000000000005","100000000000000005e-18")]
    for a,b in pairs: check(a+" equals "+b,same(Number(a),Number(b)))
    for a,b in [("0.100000000000000005","0.1"),("9007199254740993.0","9007199254740992"),("1e-4300","0")]:
        check("exact distinguishes "+a+" / "+b,not same(Number(a),Number(b)))
        check("legacy aliases "+a+" / "+b,same(Number(a),Number(b),legacy=True))
    check("legacy exact integer remains distinct",not same(Number("9007199254740993"),Number("9007199254740992.0"),legacy=True))
    for mode in [False,True]:
        check("boolean distinct "+str(mode),not same(True,Number("1.0"),mode))
        check("string distinct "+str(mode),not same("1",Number("1.0"),mode))
    exponent="9"*80
    check("huge compact exponent aliases",same(Number("1e"+exponent),Number("10e"+str(int(exponent)-1))))
    check("zero huge exponent",same(Number("-0.000e-"+("9"*4301)),Number("0")))
    check("giant fraction",not Number("1"+"0"*4299+"1.5").integral)
    value={"a":[Number("1e-4300"),False,"\u00e9\u6c49",None],"b":Number("1e"+exponent)}
    check("exact tree round trip",same(value,parse(encode(value))))
    check("objects unordered",same({"a":Number("1.0"),"b":False},{"b":False,"a":Number("1")}))
    check("arrays ordered",not same([Number("1"),Number("2")],[Number("2"),Number("1")]))
    for raw in [b'{"n":NaN}',b'{"n":Infinity}',b'{"n":-Infinity}',b'{"n":01}',b'{"n":.5}',b'{"n":1.}',b'{"n":1e}',b'{"x":"\xff"}']:
        refused=False
        try: parse(raw)
        except (ValueError,UnicodeError): refused=True
        check("invalid "+repr(raw),refused)
    return checks

if __name__=="__main__":
    print(json.dumps(dict(kind="independent client oracle self-check, no service execution",checks=self_check()),indent=2))
