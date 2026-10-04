"""Exact wire-number oracle; no JavaScript Number conversion or product import."""
import json
import re
from decimal import Decimal

VALUES=[("unsafe","9007199254740993"),("scientific","1000000000000000000001")]


def loads_exact(raw):
    def invalid(value):
        raise ValueError("Non-JSON numeric constant: "+value)
    return json.loads(raw,parse_int=int,parse_float=Decimal,parse_constant=invalid)


def party_exact(raw,digits):
    try:
        value=loads_exact(raw)["party_size"]
        return number_exact(value,digits)
    except (ValueError,KeyError,TypeError):
        return False


def number_exact(value,digits):
    return isinstance(value,(int,Decimal)) and not isinstance(value,bool) and value==int(digits)


def party_lexeme(raw):
    match=re.search(r'"party_size"\s*:\s*("[^"\\]*"|[^,}\s]+)',raw or "")
    return match.group(1) if match else None


def trace_exact(value):
    if isinstance(value,Decimal):
        return {"exact_json_number":str(value)}
    if isinstance(value,list):
        return [trace_exact(item) for item in value]
    if isinstance(value,dict):
        return {key:trace_exact(item) for key,item in value.items()}
    return value
