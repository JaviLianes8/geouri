"""Range checks shared by parsing and building."""

from __future__ import annotations

from ._model import GeoURIError


def validate(lat: float, lon: float, uncertainty: float | None = None) -> None:
    """Reject coordinates outside their WGS84 ranges or a negative uncertainty."""
    if not -90.0 <= lat <= 90.0:
        raise GeoURIError(f"latitude out of range [-90, 90]: {lat}")
    if not -180.0 <= lon <= 180.0:
        raise GeoURIError(f"longitude out of range [-180, 180]: {lon}")
    if uncertainty is not None and uncertainty < 0.0:
        raise GeoURIError(f"uncertainty must be non-negative: {uncertainty}")
