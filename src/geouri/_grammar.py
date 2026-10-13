"""Lexical rules of RFC 5870 section 3.3: numbers, labels and parameter values."""

from __future__ import annotations

import re
from decimal import Decimal

from ._errors import GeoURIError, Reason

# Character classes are spelled out: `\d` and `str.isdigit` also accept non-ASCII digits.
NUM = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")
PNUM = re.compile(r"[0-9]+(?:\.[0-9]+)?")
LABEL = re.compile(r"[A-Za-z0-9-]+")
# WGS-84 narrows the integer part (section 3.3): two digits of latitude, three of longitude.
WGS84_LAT = re.compile(r"-?[0-9]{1,2}(?:\.[0-9]+)?")
WGS84_LON = re.compile(r"-?[0-9]{1,3}(?:\.[0-9]+)?")

_ALPHANUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
# paramchar = p-unreserved / unreserved / pct-encoded
PARAM_SAFE = frozenset(_ALPHANUM + "-_.!~*'()" + "[]:&+$")
_HEX = frozenset("0123456789ABCDEFabcdef")


def number(text: str, pattern: re.Pattern[str], reason: Reason, label: str) -> Decimal:
    """Read a decimal that must match `pattern` in full."""
    if not pattern.fullmatch(text):
        raise GeoURIError(reason, f"invalid {label}: {text!r}")
    return Decimal(text)


def label(text: str, reason: Reason, what: str) -> str:
    """Check a `labeltext` and return it in lower case."""
    if not LABEL.fullmatch(text):
        raise GeoURIError(reason, f"invalid {what}: {text!r}")
    return text.lower()


def decode_value(text: str) -> str:
    """Percent-decode a `pvalue`, refusing characters outside `paramchar` and bad UTF-8.

    An empty value is left for GeoURI to refuse, as it refuses one passed by a caller.
    """
    out = bytearray()
    i = 0
    while i < len(text):
        char = text[i]
        if char == "%":
            pair = text[i + 1 : i + 3]
            if len(pair) != 2 or not set(pair) <= _HEX:
                raise GeoURIError("param-value", f"bad percent-encoding in {text!r}")
            out.append(int(pair, 16))
            i += 3
            continue
        if char not in PARAM_SAFE:
            raise GeoURIError("param-value", f"character {char!r} must be percent-encoded")
        out.append(ord(char))
        i += 1
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        raise GeoURIError("param-value", f"not UTF-8 after decoding: {text!r}") from None


def encode_value(value: str) -> str:
    """Percent-encode a parameter value as UTF-8, keeping only `paramchar` literal."""
    return "".join(
        char if char in PARAM_SAFE else "".join(f"%{b:02X}" for b in char.encode("utf-8"))
        for char in value
    )


def plain(value: Decimal) -> str:
    """Write a decimal without exponent, trailing zeros or a negative zero."""
    # Built from the digit tuple: normalize() and format() would round to the context.
    if value == 0:
        return "0"
    sign, digit_tuple, exponent = value.as_tuple()
    digits = "".join(map(str, digit_tuple)).lstrip("0")
    exp = int(exponent)
    while digits.endswith("0"):
        digits, exp = digits[:-1], exp + 1
    if exp >= 0:
        text = digits + "0" * exp
    elif len(digits) > -exp:
        text = f"{digits[:exp]}.{digits[exp:]}"
    else:
        text = "0." + "0" * (-exp - len(digits)) + digits
    return ("-" if sign else "") + text
