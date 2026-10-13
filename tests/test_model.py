"""GeoURI validates on construction, prints the canonical form and compares per 3.4.4."""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from geouri import GeoURI, GeoURIError, compare, parse


def test_construction_validates_and_normalizes() -> None:
    uri = GeoURI(1, 2, crs="WGS84", params={"Name": "x"})
    assert (uri.lat, uri.crs, dict(uri.params)) == (1.0, "wgs84", {"name": "x"})
    assert type(uri.lat) is float


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"lat": 91, "lon": 0}, "latitude-range"),
        ({"lat": 0, "lon": -180.5}, "longitude-range"),
        ({"lat": 0, "lon": 0, "uncertainty": -0.1}, "uncertainty"),
        ({"lat": float("nan"), "lon": 0}, "number"),
        ({"lat": 0, "lon": float("inf")}, "number"),
        ({"lat": 0, "lon": 0, "alt": float("-inf")}, "number"),
        ({"lat": 0, "lon": 0, "crs": ""}, "crs"),
        ({"lat": 0, "lon": 0, "crs": "a b"}, "crs"),
        ({"lat": 0, "lon": 0, "crs": 5}, "crs"),
        ({"lat": 0, "lon": 0, "params": {"u": "1"}}, "param-name"),
        ({"lat": 0, "lon": 0, "params": {"CRS": "x"}}, "param-name"),
        ({"lat": 0, "lon": 0, "params": {"a_b": "x"}}, "param-name"),
        ({"lat": 0, "lon": 0, "params": {7: "x"}}, "param-name"),
        ({"lat": 0, "lon": 0, "params": {"a": "1", "A": "2"}}, "duplicate-param"),
        ({"lat": 0, "lon": 0, "params": {"a": ""}}, "param-value"),
        ({"lat": 0, "lon": 0, "params": {"a": 1}}, "param-value"),
        ({"lat": 0, "lon": 0, "params": {"a": "\ud800"}}, "param-value"),
    ],
)
def test_construction_rejects_with_the_reason(kwargs: dict[str, object], reason: str) -> None:
    with pytest.raises(GeoURIError) as caught:
        GeoURI(**kwargs)  # type: ignore[arg-type]
    assert caught.value.reason == reason


@pytest.mark.parametrize("bad", [True, "1", None, [1]])
def test_construction_rejects_non_numbers(bad: object) -> None:
    with pytest.raises(TypeError):
        GeoURI(bad, 0)  # type: ignore[arg-type]


def test_is_frozen_and_params_are_read_only() -> None:
    uri = parse("geo:1,2;a=b")
    with pytest.raises(dataclasses.FrozenInstanceError):
        uri.lat = 5.0  # type: ignore[misc]
    with pytest.raises(TypeError):
        uri.params["a"] = "c"  # type: ignore[index]


def test_caller_dict_changes_do_not_leak_in() -> None:
    params: dict[str, str | None] = {"a": "b"}
    uri = GeoURI(1, 2, params=params)
    params["a"] = "changed"
    assert uri.params["a"] == "b"


def test_replace_revalidates() -> None:
    uri = parse("geo:1,2")
    assert str(dataclasses.replace(uri, lat=3.5)) == "geo:3.5,2"
    with pytest.raises(GeoURIError):
        dataclasses.replace(uri, lat=100.0)


def test_str_is_canonical() -> None:
    uri = parse("geo:48.2010,016.3695,-0.0;crs=WGS84;u=40.0;Type=Home;f")
    assert str(uri) == "geo:48.201,16.3695,0;u=40;type=Home;f"
    assert str(parse("geo:1,2;crs=Grid-7;u=1")) == "geo:1,2;crs=grid-7;u=1"


def test_str_writes_zero_longitude_at_the_poles_of_wgs84_only() -> None:
    assert str(parse("geo:-90,123")) == "geo:-90,0"
    assert str(parse("geo:90,5;crs=other")) == "geo:90,5;crs=other"


def test_str_keeps_digits_a_float_cannot_hold() -> None:
    text = "geo:0.10000000000000000001,-179.99999999999999999999"
    assert str(parse(text)) == text


def test_str_reencodes_parameter_values() -> None:
    assert str(parse("geo:1,2;x=%41%2c%e2%82%ac")) == "geo:1,2;x=A%2C%E2%82%AC"


def test_parameter_order_is_kept_in_str_and_ignored_by_equality() -> None:
    a, b = parse("geo:1,2;a=1;b=2"), parse("geo:1,2;b=2;a=1")
    assert str(a).endswith(";a=1;b=2")
    assert a == b
    assert hash(a) == hash(b)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("geo:43.10,1", "geo:43.1,1.000"),
        ("geo:90,10", "geo:90,-170"),
        ("geo:-90,1", "geo:-90,0"),
        ("geo:10,180", "geo:10,-180"),
        ("geo:1,2;crs=wgs84", "geo:1,2"),
        ("geo:1,2;u=0.50", "geo:1,2;u=0.5"),
        ("geo:1,2,0;crs=x", "geo:1,2,-0;crs=X"),
    ],
)
def test_equal_per_section_3_4_4(left: str, right: str) -> None:
    a, b = parse(left), parse(right)
    assert a == b
    assert hash(a) == hash(b)
    assert compare(a, b) is True


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("geo:1,2", "geo:1,2,0"),
        ("geo:1,2", "geo:1,2;u=0"),
        ("geo:1,2;u=1", "geo:1,2;u=2"),
        ("geo:89,10", "geo:89,-170"),
        ("geo:10,180;crs=x", "geo:10,-180;crs=x"),
        ("geo:90,10;crs=x", "geo:90,-170;crs=x"),
        ("geo:1,2;crs=x", "geo:1,2"),
        ("geo:1,2;crs=x", "geo:1,2;crs=y"),
        ("geo:1,2;a=1", "geo:1,2;b=1"),
        ("geo:1,2;a", "geo:1,2"),
        ("geo:0.10000000000000000001,0", "geo:0.1,0"),
    ],
)
def test_not_equal_per_section_3_4_4(left: str, right: str) -> None:
    a, b = parse(left), parse(right)
    assert a != b
    assert compare(a, b) is False


def test_differing_unknown_values_compare_as_undefined() -> None:
    a, b = parse("geo:1,2;a=1.00;b=x"), parse("geo:1,2;a=1;b=x")
    assert compare(a, b) is None
    assert a != b
    assert compare(parse("geo:1,2;a"), parse("geo:1,2;a=1")) is None


def test_equality_with_other_types_is_not_implemented() -> None:
    assert parse("geo:1,2") != "geo:1,2"
    assert parse("geo:1,2").__eq__("geo:1,2") is NotImplemented


def test_float_and_decimal_inputs_share_the_exact_value() -> None:
    assert GeoURI(0.1, 0) == GeoURI(Decimal("0.1"), 0)  # type: ignore[arg-type]
    assert str(GeoURI(1e-7, 2.5e-12)) == "geo:0.0000001,0.0000000000025"


def test_float_subclasses_use_their_float_value() -> None:
    class Degrees(float):
        def __repr__(self) -> str:
            return f"Degrees({float(self)})"

    assert str(GeoURI(Degrees(1.5), 2)) == "geo:1.5,2"
