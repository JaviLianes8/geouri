"""Public documentation, stable signatures and resource contracts."""

from __future__ import annotations

import doctest
import importlib
import inspect
import io
import typing
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

import geouri
from geouri import GeoURIError, build, build_android, compare, parse, parse_android
from geouri._cli import main


def test_only_declared_public_names_are_exposed() -> None:
    assert sorted(name for name in vars(geouri) if not name.startswith("_")) == sorted(
        geouri.__all__
    )


def test_public_docstrings_and_guide_examples_run() -> None:
    modules = {getattr(geouri, name).__module__ for name in geouri.__all__ if name != "Reason"}
    attempted = 0
    for name in modules:
        failed, count = doctest.testmod(importlib.import_module(name), raise_on_error=True)
        assert failed == 0
        attempted += count
    assert attempted >= 20
    for name in geouri.__all__:
        assert ">>>" in (getattr(geouri, name).__doc__ or "")
    runner = doctest.DocTestRunner()
    example = doctest.DocTestParser().get_doctest(
        geouri.Reason.__doc__ or "", {}, "Reason", None, 0
    )
    runner.run(example)
    assert runner.failures == 0 and runner.tries == 3
    guide = Path(__file__).resolve().parents[1] / "GUIDE.md"
    failed, count = doctest.testfile(str(guide), module_relative=False)
    assert failed == 0 and count >= 7


def test_functions_keep_their_parameter_names_and_defaults() -> None:
    expected = {
        "parse": ["uri"],
        "parse_android": ["uri"],
        "compare": ["a", "b"],
        "build": ["lat", "lon", "alt", "u", "crs", "params"],
        "build_android": ["lat", "lon", "zoom", "label"],
        "build_android_query": ["query", "zoom"],
    }
    for name, names in expected.items():
        function = getattr(geouri, name)
        params = inspect.signature(function).parameters
        assert list(params) == names
        for param in params.values():
            if param.name in {"alt", "u", "crs", "params", "zoom", "label"}:
                assert param.kind == inspect.Parameter.KEYWORD_ONLY
                assert param.default is None
        assert typing.get_type_hints(function)


@pytest.mark.parametrize("wrong", [None, "geo:1,2", 1, object()])
def test_compare_refuses_wrong_types(wrong: object) -> None:
    with pytest.raises(TypeError):
        compare(wrong, parse("geo:1,2"))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        compare(parse("geo:1,2"), wrong)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "call",
    [
        lambda: parse("secret" * 20_000),
        lambda: parse("geo:1,2;secret=%zz"),
        lambda: parse("geo:1,2;secret=x;secret=x"),
        lambda: parse_android("geo:1,2?secret=x&secret=y"),
        lambda: parse_android("geo:1,2?q=%FFsecret"),
        lambda: build(1, 2, params={"secret": "\ud800secret"}),
        lambda: build(1, 2, params={"secret": object()}),  # type: ignore[dict-item]
    ],
)
def test_generated_diagnostics_omit_input(call: Callable[[], object]) -> None:
    with pytest.raises((GeoURIError, TypeError)) as caught:
        call()
    assert "secret" not in str(caught.value)
    assert "secret" not in repr(caught.value.args)
    assert len(str(caught.value)) < 150


def test_cli_diagnostics_never_echo_inputs_or_unknown_options() -> None:
    for args, status in [(["--secret" * 10_000], 2), (["geo:1,2;secret=%zz"], 1)]:
        err = io.StringIO()
        assert main(args, stdout=io.StringIO(), stderr=err) == status
        assert "secret" not in err.getvalue()
        assert len(err.getvalue()) < 200


def test_numeric_budgets_reject_before_expansion() -> None:
    for value in (Decimal("1e10000"), Decimal("1e-10000"), 10**10000, 10**100_000):
        with pytest.raises(GeoURIError) as caught:
            build(value, 0, crs="custom")
        assert caught.value.reason == "number"
    with pytest.raises(GeoURIError) as caught:
        parse("geo:0,0," + "0" * 10_001)
    assert caught.value.reason == "number"
    assert str(parse("geo:0,0," + "0" * 10_000)) == "geo:0,0,0"
    assert build(Decimal("0e999999999"), 0) == "geo:0,0"
    assert build(Decimal("1e9999"), 0, crs="x") == "geo:" + "1" + "0" * 9999 + ",0;crs=x"


def test_built_numbers_at_the_budget_boundary_parse_back() -> None:
    for value in (Decimal("1e-9997"), Decimal("-1e-9997"), Decimal("-1e9998")):
        text = build(value, 0, crs="x")
        assert str(parse(text)) == text
    for value in (Decimal("1e-9999"), Decimal("-1e9999")):
        with pytest.raises(GeoURIError) as caught:
            build(value, 0, crs="x")
        assert caught.value.reason == "number"


def test_huge_zoom_is_a_typed_error() -> None:
    with pytest.raises(GeoURIError) as caught:
        build_android(1, 2, zoom=10**5000)
    assert caught.value.reason == "zoom"


def test_readme_links_are_absolute() -> None:
    import re

    text = (Path(__file__).resolve().parents[1] / "README.md").read_text("utf-8")
    assert all(link.startswith("https://") for link in re.findall(r"\]\(([^)]+)\)", text))
