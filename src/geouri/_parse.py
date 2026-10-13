"""Parse geo: URIs strictly against the RFC 5870 grammar."""

from __future__ import annotations

from decimal import Decimal

from ._errors import GeoURIError
from ._grammar import NUM, PNUM, WGS84_LAT, WGS84_LON, decode_value, label, number
from ._model import DEFAULT_CRS, GeoURI, new_geouri


def parse(uri: str) -> GeoURI:
    """Parse a geo: URI, checking the RFC 5870 grammar, parameter rules and ranges."""
    if not isinstance(uri, str):
        raise TypeError(f"uri must be a str, not {type(uri).__name__}")
    if uri[:4].lower() != "geo:":
        raise GeoURIError("scheme", f"not a geo: URI: {uri!r}")
    body = uri[4:]
    if "#" in body:
        raise GeoURIError("fragment", "a geo: URI has no fragment")
    if "?" in body:
        raise GeoURIError("query", "a geo: URI has no query; parse_android reads that form")
    coords, sep, rest = body.partition(";")
    parts = coords.split(",")
    if len(parts) not in (2, 3):
        raise GeoURIError("coordinates", f"expected 'lat,lon' or 'lat,lon,alt': {coords!r}")
    crs, uncertainty, params = _parse_params(rest.split(";") if sep else [])
    exact = _parse_coords(parts, crs)
    return new_geouri((*exact, uncertainty), crs, params)


def _parse_coords(parts: list[str], crs: str) -> tuple[Decimal, Decimal, Decimal | None]:
    # The WGS-84 digit limits depend on crs, so the parameters are read first.
    wgs84 = crs == DEFAULT_CRS
    lat = number(parts[0], WGS84_LAT if wgs84 else NUM, "number", "latitude")
    lon = number(parts[1], WGS84_LON if wgs84 else NUM, "number", "longitude")
    alt = number(parts[2], NUM, "number", "altitude") if len(parts) == 3 else None
    return lat, lon, alt


def _parse_params(
    segments: list[str],
) -> tuple[str, Decimal | None, dict[str, str | None]]:
    crs = DEFAULT_CRS
    uncertainty: Decimal | None = None
    params: dict[str, str | None] = {}
    seen: set[str] = set()
    for index, segment in enumerate(segments):
        raw_name, sep, value = segment.partition("=")
        name = label(raw_name, "param-name", "parameter name")
        if name in seen:
            raise GeoURIError("duplicate-param", f"parameter {name!r} appears twice")
        seen.add(name)
        # Section 3.3: crs comes first, then u, then any other parameter.
        if name == "crs":
            if index != 0:
                raise GeoURIError("param-order", "crs must be the first parameter")
            # A missing "=value" reads as an empty value, which the label rule refuses.
            crs = label(value, "crs", "crs label")
        elif name == "u":
            if index != (1 if "crs" in seen else 0):
                raise GeoURIError("param-order", "u must follow crs and precede other parameters")
            uncertainty = number(value, PNUM, "uncertainty", "uncertainty")
        else:
            params[name] = decode_value(value) if sep else None
    return crs, uncertainty, params
