"""build() writes the canonical form and refuses anything parse() would refuse."""

from __future__ import annotations

import random
from decimal import Decimal

import pytest

from geouri import GeoURIError, build, parse


def test_basic_point() -> None:
    assert build(48.2, 16.3) == "geo:48.2,16.3"


def test_trailing_zeros_and_negative_zero_are_dropped() -> None:
    assert build(48.0, -0.0) == "geo:48,0"


def test_all_parts() -> None:
    uri = build(48.2, 16.3, alt=183, u=23.5, crs="Local-1", params={"Type": "home", "f": None})
    assert uri == "geo:48.2,16.3,183;crs=local-1;u=23.5;type=home;f"


def test_default_crs_is_omitted() -> None:
    assert build(1, 2, crs="WGS84") == "geo:1,2"


def test_small_and_large_numbers_keep_every_digit() -> None:
    assert build(1.234567891234e-5, 0) == "geo:0.00001234567891234,0"
    assert build(0, 0, alt=1e20) == "geo:0,0,100000000000000000000"
    assert build(0, 0, alt=-5e-324) == "geo:0,0,-" + format(Decimal("5e-324"), "f")


def test_decimal_input_keeps_its_digits() -> None:
    assert build(Decimal("0.10000000000000000001"), Decimal("1E+2")) == (
        "geo:0.10000000000000000001,100"
    )


def test_pole_longitude_is_written_as_zero() -> None:
    assert build(90, 45) == "geo:90,0"
    assert build(-90.0, -180) == "geo:-90,0"


def test_parameter_values_are_percent_encoded() -> None:
    uri = build(1, 2, params={"name": "caf\u00e9 & bar;x=1,2%"})
    assert uri == "geo:1,2;name=caf%C3%A9%20&%20bar%3Bx%3D1%2C2%25"
    assert parse(uri).params["name"] == "caf\u00e9 & bar;x=1,2%"


@pytest.mark.parametrize(
    ("call", "reason"),
    [
        (lambda: build(91, 0), "latitude-range"),
        (lambda: build(0, 181), "longitude-range"),
        (lambda: build(1, 2, u=-1), "uncertainty"),
        (lambda: build(float("nan"), 0), "number"),
        (lambda: build(Decimal("Infinity"), 0), "number"),
        (lambda: build(Decimal("NaN"), 0), "number"),
        (lambda: build(1, 2, crs="bad label"), "crs"),
        (lambda: build(1, 2, crs=""), "crs"),
        (lambda: build(1, 2, params={"u": "3"}), "param-name"),
        (lambda: build(1, 2, params={"crs": "x"}), "param-name"),
        (lambda: build(1, 2, params={"a;b": "x"}), "param-name"),
        (lambda: build(1, 2, params={"a": ""}), "param-value"),
        (lambda: build(1, 2, params={"a": "1", "A": "2"}), "duplicate-param"),
    ],
)
def test_refuses_with_the_reason(call: object, reason: str) -> None:
    with pytest.raises(GeoURIError) as caught:
        call()  # type: ignore[operator]
    assert caught.value.reason == reason


def test_refuses_booleans_and_strings() -> None:
    with pytest.raises(TypeError):
        build(True, 0)
    with pytest.raises(TypeError):
        build(0, "1")  # type: ignore[arg-type]


def test_random_floats_round_trip_exactly() -> None:
    rng = random.Random(5870)
    for _ in range(2000):
        lat = rng.uniform(-90, 90) * 10 ** rng.randint(-12, 0)
        lon = rng.uniform(-180, 180)
        alt = rng.uniform(-1e6, 1e6) * 10 ** rng.randint(-20, 10)
        uri = parse(build(lat, lon, alt=alt))
        assert (uri.lat, uri.lon, uri.alt) == (lat, lon, alt)


def test_built_uris_parse_back_equal() -> None:
    params: dict[str, str | None] = {"x": "\u00e9 [1]", "y": None}
    text = build(-33.8688, 151.2093, alt=58, u=0, crs="other", params=params)
    uri = parse(text)
    assert (uri.lat, uri.lon, uri.alt, uri.uncertainty, uri.crs) == (
        -33.8688,
        151.2093,
        58.0,
        0.0,
        "other",
    )
    assert dict(uri.params) == params
    assert build(uri.lat, uri.lon, alt=uri.alt, u=uri.uncertainty, crs=uri.crs, params=params) == (
        text
    )
