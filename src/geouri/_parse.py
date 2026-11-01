"""Parse the RFC 5870 subset with UTF-8 values and unique parameter names."""

from __future__ import annotations

from decimal import Decimal

from ._errors import GeoURIError
from ._grammar import NUM, PNUM, WGS84_LAT, WGS84_LON, decode_value, label, number
from ._model import DEFAULT_CRS, GeoURI, new_geouri


def parse(uri: str) -> GeoURI:
    """Parse an RFC 5870 URI; invalid text raises GeoURIError, wrong types TypeError.

    Values must be UTF-8 and parameter names unique, including extension names.
    Numeric resource limits and these restrictions are described in the GUIDE.

    >>> from geouri import parse
    >>> str(parse('GEO:1.50,2;CRS=wgs84'))
    'geo:1.5,2'
    """
    if not isinstance(uri, str):
        raise TypeError("uri must be a str")
    if uri[:4].lower() != "geo:":
        raise GeoURIError("scheme", "expected the geo: scheme")
    body = uri[4:]
    if "#" in body:
        raise GeoURIError("fragment", "a geo: URI has no fragment")
    if "?" in body:
        raise GeoURIError("query", "a geo: URI has no query; parse_android reads that form")
    coords, sep, rest = body.partition(";")
    parts = coords.split(",")
    if len(parts) not in (2, 3):
        raise GeoURIError("coordinates", "expected two or three coordinates")
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
            raise GeoURIError("duplicate-param", "parameter appears twice")
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
