"""Immutable, validated representation of a geo: URI (RFC 5870)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import cast

from ._grammar import encode_value, label, plain
from ._validation import check_params, check_ranges, exact_number

DEFAULT_CRS = "wgs84"


@dataclass(frozen=True, eq=False)
class GeoURI:
    """A geo: URI (RFC 5870): a point in a coordinate reference system.

    Numbers keep their exact decimal value next to the float fields, so ranges, `==`,
    `hash` and `str` follow the text that was parsed rather than a rounded float.
    `str()` gives the canonical URI. Equality follows section 3.4.4; see `compare`.
    `dataclasses.replace` rebuilds from the float fields, so digits beyond float precision
    are not carried over; use build with Decimal values to keep them.

    Invalid values raise GeoURIError; wrong argument types raise TypeError.

    >>> from geouri import GeoURI
    >>> str(GeoURI(1, 2, uncertainty=3))
    'geo:1,2;u=3'
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
            exact_number(self.lat, "latitude"),
            exact_number(self.lon, "longitude"),
            None if self.alt is None else exact_number(self.alt, "altitude"),
            None if self.uncertainty is None else exact_number(self.uncertainty, "uncertainty"),
        )
        if not isinstance(self.crs, str):
            raise TypeError("crs must be a str")
        crs = label(self.crs, "crs", "crs label")
        check_ranges(exact, crs)
        floats = [None if v is None else float(v) for v in exact]
        for name, value in zip(("lat", "lon", "alt", "uncertainty"), floats, strict=True):
            object.__setattr__(self, name, value)
        object.__setattr__(self, "crs", crs)
        object.__setattr__(self, "params", MappingProxyType(check_params(self.params)))
        object.__setattr__(self, "_exact", exact)

    @property
    def is_wgs84(self) -> bool:
        """Whether the coordinates are WGS-84 latitude, longitude and altitude.

        >>> from geouri import GeoURI
        >>> GeoURI(1, 2).is_wgs84
        True
        """
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

    def __reduce__(self) -> tuple[object, ...]:
        # The read-only params mapping cannot be pickled; rebuild from exact values.
        return (new_geouri, (self._exact, self.crs, dict(self.params)))

    def _key(self) -> tuple[str, Decimal, Decimal | None, Decimal | None, Decimal | None]:
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

    Returns None where the RFC calls the result undefined: known fields match but
    unknown parameter names or decoded values differ. Their semantics cannot be judged
    without knowing those parameters. Differences in known fields return False.
    Wrong argument types raise TypeError.

    >>> from geouri import compare, parse
    >>> compare(parse('geo:90,1'), parse('geo:90,2'))
    True
    """
    if not isinstance(a, GeoURI) or not isinstance(b, GeoURI):
        raise TypeError("compare expects two GeoURI instances")
    if a._key() != b._key():
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
