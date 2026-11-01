"""Validate model fields without exposing caller data in diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from ._errors import GeoURIError
from ._grammar import check_number_size, label

DEFAULT_CRS = "wgs84"
_RESERVED = frozenset({"crs", "u"})


def exact_number(value: object, what: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{what} must be a number")
    # float.__repr__ gives the shortest text that reads back as the same float, also for
    # float subclasses whose own repr adds a type name.
    exact = Decimal(float.__repr__(value)) if isinstance(value, float) else Decimal(value)
    if not exact.is_finite():
        raise GeoURIError("number", f"{what} is not finite")
    check_number_size(exact)
    return exact


def check_ranges(exact: tuple[Decimal, Decimal, Decimal | None, Decimal | None], crs: str) -> None:
    lat, lon, _, unc = exact
    if unc is not None and unc < 0:
        raise GeoURIError("uncertainty", "uncertainty must be non-negative")
    if crs != DEFAULT_CRS:
        return  # section 3.4.1: ranges of other reference systems are not defined
    if not -90 <= lat <= 90:
        raise GeoURIError("latitude-range", "latitude out of range [-90, 90]")
    if not -180 <= lon <= 180:
        raise GeoURIError("longitude-range", "longitude out of range [-180, 180]")


def check_params(params: Mapping[str, str | None]) -> dict[str, str | None]:
    if not isinstance(params, Mapping):
        raise TypeError("params must be a mapping")
    checked: dict[str, str | None] = {}
    for raw, value in params.items():
        if not isinstance(raw, str) or not (value is None or isinstance(value, str)):
            raise TypeError("parameters must map str to str or None")
        name = label(raw, "param-name", "parameter name")
        if name in _RESERVED:
            raise GeoURIError("param-name", "crs and u have their own fields")
        if name in checked:
            raise GeoURIError("duplicate-param", "parameter appears twice")
        if value == "":
            raise GeoURIError("param-value", "parameter values cannot be empty")
        if value is not None:
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                raise GeoURIError(
                    "param-value", "parameter value is not encodable as UTF-8"
                ) from None
        checked[name] = value
    return checked
