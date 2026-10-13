"""Every geo: URI printed in RFC 5870, copied by script into tests/data/examples.json.

The verdicts below are written by hand from the RFC prose cited next to each one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geouri import GeoURIError, compare, parse

DATA = json.loads((Path(__file__).parent / "data" / "examples.json").read_text("utf-8"))
URIS: list[str] = DATA["rfc5870_uris"]

# Section 9.1 names geo:94,0 as invalid. Erratum 8389 (held for document update,
# https://www.rfc-editor.org/errata/eid8389) says the two section 6.4 URIs with ";"
# between latitude and longitude were meant to use ",".
INVALID = {"geo:94,0": "latitude-range"}
MISPRINTED = {"geo:22.300;-118.44", "geo:22.3;-118.4400"}


def test_the_fixture_holds_every_uri_of_the_rfc() -> None:
    assert len(URIS) == 16
    assert DATA["sources"]["rfc5870"]["url"] == "https://www.rfc-editor.org/rfc/rfc5870.txt"


@pytest.mark.parametrize("uri", URIS)
def test_each_example_parses_or_fails_as_the_rfc_says(uri: str) -> None:
    if uri in INVALID or uri in MISPRINTED:
        with pytest.raises(GeoURIError) as caught:
            parse(uri)
        assert caught.value.reason == INVALID.get(uri, "coordinates")
    else:
        assert str(parse(str(parse(uri)))) == str(parse(uri))


def test_section_6_1_reads_the_three_components() -> None:
    uri = parse(URIS[1])
    assert (uri.lat, uri.lon, uri.alt, uri.uncertainty, uri.crs) == (
        48.201,
        16.3695,
        183.0,
        None,
        "wgs84",
    )


def test_section_6_2_reads_crs_and_uncertainty() -> None:
    uri = parse(URIS[2])
    assert (uri.lat, uri.lon, uri.alt, uri.uncertainty, uri.crs) == (
        48.198634,
        16.371648,
        None,
        40.0,
        "wgs84",
    )


def _pair(index: int) -> tuple[str, str]:
    return URIS[index], URIS[index + 1]


def test_section_6_4_poles_with_case_insensitive_crs() -> None:
    a, b = map(parse, _pair(3))
    assert compare(a, b) is True


def test_section_6_4_corrected_by_erratum_8389() -> None:
    a, b = (parse(uri.replace(";", ",")) for uri in _pair(5))
    assert compare(a, b) is True


def test_section_6_4_unknown_parameter_decoded_and_case_insensitive_name() -> None:
    a, b = map(parse, _pair(7))
    assert compare(a, b) is True


def test_section_6_4_unknown_value_normalization_is_undefined() -> None:
    a, b = map(parse, _pair(9))
    assert compare(a, b) is None


def test_section_6_4_parameter_order_is_insignificant() -> None:
    a, b = map(parse, _pair(11))
    assert compare(a, b) is True
    assert a == b


def test_section_6_4_unknown_value_case_is_undefined() -> None:
    a, b = map(parse, _pair(13))
    assert compare(a, b) is None
