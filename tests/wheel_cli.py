"""Installed CLI encoding checks shared by wheel and sdist consumers."""

from __future__ import annotations

import json
import os
import subprocess
from decimal import Decimal
from pathlib import Path


def check_encoding(python: Path, script: Path, work: Path) -> None:
    number = "1.123456789012345678901"
    for command in ([str(python), "-m", "geouri"], [str(script)]):
        _check_stdin(command, work)
        _check_bom_errors(command, work)
        _check_cp1252_euro(command, work)
        for android in (False, True):
            uri = f"geo:{number},2;name=%E6%9D%B1%E4%BA%AC"
            if android:
                uri += "?q=%E6%9D%B1%E4%BA%AC"
            result = subprocess.run(
                [*command, "--android" if android else "--json", uri],
                cwd=work,
                env={**os.environ, "PYTHONPATH": "", "PYTHONIOENCODING": "cp1252:strict"},
                capture_output=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stderr
            assert result.stderr == b""
            data = json.loads(result.stdout.decode("ascii"), parse_float=Decimal)
            point = data["point"] if android else data
            assert point["lat"] == Decimal(number)
            assert point["params"] == {"name": "\u6771\u4eac"}
            if android:
                assert data["query"] == "\u6771\u4eac"


def _check_stdin(command: list[str], work: Path) -> None:
    for encoding in ("utf-8", "utf-16-le", "utf-16", "utf-32-le", "cp1252"):
        for ending in ("\n", "\r", "\r\n"):
            text = ending.join(["geo:1,2", "geo:0,0?q=caf\u00e9", "geo:3,4", ""])
            result = subprocess.run(
                [*command, "--android"],
                input=text.encode(encoding),
                cwd=work,
                env={**os.environ, "PYTHONPATH": "", "PYTHONIOENCODING": f"{encoding}:strict"},
                capture_output=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stderr
            assert result.stderr == b""
            records = [json.loads(line) for line in result.stdout.decode(encoding).splitlines()]
            assert [r["point"]["uri"] for r in records] == ["geo:1,2", "geo:0,0", "geo:3,4"]
            assert [r["query"] for r in records] == [None, "caf\u00e9", None]


def _check_bom_errors(command: list[str], work: Path) -> None:
    for encoding in ("utf-16", "utf-32"):
        for prefix in (b"", b"\xff\xff\xff\xff", b"ABCD"):
            result = subprocess.run(
                command,
                input=prefix + "geo:1,2\ngeo:3,4\n".encode(f"{encoding}-le"),
                cwd=work,
                env={**os.environ, "PYTHONPATH": "", "PYTHONIOENCODING": f"{encoding}:strict"},
                capture_output=True,
                timeout=30,
            )
            assert result.returncode == 1
            assert result.stdout == b""
            assert result.stderr.decode(encoding).splitlines() == ["invalid (encoding)"]


def _check_cp1252_euro(command: list[str], work: Path) -> None:
    result = subprocess.run(
        [*command, "--android"],
        input=b"geo:0,0?q=\x80\n",
        cwd=work,
        env={**os.environ, "PYTHONPATH": "", "PYTHONIOENCODING": "cp1252:strict"},
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    assert json.loads(result.stdout.decode("cp1252"))["query"] == "\u20ac"
