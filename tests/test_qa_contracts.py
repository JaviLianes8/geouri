"""Hand-written contracts for comparison, model storage and serialization."""

from __future__ import annotations

import copy
import pickle

import pytest

from geouri import GeoURI, GeoURIError, build_android, compare, parse, parse_android


@pytest.mark.parametrize("suffix", ["", ";y=1", ";x=1;y=2"])
def test_unknown_parameter_name_differences_are_undefined(suffix: str) -> None:
    left, right = parse("geo:1,2;x=1"), parse("geo:1,2" + suffix)
    assert compare(left, right) is None
    assert compare(right, left) is None
    assert left != right
    assert compare(left, parse("geo:3,4" + suffix)) is False


@pytest.mark.parametrize("suffix", [";x=1;x=1", ";x=1;x=2", ";flag;flag", ";X=1;x=1"])
def test_repeated_extensions_follow_the_documented_mapping_restriction(suffix: str) -> None:
    with pytest.raises(GeoURIError) as caught:
        parse("geo:1,2" + suffix)
    assert caught.value.reason == "duplicate-param"


@pytest.mark.parametrize("key", ["\ud800", "\udfff", "x\ud800y"])
def test_android_query_keys_must_be_encodable_as_utf8(key: str) -> None:
    with pytest.raises(GeoURIError) as caught:
        parse_android(f"geo:0,0?{key}=x")
    assert caught.value.reason == "query"
    assert key not in str(caught.value)


def test_parameter_string_subclasses_are_stored_as_plain_strings() -> None:
    class Text(str):
        __eq__ = str.__eq__

        def __str__(self) -> str:
            return "different display"

    model = GeoURI(1, 2, params={"x": Text("value")})
    ordinary = GeoURI(1, 2, params={"x": "value"})
    assert model == ordinary
    assert str(model) == "geo:1,2;x=value"
    assert hash(model) == hash(ordinary)
    assert type(model.params["x"]) is str


@pytest.mark.parametrize("message", ["", "detail", "a\nb"])
def test_error_args_preserve_the_complete_message_through_pickle(message: str) -> None:
    error = GeoURIError("query", message) if message else GeoURIError("query")
    assert error.args == ("query", message)
    clone = pickle.loads(pickle.dumps(error))
    assert clone.args == ("query", message)
    assert (clone.reason, clone.message) == ("query", message)


def test_non_default_crs_survives_pickle_and_copies() -> None:
    text = "geo:1000.123456789012345678901,2000,3;crs=local;u=4;x=value"
    model = parse(text)
    for clone in (pickle.loads(pickle.dumps(model)), copy.copy(model), copy.deepcopy(model)):
        assert clone.crs == "local"
        assert str(clone) == text
        assert clone == model
        assert hash(clone) == hash(model)


@pytest.mark.parametrize("label", ["a\nb", "a\r\nb", "\n"])
def test_android_newline_labels_remain_pins(label: str) -> None:
    geo = parse_android(build_android(1, 2, label=label))
    assert geo.pin == parse("geo:1,2")
    assert geo.label == label
    assert geo.query is None


def test_android_percent_encoded_newline_label_is_a_pin() -> None:
    geo = parse_android("geo:0,0?q=1,2(a%0Ab)")
    assert geo.pin == parse("geo:1,2")
    assert geo.label == "a\nb"
    assert geo.query is None
