"""Immutable representation of a parsed geo: URI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


class GeoURIError(ValueError):
    """Raised when a geo: URI is malformed or a coordinate is out of range."""


@dataclass(frozen=True)
class GeoURI:
    """A parsed geo: URI (RFC 5870)."""

    lat: float
    lon: float
    alt: float | None = None
    uncertainty: float | None = None
    crs: str = "wgs84"
    params: Mapping[str, str | None] = field(default_factory=dict)
