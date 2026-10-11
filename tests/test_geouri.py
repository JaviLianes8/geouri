import pytest

from geouri import GeoURIError, build, parse


def test_parse_latitude_and_longitude() -> None:
    uri = parse("geo:48.2010,16.3695")
    assert (uri.lat, uri.lon) == (48.2010, 16.3695)
    assert uri.alt is None
    assert uri.uncertainty is None
    assert uri.crs == "wgs84"
    assert uri.params == {}


def test_parse_altitude() -> None:
    uri = parse("geo:48.2,16.3,183")
    assert uri.alt == 183.0


def test_parse_uncertainty_and_crs() -> None:
    uri = parse("geo:48.2,16.3;crs=WGS84;u=23.5")
    assert uri.uncertainty == 23.5
    assert uri.crs == "wgs84"


def test_parse_negative_coordinates() -> None:
    uri = parse("geo:-33.8688,-151.2093")
    assert uri.lat == -33.8688
    assert uri.lon == -151.2093


def test_parse_scheme_is_case_insensitive() -> None:
    assert parse("GEO:1,2").lat == 1.0


def test_parse_extra_parameters() -> None:
    uri = parse("geo:1,2;type=home;flag;name=a%20b")
    assert uri.params == {"type": "home", "flag": None, "name": "a b"}


def test_parse_rejects_non_geo_scheme() -> None:
    with pytest.raises(GeoURIError):
        parse("http://example.com")


def test_parse_rejects_malformed_coordinates() -> None:
    with pytest.raises(GeoURIError):
        parse("geo:48.2")


def test_parse_rejects_non_numeric_coordinate() -> None:
    with pytest.raises(GeoURIError):
        parse("geo:north,16.3")


def test_parse_rejects_latitude_out_of_range() -> None:
    with pytest.raises(GeoURIError):
        parse("geo:95,16.3")


def test_parse_rejects_longitude_out_of_range() -> None:
    with pytest.raises(GeoURIError):
        parse("geo:48.2,200")


def test_parse_rejects_crs_without_value() -> None:
    with pytest.raises(GeoURIError):
        parse("geo:1,2;crs")


def test_build_basic() -> None:
    assert build(48.2, 16.3) == "geo:48.2,16.3"


def test_build_strips_trailing_zeros() -> None:
    assert build(48.0, -0.0) == "geo:48,0"


def test_build_with_altitude_uncertainty_and_crs() -> None:
    assert build(48.2, 16.3, alt=183, u=23.5, crs="WGS84") == "geo:48.2,16.3,183;crs=wgs84;u=23.5"


def test_build_rejects_latitude_out_of_range() -> None:
    with pytest.raises(GeoURIError):
        build(91, 0)


def test_build_rejects_negative_uncertainty() -> None:
    with pytest.raises(GeoURIError):
        build(1, 2, u=-1)


def test_round_trip_through_parse_and_build() -> None:
    uri = parse("geo:48.2,16.3,183;crs=wgs84;u=23.5")
    rebuilt = build(uri.lat, uri.lon, alt=uri.alt, u=uri.uncertainty, crs=uri.crs)
    assert rebuilt == "geo:48.2,16.3,183;crs=wgs84;u=23.5"
    assert parse(rebuilt) == uri


def test_geouri_is_immutable() -> None:
    uri = parse("geo:1,2")
    with pytest.raises(AttributeError):
        uri.lat = 5.0  # type: ignore[misc]
