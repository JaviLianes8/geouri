"""The error raised for a malformed geo: URI, with a machine-readable reason."""

from __future__ import annotations

from typing import Literal

Reason = Literal[
    "scheme",
    "coordinates",
    "number",
    "latitude-range",
    "longitude-range",
    "uncertainty",
    "crs",
    "param-name",
    "param-value",
    "duplicate-param",
    "param-order",
    "query",
    "fragment",
    "zoom",
]


class GeoURIError(ValueError):
    """Raised when a geo: URI is malformed or a coordinate is out of range.

    `reason` names the rule that failed, from the closed set `Reason`.
    """

    reason: Reason

    def __init__(self, reason: Reason, message: str = "") -> None:
        super().__init__(reason, message)
        self.reason = reason
        self.message = message

    def __str__(self) -> str:
        return f"{self.reason}: {self.message}" if self.message else self.reason
