"""Build canonical geo: URIs (RFC 5870) from numbers."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from ._model import DEFAULT_CRS, GeoURI


def build(
    lat: float | Decimal,
    lon: float | Decimal,
    *,
    alt: float | Decimal | None = None,
    u: float | Decimal | None = None,
    crs: str | None = None,
    params: Mapping[str, str | None] | None = None,
) -> str:
    """Build a canonical geo: URI, validating every part first.

    Numbers are written in their shortest exact decimal form (a `Decimal` keeps its
    digits), the longitude is written as 0 at a pole, `crs` must be a label and is
    omitted when it is the default, and extra parameter values are percent-encoded.
    A parameter that maps to None is written as a flag without a value.
    """
    # GeoURI reads int, float and Decimal exactly; the float annotation is for callers.
    uri = GeoURI(
        cast(float, lat),
        cast(float, lon),
        cast("float | None", alt),
        cast("float | None", u),
        DEFAULT_CRS if crs is None else crs,
        {} if params is None else params,
    )
    return str(uri)
