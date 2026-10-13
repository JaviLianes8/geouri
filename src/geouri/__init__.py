"""Typed, zero-dependency parser and builder for geo: URIs (RFC 5870)."""

from __future__ import annotations

from ._android import AndroidGeo, build_android, build_android_query, parse_android
from ._build import build
from ._errors import GeoURIError, Reason
from ._model import GeoURI, compare
from ._parse import parse

__version__ = "0.2.0"

__all__ = [
    "AndroidGeo",
    "GeoURI",
    "GeoURIError",
    "Reason",
    "build",
    "build_android",
    "build_android_query",
    "compare",
    "parse",
    "parse_android",
]
