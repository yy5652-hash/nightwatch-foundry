"""Exact finite JSON values, independent of HTTP, application state and storage.

Decimal/exponent tokens retain their finite coefficient/exponent and token kind.
Equality never expands an exponent or uses a decimal arithmetic context. The
historical profile is solely for comparing genuinely old successful receipts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json as _json
import math
import re
import sys


# The published numeric range does not inherit Python's decimal digit ceiling.
# This setting affects this interpreter process only, including native int I/O.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

EXACT_PROFILE = "exact-v1"
LEGACY_PROFILE = "python-json-v1"
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")


class JsonCodecError(ValueError):
    """Invalid JSON syntax/tree/profile, without application status policy."""


@dataclass(frozen=True, slots=True)
class JsonNumber:
    """Immutable exact numeric leaf; token is always valid finite JSON syntax.

    ``digits`` has no leading/trailing zero unless the value is zero. The exact
    value is sign * int(digits) * 10**exponent, but that power is not constructed
    by parsing, encoding, classification or comparison. Token provenance is
    retained separately from canonical value for historical receipt matching.
    """

    token: str
    negative: bool = field(init=False)
    digits: str = field(init=False)
    exponent: int = field(init=False)
    token_kind: str = field(init=False)

    def __post_init__(self):
        if type(self.token) is not str or not _NUMBER.fullmatch(self.token):
            raise JsonCodecError("Invalid JSON number token")
        negative = self.token.startswith("-")
        unsigned = self.token[1:] if negative else self.token
        parts = re.split("[eE]", unsigned, maxsplit=1)
        exponent = int(parts[1]) if len(parts) == 2 else 0
        mantissa = parts[0]
        whole, _, fraction = mantissa.partition(".")
        digits = (whole + fraction).lstrip("0")
        exponent -= len(fraction)
        if not digits:
            negative, digits, exponent = False, "0", 0
        else:
            stripped = digits.rstrip("0")
            exponent += len(digits) - len(stripped)
            digits = stripped
        object.__setattr__(self, "negative", negative)
        object.__setattr__(self, "digits", digits)
        object.__setattr__(self, "exponent", exponent)
        object.__setattr__(self, "token_kind", "decimal" if "." in self.token or len(parts) == 2 else "integer")

    @property
    def is_integral(self):
        return self.digits == "0" or self.exponent >= 0

    def __deepcopy__(self, memo):
        return self


def is_number(value):
    """Whether a leaf is a supported finite JSON number, excluding booleans."""
    return type(value) in (int, JsonNumber) or (type(value) is float and math.isfinite(value))


def number_key(value):
    """Exact normalized (negative, coefficient digits, exponent) value key."""
    if type(value) is JsonNumber:
        return value.negative, value.digits, value.exponent
    if type(value) is int:
        negative = value < 0
        digits = str(abs(value))
        if value == 0:
            return False, "0", 0
        stripped = digits.rstrip("0")
        return negative, stripped, len(digits) - len(stripped)
    if type(value) is float and math.isfinite(value):
        # Direct old diagnostic floats mean their emitted JSON decimal value,
        # not the expanded binary ratio. New HTTP decoding creates no floats.
        return number_key(JsonNumber(_json.dumps(value, allow_nan=False)))
    raise JsonCodecError("Expected a finite JSON number")


def is_integral(value):
    if not is_number(value):
        return False
    _, digits, exponent = number_key(value)
    return digits == "0" or exponent >= 0


def compare_numbers(left, right):
    """Return -1/0/1 without expanding compact positive or negative exponents."""
    an, ad, ae = number_key(left)
    bn, bd, be = number_key(right)
    if (an, ad, ae) == (bn, bd, be):
        return 0
    if ad == "0":
        return 1 if bn else -1
    if bd == "0":
        return -1 if an else 1
    if an != bn:
        return -1 if an else 1
    am, bm = len(ad) + ae, len(bd) + be
    if am != bm:
        result = 1 if am > bm else -1
    else:
        # Equal magnitude makes padding bounded by input coefficient lengths,
        # even if both exponent metadata values are enormous.
        width = max(len(ad), len(bd))
        av, bv = ad.ljust(width, "0"), bd.ljust(width, "0")
        result = (av > bv) - (av < bv)
    return -result if an else result


def to_integer(value):
    """Exact integral conversion; caller bounds any necessary materialization.

    Core can compare duration/grid against its finite window before calling
    this helper. Parsing/archiving an ignored exponent never requires it.
    """
    if not is_integral(value):
        raise JsonCodecError("Expected an integral JSON number")
    negative, digits, exponent = number_key(value)
    if digits == "0":
        return 0
    answer = int(digits) * 10 ** exponent
    return -answer if negative else answer


def multiply_integer(value, factor):
    """Multiply by an exact integer while retaining compact exponent metadata."""
    if type(factor) is not int:
        raise JsonCodecError("Expected an integer multiplier")
    if type(value) is int:
        return value * factor
    negative, digits, exponent = number_key(value)
    coefficient = int(digits) * factor * (-1 if negative else 1)
    if coefficient == 0:
        return 0
    return JsonNumber(str(coefficient) + "e" + str(exponent))


def _reject_constant(_value):
    raise JsonCodecError("JSON does not permit non-finite constants")


def loads(raw):
    """Decode strict UTF-8 bytes/string to an exact, provenance-carrying tree."""
    if type(raw) not in (bytes, str):
        raise JsonCodecError("JSON input must be bytes or text")
    try:
        text = raw.decode("utf-8") if type(raw) is bytes else raw
        return _json.loads(text, parse_int=int, parse_float=JsonNumber,
                           parse_constant=_reject_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise JsonCodecError("Invalid UTF-8 JSON text") from error


def validate_json(value):
    """Validate iteratively, refusing cycles but allowing repeated subtrees."""
    pending = [(value, False)]
    active = set()
    while pending:
        item, leaving = pending.pop()
        if leaving:
            active.remove(id(item))
            continue
        if item is None or type(item) in (str, bool) or is_number(item):
            continue
        if isinstance(item, list):
            children = item
        elif isinstance(item, dict) and all(type(key) is str for key in item):
            children = item.values()
        else:
            raise JsonCodecError("Unsupported JSON value")
        if id(item) in active:
            raise JsonCodecError("Invalid cyclic JSON tree")
        active.add(id(item))
        pending.append((item, True))
        pending.extend((child, False) for child in children)


def _encode(value):
    pieces = []
    pending = [(value, False)]
    while pending:
        item, literal = pending.pop()
        if literal:
            pieces.append(item)
        elif item is None:
            pieces.append("null")
        elif type(item) is bool:
            pieces.append("true" if item else "false")
        elif type(item) is JsonNumber:
            pieces.append(item.token)
        elif type(item) is int:
            pieces.append(str(item))
        elif type(item) is float:
            pieces.append(_json.dumps(item, allow_nan=False))
        elif type(item) is str:
            pieces.append(_json.dumps(item, ensure_ascii=True))
        elif isinstance(item, list):
            pieces.append("[")
            pending.append(("]", True))
            for index in range(len(item) - 1, -1, -1):
                pending.append((item[index], False))
                if index:
                    pending.append((",", True))
        else:
            pieces.append("{")
            pending.append(("}", True))
            entries = list(item.items())
            for index in range(len(entries) - 1, -1, -1):
                key, child = entries[index]
                pending.append((child, False))
                pending.append((_json.dumps(key, ensure_ascii=True) + ":", True))
                if index:
                    pending.append((",", True))
    return "".join(pieces)


def dumps(value):
    """Encode exact numeric leaves as compact JSON UTF-8 bytes, never strings."""
    validate_json(value)
    try:
        return _encode(value).encode("utf-8")
    except (ValueError, UnicodeError, RecursionError) as error:
        raise JsonCodecError("Unable to encode JSON tree") from error


def _legacy_number(value):
    if type(value) in (int, float):
        return value
    if value.token_kind == "integer":
        return int(value.token)
    try:
        return float(value.token)
    except OverflowError:
        return -math.inf if value.negative else math.inf


def _same(left, right, profile):
    pending = [(left, right)]
    while pending:
        a, b = pending.pop()
        if type(a) is bool or type(b) is bool:
            if type(a) is not type(b) or a != b:
                return False
        elif is_number(a) and is_number(b):
            if profile == EXACT_PROFILE:
                if number_key(a) != number_key(b):
                    return False
            else:
                av, bv = _legacy_number(a), _legacy_number(b)
                # Genuine old successful receipts cannot contain infinity. A
                # finite incoming overflow is a different body, not syntax.
                if ((type(av) is float and not math.isfinite(av)) or
                        (type(bv) is float and not math.isfinite(bv)) or av != bv):
                    return False
        elif isinstance(a, dict) and isinstance(b, dict):
            if a.keys() != b.keys():
                return False
            pending.extend((a[key], b[key]) for key in a)
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False
            pending.extend(zip(a, b))
        elif type(a) is not type(b) or a != b:
            return False
    return True


def same_value(left, right, *, profile=EXACT_PROFILE):
    """Compare complete valid JSON trees under a validated receipt profile."""
    if profile not in (EXACT_PROFILE, LEGACY_PROFILE):
        raise JsonCodecError("Unknown JSON comparison profile")
    validate_json(left)
    validate_json(right)
    try:
        return _same(left, right, profile)
    except RecursionError as error:
        raise JsonCodecError("Invalid recursive JSON comparison") from error
