from __future__ import annotations

import pickle
import typing

import pytest

from geouri import GeoURIError, Reason, parse


def test_reason_and_message_are_kept() -> None:
    error = GeoURIError("zoom", "too far")
    assert (error.reason, error.message, str(error)) == ("zoom", "too far", "zoom: too far")


def test_a_bare_reason_prints_alone() -> None:
    assert str(GeoURIError("query")) == "query"


def test_errors_survive_pickling() -> None:
    with pytest.raises(GeoURIError) as caught:
        parse("geo:95,0")
    copy = pickle.loads(pickle.dumps(caught.value))
    assert (copy.reason, copy.message) == ("latitude-range", caught.value.message)


def test_is_a_value_error() -> None:
    assert issubclass(GeoURIError, ValueError)


def test_reasons_are_unique() -> None:
    reasons = typing.get_args(Reason)
    assert len(set(reasons)) == len(reasons) == 14
