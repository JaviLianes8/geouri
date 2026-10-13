"""The public API is typed: mypy infers the documented types and rejects wrong ones."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
from geouri import GeoURIError, build, compare, parse, parse_android
uri = parse("geo:1,2")
reveal_type(uri.lat)
reveal_type(uri.alt)
reveal_type(uri.params)
reveal_type(compare(uri, uri))
reveal_type(build(1, 2))
reveal_type(parse_android("geo:1,2").zoom)
reveal_type(GeoURIError("zoom").reason)
GeoURIError("no-such-reason")
build(1, 2, 3)
parse(b"geo:1,2")
uri.lat = 1.0
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    )
    return str(out) + str(err)


def test_fields_have_their_documented_types(mypy_output: str) -> None:
    assert _revealed(mypy_output, 4) == "float"
    assert _revealed(mypy_output, 5) == "float | None"
    assert _revealed(mypy_output, 6) == "typing.Mapping[str, str | None]"


def test_functions_return_their_documented_types(mypy_output: str) -> None:
    assert _revealed(mypy_output, 7) == "bool | None"
    assert _revealed(mypy_output, 8) == "str"
    assert _revealed(mypy_output, 9) == "int | None"


def test_reasons_are_a_closed_set(mypy_output: str) -> None:
    assert "'latitude-range'" in _revealed(mypy_output, 10)
    assert re.search(r"snippet\.py:11: error: .*\[arg-type\]", mypy_output), mypy_output


def test_misuse_is_rejected(mypy_output: str) -> None:
    assert re.search(r"snippet\.py:12: error: Too many positional arguments", mypy_output)
    assert re.search(r"snippet\.py:13: error: .*\[arg-type\]", mypy_output)
    assert re.search(r"snippet\.py:14: error: .*\[misc\]", mypy_output)


def _revealed(output: str, line: int) -> str:
    match = re.search(rf"snippet\.py:{line}: note: Revealed type is \"(.+)\"", output)
    assert match, output
    # Older mypy releases spell builtins with their module prefix.
    return match.group(1).replace("builtins.", "")
