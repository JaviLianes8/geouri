"""Immutable, validated representation of a geo: URI (RFC 5870)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Any, cast

from ._errors import GeoURIError
from ._grammar import encode_value, label, plain

DEFAULT_CRS = "wgs84"
_RESERVED = frozenset({"crs", "u"})


@dataclass(frozen=True, eq=False)
class GeoURI:
    """A geo: URI (RFC 5870): a point in a coordinate reference system.

    Numbers keep their exact decimal value next to the float fields, so ranges, `==`,
    `hash` and `str` follow the text that was parsed rather than a rounded float.
    `str()` gives the canonical URI. Equality follows section 3.4.4; see `compare`.
    `dataclasses.replace` rebuilds from the float fields, so digits beyond float precision
    are not carried over; build a new URI from `Decimal` values to keep them.
    """

    lat: float
    lon: float
    alt: float | None = None
    uncertainty: float | None = None
    crs: str = DEFAULT_CRS
    params: Mapping[str, str | None] = field(default_factory=dict)
    _exact: tuple[Decimal, Decimal, Decimal | None, Decimal | None] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        exact = (
            _exact(self.lat, "latitude"),
            _exact(self.lon, "longitude"),
            None if self.alt is None else _exact(self.alt, "altitude"),
            None if self.uncertainty is None else _exact(self.uncertainty, "uncertainty"),
        )
        if not isinstance(self.crs, str):
            raise TypeError(f"crs must be a str, not {type(self.crs).__name__}")
        crs = label(self.crs, "crs", "crs label")
        _check_ranges(exact, crs)
        floats = [None if v is None else float(v) for v in exact]
        for name, value in zip(("lat", "lon", "alt", "uncertainty"), floats, strict=True):
            object.__setattr__(self, name, value)
        object.__setattr__(self, "crs", crs)
        object.__setattr__(self, "params", MappingProxyType(_check_params(self.params)))
        object.__setattr__(self, "_exact", exact)

    @property
    def is_wgs84(self) -> bool:
        """Whether the coordinates are WGS-84 latitude, longitude and altitude."""
        return self.crs == DEFAULT_CRS

    def __str__(self) -> str:
        lat, _, alt, unc = self._exact
        lon = self._key()[2]
        if lon is None:
            lon = Decimal(0)  # section 3.4.2: longitude SHOULD be 0 at a pole
        text = f"geo:{plain(lat)},{plain(lon)}"
        if alt is not None:
            text += f",{plain(alt)}"
        if not self.is_wgs84:
            text += f";crs={self.crs}"
        if unc is not None:
            text += f";u={plain(unc)}"
        for name, value in self.params.items():
            text += f";{name}" if value is None else f";{name}={encode_value(value)}"
        return text

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoURI):
            return NotImplemented
        return self._key() == other._key() and dict(self.params) == dict(other.params)

    def __hash__(self) -> int:
        return hash((self._key(), frozenset(self.params.items())))

    def __reduce__(self) -> tuple[Any, ...]:
        # The read-only params mapping cannot be pickled; rebuild from exact values.
        return (new_geouri, (self._exact, self.crs, dict(self.params)))

    def _key(self) -> tuple[Any, ...]:
        lat, lon, alt, unc = self._exact
        lon_key: Decimal | None = lon
        # copy_abs never rounds, unlike abs() under the decimal context precision.
        if self.is_wgs84:
            if lat.copy_abs() == 90:
                lon_key = None  # poles case
            elif lon == -180:
                lon_key = Decimal(180)  # date line case
        return (self.crs, lat, lon_key, alt, unc)


def compare(a: GeoURI, b: GeoURI) -> bool | None:
    """Compare two geo: URIs per RFC 5870 section 3.4.4.

    Returns None where the RFC calls the result undefined: everything else matches and
    the same unknown parameter names appear, but some decoded values differ, which an
    implementation that does not know those parameters cannot judge. URIs whose unknown
    parameter names differ are not equivalent (the first rule for unknown parameters).
    """
    if a._key() != b._key() or set(a.params) != set(b.params):
        return False
    return True if dict(a.params) == dict(b.params) else None


def new_geouri(
    exact: tuple[Decimal, Decimal, Decimal | None, Decimal | None],
    crs: str,
    params: Mapping[str, str | None],
) -> GeoURI:
    """Build a GeoURI from exact decimals; the fields are typed float for callers."""
    lat, lon, alt, unc = (cast(float, value) for value in exact)
    return GeoURI(lat, lon, alt, unc, crs, params)


def _exact(value: object, what: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{what} must be a number, not {type(value).__name__}")
    # float.__repr__ gives the shortest text that reads back as the same float, also for
    # float subclasses whose own repr adds a type name.
    exact = Decimal(float.__repr__(value)) if isinstance(value, float) else Decimal(value)
    if not exact.is_finite():
        raise GeoURIError("number", f"{what} is not finite: {value!r}")
    return exact


def _check_ranges(exact: tuple[Decimal, Decimal, Decimal | None, Decimal | None], crs: str) -> None:
    lat, lon, _, unc = exact
    if unc is not None and unc < 0:
        raise GeoURIError("uncertainty", f"uncertainty must be non-negative: {unc}")
    if crs != DEFAULT_CRS:
        return  # section 3.4.1: ranges of other reference systems are not defined
    if not -90 <= lat <= 90:
        raise GeoURIError("latitude-range", f"latitude out of range [-90, 90]: {lat}")
    if not -180 <= lon <= 180:
        raise GeoURIError("longitude-range", f"longitude out of range [-180, 180]: {lon}")


def _check_params(params: Mapping[str, str | None]) -> dict[str, str | None]:
    if not isinstance(params, Mapping):
        raise TypeError(f"params must be a mapping, not {type(params).__name__}")
    checked: dict[str, str | None] = {}
    for raw, value in params.items():
        if not isinstance(raw, str) or not (value is None or isinstance(value, str)):
            raise TypeError(f"parameters map str to str or None, not {raw!r}: {value!r}")
        name = label(raw, "param-name", "parameter name")
        if name in _RESERVED:
            raise GeoURIError("param-name", f"crs and u have their own fields: {raw!r}")
        if name in checked:
            raise GeoURIError("duplicate-param", f"parameter {name!r} appears twice")
        if value == "":
            raise GeoURIError("param-value", f"the value of {name!r} cannot be empty")
        if value is not None:
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                raise GeoURIError("param-value", f"not encodable: {value!r}") from None
        checked[name] = value
    return checked
