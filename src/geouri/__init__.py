"""Typed, zero-dependency parser and builder for geo: URIs (RFC 5870)."""

from __future__ import annotations

from ._build import build
from ._model import GeoURI, GeoURIError
from ._parse import parse

__version__ = "0.1.0"

__all__ = ["GeoURI", "GeoURIError", "build", "parse"]
