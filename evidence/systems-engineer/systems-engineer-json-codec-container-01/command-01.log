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


def _validate(value):
    if value is None or type(value) in (str, bool) or is_number(value):
        return
    if isinstance(value, list):
        for item in value:
            _validate(item)
        return
    if isinstance(value, dict) and all(type(key) is str for key in value):
        for item in value.values():
            _validate(item)
        return
    raise JsonCodecError("Unsupported JSON value")


def validate_json(value):
    try:
        _validate(value)
    except RecursionError as error:
        raise JsonCodecError("Invalid recursive JSON tree") from error


def _encode(value):
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is JsonNumber:
        return value.token
    if type(value) is int:
        return str(value)
    if type(value) is float:
        return _json.dumps(value, allow_nan=False)
    if type(value) is str:
        return _json.dumps(value, ensure_ascii=True)
    if isinstance(value, list):
        return "[" + ",".join(_encode(item) for item in value) + "]"
    return "{" + ",".join(_json.dumps(key, ensure_ascii=True) + ":" + _encode(item)
                           for key, item in value.items()) + "}"


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
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right) and left == right
    if is_number(left) and is_number(right):
        if profile == EXACT_PROFILE:
            return number_key(left) == number_key(right)
        a, b = _legacy_number(left), _legacy_number(right)
        # Genuine old successful receipts cannot contain infinity. A finite
        # incoming overflow projection is a different valid body, not syntax.
        if ((type(a) is float and not math.isfinite(a)) or
                (type(b) is float and not math.isfinite(b))):
            return False
        return a == b
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_same(left[key], right[key], profile) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same(a, b, profile) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


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
