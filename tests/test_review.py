"""Regressions for the independent review: exactness, pickling, round trips, JSON."""

from __future__ import annotations

import copy
import io
import json
import pickle
from decimal import Decimal, localcontext

import pytest

from geouri import (
    GeoURIError,
    build,
    build_android,
    build_android_query,
    parse,
    parse_android,
)
from geouri._cli import main

LONG = "12.345678901234567890123456789012345678901"


def test_more_digits_than_the_decimal_context_survive_str_and_build() -> None:
    text = f"geo:{LONG},-0.0000000000000000000000000000001"
    assert str(parse(text)) == text
    assert build(Decimal(LONG), 0) == f"geo:{LONG},0"
    assert parse("geo:1.0000000000000000000000000000001,0") != parse("geo:1,0")


def test_a_low_precision_context_changes_nothing() -> None:
    with localcontext() as context:
        context.prec = 3
        assert str(parse("geo:12.3456,0,1234567")) == "geo:12.3456,0,1234567"
        assert parse("geo:89.9999,10") != parse("geo:89.9999,20")


def test_a_latitude_just_below_the_pole_is_not_a_pole() -> None:
    near = "geo:89.99999999999999999999999999999"
    assert parse(f"{near},10") != parse(f"{near},20")
    assert str(parse(f"{near},10")) == f"{near},10"


def test_date_line_prints_one_canonical_form() -> None:
    assert str(parse("geo:10,-180")) == str(parse("geo:10,180")) == "geo:10,180"
    assert str(parse("geo:10,-180;crs=other")) == "geo:10,-180;crs=other"


def test_models_pickle_and_deep_copy_exactly() -> None:
    uri = parse(f"geo:{LONG},2,3;u=4;a=b;f")
    for clone in (pickle.loads(pickle.dumps(uri)), copy.deepcopy(uri), copy.copy(uri)):
        assert clone == uri
        assert str(clone) == str(uri)
    geo = parse_android("geo:0,0?q=1,2(Home)&z=5&x=y")
    assert pickle.loads(pickle.dumps(geo)) == geo
    assert copy.deepcopy(geo).extras["x"] == "y"


def test_android_extras_are_read_only_even_when_built_directly() -> None:
    extras = {"a": "b"}
    geo = parse_android("geo:1,2")
    built = type(geo)(geo.point, extras=extras)
    extras["a"] = "changed"
    assert built.extras["a"] == "b"
    with pytest.raises(TypeError):
        built.extras["a"] = "c"  # type: ignore[index]


@pytest.mark.parametrize("text", ["100,200", "090,1", "1,2(x", "caf\u00e9, 12", "a+b&c=d"])
def test_search_text_round_trips(text: str) -> None:
    assert parse_android(build_android_query(text)).query == text


@pytest.mark.parametrize("text", ["48.85,2.35", "1,2(Home)", "-90,180()"])
def test_search_text_that_reads_as_a_pin_is_refused(text: str) -> None:
    with pytest.raises(GeoURIError) as caught:
        build_android_query(text)
    assert caught.value.reason == "query"


def test_pin_with_label_round_trips() -> None:
    geo = parse_android(build_android(-12.5, 170, label="x(1)", zoom=23))
    assert (geo.pin, geo.label, geo.zoom) == (parse("geo:-12.5,170"), "x(1)", 23)


def test_wrong_types_raise_type_error() -> None:
    with pytest.raises(TypeError):
        build_android_query(5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build_android(1, 2, label=5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build(1, 2, crs=5)  # type: ignore[arg-type]


def test_json_numbers_are_exact_and_finite() -> None:
    out = io.StringIO()
    huge = "1" + "0" * 400
    code = main(["--json", f"geo:{huge},{LONG};crs=foo"], stdout=out, stderr=io.StringIO())
    assert code == 0
    text = out.getvalue()
    assert "Infinity" not in text
    assert f'"lat": {huge}, "lon": {LONG}' in text
    assert json.loads(text, parse_float=Decimal)["lon"] == Decimal(LONG)
