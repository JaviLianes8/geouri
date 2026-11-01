"""The Android map intent dialect: geo: URIs with a `?z=` zoom or a `?q=` search.

This form is not part of RFC 5870. It follows the Maps section of the Android common
intents guide: https://developer.android.com/guide/components/intents-common
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from urllib.parse import quote

from ._build import build
from ._errors import GeoURIError
from ._grammar import NUM
from ._model import GeoURI
from ._parse import parse

MIN_ZOOM = 1
MAX_ZOOM = 23
_PIN = re.compile(rf"({NUM.pattern}),({NUM.pattern})(?:\((.*)\))?", re.DOTALL)
_HEX = frozenset("0123456789ABCDEFabcdef")


@dataclass(frozen=True)
class AndroidGeo:
    """A parsed Android map intent URI.

    `point` is the RFC 5870 part before `?`; it is `geo:0,0` when the map app is meant to
    search. `pin` and `label` come from `q=lat,lng(label)`, `query` from any other `q`
    text, and `extras` holds query fields this dialect does not define.

    Direct construction stores fields without validating their consistency;
    use parse_android for validated input. Extras are copied and read-only.

    >>> from geouri import AndroidGeo, parse
    >>> AndroidGeo(parse('geo:1,2'), zoom=3).zoom
    3
    """

    point: GeoURI
    zoom: int | None = None
    query: str | None = None
    pin: GeoURI | None = None
    label: str | None = None
    extras: Mapping[str, str] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extras", MappingProxyType(dict(self.extras)))

    def __reduce__(self) -> tuple[object, ...]:
        # The read-only extras mapping cannot be pickled; rebuild from a plain dict.
        fields = (self.point, self.zoom, self.query, self.pin, self.label, dict(self.extras))
        return (AndroidGeo, fields)


def parse_android(uri: str) -> AndroidGeo:
    """Parse an Android map intent, raising GeoURIError or TypeError for bad input.

    >>> from geouri import parse_android
    >>> parse_android('geo:0,0?q=Main+Street&z=3').query
    'Main Street'
    """
    if not isinstance(uri, str):
        raise TypeError("uri must be a str")
    if "#" in uri:
        raise GeoURIError("fragment", "a geo: URI has no fragment")
    path, sep, query = uri.partition("?")
    point = parse(path)
    if not sep:
        return AndroidGeo(point)
    fields: dict[str, str] = {}
    for item in query.split("&"):
        key, eq, value = item.partition("=")
        if not key or not eq or key in fields:
            raise GeoURIError("query", "malformed or repeated query field")
        fields[key] = _decode(value)
    zoom = _zoom(fields.pop("z")) if "z" in fields else None
    text = fields.pop("q", None)
    pin, label, search = _search(text)
    return AndroidGeo(point, zoom, search, pin, label, fields)


def build_android(
    lat: float, lon: float, *, zoom: int | None = None, label: str | None = None
) -> str:
    """Build a point or labelled pin, raising GeoURIError or TypeError for bad input.

    >>> from geouri import build_android
    >>> build_android(1, 2, label='Home', zoom=3)
    'geo:0,0?q=1,2(Home)&z=3'
    """
    coords = build(lat, lon)[4:]
    if label is None:
        return f"geo:{coords}{_zoom_suffix(zoom, '?')}"
    return f"geo:0,0?q={coords}({_encode(label)}){_zoom_suffix(zoom, '&')}"


def build_android_query(query: str, *, zoom: int | None = None) -> str:
    """Write `geo:0,0?q=text`, asking the map app to search for an address or place.

    Text shaped like `lat,lng` or `lat,lng(label)` with valid coordinates is refused:
    map apps read it as a pin, so use `build_android` for it.
    Invalid values raise GeoURIError; wrong argument types raise TypeError.

    >>> from geouri import build_android_query
    >>> build_android_query('Main Street', zoom=3)
    'geo:0,0?q=Main%20Street&z=3'
    """
    encoded = _encode(query)
    if _search(query)[0] is not None:
        raise GeoURIError("query", "search text reads as a pin; use build_android")
    return f"geo:0,0?q={encoded}{_zoom_suffix(zoom, '&')}"


def _search(text: str | None) -> tuple[GeoURI | None, str | None, str | None]:
    if text is None:
        return None, None, None
    match = _PIN.fullmatch(text)
    if match is None:
        return None, None, text
    try:
        pin = parse(f"geo:{match.group(1)},{match.group(2)}")
    except GeoURIError:
        return None, None, text  # pin-shaped but not a WGS-84 point: plain search text
    # "lat,lng()" is a pin with an empty label, read as no label.
    return pin, match.group(3) or None, None


def _zoom(text: str) -> int:
    if not re.fullmatch(r"[0-9]{1,2}", text) or not MIN_ZOOM <= int(text) <= MAX_ZOOM:
        raise GeoURIError("zoom", "zoom must be a whole number from 1 to 23")
    return int(text)


def _zoom_suffix(zoom: int | None, sep: str) -> str:
    if zoom is None:
        return ""
    if isinstance(zoom, bool) or not isinstance(zoom, int):
        raise TypeError("zoom must be an int")
    if not MIN_ZOOM <= zoom <= MAX_ZOOM:
        raise GeoURIError("zoom", "zoom must be a whole number from 1 to 23")
    return f"{sep}z={_zoom(str(zoom))}"


def _decode(text: str) -> str:
    # Form style: "+" is a space, and every "%" must start a valid escape.
    out = bytearray()
    i = 0
    while i < len(text):
        if text[i] == "%":
            pair = text[i + 1 : i + 3]
            if len(pair) != 2 or not set(pair) <= _HEX:
                raise GeoURIError("query", "bad percent-encoding")
            out.append(int(pair, 16))
            i += 3
        else:
            out += b" " if text[i] == "+" else text[i].encode("utf-8", "surrogatepass")
            i += 1
    try:
        decoded = out.decode("utf-8")
    except UnicodeDecodeError:
        raise GeoURIError("query", "not UTF-8 after decoding") from None
    if not decoded:
        raise GeoURIError("query", "a query field cannot be empty")
    return decoded


def _encode(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("search text and labels must be str")
    if not text:
        raise GeoURIError("query", "search text and labels cannot be empty")
    try:
        return quote(text, safe="", errors="strict")
    except UnicodeEncodeError:
        raise GeoURIError("query", "not encodable as UTF-8") from None
