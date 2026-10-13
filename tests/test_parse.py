"""parse() follows the RFC 5870 grammar of section 3.3 and the ranges of section 3.4.2.

Cases written by hand from the ABNF and the prose of the RFC.
"""

from __future__ import annotations

import pytest

from geouri import GeoURIError, Reason, parse


def test_reads_latitude_longitude_and_altitude() -> None:
    uri = parse("geo:48.2010,16.3695,183")
    assert (uri.lat, uri.lon, uri.alt) == (48.201, 16.3695, 183.0)
    assert (uri.uncertainty, uri.crs, dict(uri.params)) == (None, "wgs84", {})


def test_reads_crs_uncertainty_and_other_parameters() -> None:
    uri = parse("geo:1,2;crs=WGS84;u=0;flag;Name=a%20b%C3%A9")
    assert (uri.crs, uri.uncertainty) == ("wgs84", 0.0)
    assert dict(uri.params) == {"flag": None, "name": "a b\u00e9"}


def test_scheme_and_parameter_names_are_case_insensitive() -> None:
    uri = parse("GeO:1,2;CRS=wgs84;U=3;X=Y")
    assert (uri.crs, uri.uncertainty, dict(uri.params)) == ("wgs84", 3.0, {"x": "Y"})


def test_every_paramchar_is_accepted_literally() -> None:
    uri = parse("geo:1,2;v=az09-_.!~*'()[]:&+$")
    assert uri.params["v"] == "az09-_.!~*'()[]:&+$"


def test_minus_zero_is_zero() -> None:
    assert parse("geo:-0,-0.0") == parse("geo:0,0")


def test_ranges_are_inclusive() -> None:
    assert parse("geo:-90,-180").lat == -90.0
    assert parse("geo:90,180").lon == 180.0


def test_other_crs_skips_wgs84_ranges_and_digit_limits() -> None:
    uri = parse("geo:1000.5,-2000,5;crs=Some-Grid")
    assert (uri.lat, uri.lon, uri.crs, uri.is_wgs84) == (1000.5, -2000.0, "some-grid", False)


def test_ranges_use_the_exact_text_not_a_rounded_float() -> None:
    with pytest.raises(GeoURIError) as caught:
        parse("geo:90.0000000000000000001,0")
    assert caught.value.reason == "latitude-range"
    with pytest.raises(GeoURIError) as caught:
        parse("geo:0,-180.00000000000000000001")
    assert caught.value.reason == "longitude-range"


@pytest.mark.parametrize(
    ("uri", "reason"),
    [
        ("http://example.com", "scheme"),
        (" geo:1,2", "scheme"),
        ("geo:", "coordinates"),
        ("geo:48.2", "coordinates"),
        ("geo:1,2,3,4", "coordinates"),
        ("geo:22.300;-118.44", "coordinates"),
        ("geo:north,16", "number"),
        ("geo:\u0664\u0668,16", "number"),
        ("geo:1,\uff12", "number"),
        ("geo:1.,2", "number"),
        ("geo:.5,2", "number"),
        ("geo:+1,2", "number"),
        ("geo:1e2,2", "number"),
        ("geo:1,2,", "number"),
        ("geo:1, 2", "number"),
        ("geo:%31,2", "number"),
        ("geo:090,0", "number"),
        ("geo:1,0180", "number"),
        ("geo:1,2,-", "number"),
        ("geo:1,2,\u0663", "number"),
        ("geo:1\u0661,2;crs=other", "number"),
        ("geo:94,0", "latitude-range"),
        ("geo:-90.5,0", "latitude-range"),
        ("geo:0,180.1", "longitude-range"),
        ("geo:0,-181", "longitude-range"),
        ("geo:1,2;u=-1", "uncertainty"),
        ("geo:1,2;u=", "uncertainty"),
        ("geo:1,2;u", "uncertainty"),
        ("geo:1,2;u=1e3", "uncertainty"),
        ("geo:1,2;u=-0", "uncertainty"),
        ("geo:1,2;crs", "crs"),
        ("geo:1,2;crs=", "crs"),
        ("geo:1,2;crs=wgs_84", "crs"),
        ("geo:1,2;", "param-name"),
        ("geo:1,2;;x", "param-name"),
        ("geo:1,2;=v", "param-name"),
        ("geo:1,2;a b=c", "param-name"),
        ("geo:1,2;x_y=1", "param-name"),
        ("geo:1,2;x=", "param-value"),
        ("geo:1,2;x=a b", "param-value"),
        ("geo:1,2;x=a=b", "param-value"),
        ("geo:1,2;x=a,b", "param-value"),
        ("geo:1,2;x=%zz", "param-value"),
        ("geo:1,2;x=%4", "param-value"),
        ("geo:1,2;x=%FF", "param-value"),
        ("geo:1,2;x=\u00e9", "param-value"),
        ("geo:1,2;u=1;u=2", "duplicate-param"),
        ("geo:1,2;crs=wgs84;crs=wgs84", "duplicate-param"),
        ("geo:1,2;x=1;X=2", "duplicate-param"),
        ("geo:1,2;u=1;crs=wgs84", "param-order"),
        ("geo:1,2;x=1;crs=wgs84", "param-order"),
        ("geo:1,2;x=1;u=2", "param-order"),
        ("geo:1,2;crs=wgs84;x;u=2", "param-order"),
        ("geo:1,2?z=3", "query"),
        ("geo:1,2#here", "fragment"),
    ],
)
def test_rejects_with_the_reason(uri: str, reason: Reason) -> None:
    with pytest.raises(GeoURIError) as caught:
        parse(uri)
    assert caught.value.reason == reason


def test_rejects_a_non_string() -> None:
    with pytest.raises(TypeError):
        parse(b"geo:1,2")  # type: ignore[arg-type]


def test_wgs84_digit_limits_still_allow_long_fractions() -> None:
    uri = parse("geo:-12.123456789012,-123.123456789012")
    assert str(uri) == "geo:-12.123456789012,-123.123456789012"
