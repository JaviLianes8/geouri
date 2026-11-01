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


@pytest.mark.parametrize("args", [[], ["--json"], ["--android"]])
@pytest.mark.parametrize("encoding", ["utf-16", "utf-32"])
def test_unrecoverable_large_batch_stops_after_one_diagnostic(
    args: list[str], encoding: str
) -> None:
    data = ("geo:1,2\n" * 2048).encode(f"{encoding}-le")
    result = _run(args, data, encoding)
    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr.decode(encoding).splitlines() == ["invalid (encoding)"]


@pytest.mark.parametrize("query", [b"\xff", b"Main\xffStreet", b"MainStreet\xff"])
def test_embedded_decode_error_keeps_encoding_diagnostic(query: bytes) -> None:
    result = _run(["--android"], b"geo:1,2\ngeo:0,0?q=" + query + b"\ngeo:3,4\n")
    assert result.returncode == 1
    assert result.stderr.decode("utf-8").splitlines() == ["invalid (encoding)"]
    records = [json.loads(line) for line in result.stdout.decode("utf-8").splitlines()]
    assert [record["point"]["uri"] for record in records] == ["geo:1,2", "geo:3,4"]
    assert [record["query"] for record in records] == [None, None]


@pytest.mark.parametrize("encoding", ["utf-8", "cp1252", "utf-16"])
def test_stdin_preserves_query_case(encoding: str) -> None:
    data = "geo:0,0?q=Main+Street\ngeo:1,2;name=Blue?q=1,2(Town+Hall)\n".encode(encoding)
    result = _run(["--android"], data, encoding)
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    records = [json.loads(line) for line in result.stdout.decode(encoding).splitlines()]
    assert len(records) == 2
    assert records[0]["query"] == "Main Street"
    assert records[1]["label"] == "Town Hall"
    assert records[1]["point"]["params"] == {"name": "Blue"}


@pytest.mark.parametrize("args", [[], ["--json"], ["--android"]])
def test_duplicate_stdin_records_preserve_count_and_order(args: list[str]) -> None:
    expected = ["geo:3,4", "geo:1,2", "geo:1,2", "geo:5,6", "geo:1,2"]
    result = _run(args, ("\n".join(expected) + "\n").encode())
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    assert _output_uris(result.stdout, args) == expected


@pytest.mark.parametrize("args", [[], ["--json"], ["--android"]])
def test_each_malformed_stdin_record_has_one_diagnostic(args: list[str]) -> None:
    data = b"geo:3,4\n\xff\ngeo:1,2\n\xff\xff\ngeo:5,6\n\xff\n"
    result = _run(args, data)
    assert result.returncode == 1
    assert result.stderr.decode().splitlines() == ["invalid (encoding)"] * 3
    assert _output_uris(result.stdout, args) == ["geo:3,4", "geo:1,2", "geo:5,6"]


@pytest.mark.parametrize("query", ["Main\tStreet", " Main\t\tStreet ", "\tMain Street\t"])
def test_stdin_preserves_query_whitespace(query: str) -> None:
    result = _run(["--android"], f"geo:0,0?q={query}\n".encode())
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    records = [json.loads(line) for line in result.stdout.decode().splitlines()]
    assert len(records) == 1
    assert records[0]["query"] == query


def _output_uris(output: bytes, args: list[str]) -> list[str]:
    lines = output.decode().splitlines()
    if not args:
        return lines
    records = [json.loads(line) for line in lines]
    if args == ["--android"]:
        return [record["point"]["uri"] for record in records]
    return [record["uri"] for record in records]
