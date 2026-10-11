"""Parse geo: URIs (RFC 5870) into a GeoURI."""

from __future__ import annotations

import re
from urllib.parse import unquote

from ._model import GeoURI, GeoURIError
from ._validate import validate

_SIGNED = re.compile(r"-?\d+(?:\.\d+)?")
_UNSIGNED = re.compile(r"\d+(?:\.\d+)?")


def parse(uri: str) -> GeoURI:
    """Parse a geo: URI into a GeoURI, validating coordinate ranges."""
    if uri[:4].lower() != "geo:":
        raise GeoURIError(f"not a geo: URI: {uri!r}")
    body = uri[4:]
    if not body:
        raise GeoURIError("geo: URI has no coordinates")
    coords, _, rest = body.partition(";")
    lat, lon, alt = _parse_coords(coords)
    uncertainty, crs, params = _parse_params(rest)
    validate(lat, lon, uncertainty)
    return GeoURI(lat=lat, lon=lon, alt=alt, uncertainty=uncertainty, crs=crs, params=params)


def _parse_coords(text: str) -> tuple[float, float, float | None]:
    parts = text.split(",")
    if len(parts) not in (2, 3):
        raise GeoURIError(f"expected 'lat,lon' or 'lat,lon,alt': {text!r}")
    lat = _number(parts[0], "latitude")
    lon = _number(parts[1], "longitude")
    alt = _number(parts[2], "altitude") if len(parts) == 3 else None
    return lat, lon, alt


def _parse_params(rest: str) -> tuple[float | None, str, dict[str, str | None]]:
    uncertainty: float | None = None
    crs = "wgs84"
    params: dict[str, str | None] = {}
    if not rest:
        return uncertainty, crs, params
    for segment in rest.split(";"):
        if not segment:
            raise GeoURIError("empty parameter in geo: URI")
        name, sep, value = segment.partition("=")
        key = name.lower()
        if key == "u":
            uncertainty = _unsigned(_require_value(sep, value, "u"), "uncertainty")
        elif key == "crs":
            crs = _require_value(sep, value, "crs").lower()
        else:
            params[key] = unquote(value) if sep else None
    return uncertainty, crs, params


def _require_value(sep: str, value: str, name: str) -> str:
    if not sep or not value:
        raise GeoURIError(f"{name} parameter needs a value")
    return value


def _number(text: str, label: str) -> float:
    if not _SIGNED.fullmatch(text):
        raise GeoURIError(f"invalid {label}: {text!r}")
    return float(text)


def _unsigned(text: str, label: str) -> float:
    if not _UNSIGNED.fullmatch(text):
        raise GeoURIError(f"invalid {label}: {text!r}")
    return float(text)
