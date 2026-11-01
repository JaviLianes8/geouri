"""Hand-written contracts for decoder failures, codec identity and stream ownership."""

from __future__ import annotations

import io
import json

import pytest
from test_cli_encoding import _run

from geouri._cli import main


@pytest.mark.parametrize("args", [[], ["--json"], ["--android"]])
@pytest.mark.parametrize("encoding", ["utf-16", "utf-32"])
@pytest.mark.parametrize("prefix", [b"", b"\xff\xff\xff\xff", b"ABCD"])
def test_stdin_without_valid_bom_stops_with_bounded_diagnostic(
    args: list[str], encoding: str, prefix: bytes
) -> None:
    data = prefix + "geo:1,2\ngeo:3,4\n".encode(f"{encoding}-le")
    result = _run(args, data, encoding)
    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr.decode(encoding).splitlines() == ["invalid (encoding)"]


@pytest.mark.parametrize(
    ("encoding", "data", "status", "output", "errors"),
    [
        ("utf-8", b"geo:1,2\n", 0, "geo:1,2\n", ""),
        ("utf-8", b"\xff\ngeo:1,2\n", 1, "geo:1,2\n", "invalid (encoding)\n"),
        ("utf-16", b"ABCD", 1, "", "invalid (encoding)\n"),
    ],
)
def test_stdin_remains_open_and_reusable_by_caller(
    encoding: str, data: bytes, status: int, output: str, errors: str
) -> None:
    with io.BytesIO(data) as buffer, io.TextIOWrapper(buffer, encoding=encoding) as stream:
        out, err = io.StringIO(), io.StringIO()
        assert main([], stdin=stream, stdout=out, stderr=err) == status
        assert (out.getvalue(), err.getvalue()) == (output, errors)
        assert not stream.closed
        assert not buffer.closed
        buffer.seek(0)
        assert buffer.read() == data
        stream.seek(0)
        stream.truncate()
        stream.write("geo:3,4\n")
        stream.flush()
        stream.seek(0)
        assert stream.read() == "geo:3,4\n"


def test_cp1252_stdin_preserves_euro_query() -> None:
    result = _run(["--android"], b"geo:0,0?q=\x80\n", "cp1252")
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    assert json.loads(result.stdout.decode("cp1252"))["query"] == "\u20ac"
