"""Seeded generated inputs, with Fraction and urllib as independent narrow oracles."""

from __future__ import annotations

import random
from decimal import Decimal, localcontext
from fractions import Fraction
from urllib.parse import quote, unquote, urlsplit

import pytest

from geouri import GeoURIError, build, build_android_query, compare, parse, parse_android


@pytest.mark.parametrize("seed", [5870, 20261101, 431])
def test_hostile_text_has_only_documented_errors(seed: int) -> None:
    rng = random.Random(seed)
    alphabet = "geo:GEO0123456789-,.;=u?zq%+#& ()\x00\n\ud800\u00e9\U0001f30d"
    for _ in range(2000):
        text = rng.choice(["", "geo:", "geo:1,2;", "geo:0,0?q="])
        text += "".join(rng.choices(alphabet, k=rng.randrange(100)))
        for parser in (parse, parse_android):
            try:
                result = parser(text)
            except GeoURIError as error:
                assert len(str(error)) < 150
            else:
                if parser is parse:
                    assert parse(str(result)) == result


@pytest.mark.parametrize("seed", [5870, 20261101, 431])
def test_generated_coordinates_match_fraction_and_round_trip(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(1000):
        lat = Decimal(rng.randrange(-900_000, 900_001)) / 10_000
        lon = Decimal(rng.randrange(-1_800_000, 1_800_001)) / 10_000
        alt = Decimal(rng.randrange(-100_000, 100_001)) / 100
        value = "".join(rng.choices("abc +/%;=\u00e9\U0001f30d", k=12))
        with localcontext() as context:
            context.prec = 2
            text = build(lat, lon, alt=alt, u=0, params={"x": value, "flag": None})
        uri = parse(text)
        coordinates = text[4:].split(";")[0].split(",")
        assert Fraction(coordinates[0]) == Fraction(lat)
        assert Fraction(coordinates[1]) == (
            0 if abs(lat) == 90 else abs(lon) if lon == -180 else lon
        )
        assert Fraction(coordinates[2]) == Fraction(alt)
        assert uri.params == {"x": value, "flag": None}
        assert compare(uri, parse(str(uri))) is True
        assert hash(uri) == hash(parse(str(uri)))
        encoded = text.split(";x=")[1].split(";")[0]
        assert unquote(encoded, errors="strict") == value


def test_android_encoding_matches_standard_library() -> None:
    rng = random.Random(814)
    for _ in range(2000):
        text = "street " + "".join(rng.choices("ab+ &%/=()\u00e9\U0001f30d", k=30))
        built = build_android_query(text, zoom=23)
        assert built == "geo:0,0?q=" + quote(text, safe="") + "&z=23"
        assert parse_android(built).query == text


def test_generic_url_split_does_not_validate_coordinates() -> None:
    assert urlsplit("geo:94,0").path == "94,0"
    with pytest.raises(GeoURIError):
        parse("geo:94,0")


@pytest.mark.parametrize("size", [10_000, 100_000])
def test_large_parameter_and_query_inputs_round_trip(size: int) -> None:
    text = "x" * size
    assert parse(build(1, 2, params={"x": text})).params["x"] == text
    assert parse_android(build_android_query(text)).query == text
    params = {f"x{i}": None for i in range(size // 10)}
    assert parse(build(1, 2, params=params)).params == params
