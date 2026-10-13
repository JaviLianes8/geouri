"""The Android map intent dialect (not RFC 5870), checked against the guide's examples."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geouri import AndroidGeo, GeoURIError, build_android, build_android_query, parse, parse_android

DATA = json.loads((Path(__file__).parent / "data" / "examples.json").read_text("utf-8"))
EXAMPLES: list[str] = DATA["android_examples"]


def test_the_fixture_holds_the_four_examples_of_the_guide() -> None:
    assert len(EXAMPLES) == 4


def test_plain_point() -> None:
    assert parse_android(EXAMPLES[0]) == AndroidGeo(parse("geo:47.6,-122.3"))


def test_point_with_zoom() -> None:
    geo = parse_android(EXAMPLES[1])
    assert (geo.point, geo.zoom, geo.query, geo.pin) == (parse("geo:47.6,-122.3"), 11, None, None)


def test_pin_with_label() -> None:
    geo = parse_android(EXAMPLES[2])
    assert (geo.point, geo.pin, geo.label) == (
        parse("geo:0,0"),
        parse("geo:34.99,-106.61"),
        "Treasure",
    )
    assert geo.query is None


def test_address_search_decodes_plus_and_escapes() -> None:
    geo = parse_android(EXAMPLES[3])
    assert geo.query == "1600 Amphitheatre Parkway, CA"
    assert (geo.pin, geo.label) == (None, None)


def test_builders_write_the_guide_examples() -> None:
    assert build_android(47.6, -122.3) == EXAMPLES[0]
    assert build_android(47.6, -122.3, zoom=11) == EXAMPLES[1]
    assert build_android(34.99, -106.61, label="Treasure") == EXAMPLES[2]


def test_query_text_is_encoded_as_the_guide_shows() -> None:
    text, encoded = DATA["android_encoded_text"]
    assert build_android_query(text) == f"geo:0,0?q={encoded}"
    assert parse_android(f"geo:0,0?q={encoded}").query == text


def test_pin_without_label_and_with_parentheses_in_the_label() -> None:
    assert parse_android("geo:0,0?q=1,2").pin == parse("geo:1,2")
    assert parse_android("geo:0,0?q=1,2").label is None
    uri = build_android(1, 2, label="Bar (old) & co", zoom=3)
    assert uri == "geo:0,0?q=1,2(Bar%20%28old%29%20%26%20co)&z=3"
    geo = parse_android(uri)
    assert (geo.pin, geo.label, geo.zoom) == (parse("geo:1,2"), "Bar (old) & co", 3)


def test_rfc_parameters_and_unknown_fields_are_kept() -> None:
    geo = parse_android("geo:1,2;u=5?z=23&mode=d")
    assert (geo.point.uncertainty, geo.zoom, dict(geo.extras)) == (5.0, 23, {"mode": "d"})


def test_search_round_trip_with_zoom() -> None:
    uri = build_android_query("caf\u00e9+bar", zoom=1)
    assert uri == "geo:0,0?q=caf%C3%A9%2Bbar&z=1"
    geo = parse_android(uri)
    assert (geo.query, geo.zoom) == ("caf\u00e9+bar", 1)


def test_results_are_hashable() -> None:
    assert hash(parse_android("geo:1,2?z=3&a=b")) == hash(parse_android("geo:1,2?z=3&a=b"))


@pytest.mark.parametrize(
    ("uri", "reason"),
    [
        ("geo:1,2?", "query"),
        ("geo:1,2?z", "query"),
        ("geo:1,2?=1", "query"),
        ("geo:1,2?z=1&z=2", "query"),
        ("geo:1,2?q=", "query"),
        ("geo:1,2?q=%zz", "query"),
        ("geo:1,2?q=%FF", "query"),
        ("geo:1,2?z=0", "zoom"),
        ("geo:1,2?z=24", "zoom"),
        ("geo:1,2?z=-1", "zoom"),
        ("geo:1,2?z=1.5", "zoom"),
        ("geo:1,2?z=\u0661", "zoom"),
        ("geo:0,0?q=95,0(x)", "latitude-range"),
        ("geo:95,0?z=3", "latitude-range"),
        ("geo:1,2?z=3#x", "fragment"),
        ("http:1,2?z=3", "scheme"),
    ],
)
def test_rejects_with_the_reason(uri: str, reason: str) -> None:
    with pytest.raises(GeoURIError) as caught:
        parse_android(uri)
    assert caught.value.reason == reason


@pytest.mark.parametrize(
    ("call", "reason"),
    [
        (lambda: build_android(1, 2, zoom=0), "zoom"),
        (lambda: build_android(1, 2, zoom=24), "zoom"),
        (lambda: build_android(1, 2, label=""), "query"),
        (lambda: build_android(91, 2), "latitude-range"),
        (lambda: build_android_query(""), "query"),
        (lambda: build_android_query("\ud800"), "query"),
    ],
)
def test_builders_refuse_with_the_reason(call: object, reason: str) -> None:
    with pytest.raises(GeoURIError) as caught:
        call()  # type: ignore[operator]
    assert caught.value.reason == reason


def test_builders_and_parser_refuse_wrong_types() -> None:
    with pytest.raises(TypeError):
        build_android(1, 2, zoom=True)
    with pytest.raises(TypeError):
        build_android(1, 2, zoom=3.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        parse_android(None)  # type: ignore[arg-type]
