"""Hand-written subprocess contracts for batch input and portable JSON output."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from geouri._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def _run(
    args: list[str], data: bytes = b"", encoding: str = "utf-8"
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-B", "-m", "geouri", *args],
        input=data,
        capture_output=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": f"{encoding}:strict"},
    )


@pytest.mark.parametrize("android", [False, True])
@pytest.mark.parametrize(
    "bad", [b"\xff", b"\xe6\x9d", b"\xff" * 10000], ids=["invalid", "truncated", "long"]
)
def test_malformed_stdin_lines_do_not_drop_valid_batch_lines(android: bool, bad: bytes) -> None:
    result = _run(["--android"] if android else [], b"geo:1,2\r\n" + bad + b"\ngeo:3,4\n")
    assert result.returncode == 1
    assert result.stderr.decode("ascii").splitlines() == ["invalid (encoding)"]
    lines = result.stdout.decode("ascii").splitlines()
    if android:
        assert [json.loads(line)["point"]["uri"] for line in lines] == ["geo:1,2", "geo:3,4"]
    else:
        assert lines == ["geo:1,2", "geo:3,4"]


@pytest.mark.parametrize("encoding", ["ascii", "cp1252"])
@pytest.mark.parametrize("android", [False, True])
def test_json_unicode_strings_and_keys_are_ascii_safe_and_numbers_exact(
    encoding: str, android: bool
) -> None:
    number = "1.123456789012345678901"
    uri = f"geo:{number},2;name=%E6%9D%B1%E4%BA%AC"
    if android:
        uri += "?\u6771\u4eac=%E6%9D%B1%E4%BA%AC&q=1,2(%E6%9D%B1%E4%BA%AC)"
    result = _run(["--android" if android else "--json", uri], encoding=encoding)
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    data = json.loads(result.stdout.decode("ascii"), parse_float=Decimal)
    point = data["point"] if android else data
    assert point["lat"] == Decimal(number)
    assert point["params"] == {"name": "\u6771\u4eac"}
    if android:
        assert data["extras"] == {"\u6771\u4eac": "\u6771\u4eac"}
        assert data["label"] == "\u6771\u4eac"


def test_cli_rejects_surrogate_query_keys_with_a_bounded_diagnostic() -> None:
    output = io.BytesIO()
    stream = io.TextIOWrapper(output, encoding="utf-8", errors="strict")
    errors = io.StringIO()
    assert main(["--android", "geo:0,0?\ud800=x"], stdout=stream, stderr=errors) == 1
    stream.flush()
    assert output.getvalue() == b""
    assert errors.getvalue() == "invalid (query)\n"


def test_whitespace_only_stdin_is_rejected_while_empty_lines_are_skipped() -> None:
    result = _run([], b"\n \n\t\r\ngeo:1,2\n")
    assert result.returncode == 1
    assert result.stdout.decode("ascii").splitlines() == ["geo:1,2"]
    assert result.stderr.decode("ascii").splitlines() == ["invalid (scheme)"] * 2
