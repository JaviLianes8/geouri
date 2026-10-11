"""Build geo: URIs (RFC 5870) from coordinates."""

from __future__ import annotations

from ._model import GeoURIError
from ._validate import validate


def build(
    lat: float,
    lon: float,
    *,
    alt: float | None = None,
    u: float | None = None,
    crs: str | None = None,
) -> str:
    """Build a geo: URI from coordinates, validating latitude and longitude."""
    validate(lat, lon, u)
    text = f"geo:{_format_number(lat)},{_format_number(lon)}"
    if alt is not None:
        text += f",{_format_number(alt)}"
    if crs is not None:
        text += f";crs={crs.lower()}"
    if u is not None:
        text += f";u={_format_number(u)}"
    return text


def _format_number(value: float) -> str:
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        raise GeoURIError(f"not a finite number: {value!r}")
    if number == 0.0:
        number = 0.0
    text = repr(number)
    if "e" in text or "E" in text:
        text = f"{number:.12f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
